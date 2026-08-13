#!/usr/bin/env python3
"""Apply the labels that can be derived from the org project to open issues.

Two rules, both strictly additive (see AGENTS.md):

1. The system label implied by the item's `Scraper (Morph)` field, but only when the
   issue carries no system label at all. An issue whose label already disagrees with its
   scraper field is a migration in progress and must be left alone.
2. `ready awaiting budget` when the item's `Status` is `Budget wait`.

Candidates are then filtered against each issue's timeline: if a label has ever been
removed from an issue, it is never re-applied. That check runs over candidates only, not
over every project item.

Nothing is ever removed. Standard library only -- no pip install on the runner.

Usage: GH_TOKEN=... label_from_project.py [--dry-run]
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ORG = "planningalerts-scrapers"
REPO = "planningalerts-scrapers/issues"
PROJECT_NUMBER = 3
BUDGET_STATUS = "Budget wait"
BUDGET_LABEL = "ready awaiting budget"
MORPH_PREFIX = "https://morph.io/planningalerts-scrapers/"

CONFIG_PATH = Path(__file__).resolve().parent.parent / "scraper-labels.json"
API = "https://api.github.com"

PROJECT_QUERY = """
query($org: String!, $number: Int!, $cursor: String) {
  organization(login: $org) {
    projectV2(number: $number) {
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          content {
            __typename
            ... on Issue {
              number
              state
              repository { nameWithOwner }
              labels(first: 50) { nodes { name } }
            }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
    }
  }
}
"""

REMOVED_LABELS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      timelineItems(itemTypes: [UNLABELED_EVENT], first: 100) {
        nodes { ... on UnlabeledEvent { label { name } } }
      }
    }
  }
}
"""


def request(url, token, data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "planningalerts-scrapers-issue-labeller",
        },
    )
    with urllib.request.urlopen(req) as response:
        body = response.read()
    return json.loads(body) if body else {}


def graphql(token, query, **variables):
    result = request(f"{API}/graphql", token, {"query": query, "variables": variables})
    if "errors" in result:
        raise RuntimeError(f"GraphQL error: {result['errors']}")
    return result["data"]


def project_items(token):
    """Yield (issue_number, labels, fields) for every open issue in this repo."""
    cursor = None
    total = 0
    while True:
        page = graphql(token, PROJECT_QUERY, org=ORG, number=PROJECT_NUMBER, cursor=cursor)
        items = page["organization"]["projectV2"]["items"]
        for item in items["nodes"]:
            total += 1
            content = item["content"] or {}
            if content.get("__typename") != "Issue":
                continue
            if content["state"] != "OPEN":
                continue
            if content["repository"]["nameWithOwner"] != REPO:
                continue
            fields = {}
            for value in item["fieldValues"]["nodes"]:
                name = (value.get("field") or {}).get("name")
                if name:
                    fields[name] = value.get("text") or value.get("name")
            labels = {label["name"] for label in content["labels"]["nodes"]}
            yield content["number"], labels, fields
        if not items["pageInfo"]["hasNextPage"]:
            break
        cursor = items["pageInfo"]["endCursor"]
    print(f"Read {total} items from project #{PROJECT_NUMBER}.")


def scraper_slug(field_value):
    """The morph.io scraper slug, or None if the field isn't a morph.io URL for this org.

    A few items point at planningalerts.org.au instead, and some URLs have a trailing
    slash.
    """
    if not field_value or not field_value.startswith(MORPH_PREFIX):
        return None
    return field_value[len(MORPH_PREFIX) :].strip("/") or None


def candidates(token, config):
    scraper_labels = config["scraper_labels"]
    system_labels = set(config["system_labels"])
    found = []
    for number, labels, fields in project_items(token):
        if not labels & system_labels:
            label = scraper_labels.get(scraper_slug(fields.get("Scraper (Morph)")))
            if label:
                found.append((number, label, "system label from Scraper (Morph)"))
        if fields.get("Status") == BUDGET_STATUS and BUDGET_LABEL not in labels:
            found.append((number, BUDGET_LABEL, f"Status is {BUDGET_STATUS}"))
    return found


def previously_removed(token, numbers):
    """{issue_number: {labels ever removed}} -- queried for candidates only."""
    owner, name = REPO.split("/")
    removed = {}
    for number in sorted(numbers):
        data = graphql(token, REMOVED_LABELS_QUERY, owner=owner, name=name, number=number)
        events = data["repository"]["issue"]["timelineItems"]["nodes"]
        removed[number] = {event["label"]["name"] for event in events}
    return removed


def add_label(token, number, label):
    request(f"{API}/repos/{REPO}/issues/{number}/labels", token, {"labels": [label]})


def summarise(lines):
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as handle:
            handle.write("\n".join(lines) + "\n")


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set.")

    config = json.loads(CONFIG_PATH.read_text())
    proposed = candidates(token, config)
    removed = previously_removed(token, {number for number, _, _ in proposed})

    applied, vetoed = [], []
    for number, label, reason in proposed:
        if label in removed[number]:
            vetoed.append((number, label))
            continue
        if not dry_run:
            add_label(token, number, label)
        applied.append((number, label, reason))

    verb = "Would add" if dry_run else "Added"
    lines = [f"### {verb} {len(applied)} label(s)"]
    lines += [f"- #{number} `{label}` -- {reason}" for number, label, reason in applied] or [
        "- nothing to do"
    ]
    if vetoed:
        lines.append("")
        lines.append(f"Skipped {len(vetoed)} previously removed label(s):")
        lines += [f"- #{number} `{label}`" for number, label in vetoed]

    report = "\n".join(lines)
    print(report)
    summarise(lines)


if __name__ == "__main__":
    main()
