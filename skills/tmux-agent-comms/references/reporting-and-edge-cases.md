# Step Completion Report & Edge Cases

The two output/recovery contracts moved out of SKILL.md so the body stays lean. SKILL.md keeps a one-line pointer at each section; the full definitions live here.

- Read the **Step Completion Report** section before emitting the report that closes every operation.
- Read the **Edge cases** section when a phase hits one of the named conditions — not preemptively.

## Step Completion Report

After each operation, emit only the applicable rows — never a row for a gate the operation did not run:

```text
◆ Tmux Agent Comms ([operation])
··································································
  Target resolved:     √ pass ([exact session])
  Preflight:           √ pass (idle)
  Baseline captured:   √ pass
  Message delivered:   √ pass (activity vs baseline)
  Completion marker:   √ pass (fresh and joined)
  Reply verified:      √ pass (bounded independent read)
  Context gate:        √ pass (P% or UNKNOWN · continue | HANDOFF → <folder>-main-gN)
  Destructive action:  — none (or: √ confirmed)
  Result:              PASS | FAIL | PARTIAL
```

`√` is pass, `×` is fail, `—` is context, `⚠` marks a recovered delivery or an escalated stall.

### Per-operation rows

| Operation | Rows to add |
|---|---|
| Spawn | `Session created`, `Ready gate` |
| Message / steer | the default rows above |
| Status | `Read-only` |
| Inspect | `Read-only`, plus the pane details |
| Broadcast | one `Message delivered` row per target session |
| Teardown | `Confirmed`, `Session killed` |
| HANDOFF | `Context gate`, `Successor ready`, `Brief delivered`, `Ack received` |

The report is part of the expected output: the requested reply or status **plus** this block — never raw unbounded scrollback.

## Edge cases

| Condition | Handling |
|---|---|
| Duplicate session name | Choose a collision-free name before spawn; check with `tmux has-session` first. |
| Trust/auth prompt | Exit 3. Show it to the human and stop — never type task text into a dialog. |
| Message unchanged after the recovery Enter | Report not delivered; do **not** start the reply wait. |
| Timeout, or a stable pane with no completion marker | Surface working vs stalled after a bounded independent read; never silently re-wait. |
| Follow-up message | Never reuse a deleted baseline or a marker already present in the transcript — mint a fresh pair. |
| Truncated capture | Widen `-S` stepwise; unbounded scrollback only as a last resort. |
| Human attached manually | Detach with `Ctrl-b d`; never kill a session merely to regain control. |
| Successor never acks a HANDOFF | The HANDOFF failed — stay main, keep the fleet, and report the unused session before asking to kill it. |
