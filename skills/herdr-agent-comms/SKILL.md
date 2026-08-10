---
name: herdr-agent-comms
description: "Manage AI agent fleets in Herdr: split root + sub-agents into one tab as a tiled grid, message/wait/read via herdr CLI, steer any pane. Use for Herdr multi-agent fleets. Don't use for tmux, screen, or non-Herdr terminals."
license: MIT
compatibility: "Requires `herdr` on PATH and a running Herdr server (`herdr status`)."
effort: medium
metadata:
  version: 1.23.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Herdr Agent Comms

Build and control an AI-agent fleet in the root agent's Herdr tab. Keep the **root pane** as orchestrator; add each **sub-agent** as a right-hand split; equalize all columns; then send, wait, read, steer, or tear down through the `herdr` CLI.

Use Herdr concepts, not tmux assumptions. Prefer status-aware helpers and relay reply deltas rather than whole panes to protect the context and token budget.

## Choose the Workflow

| Request | Follow |
|---|---|
| Spawn sub-agents beside root | Phases 1–2, then 4–5 if assigning work |
| Message an existing agent | Phases 3–5 |
| Read without sending | Phase 3, then Phase 5 read only |
| Broadcast to a fleet | Phases 3 and 6 |
| Focus/steer a pane | Phase 3, then Phase 6 |
| Close workers | Phase 6 teardown |
| Main agent's own context is filling up | Phase 7 HANDOFF |

Read only the reference needed by that branch:

- See `references/herdr-recipes.md` for guarded grid spawning, equalization semantics, multi-line sends, focus, and troubleshooting.
- See `references/delivery-and-waiting.md` for preflight, completion markers, delivery verification, wait outcomes, and concurrent waits.
- See `references/context-succession.md` for the main agent's context gate, HANDOFF procedure, and handoff brief template.

## Check Prerequisites

1. Run `command -v herdr` and `herdr status`. If the server is unavailable, ask the user to start Herdr from a real terminal; never run bare `herdr` from a non-TTY shell.
2. Resolve the root pane, tab, and workspace from `HERDR_PANE_ID`, `HERDR_TAB_ID`, and `HERDR_WORKSPACE_ID`, or from `herdr pane current --current` and list/get commands.
3. Run agents directly in Herdr panes. Do not nest tmux when agent detection is required.
4. Treat the installed CLI as authoritative. Check uncertain commands with `herdr <group>` rather than inventing flags.

## Follow Non-Negotiable Rules

1. **Keep root as a role.** Never replace or close the root pane during fleet work. The one exception is a Phase 7 HANDOFF, where the orchestrator role migrates to a ready successor pane; even then the outgoing pane is retired to read-only, never closed without Rule 8 confirmation.
2. **Run exactly one orchestrator.** Only the current main agent writes to fleet panes. After a HANDOFF ack, the outgoing agent issues no further sends, splits, or closes — two orchestrators writing the same panes corrupt each other's baselines.
3. **Parse IDs.** Read opaque workspace/tab/pane IDs from JSON; never infer them from display order.
4. **Use one equal-width row.** Split the current rightmost pane `right`, keep every worker in the root tab, then run the equalizer. Create separate tabs only when the user explicitly requests isolation.
5. **Fail closed before writes.** Reject missing, ambiguous, `working`, `blocked`, malformed, or off-enum targets. Only a verified safe status may receive input.
6. **Wait before follow-ups.** Never send while an agent is working. Every follow-up gets a fresh baseline and completion marker.
7. **Surface blockers.** A trust, auth, or permission prompt needs a human; do not type a task or recovery Enter into it.
8. **Confirm destruction.** Closing panes, tabs, workspaces, or the server can lose work. Obtain explicit approval and preserve the orchestrator pane unless the user says otherwise.
9. **Gate your own context.** Self-check at every Phase 7 gate point; at or above the threshold, HANDOFF instead of continuing to fill this window.

## Phase 1 — Resolve Root Context

```bash
command -v herdr >/dev/null || { echo "Error: herdr is not installed" >&2; exit 1; }
herdr status || { echo "Error: Herdr server is unavailable" >&2; exit 1; }
root_pane="${HERDR_PANE_ID:?}"; root_tab="${HERDR_TAB_ID:?}"; ws="${HERDR_WORKSPACE_ID:?}"
```

Outside Herdr, list workspaces and agents, then choose the user-named or focused root. Resolve `project_dir` from the root pane's cwd, falling back to the current directory.

**Done when:** server status passes and concrete `root_pane`, `root_tab`, `ws`, and `project_dir` values are recorded.

## Phase 2 — Spawn and Ready the Fleet

Before spawning, define each worker's unique name, CLI/model settings, task, and expected deliverable. Launch the interactive CLI first; submit the task only after readiness passes.

Resolve the scripts directory by checking repo-local installs before global ones. Then use the canonical `spawn_sub` workflow in `references/herdr-recipes.md`:

1. Run `next_grid_split.py --root-pane "$root_pane"` to plan the rightmost split.
2. Split with `--direction right --no-focus` in `project_dir`.
3. Parse the new pane ID from JSON.
4. Run `next_grid_split.py --equalize --root-pane "$root_pane"`; abort on any error or non-convergence.
5. Rename the pane and agent, then launch the CLI with `herdr pane run`.
6. After all workers launch, run concurrent `wait_for_idle.py --ready` checks. Assign no work unless every worker returns 0.

Use `pi` with only its verified flags (`--model`, `--thinking`), and launch `claude` or `opencode` bare — do not pass mode flags at startup; any mode switching happens after startup and is owned by the caller's own protocol. For any other agent CLI, launch it bare rather than inventing flags. Do not attach the long task to the initial launcher argv.

