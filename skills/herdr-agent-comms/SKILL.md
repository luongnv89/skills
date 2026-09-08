---
name: herdr-agent-comms
description: "Manage AI agent fleets in Herdr: tile root + sub-agents in one tab, start/prompt/wait/read via the herdr agent CLI, badge and monitor the fleet, steer any pane. Use for Herdr multi-agent fleets. Don't use for tmux, screen, or non-Herdr terminals."
license: MIT
compatibility: "Requires herdr 0.9.0 or later on PATH and a running Herdr server (`herdr status`). The agent surface (`agent start`, `agent prompt --wait`, `agent wait`) and `api snapshot` are load-bearing."
effort: medium
metadata:
  version: 2.0.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Herdr Agent Comms

Build and control an AI-agent fleet in the root agent's Herdr tab. Keep the **root pane** as orchestrator; add each **sub-agent** as a right-hand split; equalize all columns; then start, prompt, wait, read, monitor, steer, or tear down through the `herdr` CLI.

Use Herdr concepts, not tmux assumptions. Let the server do the work: `herdr agent prompt --wait` submits and waits in one request, `herdr agent wait` is event-driven, and `herdr api snapshot` reports the whole fleet in one call. Relay reply deltas rather than whole panes to protect the context and token budget.

## Choose the Workflow

| Request | Follow |
|---|---|
| Spawn sub-agents beside root | Phases 1–2, then 4–5 if assigning work |
| Message an existing agent | Phases 3–5 |
| Read without sending | Phase 3, then Phase 5 read only |
| Check what the fleet is doing | Phase 6 |
| Broadcast to a fleet | Phases 3 and 7 |
| Focus/steer a pane | Phase 3, then Phase 7 |
| Close workers | Phase 7 teardown |
| Main agent's own context is filling up | Phase 8 HANDOFF |

Read only the reference needed by that branch:

- See `references/herdr-recipes.md` for guarded grid spawning, equalization semantics, multi-line prompts, focus, and troubleshooting.
- See `references/delivery-and-waiting.md` for the one-call prompt contract, error codes, wait semantics, reading replies, and the no-agent fallback.
- See `references/fleet-monitoring.md` for snapshot status, sidebar badges, notifications, and the run report.
- See `references/context-succession.md` for the main agent's context gate, HANDOFF procedure, and handoff brief template.

## Check Prerequisites

1. Run `command -v herdr` and `herdr status`. If the server is unavailable, ask the user to start Herdr from a real terminal; never run bare `herdr` from a non-TTY shell.
2. Confirm `HERDR_ENV=1`. Outside a Herdr pane, do not inspect or control the focused session.
3. Resolve the root pane, tab, and workspace from `HERDR_PANE_ID`, `HERDR_TAB_ID`, and `HERDR_WORKSPACE_ID`, or from `herdr pane current --current` and list/get commands.
4. Run agents directly in Herdr panes. Do not nest tmux when agent detection is required.
5. Treat the installed CLI as authoritative. Check uncertain commands with `herdr <group>` rather than inventing flags. Client and server versions can differ after an update; `herdr status` says whether the server supports what you are about to use.

## Follow Non-Negotiable Rules

1. **Keep root as a role.** Never replace or close the root pane during fleet work. The one exception is a Phase 8 HANDOFF, where the orchestrator role migrates to a ready successor pane; even then the outgoing pane is retired to read-only, never closed without Rule 8 confirmation.
2. **Run exactly one orchestrator.** Only the current main agent writes to fleet panes. After a HANDOFF ack, the outgoing agent issues no further prompts, splits, or closes.
3. **Parse IDs.** Read opaque workspace/tab/pane IDs from JSON; never infer them from display order. A pane moved to another workspace gets a new ID.
4. **Use one equal-width row.** Split the current rightmost pane `right`, keep every worker in the root tab, then run the equalizer. Create separate tabs only when the user explicitly requests isolation.
5. **Fail closed before writes.** Herdr refuses a `blocked` target itself, but not a `working` one, and its wait tracks lifecycle state rather than one turn. Reject missing, ambiguous, `working`, or unverifiable targets yourself before dispatching.
6. **Wait before follow-ups.** Never prompt while an agent is working. Every follow-up is its own `agent prompt --wait` cycle.
7. **Surface blockers.** A trust, auth, or permission prompt needs a human. Focus the pane, notify, and never answer the dialog for them.
8. **Confirm destruction.** Closing panes, tabs, workspaces, or the server can lose work. Obtain explicit approval and preserve the orchestrator pane unless the user says otherwise.
9. **Gate your own context.** Self-check at every Phase 8 gate point; at or above the threshold, HANDOFF instead of continuing to fill this window.

## Phase 1 — Resolve Root Context

