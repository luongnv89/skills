---
name: rex-agent
description: "Manage AI agent fleets in a Rex terminal: tile root + workers in one tab, start/prompt/wait/read them, check what they do, steer fleet panes; `help` lists all. Don't use for Herdr, tmux, or one-off Rex tabs, splits or commands."
license: MIT
compatibility: "Requires the rex CLI on PATH and a running Rex server (`rex whoami`) for every operation except `help`, which runs no rex command. The server must offer the block program_status method and session.resize_pane; workers must report OSC 7501 program status (draft rev 0.4)."
effort: medium
metadata:
  version: 1.0.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Rex Agent

Build and control an AI-agent fleet in the root agent's Rex window. Keep the **root block** as orchestrator; add each **worker** as a right-hand column running the main agent's own launch profile; equalize all columns; then prompt, wait, read, monitor, steer, or tear down through the `rex` CLI and this skill's scripts.

A **session** holds **windows** (tabs), and a window holds **blocks** (panes). Rex has no agent registry and no prompt-and-wait call, so the scripts add both: a worker's **name** is its block label, and its **status** is the OSC 7501 program status record its own CLI reports. For everyday Rex commands outside fleet work, `rex skill show` prints the guide that matches the installed CLI. Relay reply deltas rather than whole screens to protect the context and token budget.

## Choose the Workflow

| Request | Follow |
|---|---|
| `help`, or what this does and how to drive it | Help in `references/help-request.md` — answer and stop |
| Spawn workers beside root | Phases 1–2, then 4–6 if assigning work |
| Message an existing agent | Phases 3–5 |
| Give several workers different tasks | Phases 3 and 7 (`dispatch`) |
| Read without sending | Phase 3, then Phase 5 read only |
| Check what the fleet is doing | Phase 6 |
| Broadcast to a fleet | Phases 3 and 7 |
| Focus/steer a pane | Phase 3, then Phase 7 |
| Close workers | Phase 7 teardown |
| Main agent's own context is filling up | Phase 8 HANDOFF |

Read only the reference needed by that branch:

- See `references/rex-recipes.md` for the layout, spawn variants, equal-width semantics, multi-line prompts, focus, troubleshooting, and edge cases.
- See `references/launch-profile.md` for where a worker's kind, model, thinking level, and flags come from, the kind gate, and what never carries over.
- See `references/delivery-and-waiting.md` for the per-kind status table, the prompt contract and exit codes, reading replies, the file fallback, and fleet monitoring.
- See `references/context-succession.md` for the main agent's context gate, HANDOFF procedure, and handoff brief template.
- See `references/final-report.md` for the closing report's status words, required parts, and examples.

## Answer a Help Request

Resolve this branch **before** Prerequisites: someone asking how this works may not have Rex installed yet. Take it on `help`, `--help`, `/rex-agent help`, or any plain question about what the skill does. Print the text in `references/help-request.md`, or for a narrower question (how to broadcast) answer from that one phase and name it. Run no `rex` command, change nothing, and emit no completion report.

**Done when:** the user has the summary or their specific answer, and no `rex` command ran.

## Check Prerequisites

1. Set `here` to the `scripts/` directory beside this SKILL.md. When the harness does not show the skill's base directory, use the resolver in `references/rex-recipes.md`.
2. Run `python3 "$here/agent.py" check`. It calls `rex whoami` with `--autostart=false`, because the default starts a missing server and a new empty server is not the user's. It confirms that `REX_SESSION` and `REX_BLOCK` name this terminal, and probes capabilities rather than versions (`rex version` is not semver): the block `program_status` method and `session.resize_pane`. On any failure it prints the fix, and the run ends `BLOCKED`. Outside a Rex terminal, never act on whatever session the app shows.
3. Treat the installed CLI as authoritative. Check an uncertain command with `rex <command> --help` rather than inventing flags; options from tmux or Herdr do not apply.

## Follow Non-Negotiable Rules

