---
name: website-clone-final-report
description: "Produce a before/after comparison report of a website clone project. Uses Phase 1 analysis as baseline and builder metadata as 'after' snapshot. Covers performance, SEO, security, UI/UX deltas, deviations, and GitHub Pages URL. Use when asked for a final report, before-after comparison, or project closure summary of a website clone. Don't use for ongoing monitoring or live site audits."
license: MIT
effort: high
metadata:
  version: 1.0.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Website Clone Final Report

Produces a before/after comparison report closing the loop on a website clone project. Uses Phase 1 analysis as baseline and builder metadata as the "after" snapshot.

## When to Use

Trigger when the user asks to:
- Generate a final report for a website clone project
- Compare before/after metrics of a site rebuild
- Produce a project closure summary for a website improvement

Do **not** use for ongoing monitoring or live site audits — those are separate activities.

## Workflow

```
1. Read Phase 1 analysis (baseline) and builder metadata (after)
2. Read tasks.md for what was implemented
3. Read prd.md for what was planned
4. Compute before/after deltas per dimension
5. List deviations from the plan
6. Write final report
7. Present to user
```

## Output: final-report.md Structure

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
| LCP | 4.3s | 1.8s | -58% |
| CLS | 0.18 | 0.03 | -83% |
| TTFB | 0.8s | 0.2s | -75% |
| Page Weight | 2.1 MB | 650 KB | -69% |
| Requests | 87 | 32 | -63% |

### SEO

| Dimension | Before | After | Delta |
|-----------|--------|-------|-------|
| Overall Score | 62/100 | 94/100 | +52% |
| Meta Tags | 60 | 95 | +58% |
| Heading Structure | 50 | 85 | +70% |
| Alt Text Coverage | 30% | 100% | +233% |
| Structured Data | 0 | 100 | +100% |

### Security

| Check | Before | After |
|-------|--------|-------|
| HTTPS | Yes | Yes |
| Security Headers | Partial | Strong |
| Mixed Content | 2 issues | 0 issues |

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

*This report was generated from the Phase 1 analysis baseline and builder metadata.*
*All metrics are based on automated analysis and may not reflect actual user experience.*
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

If any input is missing, note it and proceed with what's available.

## Step 2: Compute Deltas

Compare baseline metrics against builder metadata:

| Metric | Source | Delta |
|--------|--------|-------|
| LCP, CLS, TTFB, page weight, requests | Phase 1 analysis vs. builder metadata | after - before |
| SEO score, dimension scores | Phase 1 analysis vs. builder metadata | after - before |
| Security checks | Phase 1 analysis vs. builder metadata | qualitative comparison |

For UI/UX, describe changes based on the tasks.md implementation vs. the Phase 1 analysis.

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

Persist the assembled report using the Write tool — never `echo > path`, since markdown bodies routinely contain backticks, dollar signs, and backslashes that the shell would mangle.

Default output path: `$PROJECT_DIR/final-report.md`, falling back to `~/workspace/clones/YYYY_MM_DD_slug/final-report.md` when no project dir is set.

If `$ARGUMENTS` includes `--output <path>`, use that path verbatim.

Confirm:

```
Final report saved to: <absolute-path>
GitHub Pages URL: <url>
```

## Error Handling

| Failure | Behavior |
|---|---|
| No analysis input | Note missing baseline, proceed with qualitative comparison |
| No builder metadata | Note missing after data, request builder metadata from orchestrator |
| No tasks.md | Describe what was implemented based on available data only |