```bash
command -v herdr >/dev/null || { echo "Error: herdr is not installed" >&2; exit 1; }
test "${HERDR_ENV:-}" = 1 || { echo "Error: not running inside a Herdr pane" >&2; exit 1; }
herdr status || { echo "Error: Herdr server is unavailable" >&2; exit 1; }
root_pane="${HERDR_PANE_ID:?}"; root_tab="${HERDR_TAB_ID:?}"; ws="${HERDR_WORKSPACE_ID:?}"
```

Resolve `project_dir` from the root pane's cwd, falling back to the current directory. Resolve the skill's `scripts/` directory by probing repo-local installs before global ones.

**Done when:** server status passes and concrete `root_pane`, `root_tab`, `ws`, and `project_dir` values are recorded.

## Phase 2 — Spawn and Ready the Fleet

Before spawning, define each worker's unique name, agent kind, task, and expected deliverable. Placement and launch are two steps: `herdr agent start` never creates or moves layout, and requires a pane already sitting at its shell prompt.

Use the canonical `spawn_sub` workflow in `references/herdr-recipes.md`:

1. Run `next_grid_split.py --root-pane "$root_pane"` to plan the rightmost split.
2. Split with `--direction right --no-focus` in `project_dir`, passing `--env "HERDR_ROLE=<name>"` so the worker can read its own role instead of being told it in every prompt.
3. Parse the new pane ID from JSON.
4. Run `next_grid_split.py --equalize --root-pane "$root_pane"`; abort on any error or non-convergence.
5. Rename the pane, then `herdr agent start <name> --kind KIND --pane <id> --timeout 60000`.
6. Badge the worker with its job: `python3 scripts/badge.py <name> --title "<job>" --token role=<role>`.

`agent start` **is** the readiness gate: it returns only once Herdr detects the expected agent and considers it interactive-ready, and returns `agent_not_ready` immediately if the agent booted into a dialog. There is no separate readiness pass. Names must match `[a-z][a-z0-9_-]{0,31}` and be unique among live agents. Pass native agent flags only after `--`; never fold the task into argv.

Confirm the fleet with `python3 scripts/fleet_status.py --tab "$root_tab" --fail-on-blocked` before assigning any work.

**Done when:** every worker has a unique name and pane ID in `root_tab`, the layout widths differ by at most one cell, root remains active, and every `agent start` returned success.

## Phase 3 — Resolve One Exact Target

Run `herdr agent get <name>` or `herdr pane get <pane-id>`. If a name is missing or ambiguous, list agents and ask; never silently retarget. `agent_not_found` means the pane hosts no detected agent — start one, or take the pane-surface fallback in `references/delivery-and-waiting.md`. Record both the name and pane ID and use that same ID for every later mutation.

**Done when:** one existing target resolves uniquely and its status is valid.

## Phase 4 — Prompt Safely

```bash
python3 "$here/preflight_send.py" "$target" >/dev/null || exit $?
herdr agent prompt "$target" "$task" --wait --timeout 180000
```

The preflight refuses `working` (2), `blocked` (3), unverifiable (4), and no-agent (5) targets. The prompt then submits text plus Enter as one ordered write honoring bracketed paste, refuses a blocked target server-side before writing anything, gates on observed activity, and waits for the first settled state — all in one request. That is why this skill no longer captures a transcript baseline or plants a completion marker: there is no gap between send and wait to race.

Do not add `--until idle --until done`; those are the `--wait` defaults. Use `--until` only for a state-specific wait such as `--until blocked`.

**Done when:** the prompt returned success, or a named error code was propagated.

## Phase 5 — Read and Verify

Map the failure first. `agent_blocked` means nothing was sent and a human is needed. `agent_prompt_stalled` means it was submitted but no activity followed — inspect, never blindly resend. `timeout` means no settled state inside the budget. Propagate all three; do not report them as replies.

On success, read a capped transcript and relay only the relevant delta:

```bash
herdr agent read "$target" --source recent-unwrapped --lines 80
```

Accept `idle` or `done` as settled; they differ only in whether the completion has been marked seen. If raising `--lines` reveals no more output, the agent is on the terminal's alternate screen — use the file fallback in `references/delivery-and-waiting.md` rather than a bigger line count.

**Done when:** the requested reply is captured and verified, or blocked/stalled/timeout evidence is reported without further writes.

## Phase 6 — Monitor and Report

```bash
python3 "$here/fleet_status.py" --tab "$root_tab"
```

One `herdr api snapshot` call renders every agent's status, badge and title, sorted by attention, at flat cost for any fleet size. Prefer it over per-agent `herdr agent get` polling, which costs N round trips and can report a fleet state that never existed at one instant.

Keep the human oriented without making them read panes:

