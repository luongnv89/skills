# Final Report — tmux-agent-comms

Print the final report once per operation, after the Step Completion Report. The step report scores each gate; the final report tells the human what happened, what proves it, what is still unknown, and what they must decide.

## Four required parts, in this order

1. **`Result:`** — the status word first, then one line on what changed or was found.
   - `COMPLETE` — every requested operation met its phase's **Complete when** line. For a send, that means every target's reply was verified by a fresh joined marker and an independent capped-tail read.
   - `PARTIAL — <reason>` — the operation made at least one write (spawn, send, or kill), and after it one of these happened: a target ended blocked, stalled, timed out, or undelivered; a broadcast target was skipped or became unsafe; a HANDOFF failed; or the user declined a teardown.
   - `BLOCKED — <reason>` — the operation stopped before its first write: `tmux` missing, `$here` unresolved, a missing or ambiguous target, a preflight refusal on the only target, or a destructive action the user did not confirm.
2. **`Evidence:`** — only checks that ran, each with its command and observed result: `tmux has-session` or `tmux list-sessions`, each `preflight_send.py` and `wait_for_idle.py` exit code, the delivery check against the baseline, the completion marker, and the independent capped-tail read. Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts. A settled pane proves the agent stopped, not that its reply is correct; say so when a relayed reply was not checked against the task. List every session whose state is `unknown`, and every UNKNOWN context-gate reading. Write `none` only when nothing applies.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` Pending approvals include: answering a trust, auth, or permission dialog; confirming a teardown or `kill-server`; killing an unused successor session after a failed HANDOFF. Name any other remaining user action on its own line, such as running the printed `tmux attach-session` command.

Map the step report to the status: `Result: PASS` → `COMPLETE`; `PARTIAL` → `PARTIAL`; `FAIL` → `BLOCKED` when no write happened, otherwise `PARTIAL`.

## Example: an operation that stopped before any write

The `COMPLETE` example is in SKILL.md → *Example*.

```text
Result: BLOCKED — tests is on a trust dialog; the task was not sent
Evidence:
  tmux has-session -t myrepo-tests: exit 0
  preflight_send.py myrepo-tests: exit 3 (blocked: trust/auth/permission dialog)
Uncertainty: none
Decision: Answer the trust dialog in myrepo-tests, then ask me to resend the task.
  Remaining action: attach with `tmux attach-session -t myrepo-tests` in your own terminal.
```

## Reader checks

A final report passes review when a reader can:

1. **Find the main result** — the first line gives the status and what happened, without reading pane captures.
2. **Separate facts from assumptions** — each verified claim names its command or exit code; unknown session states, inferences, and unchecked replies sit under `Uncertainty:`.
3. **Trace every claim** — each outcome points to its evidence: typed text does not stand in for delivery, and a settled pane does not stand in for a verified reply.
4. **See the next decision** — `Decision:` names the approval needed, or states `No approval needed.`, and lists any remaining user action.

Human understanding stays unconfirmed until a user answers these checks. Agent inspection alone cannot confirm it.
