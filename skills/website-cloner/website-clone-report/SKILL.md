---
name: website-clone-report
description: "Generate a plain-language report from website-analyzer JSON and save it only after explicit approval. Use for non-technical summaries. Don't use for developer audits, raw SEO analysis, penetration testing, or unapproved persistence."
license: MIT
effort: high
metadata:
  version: 1.3.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Website Clone Report

Converts structured website analysis into a comprehensive, plain-language report for non-technical readers. Approval gate: persists only after explicit user validation.

## When to Use

Trigger when the user asks to:
- Create a report from website analysis results
- Translate technical website metrics into plain language
- Produce an end-user summary of a site assessment

Do **not** use for technical audit reports targeting developers — those belong to the analyzer skill.

## Prerequisites

1. Require valid website-analyzer JSON. Resolve an optional `--output <path>` using the documented fallback below.
2. Read `references/api_reference.md` when validating fields or translating metrics; use only the needed reference mappings to protect the context budget.
3. Confirm the user can review the draft and explicitly approve persistence.
4. Stop with a descriptive error when the JSON is invalid or contains an analyzer `error` variant.

## Repo Sync Before Edits (mandatory)

The approved report is persisted with `Write`. When that output path lives inside a git worktree, sync before the write to avoid clobbering remote work:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash → sync → pop. If `origin` is missing or a conflict occurs: **stop and ask the user.** Skip this section only when the output path is outside any git repository.

## Workflow

```
1. Read the analyzer output (JSON)
2. Translate each dimension into plain language
3. Draft the report for non-technical readers
4. Present to user for review
5. Incorporate edits (loop until approved)
6. Persist final report to file
```

## Report Structure

Write the report in plain language. Technical metrics are translated, not just listed.

```markdown
# Website Analysis Report: <site name>
**URL:** <url>
**Date:** <date>

---

## At a Glance

A plain-language summary: what this site is, who it's for, and its overall health.
Example: "This is a SaaS landing page targeting small businesses. It looks polished and modern,
but loads slowly on mobile connections and is missing key SEO elements that would help it
rank in search results."

## How It Looks and Works

Translate UI/UX findings into plain language:
- Layout style (e.g., "clean single-column layout with a large hero image")
- What draws attention first
- Any friction points (e.g., "the sign-up button is hidden below the fold")
- Responsive behavior

## What Kind of Site This Is

Category description in plain terms:
- "This is an e-commerce store selling handcrafted furniture"
- "This is a documentation site for a developer tool"

## Design and Style

Describe the visual identity accessibly:
- Typography feel (e.g., "modern sans-serif fonts that feel clean and professional")
- Color palette (e.g., "cool blues and grays with orange accents for calls to action")
- Spacing and density
- Motion and interactivity feel

## Performance

Translate metrics to plain language:
- **How fast content appears:** "The main content takes about X seconds to appear.
  For comparison, sites that load in under 2 seconds tend to keep visitors engaged."
- **Visual stability:** "The page layout is mostly stable while loading.
  You're unlikely to notice elements jumping around."
- **How quickly the server responds:** "The estimated server response delay is X seconds."
- **How much data it uses:** "The page weighs about X KB, roughly equivalent to
  loading Y average-sized images."
- **Number of resources:** "The page makes about X requests to load."

## Security Overview

Surface-level observations only, in plain language:
- "The site uses HTTPS, which means data between your browser and the site is encrypted."
- "The site sends a few security signals to browsers, but could strengthen them."

Always note this is not a full security audit.

## Search Engine Visibility

SEO findings translated:
- Overall score with context: "SEO score: X/100 — [excellent/good/fair/poor]"
- "The page has a title and description that search engines can read."
- "The heading structure could be improved to help search engines understand the content."
- "Images are missing alternative text, which helps with accessibility and search."

## Summary and Next Steps

A brief section with actionable takeaways:
- What's working well (2–3 points)
- What needs attention (2–3 points)
- What could be improved (2–3 points)

---

*This report was generated from automated analysis. All findings are based on a single-page crawl
and may not reflect the full site.*
```

