---
name: website-implementation-plan
description: "Turn approved prd.md into a phased implementation plan with landing page first, asset collection vs creation, individual tasks. Writes tasks.md after user approval. Use when asked to plan website implementation, create an implementation plan, or break down a PRD into tasks. Don't use for building or coding — that's a separate phase."
license: MIT
effort: high
metadata:
  version: 1.1.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Website Implementation Plan

Turns an approved improvement proposal (prd.md) into a phased implementation plan. Landing page first, then deeper pages. Asset collection vs. creation tracked. Writes `tasks.md` after approval.

## When to Use

Trigger when the user asks to:
- Plan the implementation of a website improvement proposal
- Break down a PRD into phased tasks
- Create an implementation plan for a site rebuild

Do **not** use for building or coding — that is Phase 5 (website-builder).

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

**Scope:** Initialize Vite + React + shadcn/ui + Tailwind CSS project. Configure build, routing, and deployment to GitHub Pages.

**Outputs:** Working project scaffold with build pipeline.

**Acceptance Criteria:**
- `npm run dev` starts a local dev server
- `npm run build` produces static assets in dist/
- GitHub Pages deployment configured

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

1. Push to GitHub repository
2. Configure GitHub Pages (settings → Pages → source: main /docs or /)
3. Verify deployment at `https://<user>.github.io/<repo>/`

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

```bash
printf '%s\n' "$TASKS_CONTENT" > "$OUTPUT_PATH"
```

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

## Error Handling

| Failure | Behavior |
|---|---|
| No prd.md provided | Ask for the PRD file path |
| Invalid PRD format | Report error and ask for valid file |
| User never approves | Keep looping; do not auto-save |
