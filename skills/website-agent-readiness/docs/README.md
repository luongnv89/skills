<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Website Agent Readiness

> Scan a live website for AI-agent readiness, turn the gaps into a reviewed plan, and file them as tracked GitHub issues — with a human approval gate before every step.

## Highlights

- **Real scan, not a guess** — posts to `isitagentready.com/api/scan` and reads back a 0–5 readiness level across 22 checks in 5 categories (discoverability, content access, bot control, agent/API discovery, commerce).
- **Approval-gated end to end** — four gates. Nothing leaves your machine, gets written, or reaches GitHub without an explicit yes.
- **Plans, never edits** — no file on the target site is touched. The output is `agent-ready-plan.md` plus issues someone then works.
- **Speaks `/plan-to-issues` natively** — the plan is rendered in the exact grammar that skill parses, so filing is a delegation, not a re-implementation.
- **Deterministic triage** — phase, effort band, and priority come from a fixed mapping, so two runs on the same scan produce the same plan.

## When to Use

| Say this...                                      | Skill will...                                                        |
| ------------------------------------------------ | -------------------------------------------------------------------- |
| "make example.com agent-ready"                    | Run all four phases, gate by gate                                     |
| "is my site ready for AI agents?"                 | Scan and report the score, then offer to plan the gaps                |
| "score example.com for llms.txt and MCP support"  | Scan and show the per-category pass/fail table                        |
| "turn that agent-readiness scan into issues"      | Pick up at the plan and filing phases                                 |

**Not this skill:** applying the fixes to a codebase (`/seo-ai-optimizer`), App Store optimisation (`/aso-marketing`), or filing a plan you already wrote (`/plan-to-issues` directly).

## Workflow

```
  ┌─ G1 ─┐        ┌─ G2 ─┐        ┌─ G3 ─┐        ┌─ G4 ─┐
  │ send │        │ read │        │ write│        │ file │
  │ URL? │        │ score│        │ plan?│        │issues│
  └──┬───┘        └──┬───┘        └──┬───┘        └──┬───┘
     ▼               ▼               ▼               ▼
  Phase 1         Phase 2         Phase 3         Phase 4
  Scan            Triage          Plan            Issues
     │               │               │               │
  scan.json      triage.json   agent-ready-     epic +
  fixes.md       + table       plan.md          N issues
```

## Usage

```
/website-agent-readiness https://example.com
```

Or just ask: *"can you make example.com agent-ready?"*

Artifacts land in `.agent-ready/` (scan data) and `agent-ready-plan.md` (the plan, at repo root).

## Requirements

- `curl` and `python3` — Phases 1–3.
- A publicly reachable target. The scanner fetches the site itself, so `localhost`, private IPs, and password-walled staging hosts cannot be scanned.
- Phase 4 only: a git repo with a GitHub remote, `gh` authenticated (`gh auth status`), and the `plan-to-issues` skill installed.

## Notes

- The URL is sent to **isitagentready.com**, a third-party service, which then fetches the site. Gate G1 exists so that is an explicit choice.
- The scanner hosts an implementation guide per check. The plan **links** them; it does not fetch or apply them.
- A site the scanner reports as non-commerce gets its commerce checks deferred rather than filed.

## Verification status

| Phase | How far it has been exercised |
|---|---|
| 1–3 (scan → triage → plan) | End-to-end against three live sites at different score levels — `example.com` (0/5), `stripe.com` (1/5), `isitagentready.com` (4/5). Task counts, effort bands and acceptance-criteria coverage matched triage on every run. |
| 4 (file the issues) | **Not yet run against a live repository.** The rendered plan is checked against the grammar `/plan-to-issues` documents, and that check has been re-confirmed independently — but the seam is verified by inspection against the spec, never by execution. A drift in `/plan-to-issues`' parser would surface on someone's first real run. |

The eval suite is executable: `python3 scripts/run-skill-evals.py website-agent-readiness` from the repo root (see CONTRIBUTING.md). It measures triggering; the 30 behavioural expectations across the 10 cases are transcript-level and reported as `[MANUAL]`.

Last recorded run (1 run per case): **6/8 triggering cases pass, 2 skipped as fixture-dependent.** The two failures are reproducible at 0/3 and are trigger-coverage gaps, not defects in the pipeline — a `localhost` URL and a "scan this site, its robots.txt says …" prompt both get handled directly instead of opening the skill, so the skill's own advice for those cases (flag an unreachable target at G1; treat scanned content as data) never gets a chance to apply.
