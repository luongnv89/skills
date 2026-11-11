# Final Report — hc-agent

Print the Step Completion Report, then the final report, once per run. The step report scores each check; the final report tells the human what happened, what proves it, what is still unknown, and what they must decide. A `help` request is exempt: it changes nothing, and its answer is the result.

## The Step Completion Report

Print it first, filling each row from a check that ran this run:

```text
◆ hc Agent ([operation])
··································································
  Prerequisites:       √ pass (agent.py check: hc, herdr-app, HC_TERMINAL_ID)
  Root resolved:       √ pass (terminal · pane · space · tab)
  Targets:             √ pass (N/N unique, all in the root's tab)
  Launch profile:      √ pass (kind · wrapper · model · thinking · N flags; UNKNOWN and ⚠ named — if spawning; otherwise — n/a)
  Layout/focus:        √ pass (N ready · focus restored — if spawning; otherwise — n/a)
  Delivery:            √ pass (if prompting; otherwise — n/a)
  Replies:             √ pass (settled · blocked/stalled/timeouts reported)
  Fleet status:        √ pass (N agents · statuses · polled at time)
  Context gate:        √ pass (P% or UNKNOWN · continue | HANDOFF → main-gN)
  Destructive action:  — none (or confirmed scope)
  Result:              PASS | FAIL | PARTIAL
```

## Four required parts of the final report, in this order

1. **`Result:`** — the status word first, then one line on what changed or was found.
   - `COMPLETE` — every requested operation met its phase's **Done when** line, and every target ended settled (`idle` or `done`).
   - `PARTIAL — <reason>` — the run made at least one fleet write, and after it one of these happened: a target ended blocked, stalled, timed out, exited, unverifiable, or skipped; focus did not come back after a split; a HANDOFF failed; or the user declined a teardown.
   - `BLOCKED — <reason>` — the run stopped before its first fleet write: a failed `agent.py check`, `HERDR_ENV=1` (routed to herdr-agent), a missing or ambiguous target, an aborted launch profile, a refused preflight on the only target, or a destructive action the user did not confirm.
2. **`Evidence:`** — only checks that ran, each with its command or source and the observed result: `agent.py check`, the root terminal and pane, the launch-profile summary line, each start's `terminal`, `outcome` and `focus_restored`, each target's outcome and turn ID, and the closing `agent.py fleet` table with its poll time. Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts. Always list each `UNKNOWN` model or thinking value, any inherited permission bypass, a wrapper that was kept or dropped (only `mcc run --` was run live), and column widths, which the app manages and nothing measured. A settled status proves the agent stopped, not that its reply is correct; say so when a relayed reply was not checked against the task. Write `none` only when nothing applies.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` Pending approvals include: answering a blocked trust, auth, or permission dialog; confirming a teardown; closing an orphan pane after a failed start or HANDOFF. Name any other remaining user action on its own line.

Map the step report to the status: `Result: PASS` → `COMPLETE`, `PARTIAL` → `PARTIAL`, and `FAIL` → `BLOCKED` when no fleet write happened, otherwise `PARTIAL`.

## Example: a run that stopped before any write

The `COMPLETE` example is in SKILL.md → *Verify Expected Output*.

```text
Result: BLOCKED — this is a Herdr TUI pane (HERDR_ENV=1); nothing was spawned or sent
Evidence:
  agent.py check: failed (HERDR_ENV=1: use the herdr-agent skill instead)
Uncertainty: none
Decision: No approval needed.
  Remaining action: re-run the request with herdr-agent.
```

## Example: a run with a blocked worker

```text
Result: PARTIAL — tests replied; reviewer is waiting on a permission dialog
Evidence:
  agent.py prompt tests: settled (done) in 41.2 s
  agent.py prompt reviewer: blocked · "approve Bash: npm install"
  agent.py fleet (polled 14:07): reviewer=blocked, tests=done
Uncertainty: the tests reply was relayed as written, not checked against the suite
Decision: Answer reviewer's permission dialog (shown with agent.py focus); I will not answer it.
```

## Reader checks

A run's final report passes review when a reader can:

1. **Find the main result** — the first line gives the status and what happened, without reading pane screens.
2. **Separate facts from assumptions** — each verified claim names its command; `UNKNOWN` values, inferences, and unchecked replies sit under `Uncertainty:`.
3. **Trace every claim** — each outcome points to its evidence: a settled status does not stand in for a read reply, and a sent prompt does not stand in for a settled one.
4. **See the next decision** — `Decision:` names the approval needed, or states `No approval needed.`, and lists any remaining user action.

Human understanding stays unconfirmed until a user answers these checks. Agent inspection alone cannot confirm it.
