---
name: website-clone-final-report
description: "Generate a website-clone closure report comparing baseline analysis, builder metadata, planned tasks, and implemented results. Use after a completed rebuild. Don't use for live audits, ongoing monitoring, implementation, or speculative metrics."
license: MIT
effort: high
metadata:
  version: 1.3.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Website Clone Final Report

Produces a before/after comparison report closing the loop on a website clone project. Uses Phase 1 analysis as the baseline and the builder's post-deployment re-audit as the comparable "after" snapshot.

## When to Use

Trigger when the user asks to:
- Generate a final report for a website clone project
- Compare before/after metrics of a site rebuild
- Produce a project closure summary for a website improvement

Do **not** use for ongoing monitoring or live site audits — those are separate activities.

## Workflow

```
1. Read Phase 1 analysis (baseline) and validate builder metadata's post-deployment after snapshot
2. Read tasks.md for what was implemented
3. Read prd.md for what was planned
4. Compute before/after deltas per dimension
5. List deviations from the plan
6. Write final report
7. Present to user
```

## Output: final-report.md Structure

Use the report template below as the only output template. Read only the source sections needed for each comparison to preserve the context budget.

```markdown
# Final Report: <site name> Clone

**Original URL:** <url>
**New Site:** https://<user>.github.io/<repo>/
**Date:** <date>

---

## What Was Implemented

A plain-language summary of what was built, drawn from tasks.md:

"The improved website includes:
- A redesigned landing page with a prominent CTA above the fold
- Three additional pages: Features, About, and Contact
- Performance optimizations including image compression and lazy loading
- Full SEO implementation with structured data and meta tags"

## Before/After Comparison

### Performance

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| LCP estimate (seconds) | 4.3 | 1.8 | -58% |
| CLS estimate (unitless) | 0.18 | 0.03 | -83% |
| TTFB estimate (seconds) | 0.8 | 0.2 | -75% |
| Page Weight (KB) | 2100 | 650 | -69% |
| Requests (count) | 87 | 32 | -63% |

### SEO

| Dimension | Before | After | Delta |
|-----------|--------|-------|-------|
| Overall Score | 62/100 | 94/100 | +52% |
| Meta Tags | 60 | 95 | +58% |
| Heading Structure | 50 | 85 | +70% |
| Alt Text Score | 30/100 | 100/100 | +233% |
| Structured Data | 20/100 | 100/100 | +400% |
| Crawlability | 60/100 | 90/100 | +50% |

### Security

| Check | Before | After |
|-------|--------|-------|
| HTTPS | Yes | Yes |
| Mixed Content | Detected | Not detected |
| Security Headers Detected | 2 | 4 |
| Exposed Metadata Findings | 2 | 0 |

### UI/UX Changes

Plain-language description of UI/UX improvements:

- **Hero section:** Restructured to put the CTA immediately above the fold. The original buried the sign-up button below two content sections.
- **Navigation:** Simplified from 8 menu items to 5, removing low-value links.
- **Mobile experience:** Completely redesigned for mobile with a hamburger menu and stacked layout.
- **Visual hierarchy:** Improved contrast and spacing make the primary action 3x more prominent.

### Style Enhancements

- Typography upgraded from generic system fonts to a modern paired font system
- Color palette refined with better contrast ratios (WCAG AA compliant)
- Spacing made more consistent and generous
- Motion added sparingly for micro-interactions (button hover, scroll reveal)

## Deviations from Plan

List any deviations from prd.md or tasks.md:

| Planned | Actual | Reason |
|---------|--------|--------|
| 5 additional pages | 3 additional pages | Scope reduction requested |
| Custom icon set | lucide-react icons | Time constraint |
| Animated hero | Static hero with CSS fade-in | Performance priority |

If no deviations, state: "No deviations from the approved plan."

## Summary

A closing summary for non-technical stakeholders:

"This website improvement project successfully addressed the key issues identified
in the initial analysis. Performance improved by 58-83% across all metrics, SEO
score increased from 62 to 94, and the user experience was significantly enhanced
with a clearer visual hierarchy and better mobile support. The new site is live at
the URL above."

---

*This report was generated from the Phase 1 analysis baseline and the builder's post-deployment re-audit.*
*LCP, CLS, TTFB, page weight, and request values are static-analysis estimates, not field measurements.*
```

## Step 1: Read Inputs

Read the analysis baseline and builder metadata:

```
Read file <path-to-analysis.json>
Read file <path-to-builder-metadata.json>
```

Also read `tasks.md` for what was implemented and `prd.md` for what was planned:

