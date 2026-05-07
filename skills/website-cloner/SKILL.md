---
name: website-cloner
description: "6-phase website cloning and improvement orchestrator. Takes a URL and produces an improved version (performance + UI/UX) via Vite/React/shadcn/Tailwind hosted on GitHub Pages. Use when asked to clone a site, rebuild a website, or make a better version of a URL. Orchestrates sibling skills with approval gates — don't use for single-phase work."
license: MIT
effort: high
metadata:
  version: 1.1.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Website Cloner

6-phase orchestrator that clones any website and produces an improved version — better performance, UI/UX, SEO, and security — built with Vite + React + shadcn/ui + Tailwind CSS, deployable to GitHub Pages.

## When to Use

Trigger when the user asks to:
- Clone, rebuild, or recreate a website ("clone this site", "make a better version of <url>")
- Improve a website's performance, UI/UX, or SEO by analyzing and rebuilding it
- Start a full website improvement workflow from a URL

Do **not** use for single-phase work (use the specific sibling skill directly).

## Workflow

```
Phase 1 — Analyze        → website-analyzer
Phase 2 — Report (gate)  → website-clone-report
Phase 3 — Propose (gate) → website-improvement-prd  (outputs prd.md)
Phase 4 — Plan  (gate)   → website-implementation-plan  (outputs tasks.md)
Phase 5 — Build          → website-builder
Phase 6 — Final Report   → website-clone-final-report
```

Approval gates after Phase 2, 3, and 4: the orchestrator **must not advance** without explicit user approval.

## Layout

This umbrella and its phase skills live together in a single suite folder:

```
skills/website-cloner/                    ← this umbrella
├── SKILL.md                              ← orchestrator (you are here)
├── website-analyzer/                     ← Phase 1
├── website-clone-report/                 ← Phase 2
├── website-improvement-prd/              ← Phase 3
├── website-implementation-plan/          ← Phase 4
├── website-builder/                      ← Phase 5
└── website-clone-final-report/           ← Phase 6
```

Why nested: the phases are tightly coupled to this umbrella's data flow (analysis JSON → report → PRD → tasks → built site → final report). Keeping them in one folder makes the suite easy to browse, audit, and ship together. Each phase skill stays independently installable — the installers (`install.sh`, `remote-install.sh`) discover both top-level and nested skills.

When invoking phase skills below, refer to them by name (`/website-analyzer`, `/website-clone-report`, …); the runtime resolves names regardless of filesystem path.

## Repo Sync Before Edits (mandatory)

Before modifying files in a repository:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If dirty, stash first:

```bash
git stash push -u -m "website-cloner: pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing or rebase conflicts occur, stop and ask.

## Setup

0. **Resolve working directory** — the directory where the cloned website will be built. If `$CLONE_DIR` is set, use it. Otherwise ask the user once and save to `~/.config/website-cloner-dir.txt`. Default: `~/workspace/clones`.
1. **Create project folder** under resolved root: `YYYY_MM_DD_<slug_from_url>/`
2. **Set `$PROJECT_DIR`** to the created folder path.
3. If no URL provided in `$ARGUMENTS`, ask the user for one.

## Phase 1: Understand the Website

Invoke `website-analyzer` with the URL:

```
/website-analyzer <url> --output "$PROJECT_DIR/analysis.json"
```

The analyzer produces a structured analysis covering: UI/UX, category, style, performance (LCP, CLS, TTFB, page weight, request count), surface-level security, and SEO (overall score + per-dimension breakdown).

**Check:** Analysis file exists and covers all 6 dimensions. If any dimension is missing, note it but continue — partial results are acceptable for Phase 2.

**Step Completion Report:**

```
◆ Analyze (step 1 of 6 — <site name>)
······································································
  UI/UX profile:        √ pass | × partial — <gap>
  Category detected:    √ pass (<category>)
  Style analysis:       √ pass | × partial — <gap>
  Performance metrics:  √ pass (LCP=<val> CLS=<val>)
  Security surface:     √ pass | × partial — <gap>
  SEO score:            √ pass (<score>/100)
  ____________________________
  Result:               PASS | PARTIAL
