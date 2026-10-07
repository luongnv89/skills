# Final Report

The closing chat response of every logo-designer run, stops included. It sits beside the
deliverables (the 7 SVGs and `brand-showcase.html`) and never replaces them. `SKILL.md`
(*Final Report*) holds the status rule and a `COMPLETE` example; this file holds the
`PARTIAL` and `BLOCKED` examples, the fill rules, and the reader checks.

The report is a compact text block of four lines. Do not replace it with a long Markdown
report, a table, or a rendered page. If the user asks for a different format, keep the
four items (`Result`, `Evidence`, `Uncertainty`, `Decision`) and present them in that
format.

## Status

Apply the first row that matches:

| Status | When |
|--------|------|
| `COMPLETE` | All 7 SVGs and `brand-showcase.html` are written, and the Phase 3 geometry verification passed (the `d=""` strings match across variants, or are correctly scaled via `transform`). |
| `PARTIAL` | Files were written and at least one holds: a variant is missing, the geometry verification still fails after re-running it, the showcase page was not written, or an SVG contains an embedded raster. |
| `BLOCKED` | No files were written: the user gave no product context after one request, the style or wordmark-casing confirmation went unanswered and the user ended the run, or Repo Sync stopped on a conflict. |

A question that awaits the user's answer (product context, style approval, wordmark
casing) does not end the run. If the user ends the run without answering, the status is
`BLOCKED`.

## PARTIAL example

```text
Result: PARTIAL. Wrote 6 of 7 SVGs to /assets/logo/; favicon.svg still fails the 2-layer simplification rule.
Evidence: Read back logo-mark.svg, logo-full.svg, logo-icon.svg, logo-white.svg and logo-black.svg: d="" strings identical. svg-reviewer reported favicon.svg keeps the middle detail layer at 16x16.
Uncertainty: Assumed the middle layer is droppable without changing the mark's silhouette; not confirmed with the user.
Decision: Approve dropping the middle layer in favicon.svg, or pick a different simplification.
```

## BLOCKED examples

### No product context

```text
Result: BLOCKED. No files written: no project context was found and the user did not answer.
Evidence: Checked README.md, package.json, pyproject.toml, Cargo.toml and go.mod: none present. Asked for product name, type and one-sentence purpose; no answer.
Uncertainty: No brand brief exists, so no style was selected.
Decision: Provide the product name, product type, and one-sentence purpose.
```

### Sync conflict

```text
Result: BLOCKED. No files written: Repo Sync stopped on a rebase conflict.
Evidence: git pull --rebase origin main conflicted in assets/logo/logo-mark.svg; ran git rebase --abort and restored the stash.
Uncertainty: The confirmed style and casing are unchanged; no file was written.
Decision: Resolve the conflict on the branch or tell me to continue without syncing.
```

## Fill rules

- `Result:` comes first. The first word after `Result:` is the status. Name each file
  written, or say `No files written`.
- `Evidence:` names each verification check that ran and its observed result: the Phase
  3 read-back of the five compared variants, the svg-reviewer's findings, the Default
  Quality Bar pass. Cite a file name for each failure. Cite only checks that ran.
- `Uncertainty:` lists each check that could not run, a `sync: failed (...)` or
  `sync: skipped (...)` record (for example `sync: skipped (not a git repo)`), and each
  assumption made where the user was silent. Label assumptions as assumptions.
- `Decision:` names the one action the user must take, or says `No approval needed.`
  Name a remaining user action (for example, exporting a PNG from the SVGs) in the same
  line after `No approval needed.`

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in
`SKILL.md` → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and the files written (or `No files written`) without opening `/assets/logo/`. |
| Facts and assumptions are separated | Verified claims name a check that ran; untested checks and assumptions are on the `Uncertainty:` line. |
| Claims are traceable | Each failed check cites the file it failed in; `COMPLETE` appears only when every file is written and the geometry verification passed. |
| Next decision is clear | The `Decision:` line names the pending choice or says `No approval needed.` |

A heading's presence alone does not pass a check. Ask a human reviewer the same four
questions. If no reviewer answers, record human understanding as unconfirmed; agent
inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded
from these checks.
