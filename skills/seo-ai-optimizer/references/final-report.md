# Final Report

The closing chat response of every seo-ai-optimizer run, stops included. It follows the
step reports and sits beside the audit report (in chat, or `<output-dir>/seo-audit-report.md`
in an orchestrated run); it never replaces the audit report. `SKILL.md` (*Final Report*)
holds the status summary; this file holds the status table, the `COMPLETE`, `PARTIAL` and
`BLOCKED` examples, the fill rules, and the reader checks.

## Format

The report is a compact text block of four lines. The audit report already carries the
per-file findings, so do not repeat them here and do not render an HTML page. If the user
asks for a different format, keep the four items (`Result`, `Evidence`, `Uncertainty`,
`Decision`) and present them in that format.

## Status

Apply the first row that matches:

| Status | When |
|--------|------|
| `BLOCKED` | No audit report was produced: the project is not a git repo and the run is not live-evidence-only; `audit_seo.py` reported "No HTML/template files found"; `audit_seo.py` could not run (no Python 3); or Repo Sync stopped on a missing `origin`, a failed pull, or a conflict before the audit report was written. |
| `PARTIAL` | The audit report exists and at least one Acceptance Criteria item is unchecked: the user approved only part of the plan or ended the run before approving; a critical issue remains after Step 7; a Diff & Confirm was refused for a file in the approved plan; Repo Sync stopped after the audit report was written, so no fix was applied; or Step 8 returned `FAIL`. |
| `COMPLETE` | Every applicable Acceptance Criteria item in `references/workflow-detail.md` is checked. Step 8 `SKIPPED` with its unmet condition named, and Step 8 `REUSED`, both count as checked. A live-evidence-only run is `COMPLETE` when its report is written and every item in `references/live-evidence-only.md` (*Done when*) holds. |

A plan awaiting the user's approval (Step 5) or a diff awaiting confirmation (Step 6) does
not end the run. If the user ends the run there, the status is `PARTIAL`, because the audit
report exists. An audit-only request ("audit, don't change anything") is `COMPLETE` once the
report and plan are presented and the user declines implementation; name the declined plan in
`Decision:`.

## COMPLETE example

```text
Result: COMPLETE. Audited 14 Next.js pages; fixed 3 critical and 5 warning issues; added llms.txt and Organization JSON-LD.
Evidence: audit_seo.py before 3 critical / 9 warning, after 0 / 4; diffs shown and confirmed for 6 files; Step 8 score 3/5, agent-ready-plan.md written.
Uncertainty: Search Console indexing is untested; the live scan may predate the deploy of these fixes.
Decision: No approval needed. Commit and deploy the changes, then re-run Step 8.
```

## PARTIAL example

```text
Result: PARTIAL. Audited 22 Astro pages; applied 4 of 7 planned fixes; 1 critical issue remains.
Evidence: audit_seo.py before 2 critical / 11 warning, after 1 / 6; the user approved items 1-4 only; src/pages/blog/[slug].astro still has no meta description.
Uncertainty: Step 8 skipped — no live URL supplied; rendered output on the deployed site is untested.
Decision: Approve plan items 5-7, or confirm the blog template should stay without a meta description.
```

## BLOCKED example

```text
Result: BLOCKED. No audit report: /work/site is not a git repository and no evidence-dir was given.
Evidence: git rev-parse --git-dir failed in /work/site; audit_seo.py was not run; no file was read or written.
Uncertainty: The framework and page count are unknown.
Decision: Run the skill from the site's git repository, or pass the captured live evidence through /search-optimizer.
```

## Fill rules

- `Result:` comes first. The first word after `Result:` is the status. State the page or
  file count audited, the fixes applied, and the files created, or say `No audit report`.
  In a live-evidence-only run, say `live evidence only` and count the fixes listed as
  `needs source repo`.
- `Evidence:` names each check that ran and its observed result: the `audit_seo.py` critical
  and warning counts before and after, the files whose diffs were shown and confirmed, and
  the Step 8 outcome (score and `agent-ready-plan.md`, `REUSED` with `scannedAt`, or
  `SKIPPED` with its unmet condition). Cite only checks that ran.
- `Uncertainty:` lists each check that could not run (for example, Step 8 skipped, Step 3
  web search unavailable, files the manifest records as blocked) and each assumption made.
  Label assumptions as assumptions. A validator re-run proves the static audit result only;
  it does not prove search-engine indexing or ranking.
- `Decision:` names the one approval the user must give, or says `No approval needed.`
  Name a remaining user action (commit and deploy the fixes, supply a live URL for Step 8,
  apply a `needs source repo` fix in the source repo) on the same line after
  `No approval needed.`

## Step completion reports

The per-step reports (`references/step-reports.md`) use `PASS`, `PARTIAL` and `FAIL`, plus
`REUSED` and `SKIPPED` for Step 8. A step `FAIL` before Step 4 becomes a Final Report
`BLOCKED`. A step `FAIL` or `PARTIAL` from Step 4 onward becomes a Final Report `PARTIAL`.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in
`references/workflow-detail.md` (*Acceptance Criteria*):

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and what was audited and changed (or `No audit report`) without re-reading the conversation. |
| Facts and assumptions are separated | Verified claims name a check that ran (`audit_seo.py` counts, confirmed diffs, Step 8 score); untested checks and assumptions are on the `Uncertainty:` line. |
| Claims are traceable | Each remaining issue cites the file it is in; `COMPLETE` appears only when every applicable Acceptance Criteria item is checked. |
| Next decision is clear | The `Decision:` line names the pending approval or says `No approval needed.` and names any remaining user action. |

A heading's presence alone does not pass a check. Ask a human reviewer the same four
questions. If no reviewer answers, record human understanding as unconfirmed; agent
inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded
from these checks.