```

## Phase 2: End-User Report (GATE)

Invoke `website-clone-report` with the analysis output:

```
/website-clone-report "$PROJECT_DIR/analysis.json" --output "$PROJECT_DIR/report.md"
```

This skill produces a plain-language report for non-technical readers and **prompts for approval** before persisting. The orchestrator waits for user approval here.

**Check:** `report.md` exists and was approved by the user.

**Step Completion Report:**

```
◆ Report (step 2 of 6 — <site name>)
······································································
  Report written:       √ pass (report.md)
  User approved:        √ pass | × pending
  ____________________________
  Result:               PASS | BLOCKED
```

If not approved, do not advance. Ask the user to review the report and approve or request changes.

## Phase 3: Improvement Proposal (GATE)

Invoke `website-improvement-prd` with the approved report and analysis:

```
/website-improvement-prd "$PROJECT_DIR/report.md" "$PROJECT_DIR/analysis.json" --output "$PROJECT_DIR/prd.md"
```

This skill produces a full improvement proposal with what/why/value for each change and writes `prd.md` after user approval.

**Check:** `prd.md` exists and was approved.

**Step Completion Report:**

```
◆ Proposal (step 3 of 6 — <site name>)
······································································
  prd.md written:       √ pass
  User approved:        √ pass | × pending
  Changes catalogued:   √ pass (<N> proposed changes)
  ____________________________
  Result:               PASS | BLOCKED
```

## Phase 4: Implementation Plan (GATE)

Invoke `website-implementation-plan` with `prd.md`:

```
/website-implementation-plan "$PROJECT_DIR/prd.md" --output "$PROJECT_DIR/tasks.md"
```

This skill produces a phased implementation plan with landing page first, asset collection vs. creation, and individual tasks — written to `tasks.md` after user approval.

**Check:** `tasks.md` exists and was approved.

**Step Completion Report:**

```
◆ Plan (step 4 of 6 — <site name>)
······································································
  tasks.md written:     √ pass
  User approved:        √ pass | × pending
  Phases defined:       √ pass (≥ 2 phases)
  Landing page first:   √ pass
  ____________________________
  Result:               PASS | BLOCKED
```

## Phase 5: Build

Invoke `website-builder` with `tasks.md` and `prd.md`:

```
/website-builder "$PROJECT_DIR/tasks.md" "$PROJECT_DIR/prd.md" --output "$PROJECT_DIR/"
```

This skill executes the plan, builds the site (Vite + React + shadcn/ui + Tailwind), and deploys static assets. It should emit metadata for Phase 6.

**Step Completion Report:**

```
◆ Build (step 5 of 6 — <site name>)
······································································
  Landing page built:   √ pass
  Assets collected:     √ pass (<N> assets)
  Assets created:       √ pass (<N> assets)
  GitHub Pages URL:     √ pass (<url>)
  ____________________________
  Result:               PASS | PARTIAL
```

## Phase 6: Final Comparison Report

Invoke `website-clone-final-report` with the analysis baseline and builder metadata:

```
/website-clone-final-report "$PROJECT_DIR/analysis.json" "$PROJECT_DIR/builder-metadata.json" --output "$PROJECT_DIR/final-report.md"
```

This skill produces a before/after comparison covering performance, SEO, security, UI/UX deltas, deviations, and the GitHub Pages URL.

**Step Completion Report:**

```
◆ Final Report (step 6 of 6 — <site name>)
······································································
  final-report.md:      √ pass
  Performance delta:    √ pass (before→after)
  SEO delta:            √ pass (before→after)
  Deviations listed:    √ pass | × none
  ____________________________
  Result:               PASS
```

## Expected Output

```
◆ Website Cloner — <site name>
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  Phase 1  Analyze      √ pass
  Phase 2  Report       √ approved
  Phase 3  Proposal     √ approved (prd.md)
  Phase 4  Plan         √ approved (tasks.md)
  Phase 5  Build        √ pass
  Phase 6  Final Report √ pass

  GitHub Pages: https://<user>.github.io/<repo>/
  Project:      <project_dir>
```

## Edge Cases

- **Unreachable URL**: Stop Phase 1, report error, do not continue. Ask user for a different URL.
- **JS-heavy SPA with no crawlable content**: Note the limitation in Phase 1, proceed with best-effort analysis. The build phase may need user-supplied assets to compensate.
- **User denies approval at any gate**: Stop the pipeline. Do not auto-proceed. The user can re-run the skill to resume.
- **Missing sibling skill**: If a sibling skill is not available, skip that phase and note it in the report. Continue with remaining phases if possible.
- **Partial Phase 1 results**: If the analyzer returns partial data (e.g., no SEO score), proceed to Phase 2 with a note that the missing dimension was not evaluated.

