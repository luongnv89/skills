# Final Report — herdr-agent

Print the final report once per run, after the Step Completion Report. The step report scores each check; the final report tells the human what happened, what proves it, what is still unknown, and what they must decide. A `help` request is exempt: it changes nothing, and its answer is the result.

## Four required parts, in this order

1. **`Result:`** — the status word first, then one line on what changed or was found.
   - `COMPLETE` — every requested operation met its phase's **Done when** line, and every target ended settled (`idle` or `done`).
   - `PARTIAL — <reason>` — the run made at least one fleet write, and at least one target ended blocked, stalled, timed out, failed, or skipped, or a HANDOFF failed, or the user declined a teardown.
   - `BLOCKED — <reason>` — the run stopped before its first fleet write: a failed prerequisite, a missing or ambiguous target, an aborted launch profile, a refused preflight on the only target, or a destructive action the user did not confirm.
2. **`Evidence:`** — only checks that ran, each with its command or source and the observed result: `herdr status`, the root pane ID, the launch-profile summary line, each target's outcome or error code, and the `fleet_status.py` snapshot. Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts. Always list each `UNKNOWN` model or thinking value, and any inherited permission bypass. A settled status proves the agent stopped, not that its reply is correct; say so when a relayed reply was not checked against the task. Write `none` only when nothing applies.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` Pending approvals include: answering a blocked trust, auth, or permission dialog; confirming a teardown; closing an orphan pane after a failed HANDOFF. Name any other remaining user action on its own line.

Map the step report to the status: `Result: PASS` → `COMPLETE`, `PARTIAL` → `PARTIAL`, and `FAIL` → `BLOCKED` when no fleet write happened, otherwise `PARTIAL`.

## Example: a run that stopped before any write

The `COMPLETE` example is in SKILL.md → *Verify Expected Output*.

```text
Result: BLOCKED — Herdr server unavailable; nothing was spawned or sent
Evidence:
  command -v herdr: /opt/homebrew/bin/herdr
  herdr status: failed (server not running)
Uncertainty: none
Decision: No approval needed.
  Remaining action: start Herdr from a real terminal, then re-run the request.
```

## Reader checks

A run's final report passes review when a reader can:

1. **Find the main result** — the first line gives the status and what happened, without reading pane transcripts.
2. **Separate facts from assumptions** — each verified claim names its command; `UNKNOWN` values, inferences, and unchecked replies sit under `Uncertainty:`.
3. **Trace every claim** — each outcome points to its evidence: a target's settled status does not stand in for a captured reply, and a sent prompt does not stand in for a settled one.
4. **See the next decision** — `Decision:` names the approval needed, or states `No approval needed.`, and lists any remaining user action.

Human understanding stays unconfirmed until a user answers these checks. Agent inspection alone cannot confirm it.
