<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Plan to Issues

> You have a plan — a 50-task modernization file with phases and milestones, a hand-written
> `ROADMAP.md`, or just a conversation you finished five minutes ago. Either way it is not in the
> tracker, and until it is, nobody works from it. This skill moves it in: one labelled issue per
> task, one epic on top, and the epic's body maps every issue back to the task it came from.
>
> **No plan file required.** Talk through what needs doing, then run
> `/plan-to-issues --from-conversation`; it drafts the task list, shows it to you, and files it
> once you say yes.

It writes to your issue tracker, not to your code. No source file is modified.

## What you get

| Artifact | Contents |
|---|---|
| **One epic issue** | Whole-effort acceptance criteria (the plan's milestones) plus a live dashboard: every child issue grouped by phase, per-phase progress bars, milestone status, critical path, and what's actionable right now |
| **One issue per task** | Written by `/issue-creator` — normalized template, acceptance criteria, the plan text preserved verbatim as reporter context — bound to the epic with `Part of #N` |
| **A label scheme** | `phase:p0`, `dim:dep`, `priority:high`, `bug`/`improvement`/`feature` — derived by rule from the plan, so you can filter the backlog by phase, dimension, or urgency |

## The dashboard

The epic body renders like this, and `sync` refreshes it from live issue states:

```markdown
## Implementation Dashboard

**Progress:** 12/50 closed ██░░░░░░░░ 24% · **Last synced:** 2026-08-26

| Phase | Progress | Milestone | Status |
|---|---|---|---|
| Pre Agent environment | 3/3 ██████████ 100% | ME — CLAUDE.md and AGENTS.md exist | ✅ met |
| P0 Stabilize | 4/6 ███████░░░ 67% | M0 — baseline-green reproducible in CI | ◐ in progress |
| P1 Secure & Patch | 0/11 ░░░░░░░░░░ 0% | M1 — zero High/Critical advisories | ○ not started |

### P0 — Stabilize · 4/6 ███████░░░ 67%

- [x] #104 — 0.1 Commit the lockfile and restore the build
- [ ] #108 — 0.5 Add the CI workflow  ·  depends on #104, #107

**Critical path:** #101 ✅ → #102 ✅ → #104 ✅ → #118 ○
**Next actionable** — open, every dependency closed: #105, #106, #107
```

## Usage

```bash
/plan-to-issues                        # find the plan, file everything, build the epic
/plan-to-issues docs/PLAN.md           # explicit plan path
/plan-to-issues --dry-run              # preview the issue table and dashboard, create nothing
/plan-to-issues --phase P0,P1          # file only these phases (others show as "not filed")
/plan-to-issues sync 100               # refresh epic #100's dashboard from live issue states
```

Typical flow:

```text
/codebase-modernizer   →  MODERNIZATION_REPORT.md + MODERNIZATION_PLAN.md
/plan-to-issues        →  epic #100 + 50 labelled issues
/issue-resolver 104    →  atomic PR closing #104
/plan-to-issues sync 100  →  dashboard shows P0 at 5/6
```

## Requirements

Checked in a preflight gate before anything is filed — the run either has everything or has not
started. Missing pieces are reported together, each with its exact install command.

- `git` and a GitHub remote
- The GitHub CLI `gh`, **ready** — not just installed. Preflight checks that you're authenticated as
  the account you expect (it asks when two are logged in), that the token has the `repo` scope, that
  the repo has issues enabled and isn't archived, that you have write access, that the target repo is
  unambiguous when there are several remotes, and that your API budget covers the run
- Python 3 for the dashboard renderer (stdlib only)
- The **`issue-creator`** skill — it writes every issue body:

  ```bash
  npm install -g agent-skill-manager                                        # asm itself
  asm install https://github.com/luongnv89/idd --skill issue-creator        # the skill
  asm list | grep issue-creator                                             # verify
  ```

- `/codebase-modernizer` only if you don't have a plan yet:
  `asm install github:luongnv89/skills:skills/codebase-modernizer`

## Design notes

- **Re-running is safe.** A plan task that already has an issue under the epic is skipped, not
  duplicated. If a batch dies halfway through a rate limit, re-run it.
- **It never edits an epic it didn't write.** The dashboard sits between HTML sentinels; `sync`
  refuses to touch an issue that has none.
- **It never reads your source code.** Everything in every issue traces to a line of the plan. That
  keeps the issues honest about being intent, not stale analysis.
- **Deferred findings get no issues.** The plan deferred them on purpose; they appear in the
  dashboard as a table so the decision stays visible.

## Related skills

| Skill | Relationship |
|---|---|
| `/codebase-modernizer` | Produces the plan this skill consumes |
| `/tasks-generator` | Produces PRD-derived plans in the same task format — also accepted |
| `/issue-creator` | Writes every issue body; required |
| `/issue-triage`, `/issue-resolver`, `/auto-pilot` | What you run next, against the backlog this skill files |
