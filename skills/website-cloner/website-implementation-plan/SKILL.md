---
name: website-implementation-plan
description: "Generate phased tasks.md from an approved website PRD, with landing page first, measurable tasks, and collect/create asset tracking. Use for implementation planning. Don't use for coding, design review, unapproved PRDs, or direct deployment."
license: MIT
effort: high
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Website Implementation Plan

Turns an approved improvement proposal (prd.md) into a phased implementation plan. Landing page first, then deeper pages. Asset collection vs. creation tracked. Writes `tasks.md` after approval.

## When to Use

Trigger when the user asks to:
- Plan the implementation of a website improvement proposal
- Break down a PRD into phased tasks
- Create an implementation plan for a site rebuild

Do **not** use for building or coding — that is Phase 5 (website-builder).

## Repo Sync Before Edits (mandatory)

The approved `tasks.md` is persisted with `Write`. When that output path lives inside a git worktree, sync before the write to avoid clobbering remote work:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash → sync → pop. If `origin` is missing or a conflict occurs: **stop and ask the user.** Skip this section only when the output path is outside any git repository.

## Workflow

```
1. Read the approved prd.md
2. Identify phases: landing page first, then deeper content
3. For each task: define scope, outputs, acceptance criteria
4. Track assets: collect from original vs. create new
5. Assemble into tasks.md
6. Present for review
7. Incorporate edits (loop until approved)
8. Persist tasks.md
```

## Output: tasks.md Structure

Use the tasks.md template below as the only output template. Read only the PRD sections needed for the current phase to preserve the context budget.

```markdown
# Implementation Plan: <site name>
**Source PRD:** prd.md
**Date:** <date>

---

## Overview

Brief summary of the implementation approach and phase ordering rationale.

## Phase 1: Landing Page

The landing/home page is built first so it can be shown to potential users early.

### Task 1.1: Project Setup

**Scope:** Initialize Vite + React + shadcn/ui + Tailwind CSS project. Configure build, base-aware routing/assets, and deterministic GitHub Actions Pages artifact deployment.

**Outputs:** Working project scaffold, base-aware Vite configuration, and `.github/workflows/deploy-pages.yml`.

**Acceptance Criteria:**
- `npm run dev` starts a local dev server
- `npm run build` produces `dist/index.html`
- `vite.config.*` consumes `VITE_BASE_PATH`; the workflow sets `/` for user/organization Pages and `/<repo>/` for project Pages
- Internal routes and public assets resolve under the configured base; the selected SPA route strategy has a direct-refresh check
- The Pages workflow runs `npm ci` and `npm run build`, uploads exactly `dist/` with `actions/upload-pages-artifact`, and deploys it with `actions/deploy-pages`
- Pages source is GitHub Actions, never repository-root, `/docs`, or branch-folder publishing

**Assets Needed:**
- [Collect] Logo, brand colors, brand name from original site
- [Create] Project repository on GitHub

### Task 1.2: Landing Page Layout

**Scope:** Build the hero section, nav, CTA, and footer based on the improvement proposal. Implement the improved layout, not a clone.

**Outputs:** Landing page component with improved structure.

**Acceptance Criteria:**
- Hero section with clear headline, subtext, primary CTA above the fold
- Responsive layout (mobile + desktop)
- Navigation matches the improved structure

**Assets Needed:**
- [Collect] Hero imagery, copy text, brand colors
- [Create] New CTA copy (if improvement proposes different messaging)

---

## Phase 2: Core Pages

Deeper pages beyond the landing page.

### Task 2.1: <Page Name>

**Scope:** ...
**Outputs:** ...
**Acceptance Criteria:** ...
**Assets Needed:**
- [Collect] ...
- [Create] ...

---

Repeat for each task across phases.

## Phase 3: Optimization and Polish

Performance, SEO, and security improvements from the PRD.

### Task 3.1: Performance Optimization

**Scope:** Image optimization, lazy loading, code splitting, font optimization.

**Acceptance Criteria:**
- LCP ≤ target (from prd.md metrics table)
- CLS ≤ target
- Page weight ≤ target

### Task 3.2: SEO Implementation

**Scope:** Meta tags, structured data, heading structure, alt text, canonical URLs.

**Acceptance Criteria:**
- SEO score ≥ target
- All pages have title, meta description, structured data

### Task 3.3: Security Hardening

**Scope:** HTTPS enforcement, security headers, mixed content fixes.

**Acceptance Criteria:**
- All resources loaded over HTTPS
- Key security headers present

## Asset Summary

| Asset | Source | Action |
|-------|--------|--------|
| Logo | Original site | Collect |
| Brand colors | Original site | Collect |
| Hero image | Original site | Collect |
| CTA copy | Improvement proposal | Create |
| New icons | Generated | Create |

## Deployment

1. Include `package-lock.json`, base-aware `vite.config.*`, and `.github/workflows/deploy-pages.yml` in the implementation tasks.
2. Push the approved project to the default branch and configure Repository Settings → Pages → Source as **GitHub Actions**.
3. Require the workflow to build and verify `dist/index.html`, upload exactly `dist/` as the Pages artifact, and deploy that artifact.
4. Verify project Pages at `https://<user>.github.io/<repo>/`; for a `<user>.github.io` repository, verify the root URL instead.