1. **Keep root as a role.** Never replace or close the root block during fleet work. The one exception is a Phase 8 HANDOFF, where the orchestrator role migrates to a ready successor block; even then the outgoing block is retired to read-only, never closed without Rule 8 confirmation.
2. **Run exactly one orchestrator.** Only the current main agent writes to fleet blocks. After a HANDOFF ack, the outgoing agent issues no further prompts, splits, or closes.
3. **Use full IDs.** Resolve a worker by exact label from `rex block ls --json`, then use its full `block:` ID for every later call. Never pass a bare name to `-b`: Rex falls back to ID suffixes, so a hex-only name such as `beef` can select another block.
4. **Use one equal-width row.** Split the rightmost column `right`, keep every worker in the root window, and equalize. Create separate windows only when the user explicitly requests isolation. If the window holds a pane stacked above or below another, stop and ask.
5. **Fail closed before writes.** Refuse a `working`, `blocked`, unverifiable (no fresh record), or agent-less target, and never write to your own block. A `done` record survives its agent exiting to the shell, so a record counts only while its owner is the block's foreground process.
6. **Wait before follow-ups.** Never prompt while an agent is working. Every follow-up is its own `agent.py prompt` cycle.
7. **Surface blockers.** A trust, auth, or permission prompt needs a human. Focus the block and tell the user; never answer the dialog for them, and never type into a block whose state you cannot verify.
8. **Confirm destruction.** Closing blocks, windows, or sessions can lose work. Obtain explicit approval and preserve the orchestrator block unless the user says otherwise. Never stop the Rex server or kill Rex processes.
9. **Gate your own context.** Self-check at every Phase 8 gate point; at or above the threshold, HANDOFF instead of continuing to fill this window.
10. **Mirror the main agent.** Start every worker, including a HANDOFF successor, on the **inherited launch profile**: the main agent's harness kind, model, thinking level, and setup flags. Change only what the user names concretely (a kind, model, thinking level, or flag) or a calling skill's launch contract requires; ask when a request is vague ("something cheaper"). A worker of another kind inherits nothing else. Unreadable same-kind setup flags abort the launch unless `--without flags` opts out.

## Phase 1 — Resolve Root Context

Record `session`, `root_block`, and `root_window` from the `check` output (`session_id`, `block_id`, `window_id`), and `project_dir` from its `cwd`, which is the root block's working directory. Every script defaults its session and root to `$REX_SESSION` and `$REX_BLOCK`, which persist between tool calls even when shell variables do not.

**Done when:** `agent.py check` exited 0 and concrete `session`, `root_block`, `root_window`, `project_dir`, and `here` values are recorded.

## Phase 2 — Spawn and Ready the Fleet

Before spawning, define each worker's unique name, task, and expected deliverable. Names must match `[a-z][a-z0-9_-]{0,31}`; a name already used in the session gets an epoch suffix.

Resolve the inherited launch profile once per spawn wave, as its own tool call, so the user sees it before any agent starts:

```bash
python3 "$here/launch_profile.py" --main-model "$main_model" --main-thinking "$main_thinking" >/dev/null
```

Set `main_model` and `main_thinking` to your own model ID and thinking level, and leave either one empty rather than guess. On Claude Code, leave `main_thinking` empty, because the script reads `CLAUDE_EFFORT`. Relay the summary line to the user before the first spawn, including any `⚠` or `warning:` line. If the user already declined bypass for this run, pass `--without bypass` on every worker. `references/launch-profile.md` has the source order and what never carries over.

Then start each worker with one `--start` call per worker (a loop over names is fine):

```bash
python3 "$here/launch_profile.py" --main-model "$main_model" --main-thinking "$main_thinking" \
  --start reviewer --cwd "$project_dir"
```

`--start` places and launches in one call: it refuses a layout that is not one row, splits the rightmost column `right` (`--focus=false --keep-open`), runs the worker as that block's command through the user's interactive shell with `REX_AGENT_ROLE=<name>` set, equalizes every column, and prints the worker's JSON only after the worker's own status reports `idle`. Exit 3 means the worker booted into a dialog: focus it and ask the human. Exit 1 means it failed; the message names the orphan block and shows its last screen lines. Add only what the user named: `--kind`, `--model`, `--thinking`, `--without bypass|flags`, `--new-window`, or native flags after `--`. Never fold the task into argv.

