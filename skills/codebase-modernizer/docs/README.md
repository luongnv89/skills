<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Codebase Modernizer

> For the codebase you're coming back to after six months away — or the one that's drifted through
> forty tasks with nobody watching the whole. It audits every dimension at once, then hands you a
> phased plan with sprints, milestones, and tasks you can actually check off.

It is **read-only**: no tracked file's content changes. It never upgrades a dependency, refactors a
file, installs a hook, or rewrites your docs. It writes two documents — plus, if it delegates the bug
review, that skill's own `CODE_REVIEW.md` — and every file it created is listed in the report.

## What you get

| File | Contents |
|---|---|
| `MODERNIZATION_REPORT.md` | Baseline health + every finding, severity-ranked, each citing `file:line` |
| `MODERNIZATION_PLAN.md` | Pre + P0–P4 → sprints → tasks → milestones, every task closing named findings |

## When to Use

| Say this... | You get |
|---|---|
| "Review this whole codebase and give me a plan to modernize it" | full audit + plan |
| "I haven't touched this project in a year — what needs doing?" | full audit + plan |
| "Update all the dependencies" | a classified dependency report and an upgrade-wave plan — **not** a bulk `npm update` |
| "This repo is a mess after all these tasks, help me clean it up properly" | full audit + plan |
| "Audit just the deps and test coverage" | those two dimensions, the rest marked Not Assessed |

**Not this skill:**

- Reviewing one PR or diff → `code-review`
- Turning a PRD into sprint tasks → `tasks-generator`
- A usability review on its own → `dont-make-me-think`
- Actually applying the refactors → `code-review` mode `cleanup`, run against the plan afterward

## How it works

```
Phase 0  Baseline        does it build? do tests run? what's the pass rate?  → GREEN | AMBER | RED
Phase 1  Inventory       stack, ecosystems, UI present?, repo size           → dimension worklist
Phase 2  Dimension audits  10 dimensions, parallel subagents on big repos    → evidence-cited findings
Phase 3  Report          merge, dedupe, rank                                 → MODERNIZATION_REPORT.md
Phase 4  Plan            findings → phases → sprints → tasks → milestones    → MODERNIZATION_PLAN.md
Phase 5  Validation      fresh-eyes pass: do the citations actually resolve? → corrections applied
```

### The ten dimensions

Dependency currency is this skill's own work. The other nine reuse skills already in this catalog —
but only three of them actually run during the audit.

| Dimension | During the audit | Scheduled in the plan |
|---|---|---|
| Dependency + runtime currency | **this skill** | — |
| Bugs, security, quality | runs `code-review` mode `review` | — |
| Performance | runs `code-review` mode `perf` | — |
| Usability / UI | runs `dont-make-me-think` | — |
| Readability / Clean Code | checklist scan | `code-review` mode `clean` |
| Dead code, duplication, slop | checklist scan | `code-review` mode `cleanup` |
| Test gaps | checklist scan | `test-coverage` |
| CI / pipelines | checklist scan | `devops-pipeline` |
| Secrets / vulnerabilities | checklist scan | `security-setup` |
| Docs drift | checklist scan | `doc-manager` |
| Agent environment (`CLAUDE.md`, `AGENTS.md`) | not written | `/agent-config create` or `update` (plan Pre step) |

**Why the split:** those skills *write* — they install pre-commit hooks, generate workflow files,
create test files, rewrite docs, refactor source, or write `CLAUDE.md` / `AGENTS.md`. Running one
during an audit would break the read-only promise. So the audit scans those dimensions itself, and
the plan names the exact skill to run for each task — which is more useful anyway: "Task 3.2: run
`/test-coverage` on `src/payments`" beats a finding that says coverage is low. `/agent-config` is
the same pattern for the plan's Pre step: named, never run during the audit.

## The three ideas that make the output useful

**Baseline first.** Before anything else it records whether the project builds and what fraction of
tests pass. Every task in the plan then carries "and the suite is still green" as an acceptance
criterion. That's what makes the plan *testable* instead of aspirational — and if the baseline is
RED, restoring it becomes Sprint 0 and everything else waits.

**No bulk upgrades.** Running `npm update` across a stale tree gives you a broken build and a diff
nobody can review. Instead every dependency is classified (patch / minor / major / vulnerable /
EOL / unmaintained) and sorted into **upgrade waves**: security patches first, then the patch+minor
batch, then **one major per task** with its migration guide named. When the suite goes red you know
exactly which bump did it.

**Nothing without evidence.** Every finding cites `file:line`. A dimension that can't be checked —
no UI, no tool installed, no network — is marked **Not Assessed** with the reason, never quietly
filled in with a plausible guess. The Limitations section lists every one of them.

## The plan's shape

| Phase | Goal | Milestone |
|---|---|---|
| **Pre Agent environment** | env an agent can use autonomously; create or improve `CLAUDE.md` / `AGENTS.md` | both files exist and document how to run the project |
| **P0 Stabilize** | build green, tests runnable, CI running | baseline reproducible in CI |
| **P1 Secure & Patch** | vulnerabilities closed, waves W1–W2 shipped | zero High/Critical advisories |
| **P2 Modernize** | runtime upgrade, then majors one at a time | every major current or deferred with a reason |
| **P3 Clean & Harden** | dead code, duplication, weak types, coverage | coverage target met |
| **P4 Polish** | UI/UX, performance, docs | UX findings closed, docs match code |

Tasks use the same format as `tasks-generator`, so the plan drops straight into that workflow.

## Usage

```
/codebase-modernizer
/codebase-modernizer ./path/to/repo
/codebase-modernizer audit just deps and test coverage
```

Or just describe the situation — "this codebase has been neglected for a year, give me a plan to
bring it up to date" — and the skill triggers on its own.

## Dependency scan on its own

The dependency probe is a standalone script if you only want that part:

```bash
bash scripts/dep_scan.sh /path/to/repo            # full probe
bash scripts/dep_scan.sh /path/to/repo --offline  # skip network probes
bash scripts/dep_scan.sh --help
```

It detects 14 ecosystems, runs each one's read-only `outdated` and audit commands, and reports
"Not Assessed" for anything it can't check. It installs nothing and modifies nothing.

## Notes

- Works without the Agent tool — dimensions run sequentially instead of in parallel, and the report
  discloses the reduced depth.
- On a repo over ~2000 source files it audits by subsystem in priority order and states exactly what
  it didn't scan.
- Existing report files are backed up with a timestamp before being overwritten.
- It syncs the branch with `origin` before writing (stashing first if your tree is dirty) — a
  neglected repo often has uncommitted work, and none of it gets discarded.
