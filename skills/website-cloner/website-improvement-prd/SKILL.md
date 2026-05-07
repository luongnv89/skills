---
name: website-improvement-prd
description: "Turn approved end-user report into a full improvement proposal with what/why/value for each change. Writes prd.md after user approval. Use when asked to propose website improvements, create a PRD for a site rebuild, or plan improvements with measurable impact. Don't use for implementation planning or coding — those are separate phases."
license: MIT
effort: high
metadata:
  version: 1.1.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Website Improvement PRD

Turns an approved end-user report into a full improvement proposal with measurable value metrics. Writes `prd.md` after user approval.

## When to Use

Trigger when the user asks to:
- Propose website improvements with expected impact
- Create a PRD for a site rebuild or improvement
- Plan improvements with measurable metrics

Do **not** use for implementation planning or coding — those are separate phases.

## Workflow

```
1. Read the approved report (Phase 2) and analysis (Phase 1)
2. Identify improvement opportunities per dimension
3. For each change: define what, why, and expected value
4. Assemble into prd.md
5. Present to user for review
6. Incorporate edits (loop until approved)
7. Persist prd.md
```

## Output: prd.md Structure

```markdown
# Improvement Proposal: <site name>
**Source URL:** <url>
**Date:** <date>
**Version:** 1.0

---

## Executive Summary

2–3 sentences summarizing the main improvement themes and expected impact.

## Current State

Brief summary of the baseline from Phase 1 analysis:
- Category and audience
- Current performance highlights
- Current SEO standing
- Current security posture

## Proposed Improvements

### Change 1: <Title>

**What:** Specific, scoped description of the change.
Example: "Replace the current hero section with a centered layout featuring a clear headline, subtext, and primary CTA button above the fold."

**Why:** Problem being solved, evidence from Phase 1 analysis.
Example: "The current hero burying the CTA below two content sections. Users must scroll past unrelated content before seeing the sign-up option (Phase 1 UI/UX friction point: 'CTA not immediately visible')."

**Expected Value:** Measurable impact.
Example: "Estimated +15–25% improvement in CTA click-through rate. Reduced scroll depth requirement from 600px to 0px for primary action."

---

Repeat for each change. Group changes by dimension:

### UI/UX Improvements
### Performance Improvements
### SEO Improvements
### Security Improvements
### Style Enhancements

## Metrics Summary

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| LCP | 4.3s | ≤ 2.0s | -53% |
| CLS | 0.18 | ≤ 0.05 | -72% |
| SEO Score | 62/100 | ≥ 90/100 | +45% |
| Page Weight | 2.1 MB | ≤ 800 KB | -62% |

## Next Steps

Reference Phase 4 (implementation plan) — the approved proposal feeds into `tasks.md` for phased execution.

---

*This proposal is based on analysis of a single crawl of the source site. Actual improvements may vary based on implementation decisions.*
```

## Step 1: Read Inputs

Read the approved report and analysis:

```
Read file <path-to-report.md>
Read file <path-to-analysis.json>
```

If either is missing, ask for paths. The orchestrator should have already produced both.

## Step 2: Identify Improvements

For each dimension, identify specific, actionable improvements:

- **UI/UX**: Layout changes, navigation fixes, CTA improvements, content restructuring
- **Performance**: Image optimization, lazy loading, code splitting, font optimization, caching
- **SEO**: Meta tag fixes, heading structure, structured data, alt text, canonical URLs
- **Security**: HTTPS hardening, security headers, mixed content fixes
- **Style**: Typography improvements, color palette refinement, spacing consistency, motion polish

Each improvement must include:
1. **What** — specific, scoped change description
2. **Why** — problem + evidence from Phase 1
3. **Expected Value** — measurable impact statement

## Step 3: Compute Metrics Summary

Compare current metrics from Phase 1 against realistic targets:

| Current | Target Logic |
|---------|-------------|
| LCP > 3s | Target ≤ 2.0s (good) or ≤ 1.5s (excellent) |
| CLS > 0.1 | Target ≤ 0.05 (good) |
| SEO < 80 | Target ≥ 90 |
| Page weight > 1 MB | Target ≤ 800 KB |

## Step 4: Write Draft prd.md

Assemble the proposal using the structure above.

## Step 5: Present for Review

Present the draft to the user:

"Here is the improvement proposal. Please:
1. **Approve** — save as prd.md
2. **Edit** — specify what to change
3. **Regenerate** — start over with different focus"

## Step 6: Incorporate Edits (loop)

If edits requested:
- Update the proposal
- Re-present
- Repeat until approved

Do **not** persist until explicit approval.

## Step 7: Persist prd.md

Write to output path:

```bash
printf '%s\n' "$PRD_CONTENT" > "$OUTPUT_PATH"
```

Default: `$PROJECT_DIR/prd.md` or `~/workspace/clones/YYYY_MM_DD_slug/prd.md`.

If `$ARGUMENTS` includes `--output <path>`, use that.

Confirm:

```
prd.md saved to: <absolute-path>
STATUS: approved
```

## Return Contract

When invoked by the `website-cloner` umbrella (Phase 3 gate), the orchestrator
gates Phase 4 on this skill's outcome. The contract:

| Outcome  | Signal                                                              |
|----------|---------------------------------------------------------------------|
| approved | `prd.md` exists at the resolved output path AND final line of stdout reads `STATUS: approved` |
| pending  | no `prd.md` written; final line reads `STATUS: pending` (user still iterating) |
| aborted  | no `prd.md` written; final line reads `STATUS: aborted` (user declined) |

The orchestrator MUST NOT advance to Phase 4 unless the outcome is `approved`.
A standalone invocation may ignore the status line, but the file-existence rule
still holds: no approval, no `prd.md`.

## Error Handling

| Failure | Behavior |
|---|---|
| No input files provided | Ask for report.md and analysis.json paths |
| Invalid input format | Report error and ask for valid files |
| User never approves | Keep looping; do not auto-save |

