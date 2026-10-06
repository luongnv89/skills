# Final response and run status

The chat response that closes a run. It sits beside the two artifacts and never replaces
them. In an orchestrated run the orchestrator relays this response; it never answers the
closing question for the user.

## Status rule

Apply the first row that matches. Use the same word as the `Executive Summary` outcome in
`UX_AX_REVIEW.md`; `BLOCKED` has no report, so it appears only in the chat response.

| Status | When |
|---|---|
| `BLOCKED` | No artifacts were written: the user gave no target or evidence after one request; or a sync failed for an output directory inside a git worktree and the user chose no external directory; or the user stopped the run. |
| `PARTIAL` | Artifacts were written and at least one holds: an aspect is `not-tested` for missing evidence, a missing tool or an access blocker (an aspect listed in `skip-checks` does not count); the validator was not run; the artifacts were returned inline; an unexpected change to the target is still unresolved. |
| `PASS` | Artifacts were written, the validator exited 0, and no aspect outside `skip-checks` is `not-tested`. |

`PASS` describes audit coverage, not product quality. A `PASS` audit can list many findings,
and a validator exit 0 alone never makes a run `PASS`: an audit with honest gaps is `PARTIAL`.

## Response shape (PASS or PARTIAL)

```text
Result: PARTIAL — <one-line reason>; <n> findings, <n> plan tasks
Top priorities: T1 <title> (P1) · T2 <title> (P2) · T3 <title> (P2)
Evidence: <output-dir>/UX_AX_REVIEW.md, <output-dir>/ux-ax-findings.json; validator exit 0 | not run;
          <n> surfaces inspected, <n> E records; target state unchanged | <disclosed change>
Uncertainty: not-tested <aspect ids>; hypotheses <F ids>; <tool limits, missing field data>
Decision: Would you like me to implement any of these fixes? Choose the finding/task IDs and scope.
```

- `Result` comes first. Its reason names the cause of `PARTIAL` (for example "no screenshots,
  so brand and responsive are not-tested").
- List only supported priorities. Fewer than three is correct when fewer exist.
- `Evidence` names checks that ran and their observed result. A validator exit 0 establishes
  structure only, not the truth of the findings.
- `Uncertainty` labels every hypothesis and every `not-tested` aspect. Never fold an
  assumption into a verified claim.
- `Decision` is the closing question, word for word. Then stop.

## Response shape (BLOCKED)

```text
Result: BLOCKED — <reason>
Evidence: <what was checked, e.g. "no URL, repository or evidence files in the request">
Uncertainty: nothing was audited; no aspect has a status
Decision: Provide a URL, repository path or evidence files (and an output directory if the target is a git checkout).
```

## Step completion reports

The per-step report in SKILL.md (*Completion report*) uses its own result words:

- `PASS` — every **Done when** check of that step is met.
- `PARTIAL` — the step ended with a recorded gap, such as a `not-tested` aspect.
- `FAIL` — a check is blocked and the run cannot continue; the run then ends `BLOCKED` if
  no artifacts were written.

## Understanding criteria

Use these with correctness when grading an eval or reviewing a run. Negative-trigger evals
are excluded: they test that the skill did not run.

| Criterion | Observable check |
|---|---|
| Main result is findable | The first line of the response and the `Executive Summary` state the status and the count of findings. |
| Facts and assumptions are separated | Observed findings cite `E` ids; hypotheses and `not-tested` aspects are labeled as such. |
| Claims are traceable | Each finding links to evidence and a plan task; a validator pass is not presented as proof of findings. |
| Next decision is clear | The response ends with the choice-of-IDs question, or for `BLOCKED` names the input the user must supply. |

Agent inspection cannot confirm human understanding. With no human feedback, record human
understanding as unconfirmed.
