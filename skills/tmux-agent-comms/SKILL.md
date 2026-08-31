---
name: tmux-agent-comms
description: "Manage AI agents in tmux: spawn sessions, send messages, wait, capture replies, inspect fleets, and tear down safely. Use for tmux-hosted CLI agents. Don't use for SSH, GNU screen, or GUI apps."
license: MIT
compatibility: "Requires `tmux` on PATH. Optional Python 3 for wait/preflight/broadcast helpers."
effort: medium
metadata:
  version: 2.3.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Tmux Agent Comms

Manage CLI agents in separate tmux sessions. Treat each session as one agent; orchestrate it with `send-keys` and `capture-pane`. Relay reply deltas instead of whole screens to protect the context/token budget.

New sessions open in a terminal tab inside the current app by default. If the environment cannot open one, create the session detached and print the exact attach command. Never invoke `attach-session` from a non-TTY tool.

Use `herdr-agent-comms` instead when agents live in Herdr.

## When to Use

Route directly to the required mode; do not read unrelated references.

| Task | Start |
|---|---|
| Spawn an agent | Phase 1 |
| Message or steer an existing agent | Phase 2 |
| Read a pane, show status, or inspect | Phase 5 |
| Broadcast to a fleet | Phase 6 |
| Shut down an agent | Phase 6 |
| Main agent's own context is filling up | Phase 7 HANDOFF |

## Prerequisites

1. Run `command -v tmux`; stop with installation guidance if it fails.
2. Resolve helper scripts using `references/tmux-recipes.md` when messaging, waiting, or broadcasting.
3. Confirm the exact session and inspect its pane before writing to it.

## Critical Rules

1. **Confirm destructive actions.** Never send `exit`/`/quit`, kill a session, or kill the server without explicit approval.
2. **Fail closed before every send.** Only preflight exit 0 is sendable; every other code means do not send. Codes are defined once, in *the exit-code table* (`references/delivery-and-waiting.md`).
3. **Use a fresh proof cycle.** Every message needs a new baseline file and split completion marker. Never reuse either for a follow-up.
4. **Send text and Enter separately.** For multiline/code-heavy text, use tmux paste-buffer; see `references/tmux-recipes.md`.
5. **Bound waiting.** Use a wall-clock cap or at most 2–3 re-waits. Surface a stall instead of polling forever.
6. **Keep reads bounded.** Start with `capture-pane -S -40` and widen only when the reply is truncated.
7. **Escalate blocked panes.** A trust/auth/permission dialog requires a human; do not type task text into it.
8. **Run exactly one orchestrator.** Only the current main agent writes to fleet sessions. Orchestrator is a role, not a session: after a Phase 7 HANDOFF ack, the outgoing agent goes read-only and issues no further `send-keys`, spawns, or kills.
9. **Gate your own context.** Self-check at every Phase 7 gate point; at or above the threshold, HANDOFF instead of continuing to fill this window.

## Workflow

Run Phases 1–6 in order for a send. A read-only status/inspect operation may jump to Phase 5. Phase 7 is the orchestrator's own context gate, evaluated at its named gate points rather than in sequence.

### Phase 1 — Create or Discover

List sessions:

```bash
tmux list-sessions 2>/dev/null || echo "no tmux server running yet"
```

Name new sessions `<folder>-<short-task>` (for example, `myrepo-reviewer`). Avoid collisions with `tmux has-session` before creating one. Launch the requested interactive CLI in a new app terminal tab; if no tab facility exists, use detached mode and print `tmux attach-session -t <name>` for the human.

After spawn, require readiness before assigning work:

```bash
python3 "$here/wait_for_idle.py" "$name" --ready --timeout 60 --no-print
```

Read the result off *the exit-code table* in `references/delivery-and-waiting.md`; only exit 0 clears the session for work. Spawn fleets first, then check readiness concurrently. Read `references/tmux-recipes.md` for naming, tab/detached branches, script resolution, and fleet readiness.

**Complete when:** every created session has an exact name and passes the ready gate, or the failure is surfaced without sending work.

### Phase 2 — Resolve the Exact Target

```bash
tmux has-session -t "$target" 2>/dev/null
```

If missing, list sessions and ask on ambiguity; never guess. Use `session:window.pane` for a specific pane.

**Complete when:** one existing tmux target is confirmed.

### Phase 3 — Baseline, Preflight, and Send

Read `references/delivery-and-waiting.md` before sending. Follow its contract:

1. Capture `-S -80` to a temporary baseline file.
2. Mint a fresh suffix and define `completion_marker="TAC_DONE_$suffix"`.
3. Append an instruction that prints `TAC_DONE_` joined with the suffix only after completion.
4. Run `preflight_send.py` immediately before dispatch; send only on exit 0.
5. Send message text, then send `Enter` in a separate call.
6. Check once for post-send activity against the baseline. If unchanged, re-preflight before one recovery Enter; fail if still unchanged.

On multiline/code-heavy input, use paste-buffer rather than shell escaping. Always clean up temporary files on failure.

**Complete when:** post-send activity proves delivery, or a descriptive failure is surfaced. Typed text alone is not proof.

### Phase 4 — Wait and Verify

```bash
python3 "$here/wait_for_idle.py" "$target" --timeout 180 --scrollback 80 \
  --baseline-file "$baseline_file" --completion-marker "$completion_marker"
rc=$?
rm -f "$baseline_file"
```

