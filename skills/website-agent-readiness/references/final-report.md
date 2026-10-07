# Final response and run status

The chat response that closes a run. It sits beside `agent-ready-plan.md` and never
replaces it. In an orchestrated run the orchestrator relays this response; it never
answers a gate for the user.

## Status rule

Apply the first row that matches — every reachable outcome has exactly one row.

| Status | When |
|---|---|
| `BLOCKED` | Nothing was scanned or planned: no URL after one ask; gate G1 declined; the target is unreachable by the scanner and no reachable alternative was approved; the user stopped the run before Phase 1 completed. |
| `PARTIAL` | A scan or triage was reported but no plan was written: gate G3 declined; the dependency preflight missed and the run stopped before Phase 3; the approved sync failed and the plan was not written; `render_plan.py` failed for a reason other than exit 3. Also: the plan was written but filing could not start — the Phase 4 lease acquire failed. |
| `PASS` | `agent-ready-plan.md` was written — filing done at G4, declined at G4, or not requested (Phase 4 is opt-in) — or `render_plan.py` exited 3 (nothing fileable) and the score was reported. |

`PASS` describes run completion, not site quality. A `PASS` run can report 0/5.

## Response shape (PASS or PARTIAL)

```text
Result: PARTIAL — <one-line reason>; score <n>/5 (<levelName>), <n> tasks across <phases>
Evidence: <url> scanned at <scannedAt> (fresh scan | reused from <evidence-dir>);
          triage.json <n> tasks; plan at <path> (grammar checks 3/3) | no plan written
Uncertainty: <deferred commerce checks, checks without scanner prose, issues not filed>
Decision: <the pending gate, or "No approval needed. Applying the fixes is a separate
          task — this skill never edits the target site.">
```

- `Result` comes first; its reason names the cause of `PARTIAL` (for example "plan not
  written; G3 declined").
- `Evidence` names the artifacts actually produced and the checks actually run. A high
  score is the scanner's tally, not proof the site works for agents.
- `Uncertainty` lists deferred commerce checks, checks left without scanner prose, and
  anything not verified. Never fold an assumption into a verified claim.
- `Decision` names the remaining user action — the next gate, or the filing the user
  declined. Do not invent an approval gate.

## Response shape (BLOCKED)

```text
Result: BLOCKED — <reason>
Evidence: <what was checked, e.g. "no URL supplied; none detectable in the request">
Uncertainty: nothing was scanned; no check has a status
Decision: Provide a publicly reachable URL to scan.
```

## Step completion reports

The per-phase report in `step-reports.md` uses its own result words: `PASS`, `PARTIAL`
(a gap recorded), and `FAIL` (the run cannot continue; it closes `BLOCKED` when nothing
was produced).

## Understanding criteria

Use these with correctness when grading an eval or reviewing a run. Negative-trigger
evals are excluded: they test that the skill did not run.

| Criterion | Observable check |
|---|---|
| Main result is findable | The first line states the status, the score and the task count without opening the plan file. |
| Facts and assumptions are separated | Verified claims name the artifacts read (`scan.json`, `triage.json`); deferred and unverified items are labeled. |
| Claims are traceable | The score comes from `scan.json`, the task count from `triage.json`, the grammar verdict from the checks in `plan-format.md`. |
| Next decision is clear | The response names the pending gate or the input to supply, or states that no approval is needed. |

Agent inspection cannot confirm human understanding. With no human feedback, record
human understanding as unconfirmed.
