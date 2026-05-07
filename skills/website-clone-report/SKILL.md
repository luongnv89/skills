---
name: website-clone-report
description: "Convert website analyzer output into a comprehensive plain-language report for non-technical users. Prompts for validation before persisting. Use when asked to report on a website analysis, create an end-user report, or translate technical metrics into plain language. Don't use for technical audit reports targeting developers, raw SEO audits, or penetration testing. Approval gate: never saves without explicit user approval."
license: MIT
effort: high
metadata:
  version: 1.0.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Website Clone Report

Converts structured website analysis into a comprehensive, plain-language report for non-technical readers. Approval gate: persists only after explicit user validation.

## When to Use

Trigger when the user asks to:
- Create a report from website analysis results
- Translate technical website metrics into plain language
- Produce an end-user summary of a site assessment

Do **not** use for technical audit reports targeting developers — those belong to the analyzer skill.

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
  - LCP: "how fast the main content appears"
  - CLS: "how stable the page feels while loading"
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

Once approved, write the report to the output path:

```bash
echo "$REPORT_CONTENT" > "$OUTPUT_PATH"
```

Default output path: `$PROJECT_DIR/report.md` or `~/workspace/clones/YYYY_MM_DD_slug/report.md`.

If `$ARGUMENTS` includes `--output <path>`, use that path. Otherwise use the default.

After writing, confirm:

```
Report saved to: <absolute-path>
```

## Error Handling

| Failure | Behavior |
|---|---|
| No analyzer input provided | Ask for the analysis JSON file path |
| Invalid JSON | Report error and ask for valid input |
| User never approves | Keep the loop going; do not auto-save |

## Acceptance Criteria

- [ ] The skill consumes the website-analyzer output without re-scraping the original site
- [ ] The report is written in plain language; technical metrics are translated
- [ ] The skill explicitly prompts the user to validate or edit the report before persisting
- [ ] The final report is written to a known file path only after user approval
- [ ] If the user requests edits, the skill incorporates them and re-prompts for approval
- [ ] When run inside website-cloner, the orchestrator does not advance until "approved"