---

*This plan is derived from the approved improvement proposal. Actual task scope may need adjustment during implementation.*
```

## Step 1: Read prd.md

```
Read file <path-to-prd.md>
```

If missing, ask for the path. The orchestrator should have produced this in Phase 3.

## Step 2: Define Phases

Structure phases so something usable ships early:

| Phase | Focus | Rationale |
|-------|-------|-----------|
| Phase 1 | Landing/home page | Usable immediately, can be shown to users |
| Phase 2 | Core pages | About, features, contact, etc. |
| Phase 3 | Optimization | Performance, SEO, security polish |
| Phase 4 (optional) | Extra features | Nice-to-have improvements |

Phase 1 **must** produce an independently usable landing page.

## Step 3: Define Tasks

For each task:
- **Scope**: Clear, bounded description of what to build
- **Outputs**: Concrete deliverables
- **Acceptance Criteria**: Measurable pass/fail conditions
- **Assets Needed**: Distinguish `[Collect]` from `[Create]`

Tasks should be small enough for a single implementation cycle.

## Step 4: Asset Tracking

For every asset referenced in the plan:
- Mark as **[Collect]** if it exists on the original site (logos, images, copy, colors)
- Mark as **[Create]** if it needs to be newly produced (new icons, rewritten copy, generated images)

## Step 5: Write Draft tasks.md

Assemble using the structure above.

## Step 6: Present for Review

"Here is the implementation plan. Please:
1. **Approve** — save as tasks.md
2. **Edit** — specify changes
3. **Regenerate** — start over"

## Step 7: Incorporate Edits (loop)

If edits requested: update, re-present, repeat until approved.

Do **not** persist until explicit approval.

## Step 8: Persist tasks.md

Persist the assembled content using the `Write` tool with literal content only. If the `Write` tool is unavailable, stop with a descriptive error and do not use shell persistence or another output path.

Default: `$PROJECT_DIR/tasks.md` or `~/workspace/clones/YYYY_MM_DD_slug/tasks.md`.

If `$ARGUMENTS` includes `--output <path>`, use that.

Confirm:

```
tasks.md saved to: <absolute-path>
STATUS: approved
```

## Return Contract

When invoked by the `website-cloner` umbrella (Phase 4 gate), the orchestrator
gates Phase 5 on this skill's outcome. The contract:

| Outcome  | Signal                                                              |
|----------|---------------------------------------------------------------------|
| approved | `tasks.md` exists at the resolved output path AND final line of stdout reads `STATUS: approved` |
| pending  | no `tasks.md` written; final line reads `STATUS: pending` (user still iterating) |
| aborted  | no `tasks.md` written; final line reads `STATUS: aborted` (user declined) |

The orchestrator MUST NOT advance to Phase 5 unless the outcome is `approved`.
A standalone invocation may ignore the status line, but the file-existence rule
still holds: no approval, no `tasks.md`.

## Acceptance Criteria and Expected Output

Verify the complete plan before requesting approval:

- Every in-scope PRD requirement maps to at least one numbered task or an explicitly justified exclusion.
- Phase 1 produces an independently usable landing page; later phases preserve dependency order.
- Every task has bounded scope, concrete outputs, measurable acceptance criteria, and all required assets classified as `[Collect]` or `[Create]`.
- Project setup includes the artifact-based Pages workflow, deterministic Vite base-path behavior, and route/asset checks; no plan publishes Vite output from repository root or `/docs`.
- Asset Summary contains every asset named by a task exactly once with a source and action.
- The expected result is valid markdown at the approved path plus exactly one final `STATUS: approved`; pending or aborted outcomes write no file.

## Step Completion Report

```text
◆ Implementation Plan
··································································
  Approved PRD:         √ pass | × fail ([reason])
  Landing page first:  √ pass
  Tasks measurable:    √ pass ([count])
  Assets classified:   √ pass ([collect]/[create])
  User approved:       √ pass | × pending
  tasks.md saved:      √ pass ([absolute path]) | — not approved
  Result:              PASS | BLOCKED | FAIL
```

Report `PASS` only when the return contract's file and final status-line conditions both hold.

## Edge Cases and Error Handling

| Failure | Behavior |
|---|---|
| No prd.md provided | Ask for the PRD file path |
| Invalid PRD format | Report error and ask for valid file |
| Conflicting PRD requirements | Surface the conflict and ask before task decomposition |
| No assets required | Include an empty Asset Summary and state that no collection or creation is needed |
| User never approves | Keep looping; do not auto-save |