```
Read file <path-to-tasks.md>
Read file <path-to-prd.md>
```

Validate `builder-metadata.json` has `after_snapshot_source`, `after_snapshot_status`, and the
embedded `performance`, `seo`, and `security` objects copied from the post-deployment analyzer run.
If any input is missing, note it and proceed only to produce a clearly `PARTIAL` report.

## Step 2: Compute Deltas

Compare matching baseline and after-snapshot fields:

| Metric | Baseline source | After source |
|--------|-----------------|--------------|
| LCP estimate (seconds) | `analysis.performance.lcp_estimate_seconds` | `builder.performance.lcp_estimate_seconds` |
| CLS estimate (unitless) | `analysis.performance.cls_estimate` | `builder.performance.cls_estimate` |
| TTFB estimate (seconds) | `analysis.performance.ttfb_estimate_seconds` | `builder.performance.ttfb_estimate_seconds` |
| Page weight (KB), requests (count) | `analysis.performance.*` | `builder.performance.*` |
| SEO score and five dimension scores | `analysis.seo.*` | `builder.seo.*` |
| HTTPS, mixed content, header list, exposed metadata | `analysis.security.*` | `builder.security.*` |

For numeric metrics, normalize to the displayed unit and calculate percentage delta as
`((after - before) / before) × 100`, rounded to the nearest whole percent. If the baseline is zero,
show the absolute `after - before` change and label percentage delta `N/A (zero baseline)`. Compare
security booleans directly and arrays by reproducible counts; do not invent qualitative ratings.
For UI/UX, describe changes based on tasks.md versus the Phase 1 analysis.

## Step 3: Identify Deviations

Compare tasks.md (what was planned) against what the builder actually delivered:

- Tasks that weren't completed
- Features implemented differently than specified
- Assets that weren't collected or created as planned
- Any scope changes

## Step 4: Write Draft Report

Assemble the report using the structure above.

## Step 5: Present to User

"Here is the final comparison report. Review it for completeness and accuracy."

No approval gate is required for this phase — it's the last step and informational only.

## Step 6: Save Report

Persist the assembled content using the `Write` tool with literal content only. If the `Write` tool is unavailable, stop with a descriptive error and do not use shell persistence or another output path.

Default output path: `$PROJECT_DIR/final-report.md`, falling back to `~/workspace/clones/YYYY_MM_DD_slug/final-report.md` when no project dir is set.

If `$ARGUMENTS` includes `--output <path>`, use that path verbatim.

Confirm:

```
Final report saved to: <absolute-path>
GitHub Pages URL: <url>
```

## Acceptance Criteria and Expected Output

Verify the report before saving:

- Every source file is named as present or missing; no absent input is silently treated as evidence.
- Required comparison data comprises all five performance fields, SEO overall score plus all five dimension scores, and the four security fields (`https`, `mixed_content`, `security_headers`, `exposed_metadata`) in both snapshots.
- For each numeric metric, show the formula, deterministic unit, and correctly rounded delta; label estimates and never invent unavailable values.
- Each qualitative claim cites an implemented task, builder deviation, or baseline observation.
- `final-report.md` contains implementation summary, performance, SEO, security, UI/UX, deviations, caveats, and Pages URL sections.
- `PASS` requires valid baseline, builder metadata, tasks, and PRD inputs; a responsive Pages URL; `after_snapshot_status: complete`; every required comparison supported; and a non-empty saved report.
- `PARTIAL` is mandatory when the report is saved but any required input, URL, snapshot, metric, or comparison is missing, null, invalid, or unavailable. A report write failure or inability to produce a valid report is `FAIL`.

## Step Completion Report

```text
◆ Final Comparison Report
··································································
  Inputs accounted for: √ pass | × partial ([missing])
  Deltas verified:      √ pass | × partial ([unavailable])
  Deviations compared:  √ pass
  Report saved:         √ pass ([absolute path])
  Pages URL:            √ pass | × unavailable
  Result:               PASS | PARTIAL | FAIL
```

Use `PASS` only when every required comparison above is supported. Any unavailable required before/after value forces `PARTIAL`, even when the report can explain the gap; never promote unavailable comparisons to `PASS`.

## Edge Cases and Error Handling

| Failure | Behavior |
|---|---|
| No analysis input | Produce a qualitative report only if useful; result is `PARTIAL` |
| No builder metadata | Request builder metadata from the orchestrator; any saved report is `PARTIAL` |
| Missing/incomplete after snapshot | Preserve unavailable values and analyzer errors; result is `PARTIAL` |
| No tasks.md or prd.md | Describe only supported implementation/deviation facts; result is `PARTIAL` |
