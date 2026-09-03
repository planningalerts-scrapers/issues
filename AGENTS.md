# AGENTS.md

Guidance for AI coding agents working anywhere in the `planningalerts-scrapers`
org. `CLAUDE.md` in this repo points here so the guidance lives in one place, and
every scraper repo carries a stub `AGENTS.md` that fetches this file. So most
agents reading it are working in a scraper repo rather than in this one.

Read all of it. Section 1 explains where the work comes from, section 2 how to do
it in a scraper repo, and section 3 the conventions that apply in either place.
Nothing here is inherited from `openaustralia/.github`: planningalerts-scrapers
is a separate org with its own contributors, so everything an agent needs is
stated in this file.

## 1. The tracker

### What this repo is

This repo contains **no scraper code**. It is a tracker: one issue per
PlanningAlerts authority that has stopped returning data, covering every scraper
in the org.

Issues are centralised here rather than kept in each scraper's own repo because
authorities migrate between systems. When a council moves from, say, ePathway to
Development.i, the fix spans two scraper repos plus a change to the PlanningAlerts
authority record. A single issue can hold that whole story; three issues in three
repos cannot.

Issues are opened from the PlanningAlerts side and currently appear under
`@mlandauer` (there is an open issue to change this to a service user).

### Where the real data is

Almost nothing useful lives in the issue body. The body is boilerplate. The
context is in the org project,
[PlanningAlerts authorities with no new data](https://github.com/orgs/planningalerts-scrapers/projects/3),
and in the labels.

Project fields worth reading:

| Field | What it tells you |
| --- | --- |
| `Authority` | The council's name as PlanningAlerts knows it |
| `Scraper (Morph)` | **The scraper currently pointed at this authority**, see below |
| `Authority admin (PA)` | Direct link to the authority record in PlanningAlerts admin |
| `Website` | The council's own site |
| `No data received since` | When the data stopped |
| `State`, `Population` | Jurisdiction and rough priority |
| `Status` | Blocked / Todo / In Progress / Budget wait / Review / Done |

Project fields are populated after the issue is created, so a freshly opened
issue may briefly have none of them. A handful of older issues were never added
to the project at all.

### Finding the repo to work in

`Scraper (Morph)` gives a morph.io URL. The code is the matching GitHub repo:

```
https://morph.io/planningalerts-scrapers/multiple_greenlight
                                          └─────────┬────────┘
https://github.com/planningalerts-scrapers/multiple_greenlight
```

A `multiple_*` slug is a **multi-authority scraper**: the authority is one entry
in that repo's configuration, and adding or removing a council means editing that
config, not writing new code. Any other slug is a **single-authority scraper**
written just for that council.

### The label leads, the Scraper field lags

The system label (`epathway`, `greenlight`, `development-i`, and so on) records
the system the authority **is on now**. The `Scraper (Morph)` field records the
scraper **still pointed at it**. When an authority migrates, the label changes
first and the field only changes once the work is done.

So the two disagreeing is not an error. It is the signal that the authority has
moved and the scraper needs to follow. **Never "correct" a label to match the
`Scraper (Morph)` field.** A minority of open issues are in this state
deliberately.

### Worked example

[#1391 Gold Coast City Council](https://github.com/planningalerts-scrapers/issues/issues/1391).
Read together, the tags and fields say what the job is:

- `Scraper (Morph)` = `multiple_epathway_scraper`, the repo currently
  responsible, so that is where the failure shows up and where you look first.
- Label `development-i`, the system Gold Coast has **moved to**. The destination
  repo is therefore
  [`multiple_developmenti`](https://github.com/planningalerts-scrapers/multiple_developmenti).
- Label `new authority for existing scraper`: extend an existing multi-scraper's
  config, do not write a new scraper.
- Label `reported`: someone outside the team reported it, and there is a
  `Missive conversation:` comment on the issue.

Which resolves to work in **two** scraper repos, adding Gold Coast to
`multiple_developmenti` and removing the dead authority from
`multiple_epathway_scraper`, plus repointing the PlanningAlerts authority record
from one morph scraper to the other. That last step is in neither repo: see
"Where your work ends".

### Labels

**System**, which platform the authority is on:
`masterview`, `greenlight`, `epathway`, `icon`, `technology one`, `horizon`,
`civica`, `nsw planning portal`, `ATDIS`, `development-i`, `ci-anywhere`,
`html table`, `div_card`, `ePlanning`, `planbuild (tas)`, `granicus`,
`elementorg`, `DxP T1`, `custom`

**Cause**, why the data stopped:
`anti scraping technology`, `cloudflare`, `blocked by ip`,
`blocked by authority`, `does not publish`, `no da tracking site`, `site in flux`

**Effort and state**:
`quick fix`, `extended effort`, `stuck - need help`, `ready awaiting budget`,
`new scraper needed`, `new authority for existing scraper`, `probably fixed`

**Process**:
`reported`, `waiting callback`, `compare data`, `research`,
`council website good`, `council website bad`

`compare data` means the scraper's output was checked against the council's own
site before and after the change. What that involves is in section 2.

### The `reported` convention

An issue gets `reported` when a comment beginning exactly `Missive conversation:`
is added. Someone outside the team told us this was broken, and that link is the
thread.

Outbound correspondence does **not** count. Comments like
`Missive conversation (email to council):`, `Email sent:` or
`Email to local council:` are us contacting them, not them reporting to us, and
deliberately do not trigger the label.

Those threads are members of the public who emailed OAF, and these issues are
public. Link the thread. Never paste the reporter's name, email address, street
address, or the text of their message into an issue, a comment or a pull request.

### Automation

Two workflows keep the mechanical parts of the labelling current. Both are
**add-only** and neither ever removes a label.

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `.github/workflows/label-reported.yml` | A comment is posted | Adds `reported` when the comment starts with `Missive conversation:` |
| `.github/workflows/label-from-project.yml` | Daily, or manually | Adds the system label implied by `Scraper (Morph)`, and `ready awaiting budget` when Status is `Budget wait`. **Does nothing until the `planningalerts-bot` secrets described in the workflow are configured** |

The slug-to-label mapping lives in `.github/scraper-labels.json`, so adding a new
multi-scraper means editing that file, not the script.

Three rules constrain both:

1. **Never overwrite a system label.** If an issue already carries one, the
   scraper-derived label is skipped. This is what protects the migration cases
   above.
2. **A removed label is permanent.** If a label has ever been taken off an issue,
   the automation will not put it back. Removing a label is how you tell the bot
   to stop applying it. The veto is per label, so removing `epathway` from an
   issue does not stop a later, correct `greenlight` from being added.
3. **Single-authority scrapers get no system label.** Whether a bespoke scraper
   counts as `custom` is a judgement call, so the automation leaves it alone.

## 2. Working in a scraper repo

### Find the default branch first

Default branches vary across the org: older repos use `master`, newer ones
`main`. Never assume.

    git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|^origin/||'

If that prints nothing the clone has no recorded head, so run
`git remote set-head origin -a` first. With only the GitHub CLI available:

    gh repo view <owner>/<repo> --json defaultBranchRef -q .defaultBranchRef.name

### Running a scraper

Most scrapers are Ruby, pinned to 3.2.2, and run with:

    bundle exec ruby scraper.rb

Success is the count line at the end, `Finished - added N records`. The output is
a SQLite database that morph.io collects.

Not every repo is Ruby. There are scrapers in Node and in PHP, and some older
Ruby ones predate bundler and have no Gemfile. The repo's own README is
authoritative for the run command, and nearly every repo has one.

### Verifying output

Running without an error proves the scraper ran, not that the data is right. A
scraper that cheerfully saves malformed records is worse than one that fails
loudly, because those records reach a public service.

Before opening a pull request:

- Check the record count is plausible against what the council's own site shows.
- Spot-check a few addresses, dates and description fields against the source
  pages they came from.
- For a `multiple_*` config change, confirm the newly added authority returns
  records and that the others still do.
- Run the checks the repo actually has: `ruby -c scraper.rb` always,
  `bundle exec rubocop` if there is a `.rubocop.yml`, and `bundle exec rspec`
  only if the repo has a `spec/` directory. Most do not.

That comparison is what the `compare data` label refers to. Say what you checked
in the pull request description.

Almost no scraper repo has CI, so these local checks are the only gate before a
change reaches production. Never describe a change as tested on the basis that
GitHub Actions is green: in most of these repos there is nothing running.

### Repo conventions

- A scraper that builds on morph.io needs a `platform` file containing exactly
  `heroku-18`, newline-terminated. Morph uses it to pick the build stack, so a
  Ruby upgrade without it is broken. This is the single most common review
  rejection. Repos that are not morph-built Ruby scrapers, and the older
  pre-bundler ones, do not carry it.
- Match the conventions in
  [`ianheggie-oaf/example_ruby_scraper`](https://github.com/ianheggie-oaf/example_ruby_scraper):
  a README.md (morph.io boilerplate, a link back to this issues repo, run
  instructions, expected output), an explicit `Finished - added N records` line
  at the end of `scraper.rb`, a `.rubocop.yml` with `NewCops` and
  `TargetRubyVersion`, an expanded `.gitignore`, and the morph.io comment header
  in the `Gemfile`.
- Stricter `.rubocop.yml` settings routinely surface autocorrectable offences in
  older scrapers. Fix those in their own commit, separate from the change you
  came to make.

### Review

Every repo's `.github/CODEOWNERS` names the
`@planningalerts-scrapers/scraper-reviewers` team, and GitHub requests that team
automatically. **Do not request reviewers by hand.**

That request only fires when a pull request is marked ready for review. Code
owners are deliberately not requested on drafts, so a draft with no reviewer on
it is normal and not a fault. Once a pull request is out of draft and still has
nobody requested, that repo's CODEOWNERS is missing or the team has lost write
access to it. GitHub silently ignores a CODEOWNERS naming a team without access
rather than reporting an error, so fix the cause instead of assigning someone
manually.

In practice `ianheggie-oaf` reviews most scraper pull requests. Two things follow:

- A `CHANGES_REQUESTED` review blocks merging. After addressing feedback,
  re-request review from the team. Pushing new commits alone does not re-request
  it.
- He sometimes fixes and tests a pull request on his own fork
  (`ianheggie-oaf/<scraper>`) and says so in the review. When he has, cherry-pick
  his commits with authorship preserved rather than re-implementing them. His
  versions are already verified on morph.io.

### Where your work ends

**Do not merge.** Merging to the default branch is a deploy: morph.io runs
whatever is on it, against a live council website, feeding a public service. With
no CI and a review team that is not always available, that is a judgement call
about production, and it belongs to the human driving the change.

**Do not close these issues.** Most fixes also need the PlanningAlerts authority
record repointed at the new scraper, and that record lives in the PlanningAlerts
admin, outside every repo in this org. An issue closed while the authority record
still points at a dead scraper is worse than an open one, because this tracker is
the only place that knowledge lives.

So an agent's work ends at a reviewed pull request, plus a comment on the issue
saying what changed and what still needs doing on the PlanningAlerts side.

## 3. Conventions for any repo in this org

Follow the org
[CONTRIBUTING.md](https://github.com/planningalerts-scrapers/.github/blob/main/CONTRIBUTING.md).
The points that matter most for agents:

- Branch names carry a type prefix, an issue number and a short description:
  `chore/123-short-description`, `bugfix/890-fix-pagination`.
- Open pull requests as drafts while they are still in progress, and assign them
  to the human driving the change, never to the agent. Taking one out of draft is
  that person's call.
- Fill in the pull request template. It is synced from `openaustralia/.github` and
  not every checkbox applies here, so leave inapplicable ones unticked rather than
  ticking them untruthfully. "Confirmed it passed the GitHub actions tests" is not
  something most of these repos can satisfy.
- Every commit ends with an `Assisted-by: <agent>:<model-id>` trailer naming the
  agent and model actually used, for example
  `Assisted-by: Claude Code:claude-opus-4-6` or
  `Assisted-by: OpenCode:anthropic.claude-fable-5`. Report the model actually
  running, not a remembered default.
- Make each commit a single logical change. Do not bundle a fix, a typo and a
  dependency bump together just because they came from the same session.
- Do not hard-wrap prose in pull request descriptions, issue bodies, issue
  comments or review comments. GitHub renders each newline in those fields as a
  line break, so text wrapped at a column width comes out ragged. Write one
  paragraph per line, however long, whether passed via `--body`, `--body-file`, a
  heredoc, or typed into the web UI. Hard-wrapping markdown files committed to a
  repo is a different matter and stays fine.
- Never commit real personal details or credentials. Use fictional placeholders
  in examples and test data: the Australian Privacy Principles apply here as much
  as anywhere. If you need one fact from a file that plausibly holds live
  credentials, grep for that line rather than reading the whole file.
- When leaving a review comment, give the actual replacement code rather than
  describing the change, but only when there are no remaining decisions to make,
  it replaces just one section, and it is not much longer than the description
  would be. Otherwise describe it in prose as usual.
- If this file contradicts what you consistently see in the code, flag the
  mismatch and ask which needs fixing rather than silently trusting either.

### Voice

- Australian English.
- No em dashes. Use a hyphen, a comma or a full stop.
- Non-partisan. Nothing written in these repos should imply that OAF endorses or
  opposes any party, candidate or position. Report what a council or portal does
  neutrally. `council website bad` is a label about a site's scrapability, not a
  judgement to repeat in prose.

## Maintaining this file

Every scraper repo carries a stub `AGENTS.md`, plus a `CLAUDE.md` importing it,
that points back here. This file is the single source of truth for org-wide agent
guidance: update it here, not in the scraper repos. The stubs deliberately carry
no guidance of their own, and name no section and no version, so that they never
need updating and agents always read the current version of this file.