Handle `rc` per *the exit-code table* in `references/delivery-and-waiting.md`. Before relaying an actionable result, independently compare two short capped-tail captures. Changing output/spinner means working; unchanged output without completion means stalled.

Read `references/delivery-and-waiting.md` for delivery recovery, wait modes, advisory verdicts, and the anti-deadloop budget.

**Complete when:** a fresh marker and independent bounded read verify the reply, or the bounded wait ends with an explicit state.

### Phase 5 — Read, Status, or Inspect

Read a reply with:

```bash
tmux capture-pane -t "$target" -p -S -40
```

Widen stepwise if capture starts mid-sentence; use unbounded scrollback only as a last resort. Relay substantive lines, not TUI chrome or old turns.

For **status**, remain read-only and report: agent ID, exact session, state (`in-progress`, `done`, `blocked`, `unknown`), short progress, start time, and workdir. For **inspect**, resolve one exact session, include a bounded tail and pane details, then print—but do not run—the human attach command.

Read `references/tmux-recipes.md` for classification commands, periodic fleet status, scrollback, and troubleshooting.

**Complete when:** the requested reply or status is concise, target-specific, and not truncated.

### Phase 6 — Continue, Broadcast, or Tear Down

- **Continue:** restart Phase 3 with a fresh baseline and marker.
- **Broadcast:** run `"$here/broadcast.sh" "<message>" <session...>`; it preflights, sends first, then waits concurrently. Do not serialize send/wait by agent.
- **Long fleet run:** emit a read-only status table about every five minutes within the same overall wait budget.
- **Tear down:** after explicit confirmation, prefer `tmux kill-session -t <name>` over `tmux kill-server`.

**Complete when:** every follow-up has an independent proof cycle, broadcast failures are reported per target, or confirmed teardown affects only named sessions.

### Phase 7 — Hand Off the Orchestrator Role

Long fleet runs outlive one context window. Self-check your own usage at three gate points — before a spawn wave, before a broadcast, and after each relayed capture — never mid-cycle between a send and its wait.

| Self-reported usage | Action |
|---|---|
| `P >= threshold` (default 50, overridable in conversation) | HANDOFF |
| `P < threshold` | Continue as main |
| UNKNOWN or unavailable | Count relayed reads and spawn waves; HANDOFF at 20 reads or 4 spawn waves |

HANDOFF spawns a successor with the same Phase 1 machinery — `<folder>-main-g<N>`, app terminal tab by default, ready-gated — then delivers a compact handoff brief through the Phase 3 cycle (paste-buffer, since it is multi-line) and waits for the ack `HANDOFF ACCEPTED gen=<N> fleet=<k>`. After the ack, that session is the orchestrator; this agent goes read-only and prints the successor's `tmux attach-session` command for the human. A successor that fails readiness or never acks means the HANDOFF failed: stay main, report the unused session, and ask before killing it.

Read `references/context-succession.md` for the gate-point table, UNKNOWN fallback logging, full procedure, and the brief template. Never paste transcripts or diffs into a brief.

**Complete when:** the gate decision is recorded with a percentage or an explicit UNKNOWN fallback, and any HANDOFF has a ready successor session, a delivered brief, a received ack, and no write from the outgoing agent afterward.

## Acceptance Criteria

- Every write targets a confirmed session and immediately follows a successful preflight.
- Every message has a fresh baseline, split marker, delivery check, bounded wait, and independent capped-tail verification.
- No blocked dialog receives task text; no destructive command runs without confirmation.
- Fleet sends and readiness checks run concurrently, with partial failures identified by session.
- The context gate is evaluated at each gate point, and any HANDOFF ends with exactly one acked orchestrator.
- The expected output is the requested reply/status plus the adapted Step Completion Report below—not raw unbounded scrollback.

## Example

```bash
target=reviewer
tmux has-session -t "$target" 2>/dev/null || { echo "Error: missing $target" >&2; exit 1; }
# Resolve $here, then follow references/delivery-and-waiting.md for the
# baseline → preflight → send → delivery → wait → verify cycle.
```

Expected result: the agent's new reply is relayed, the joined marker proves this turn completed, and the report records each gate.

## Edge Cases

Eight named conditions — duplicate session name, trust/auth prompt, an undelivered message after the recovery Enter, timeout or stalled pane, follow-up marker reuse, truncated capture, a manually attached human, and a successor that never acks. Read `references/reporting-and-edge-cases.md` when a phase hits one; do not read it preemptively.

## Step Completion Report

Every operation closes with the Step Completion Report block — the requested reply or status **plus** that block, never raw unbounded scrollback. Emit only the rows the operation actually ran. The block layout, the `√ × — ⚠` legend, and the per-operation row table are in `references/reporting-and-edge-cases.md`.

## References

- `references/delivery-and-waiting.md` — read for any send/wait cycle, recovery, marker contract, or timeout. Holds *the exit-code table*, the one definition of every helper exit code.
- `references/context-succession.md` — read at the context gate for the HANDOFF procedure and brief template.
- `references/tmux-recipes.md` — read only for script resolution, spawn modes, fleets, status/inspect, multiline sends, attach, scrollback, or troubleshooting.
- `references/reporting-and-edge-cases.md` — read for the Step Completion Report layout and when an edge case fires.
- `scripts/preflight_send.py` — fail-closed check before every send or recovery Enter.
- `scripts/wait_for_idle.py` — readiness and settled-reply waiter.
- `scripts/broadcast.sh` — safe concurrent fleet broadcast.
