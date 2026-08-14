# AGENTS.md

Guidance for agents working in `planningalerts-scrapers/issues`.

## What this repo is

This repo contains **no scraper code**. It is a tracker: one issue per PlanningAlerts
authority that has stopped returning data, covering every scraper in the org.

Issues are centralised here rather than kept in each scraper's own repo because
authorities migrate between systems. When a council moves from, say, ePathway to
Development.i, the fix spans two scraper repos plus a change to the PlanningAlerts
authority record. A single issue can hold that whole story; three issues in three repos
cannot.

Issues are opened from the PlanningAlerts side and currently appear under `@mlandauer` (there is an open issue to change this to a service user).

## Where the real data is

Almost nothing useful lives in the issue body. The body is boilerplate. The context is in
the org project, [PlanningAlerts authorities with no new data](https://github.com/orgs/planningalerts-scrapers/projects/3),
and in the labels.

Project fields worth reading:

| Field | What it tells you |
| --- | --- |
| `Authority` | The council's name as PlanningAlerts knows it |
| `Scraper (Morph)` | **The scraper currently pointed at this authority** — see below |
| `Authority admin (PA)` | Direct link to the authority record in PlanningAlerts admin |
| `Website` | The council's own site |
| `No data received since` | When the data stopped |
| `State`, `Population` | Jurisdiction and rough priority |
| `Status` | Blocked / Todo / In Progress / Budget wait / Review / Done |

Project fields are populated after the issue is created, so a freshly opened issue may
briefly have none of them. A handful of older issues were never added to the project at
all.

## Finding the repo to work in

`Scraper (Morph)` gives a morph.io URL. The code is the matching GitHub repo:

```
https://morph.io/planningalerts-scrapers/multiple_greenlight
                                          └─────────┬────────┘
https://github.com/planningalerts-scrapers/multiple_greenlight
```

A `multiple_*` slug is a **multi-authority scraper**: the authority is one entry in that
repo's configuration, and adding or removing a council means editing that config, not
writing new code. Any other slug is a **single-authority scraper** written just for that
council.

## The label leads, the Scraper field lags

The system label (`epathway`, `greenlight`, `development-i`, …) records the system the
authority **is on now**. The `Scraper (Morph)` field records the scraper **still pointed at
it**. When an authority migrates, the label changes first and the field only changes once
the work is done.

So the two disagreeing is not an error — it is the signal that the authority has moved and
the scraper needs to follow. **Never "correct" a label to match the `Scraper (Morph)`
field.** Roughly one in ten open issues is in this state deliberately.

## Worked example: [#1391 Gold Coast City Council](https://github.com/planningalerts-scrapers/issues/issues/1391)

Read together, the tags and fields say what the job is:

- `Scraper (Morph)` = `multiple_epathway_scraper` → the repo currently responsible, so
  that is where the failure is showing up and where you look first.
- Label `development-i` → the system Gold Coast has **moved to**. The destination repo is
  therefore [`multiple_developmenti`](https://github.com/planningalerts-scrapers/multiple_developmenti).
- Label `new authority for existing scraper` → extend an existing multi-scraper's config.
  Do not write a new scraper.
- Label `reported` → someone outside the team cared enough to report it, and there is a
  `Missive conversation:` comment on the issue
  ([example](https://github.com/planningalerts-scrapers/issues/issues/1391#issuecomment-5247828005)).
- Project: QLD, population 625,087, no data since 2026-06-13, Status `Todo`, authority
  record at `/admin/authorities/42`.

Which resolves to work in **two** scraper repos — add Gold Coast to `multiple_developmenti`,
remove the dead authority from `multiple_epathway_scraper` — plus repointing the
PlanningAlerts authority record from one morph scraper to the other. Only then can the
issue close.

## Labels

**System** — which platform the authority is on:
`masterview`, `greenlight`, `epathway`, `icon`, `technology one`, `horizon`, `civica`,
`nsw planning portal`, `ATDIS`, `development-i`, `ci-anywhere`, `html table`, `div_card`,
`ePlanning`, `planbuild (tas)`, `granicus`, `elementorg`, `DxP T1`, `custom`

**Cause** — why the data stopped:
`anti scraping technology`, `cloudflare`, `blocked by ip`, `blocked by authority`,
`does not publish`, `no da tracking site`, `site in flux`

**Effort and state**:
`quick fix`, `extended effort`, `stuck - need help`, `ready awaiting budget`,
`new scraper needed`, `new authority for existing scraper`, `probably fixed`

**Process**:
`reported`, `waiting callback`, `compare data`, `research`, `council website good`,
`council website bad`

### The `reported` convention

An issue gets `reported` when a comment beginning exactly `Missive conversation:` is added
— someone outside the team told us this was broken, and that link is the thread.

Outbound correspondence does **not** count. Comments like
`Missive conversation (email to council):`, `Email sent:` or `Email to local council:` are
us contacting them, not them reporting to us, and deliberately do not trigger the label.

## Automation

Two workflows keep the mechanical parts of the labelling current. Both are **add-only** and
neither ever removes a label.

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `.github/workflows/label-reported.yml` | A comment is posted | Adds `reported` when the comment starts with `Missive conversation:` |
| `.github/workflows/label-from-project.yml` | Daily, or manually | Adds the system label implied by `Scraper (Morph)`, and `ready awaiting budget` when Status is `Budget wait` — **does nothing until the `planningalerts-bot` secrets described in the workflow are configured** |

The slug-to-label mapping lives in `.github/scraper-labels.json`, so adding a new
multi-scraper means editing that file, not the script.

Three rules constrain both:

1. **Never overwrite a system label.** If an issue already carries one, the scraper-derived
   label is skipped. This is what protects the migration cases described above.
2. **A removed label is permanent.** If a label has ever been taken off an issue, the
   automation will not put it back. Removing a label is how you tell the bot to stop
   applying it. The veto is per label, so removing `epathway` from an issue does not stop a
   later, correct `greenlight` from being added.
3. **Single-authority scrapers get no system label.** Whether a bespoke scraper counts as
   `custom` is a judgement call, so the automation leaves it alone.

## Working on scraper pull requests

Lessons from PR review rounds across the org's scraper repos (act#9, maribyrnong#2,
moreton_bay_qld#1, nsw_joint_regional_planning_panels#8,
nsw_office_of_liquor_gaming_and_racing#5):

- Every scraper repo needs a `platform` file containing exactly `heroku-18`
  (newline-terminated). Morph uses it to pick the build stack; a Ruby upgrade PR without
  it is broken even if CI is green. This is the single most common review rejection.
- Match the conventions in [`ianheggie-oaf/example_ruby_scraper`](https://github.com/ianheggie-oaf/example_ruby_scraper):
  a README.md (morph.io boilerplate, a link back to this issues repo, run instructions,
  expected output), an explicit `Finished - added N records` line at the end of
  `scraper.rb`, a `.rubocop.yml` with `NewCops`/`TargetRubyVersion`, an expanded
  `.gitignore`, and the morph.io comment header in the `Gemfile`.
- `ianheggie-oaf` reviews scraper PRs, and a `CHANGES_REQUESTED` review blocks merging.
  After addressing feedback, re-request review with
  `gh api repos/<owner>/<repo>/pulls/<n>/requested_reviewers -f 'reviewers[]=ianheggie-oaf'`
  — pushing new commits alone does not re-request it.
- He sometimes fixes and tests a PR on his own fork (`ianheggie-oaf/<scraper>`) and says
  so in the review. When he has, cherry-pick his commits with authorship preserved rather
  than re-implementing; his versions are already verified on morph.io.
- Default branches vary between scraper repos (`master` on older ones, `main` on newer) —
  check per repo, never assume.
- Merging to the default branch deploys: morph.io runs whatever is on it. Do not merge
  over an unresolved blocking review.
- Verify locally before pushing: `ruby -c scraper.rb`, `bundle exec rspec`,
  `bundle exec rubocop`. Stricter `.rubocop.yml` settings routinely surface autocorrectable
  offences in older scrapers.

## Conventions

- Never remove a curated label to make it match the `Scraper (Morph)` field.
- The default branch is `master`. Branch off it, and open pull requests against it. (The
  org `CONTRIBUTING.md` says `main`; this repo predates that and has not been renamed.)
- Follow the org [CONTRIBUTING.md](https://github.com/planningalerts-scrapers/.github/blob/main/CONTRIBUTING.md)
  otherwise: branch names like `chore/123-short-description`, fill in the pull request
  template, assign the pull request to yourself.
- Every commit ends with an `Assisted-by: <agent>:<model-id>` trailer naming the agent
  and model actually used, e.g. `Assisted-by: Claude Code:claude-opus-4-6` or
  `Assisted-by: OpenCode:anthropic.claude-fable-5`.
