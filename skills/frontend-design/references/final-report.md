# Final Report

The closing output of every frontend-design run, stops included. `SKILL.md` (*Final Report*) holds the status rule and a `COMPLETE` example; this file holds the `PARTIAL` and `BLOCKED` examples, the fill rules, and the reader checks.

The report is a compact text block of four lines. Do not replace it with a long Markdown report, a table, or a rendered page. If the user asks for a different format, keep the four items (`Result`, `Evidence`, `Uncertainty`, `Decision`) and present them in that format.

## Status

| Status | When |
|--------|------|
| `COMPLETE` | Code is written and no verification check (Instructions step 7) failed. A check that could not run is not a failure; it goes on the `Uncertainty:` line. |
| `PARTIAL` | Code is written and at least one verification check still fails after the second fix cycle. |
| `BLOCKED` | No code is written: approval was not given, a required answer is missing, or Repo Sync stopped on a conflict. |

## PARTIAL example

```text
Result: PARTIAL. Wrote src/components/PricingTable.vue; 1 of 4 checks still fails.
Evidence: Contrast check: Gray #6B7280 on Black #000000 for the plan footnote is 4.3:1, below 4.5:1 (PricingTable.vue:88). Responsive check passed at 375, 768 and 1280 px in the browser. npm run build passed. Quality Bar and usability Quick rules passed.
Uncertainty: Assumed the footnote must stay gray to match the existing design system; the brief did not say.
Decision: Choose a fix: lighten the footnote to White, or enlarge it to 24 px so the 3:1 large-text threshold applies.
```

## BLOCKED examples

### No approval

```text
Result: BLOCKED. No code written: the aesthetic direction was not approved.
Evidence: Proposed "editorial, monochrome with green rule lines" for the landing page. The user did not answer.
Uncertainty: No code was written, so no check ran.
Decision: Approve the proposed direction, ask for a different one, or say "just build it".
```

### Sync conflict

```text
Result: BLOCKED. No code written: Repo Sync stopped on a rebase conflict.
Evidence: git pull --rebase origin main conflicted in src/styles/tokens.css; ran git rebase --abort and git stash pop.
Uncertainty: The approved direction is unchanged; no file was written.
Decision: Resolve the conflict on main or tell me to continue without syncing.
```

## Fill rules

- `Result:` comes first. The first word after `Result:` is the status. Name each file written, or say `No code written`.
- `Evidence:` names each verification check that ran and its observed result: the widths rendered, the lowest contrast ratio found, and the build, lint, or test command with its exit result. Cite a `file:line` for each failure. Cite only checks that ran.
- `Uncertainty:` lists each check that could not run (for example `Responsive rendering untested: no browser available`), a `sync: failed (...)` or `sync: skipped (...)` record, and each assumption made where the brief was silent. Label assumptions as assumptions.
- `Decision:` names the one action the user must take, or says `No approval needed.` Name a remaining user action (for example, adding real images) in the same line after `No approval needed.`

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in `SKILL.md` → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and the files written (or `No code written`) without reading the code. |
| Facts and assumptions are separated | Verified claims name a check that ran; untested checks and assumptions are on the `Uncertainty:` line. |
| Claims are traceable | Each failed check cites a `file:line` and the measured value; `COMPLETE` appears only when no check failed. |
| Next decision is clear | The `Decision:` line names the pending choice or says `No approval needed.` |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from these checks.