## Step 1: Read Analyzer Output

Read the JSON analysis file (or content passed via stdin/argument):

```
Read file <path-to-analysis.json>
```

If no file is provided and `$ARGUMENTS` contains a URL, note that this skill requires pre-existing analysis output (produced by `website-analyzer`), not raw URLs. The orchestrator should have already run Phase 1.

## Step 2: Translate to Plain Language

For each dimension:
- **UI/UX**: Describe layout and friction in terms a non-technical person understands. Avoid jargon like "visual hierarchy" — say "what catches the eye first."
- **Category**: Explain what kind of site it is in plain terms.
- **Style**: Describe the feel and look without needing CSS knowledge.
- **Performance**: Translate numbers to relatable comparisons:
  - `lcp_estimate_seconds`: "how fast the main content appears" (estimated seconds)
  - `cls_estimate`: "how stable the page feels while loading" (unitless)
  - `ttfb_estimate_seconds`: "how quickly the server responds" (estimated seconds)
  - Page weight: "how much data the page uses"
  - Request count: "how many pieces the page needs to load"
- **Security**: Surface-level observations only, no technical headers jargon.
- **SEO**: Explain each finding in terms of "helping people find this site on Google."

## Step 3: Draft the Report

Assemble the translated content into the report structure above.

## Step 4: Present for Review

Present the draft report to the user. Ask:

"Here is the analysis report. Please review it and let me know:
1. **Approve** — it looks good, save it
2. **Edit** — I'd like to change something (specify what)
3. **Regenerate** — start over with different focus"

## Step 5: Incorporate Edits (loop)

If the user requests edits:
- Update the report accordingly
- Re-present for review
- Repeat until approved

Do **not** persist the file until explicit approval.

## Step 6: Persist Final Report

Once approved, persist the assembled content using the `Write` tool with literal content only. If the `Write` tool is unavailable, stop with a descriptive error and do not use shell persistence or another output path.

- **Path:** the value passed via `--output <path>`. If absent, fall back to `$PROJECT_DIR/report.md` when the orchestrator set `$PROJECT_DIR`, otherwise to `report.md` in the current working directory.
- **Content:** the approved markdown report assembled in Step 3, with any edits from Step 5 applied.

After the `Write` call returns, confirm to the user:

```
Report saved to: <absolute-path>
```

## Acceptance Criteria and Expected Output

Verify the approved report before saving:

- It covers UI/UX, category, style, performance, surface security, SEO, and next steps, or names each unavailable dimension.
- Every metric and observation traces to the analyzer JSON; assert that no unsupported benchmark or claim was invented.
- Language is understandable without developer terminology, while the security and single-page-crawl caveats remain explicit.
- The expected result is a non-empty approved markdown file at the resolved path, written only after explicit approval such as `Approve`.
- Re-read the saved file state or Write result and report its absolute path.

## Edge Cases and Error Handling

| Failure | Behavior |
|---|---|
| No analyzer input provided | Ask for the analysis JSON file path |
| Invalid JSON | Report error and ask for valid input |
| Analyzer error variant | Surface its `error` and `detail`; do not draft a health report |
| Missing or null dimension | Omit unsupported specifics and identify the gap in next steps |
| User never approves | Keep the loop going; do not auto-save |

## Step Completion Report

```text
◆ Website Clone Report
··································································
  Analyzer JSON:        √ pass | × fail ([reason])
  Six dimensions:      √ translated | × partial ([missing])
  Draft reviewed:      √ pass
  User approved:       √ pass | × pending
  Report saved:        √ pass ([absolute path]) | — not approved
  Result:              PASS | BLOCKED | FAIL
```

Never report `PASS` before both explicit approval and a successful Write result.

