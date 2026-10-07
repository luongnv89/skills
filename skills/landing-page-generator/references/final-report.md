# Final Report

The closing chat response of every landing-page-generator run, stops included, in both
modes. It sits beside the deliverable (Mode A copy in chat; Mode B the rewritten
`README.md`) and never replaces it. `SKILL.md` (*Final Report*) holds the status rule and
a `COMPLETE` example; this file holds the `PARTIAL` and `BLOCKED` examples, the fill
rules, and the reader checks.

The report is a compact text block of four lines. Do not replace it with a long Markdown
report or a rendered page. If the user asks for a different format, keep the four items
(`Result`, `Evidence`, `Uncertainty`, `Decision`) and present them in that format.

## Status

Apply the first row that matches:

| Status | When |
|--------|------|
| `COMPLETE` | The deliverable is produced and every applicable check passes. Mode A: the full-page copy follows the chosen framework's template in `references/section-templates.md` and the Acceptance Criteria pass, or the user asked for a single section and that section plus its fit note is delivered. Mode B: `README.md` is rewritten, `README.backup.md` exists, all original content is preserved (backup plus `<details>` blocks), and the Step 6 Self-Review Checklist passes. |
| `PARTIAL` | A deliverable was produced and at least one holds: a template section is missing, a CTA fails the CTA Button Rules, the A/B test ideas and conversion tips are missing from a full-page deliverable, the Mode B Self-Review Checklist still fails after the fix pass, original README content was lost, or a change the user asked for was not made. |
| `BLOCKED` | No deliverable: the Mode A core inputs (product/service name, target audience, problem solved, primary CTA) or a Mode B context question went unanswered and the user ended the run; Mode B found no `README.md` and the user declined creating one from scratch; or Repo Sync stopped on a missing `origin` or a conflict. |

A question that awaits the user's answer (core inputs, framework override, Mode B
feedback) does not end the run. If the user ends the run without answering, the status is
`BLOCKED`. A user declining an optional follow-up (for example, a suggested commit or a
second A/B variant) after the deliverable exists does not change a `COMPLETE`.

## PARTIAL example

```text
Result: PARTIAL. Rewrote README.md with the PAS structure; the Self-Review Checklist still fails on feature descriptions over 15 words (2 of 4).
Evidence: README.backup.md created before the rewrite; all original content preserved in <details> blocks; Self-Review Checklist 11/13 — feature descriptions and the no-rhetorical-questions check fail.
Uncertainty: Trimming the two long feature descriptions further may drop technical detail the project wants visible; not confirmed with the user.
Decision: Approve the shorter feature wording, or tell me which technical detail to keep and I will rebalance the sections.
```

## BLOCKED examples

### Mode A — core inputs unanswered

```text
Result: BLOCKED. No copy written: the product name, target audience, problem solved, and primary CTA were not supplied.
Evidence: Asked 3 targeted questions covering the four core inputs; the run ended with no answer.
Uncertainty: Nothing about the product is known, so no framework was selected.
Decision: Provide the product name, target audience, problem solved, and primary CTA.
```

### Mode B — sync conflict

```text
Result: BLOCKED. No files written: Repo Sync stopped on a rebase conflict.
Evidence: git pull --rebase origin main conflicted in README.md; ran git rebase --abort and restored the stash. README.md and README.backup.md untouched.
Uncertainty: The planned framework choice (PAS) is unchanged; no file was written.
Decision: Resolve the conflict on the branch or tell me to continue without syncing.
```

## Fill rules

- `Result:` comes first. The first word after `Result:` is the status. Name the
  deliverable produced (the framework and sections delivered, or the files written), or
  say `No copy written` / `No files written`.
- `Evidence:` names each verification check that ran and its observed result: the
  framework template applied, the hero headline word count, the CTA Button Rules check,
  the `[proof needed]` markers placed, the anti-slop check, and for Mode B the backup,
  the content-preservation check, the Self-Review Checklist count, and the `sync:`
  record (`sync: skipped (...)` or `sync: failed (...)`; a failed sync that stopped the
  run is the `BLOCKED` reason). Cite only checks that ran.
- `Uncertainty:` lists each check that could not run and each assumption made where the
  user was silent. Label assumptions as assumptions.
- `Decision:` names the one action the user must take, or says `No approval needed.`
  Name a remaining user action (for example, replacing `[proof needed]` markers with
  real metrics, or committing the rewritten README) in the same line after
  `No approval needed.`

## Step completion reports

The per-step report (`SKILL.md` → *Step Completion Reports*) uses its own result words:
`PASS` when every check of the step passes, `PARTIAL` when the step ends with a recorded
gap, `FAIL` when a check is blocked and the run cannot continue. A step `FAIL` that stops
the run before any deliverable becomes a Final Report `BLOCKED`; a step `PARTIAL` that
survives to the end becomes a Final Report `PARTIAL`.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in
`SKILL.md` → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and the deliverable (or `No copy written` / `No files written`) without re-reading the conversation. |
| Facts and assumptions are separated | Verified claims name a check that ran; untested checks and assumptions are on the `Uncertainty:` line. |
| Claims are traceable | Each failed check cites the section or file it failed in; `COMPLETE` appears only when the deliverable exists and every applicable check passed. |
| Next decision is clear | The `Decision:` line names the pending choice or says `No approval needed.` |

A heading's presence alone does not pass a check. Ask a human reviewer the same four
questions. If no reviewer answers, record human understanding as unconfirmed; agent
inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded
from these checks.