- **Badge** each worker as its job changes: `python3 scripts/badge.py <name> --token phase=<phase>`. Display-only, so it never perturbs waits or rollups.
- **Notify** only for events that need them: `herdr notification show "Agent blocked" --body "<name> needs input" --sound request`, and once at run completion with `--sound done`.

See `references/fleet-monitoring.md` for field caps, token semantics, and workspace-level rollups.

**Done when:** the current fleet state came from a snapshot call, not from memory of what was dispatched.

## Phase 7 — Broadcast, Steer, or Tear Down

- **Broadcast:** run `scripts/broadcast.sh "<task>" <targets...>`. It resolves all targets from one `agent list`, dedupes, refuses unsafe ones, dispatches `agent prompt --wait` concurrently, and maps every error code to a reason. `HAC_BADGE=1` badges each row with its phase.
- **Steer:** focus with `herdr agent focus <name>`, which also marks that agent's completion seen. For follow-ups, repeat Phases 4–5.
- **Tear down:** after explicit confirmation, close only worker panes created by this run. Close the root tab, workspace, or server only when explicitly requested. Never run `herdr server stop` from an active session unless the user intends to stop every pane process.

**Done when:** every requested target has a recorded outcome and destructive actions match the user's confirmed scope.

## Phase 8 — Hand Off the Orchestrator Role

Long fleet runs outlive one context window. Self-check your own usage at three gate points — before a spawn wave, before a broadcast, and after each relayed reply — never mid-cycle between a dispatch and its wait.

| Self-reported usage | Action |
|---|---|
| `P >= threshold` (default 50, overridable in conversation) | HANDOFF |
| `P < threshold` | Continue as main |
| UNKNOWN or unavailable | Count relayed reads and spawn waves; HANDOFF at 20 reads or 4 spawn waves |

HANDOFF spawns a successor with the same Phase 2 machinery — `main-g<N>` in the root tab, equalized, started through `agent start` — then delivers a compact handoff brief through the Phase 4 cycle and waits for the ack `HANDOFF ACCEPTED gen=<N> fleet=<k>`. After the ack, that pane is the orchestrator; this pane goes read-only and announces the new one with `herdr agent focus main-g<N>`. A successor that fails to start or never acks means the HANDOFF failed: stay main, report the orphan pane, and ask before closing it.

Read `references/context-succession.md` for the gate-point table, UNKNOWN fallback logging, full procedure, and the brief template. Never paste transcripts or diffs into a brief.

**Done when:** the gate decision is recorded with a percentage or an explicit UNKNOWN fallback, and any HANDOFF has a ready successor pane, a delivered brief, a received ack, and no write from the outgoing pane afterward.

## Verify Expected Output

Expected output for a successful fleet operation:

```text
Fleet: PASS
Root kept: w26:p1
Workers: reviewer=settled, tests=settled
Layout: 3 equal-width columns
Replies: 2 captured, 0 blocked, 0 timed out
```

Acceptance criteria:

- `herdr status` succeeds and every target resolves uniquely.
- Root remains in its original pane and all default workers share its tab.
- Spawned columns are equal within one terminal cell.
- Every prompt passed preflight and returned either success or a named error code.
- Every agent ends as settled, blocked, stalled, timed out, failed, or skipped — none disappear from the report.
- The closing status came from `fleet_status.py`, not from recollection.
- Errors and destructive confirmations are surfaced explicitly.
- The context gate is evaluated at each gate point, and any HANDOFF ends with exactly one acked orchestrator.

## Handle Edge Cases

- `blocked`: focus the pane, notify, and request human action.
- `agent_not_found`: no detected agent in that pane — `agent start` it, or drop to the pane-surface fallback.
- `unknown` status: `herdr integration status`, then `herdr agent explain <target> --json` to see which rule matched.
- Name collision: suffix the requested name; never reuse an existing agent accidentally.
- More than four panes: warn that columns become cramped; change layout only with user approval.
- Unequal grid: rerun the equalizer and abort worker launch if it still fails.
- Wrong workspace or accidental tab: stop, preserve work, and ask before moving or closing panes.
- Successor never acks: HANDOFF failed — stay main, keep the fleet, and report the orphan pane before asking to close it.

## Emit the Step Completion Report

```text
◆ Herdr Agent Comms ([operation])
··································································
  Server:              √ pass
  Root resolved:       √ pass (pane · tab · workspace)
  Targets:             √ pass (N/N unique)
  Layout/readiness:    √ pass (if spawning; otherwise — n/a)
  Delivery:            √ pass (if prompting; otherwise — n/a)
  Replies:             √ pass (settled · blocked/stalled/timeouts reported)
  Fleet snapshot:      √ pass (N agents · statuses)
  Context gate:        √ pass (P% or UNKNOWN · continue | HANDOFF → main-gN)
  Destructive action:  — none (or confirmed scope)
  Result:              PASS | FAIL | PARTIAL
```
