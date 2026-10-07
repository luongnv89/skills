# Final response and run status

The chat response that closes a run. It sits beside `viral-evaluation.md` and never replaces
it. In an orchestrated run the orchestrator relays this response; it never answers for the
user.

## Status rule

Apply the first row that matches.

| Status | When |
|---|---|
| `BLOCKED` | Nothing was scored and no report was written: no landing page input and no answer after one request; a live URL with `/browse` unavailable and no local file offered; a prerequisite is missing; the user stopped the run. |
| `PARTIAL` | A report was produced and at least one holds: a principle's evidence source was unavailable (no codebase access, a failed fetch) so its verdict is low-confidence beyond the rubric's `judgment`/`visual` set; the user declined the write and the report was returned inline; the sync for an in-repo output path failed and the report went elsewhere. |
| `PASS` | All 32 principles were scored from full evidence (only the rubric's own `judgment`/`visual` flags remain) and `viral-evaluation.md` was written. |

`PASS` describes evaluation coverage, not product quality. A `PASS` run can score 12/100.

## Response shape (PASS or PARTIAL)

```text
Result: PARTIAL — <one-line reason>; Virality Score <NN>/100 (<Tier>), <n> top fixes
Evidence: landing page <url | file | evidence-dir>, codebase <path>; score from
          scripts/virality_score.py (<a> PASS / <b> PARTIAL / <c> FAIL); report at <path> | inline only
Uncertainty: <low-confidence items and what a human must eyeball; evidence sources not checked>
Decision: No approval needed to act on the report. To implement fixes, name the fix numbers —
          that is a separate task handed to a copy/frontend skill.
```

- `Result` comes first. Its reason names the cause of `PARTIAL` (for example "report returned
  inline; user declined the write").
- `Evidence` names the inputs actually read and the checks actually run. A high score is not
  evidence the product will spread; it is the rubric's tally.
- `Uncertainty` lists every low-confidence verdict. Never fold an assumption into a verified
  claim.
- `Decision` names the remaining user action. Adapt the last line when the user already gave
  one; do not invent an approval gate.

## Response shape (BLOCKED)

```text
Result: BLOCKED — <reason>
Evidence: <what was checked, e.g. "no URL, file or detectable landing page; no codebase path">
Uncertainty: nothing was scored; no principle has a verdict
Decision: Provide a landing page (URL, file or evidence-dir) or a codebase path.
```

## Step completion reports

The per-phase report in `references/step-reports.md` uses its own result words:

- `PASS` — every check of that phase is met.
- `PARTIAL` — the phase ended with a recorded gap, such as an unavailable evidence source.
- `FAIL` — a check is blocked and the run cannot continue; the run then ends `BLOCKED` when
  nothing was scored.

## Understanding criteria

Use these with correctness when grading an eval or reviewing a run. Negative-trigger evals
are excluded: they test that the skill did not run.

| Criterion | Observable check |
|---|---|
| Main result is findable | The first line states the status, the Virality Score and the fix count without opening the report file. |
| Facts and assumptions are separated | Verified claims name the inputs read; low-confidence verdicts and unchecked sources are labeled. |
| Claims are traceable | Each verdict and fix points to quoted product evidence; the score comes from the helper, not from prose. |
| Next decision is clear | The response names the remaining user action, or for `BLOCKED` the input to supply. |

Agent inspection cannot confirm human understanding. With no human feedback, record human
understanding as unconfirmed.