Use the `name` and `block_id` each start printed for every later call, because a taken name gets a suffix. Confirm the fleet with `python3 "$here/agent.py" fleet --fail-on-blocked` before assigning any work. If the user asked only for spawning, still send each worker the worker preamble (Phase 4) as its first prompt, so it knows its role before anyone types into it.

**Done when:** the launch-profile summary reached the user, and every start printed `"outcome": "ready"` with a unique name, a block ID in `root_window`, and equal `widths`, while root remained in its block.

## Phase 3 — Resolve One Exact Target

Run `python3 "$here/agent.py" get <name>`. It matches the exact label or a full `block:` ID and prints the block ID, kind, and status (the status table is in `references/delivery-and-waiting.md`). If a name is missing or ambiguous, list the fleet with `agent.py fleet` and ask; never silently retarget. Record the name and block ID and use that ID for every later mutation.

**Done when:** one existing target resolves uniquely, and its name, block ID, and current status are recorded.

## Phase 4 — Prompt Safely

```bash
python3 "$here/agent.py" prompt "$target_block" - --timeout 180 <<'EOF'
<task text>
EOF
```

One call refuses an unsafe target before writing anything, appends a turn tag `(rex-agent turn <id>)`, pastes the text, presses Enter, and waits for **this** turn to settle. Its JSON carries the `turn` ID for Phase 5. The quoted heredoc keeps `$` and backticks unexpanded. Give the shell call a timeout above `--timeout` (Claude Code's Bash default is 2 minutes: pass at least 210000 ms), or run long turns in the background. Exit codes: `0` settled, `3` blocked, `4` unverifiable, `5` no agent, `6` working, `7` stalled, `8` timeout, `9` exited; `references/delivery-and-waiting.md` has the full contract, `--raw`, and the response to each code.

Start each worker's **first** task with the worker preamble: `You are <name>, a worker in a Rex agent fleet. The orchestrator owns this session, its label, and its layout: do not rename the session or create, close, or type into other blocks.` Rex's session-start hook, when installed, tells every new agent to rename the session, and the workers share root's session.

**Done when:** the prompt printed `"outcome": "settled"`, or a named outcome was propagated.

## Phase 5 — Read and Verify

Map the failure first: `blocked` needs a human, `stalled` was submitted with no activity after it (inspect, never blindly resend), and `timeout` found no settled state inside the budget. Propagate each; never report it as a reply.

On success, read the rows after that turn's echo and relay only the relevant delta:

```bash
python3 "$here/agent.py" read "$target_block" --turn "$turn"
```

`rex capture` reads only the visible screen, and agent TUIs run on the alternate screen, so there is no scrollback to widen. `--turn` anchors on the tag the prompt appended, so a reply that repeats the task cannot move the anchor. Exit 4 means the reply pushed that tag off the screen: use the file fallback in `references/delivery-and-waiting.md` rather than re-reading.

**Done when:** the reply delta came from `agent.py read` after a settled outcome, or the blocked/stalled/timeout outcome is reported and nothing more was sent.

## Phase 6 — Monitor and Report

```bash
python3 "$here/agent.py" fleet
```

It lists every block in the root window (`--all`: every window) with status, kind, and message, blocked first. It polls each block in turn, so report it as "polled at <time>", not as an atomic snapshot, and re-run it rather than trusting memory of what was dispatched.

Rex itself shows spinners and blocked symbols on unfocused tab headers and marks sessions with finished or blocked work, so a worker's label is its badge. When a worker blocks, focus it with `rex focus -s "$session" <block_id>` and tell the user.

**Done when:** the current fleet state came from an `agent.py fleet` call made after the last dispatch.

## Phase 7 — Broadcast, Steer, or Tear Down

- **Broadcast:** run `python3 "$here/agent.py" broadcast "<task>" <targets...>` for one task, or `python3 "$here/agent.py" dispatch tasks.json` for a `{name: task}` object. Each resolves every target from one block listing, dedupes, refuses unsafe ones, prompts the rest concurrently, and prints one outcome and turn ID per target.
- **Steer:** focus with `rex focus -s "$session" <block_id>`. For UI keys such as dismissing a menu, use `rex send-key -s "$session" -b <block_id> escape`. For follow-ups, repeat Phases 4–5.
- **Tear down:** list the candidates with `agent.py fleet`: role `worker` marks a block started by `--start` (its process carries `REX_AGENT_ROLE`). After explicit confirmation, close only those worker blocks with `rex block close -s "$session" <block_ids...>`; never close `other` or `unknown` blocks unless the user names them. If the user declines or does not answer, close nothing and record the teardown as skipped. Close a window or session only when explicitly requested, and never close your own session without reporting first, because it disconnects you.

**Done when:** every requested target has a recorded outcome and destructive actions match the user's confirmed scope.

## Phase 8 — Hand Off the Orchestrator Role

Long fleet runs outlive one context window. Self-check your own usage at three gate points — before a spawn wave, before a broadcast, and after each relayed reply — never mid-cycle between a dispatch and its wait. HANDOFF when self-reported usage is at or above the threshold (default 50%); when usage is UNKNOWN, apply the counter fallback in the reference below.

HANDOFF starts a successor with the Phase 2 call (`launch_profile.py --start main-g<N>`, on your own profile), delivers a compact brief through the Phase 4 cycle, and reads back the ack `HANDOFF ACCEPTED gen=<N> fleet=<k>`, after which the successor waits. This block then sends `GO gen=<N>`, goes read-only, and focuses the successor with `rex focus`. A successor that fails to start or never acks means the HANDOFF failed: stay main, report the orphan block, and ask before closing it. `references/context-succession.md` has the gate-point table, UNKNOWN fallback, full procedure, and brief template; never paste transcripts or diffs into a brief.

**Done when:** the gate decision is recorded with a percentage or an explicit UNKNOWN fallback, and any HANDOFF has a ready successor block, a delivered brief, a received ack, a sent `GO`, and no write from the outgoing block afterward.

## Verify Expected Output

Expected final report for a successful fleet operation:

```text
Result: COMPLETE — spawned reviewer and tests; both replied
Evidence:
  agent.py check: ok · root kept block:…3f21 · 3 columns at 33.3%
  Profile: claude · claude-opus-5-5 · thinking max (inherited)
  agent.py fleet (polled 14:02): reviewer=done, tests=done · 2 replies read, 0 blocked, 0 timed out
Uncertainty: reply content relayed as written, not checked against the task
Decision: No approval needed.
```

Acceptance criteria:

- A `help` request prints the usage summary, runs no `rex` command, and emits no completion report.
- `agent.py check` passes (server, this terminal, capabilities) and every target resolves to one full block ID.
- Root remains in its original block and all default workers share its window.
- Spawned columns are equal within 0.2% of the window width, per the start's `widths`.
- Every worker runs the main agent's launch profile (kind, model, thinking level, setup flags) except fields the user named. UNKNOWN model/thinking values and inherited permission bypass are reported; unreadable same-kind setup flags fail closed unless explicitly disabled.
- Every prompt went through `agent.py prompt` (or `broadcast`/`dispatch`), which refused unsafe targets before writing, and returned a named outcome and turn ID.
- Every agent ends as settled, blocked, stalled, timed out, exited, unverifiable, or skipped — none disappear from the report.
- The closing status came from `agent.py fleet`, not from recollection.
- The context gate is evaluated at each gate point, and any HANDOFF ends with exactly one acked orchestrator.
- Every run except `help` ends with the final report, which passes its four reader checks: result on the first line, facts separated from assumptions, every claim traced to evidence, next decision named. Without user feedback, human understanding stays unconfirmed.

## Handle Edge Cases

Read `references/rex-recipes.md` → *Edge cases* when a target is `blocked`, `unverified`, or `exited`; a name collides or looks like an ID suffix; the window is not one row or exceeds four columns; a start hits a dialog or a rejected flag; the session is wrong; a successor never acks; or root argv is unreadable.

## Report the Run

Every run except `help` ends with two blocks from `references/final-report.md`: the Step Completion Report (one row per check: server, root, targets, launch profile, layout, delivery, replies, fleet status, context gate, destructive action), then the final report: `Result:` (`COMPLETE`, `PARTIAL — <reason>`, or `BLOCKED — <reason>`), `Evidence:` (only checks that ran), `Uncertainty:`, and `Decision:` (the approval needed, or `No approval needed.`).
