# Interactive HTML report

Read this only when SKILL.md's **Format** input selects HTML: more than five roles requested, or the user asked to filter roles. The content comes from `report-format.md`; this file adds the interaction layer and the layout below.

## Layout

- Produce one self-contained `.html` file with inline CSS and JavaScript.
- Show the Result line, the search evidence summary, the main uncertainty, and the Decision line at the top. Keep them visible without expanding anything.
- Show one card or row per role. List ranked roles first, then near-misses and rejected roles in a separate group, each with its failed gate.
- In the chat reply, print the Result line, the Decision line, and the HTML file's path.

## Filters

Add a filter for each field the candidate decides on:

| Filter | Values |
|---|---|
| Location eligibility | passes · conditional · fails · unknown, plus hybrid or remote |
| Salary | minimum and maximum, in the listing's currency · "not listed" |
| Equity | published · "not listed" |
| Seniority | the levels in the shortlist |
| Interestingness verdict | High · Medium · Low |
| Gate status | ranked · near-miss (failed step 3) · rejected (failed a hard reject) |

- Keep "not listed" and "unknown" as their own values. Never merge a missing value with a value that fails a criterion.
- Show the visible result count, for example "Showing 4 of 11 roles".
- Add a reset control that restores every filter and the full count.
- Add a funding or traction field only when step 3 sourced it.

## Evidence

- Put an expandable evidence panel beside each claim it supports: the quoted location policy, the listing fields, the product sources, and the candidate-fit evidence.
- Show why each role met or failed each gate.
- Link every source to its original URL. Label missing evidence "unavailable".
- Make filters hide or show whole roles only. A filter never separates a claim from its evidence.

## Delivery check

Before delivery, exercise each control and record the outcome in step 4's Step Completion Report:

1. Apply each filter value. Check that the visible count changes to match the roles shown.
2. Open each expand control. Check that it shows the evidence for its own claim.
3. Use the reset control. Check that the full count returns.
4. Check that each source link has its original URL.

If a browser is not available, or a control or link could not be exercised, list it as untested under Uncertainty. If this environment cannot produce HTML at all, say so and deliver the text report.