**Done when:** every worker has a unique name and pane ID in `root_tab`, the layout widths differ by at most one cell, root remains active, and all readiness checks pass.

## Phase 3 — Resolve One Exact Target

Run `herdr agent get <name>` or `herdr pane get <pane-id>`. If a name is missing or ambiguous, list agents and ask; never silently retarget. Record both the name and pane ID and use that same pane ID for every later mutation.

**Done when:** one existing target resolves uniquely and its status is valid.

## Phase 4 — Send Safely

Follow the canonical baseline → marker → preflight → send → delivery-check sequence in `references/delivery-and-waiting.md`:

1. Capture `recent-unwrapped` output to a baseline file before sending.
2. Create a fresh split `HERDR_DONE_` completion marker.
3. Run `scripts/preflight_send.py` immediately before dispatch.
4. Submit with `herdr pane run "$pane_id" "$task"`.
5. Verify `working` status or transcript activity. Transcript activity may be prompt echo; only the joined marker proves completion.

For multi-line payloads or literal typing, use the guarded recipes in `references/herdr-recipes.md`. Re-run preflight immediately before any recovery Enter.

**Done when:** dispatch succeeded and status or transcript activity proves delivery; otherwise return a descriptive error.

## Phase 5 — Wait, Read, and Verify

Run `scripts/wait_for_idle.py` with the pre-send baseline and fresh completion marker. Handle its result: `0` completed, `1` error, `2` timeout, `3` blocked. Propagate non-zero results; do not report them as replies.

Accept `idle` or `done` after observed work. Read a capped `recent-unwrapped` transcript and relay only the relevant delta. On timeout, inspect `pane get`, `pane read`, and `agent explain`; stop after the bounded retry budget.

**Done when:** the requested reply is captured and verified, or blocked/timeout evidence is reported without further writes.

## Phase 6 — Broadcast, Steer, or Tear Down

- **Broadcast:** run `scripts/broadcast.sh "<task>" <targets...>`. It resolves targets, preflights, baselines, dispatches safe panes first, waits concurrently, and fails if any target is skipped or unsuccessful.
- **Steer:** focus with `herdr agent focus <name>`. For CLI follow-ups, repeat Phases 4–5 with a new baseline and marker.
- **Tear down:** after explicit confirmation, close only worker panes created by this run. Close the root tab, workspace, or server only when explicitly requested.

**Done when:** every requested target has a recorded outcome and destructive actions match the user's confirmed scope.

## Phase 7 — Hand Off the Orchestrator Role

Long fleet runs outlive one context window. Self-check your own usage at three gate points — before a spawn wave, before a broadcast, and after each relayed reply — never mid-cycle between a dispatch and its wait.

| Self-reported usage | Action |
|---|---|
| `P >= threshold` (default 50, overridable in conversation) | HANDOFF |
| `P < threshold` | Continue as main |
| UNKNOWN or unavailable | Count relayed reads and spawn waves; HANDOFF at 20 reads or 4 spawn waves |

HANDOFF spawns a successor with the same Phase 2 machinery — `main-g<N>` in the root tab, equalized, readiness-gated — then delivers a compact handoff brief through the Phase 4 cycle and waits for the ack `HANDOFF ACCEPTED gen=<N> fleet=<k>`. After the ack, that pane is the orchestrator; this pane goes read-only and announces the new one with `herdr agent focus main-g<N>`. A successor that fails readiness or never acks means the HANDOFF failed: stay main, report the orphan pane, and ask before closing it.

Read `references/context-succession.md` for the gate-point table, UNKNOWN fallback logging, full procedure, and the brief template. Never paste transcripts or diffs into a brief.

**Done when:** the gate decision is recorded with a percentage or an explicit UNKNOWN fallback, and any HANDOFF has a ready successor pane, a delivered brief, a received ack, and no write from the outgoing pane afterward.

## Verify Expected Output

Expected output for a successful fleet operation:

```text
Fleet: PASS
Root kept: w26:p1
Workers: reviewer=done, tests=idle
Layout: 3 equal-width columns
Replies: 2 captured, 0 blocked, 0 timed out
```

Acceptance criteria:

- `herdr status` succeeds and every target resolves uniquely.
- Root remains in its original pane and all default workers share its tab.
- Spawned columns are equal within one terminal cell.
- Every send passes preflight and every completed reply has delivery evidence.
- Every agent ends as completed, blocked, timed out, or failed—none disappear from the report.
- Errors and destructive confirmations are surfaced explicitly.
- The context gate is evaluated at each gate point, and any HANDOFF ends with exactly one acked orchestrator.

## Handle Edge Cases

- `blocked`: show the dialog and request human action.
- `unknown`: use the wait helper's stability fallback or install the integration.
- Name collision: suffix the requested name; never reuse an existing agent accidentally.
- More than four panes: warn that columns become cramped; change layout only with user approval.
- Unequal grid: rerun the equalizer and abort worker launch if it still fails.
- Wrong workspace or accidental tab: stop, preserve work, and ask before moving or closing panes.
- Successor never acks: HANDOFF failed—stay main, keep the fleet, and report the orphan pane before asking to close it.

## Emit the Step Completion Report

```text
◆ Herdr Agent Comms ([operation])
··································································
  Server:              √ pass
  Root resolved:       √ pass (pane · tab · workspace)
  Targets:             √ pass (N/N unique)
  Layout/readiness:    √ pass (if spawning; otherwise — n/a)
  Delivery:            √ pass (if sending; otherwise — n/a)
  Replies:             √ pass (done|idle · blocked/timeouts reported)
  Context gate:        √ pass (P% or UNKNOWN · continue | HANDOFF → main-gN)
  Destructive action:  — none (or confirmed scope)
  Result:              PASS | FAIL | PARTIAL
```
