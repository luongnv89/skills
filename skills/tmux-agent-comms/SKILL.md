---
name: tmux-agent-comms
description: "Manage AI agents in tmux: spawn sessions in current app terminal tabs by default; message CLI agents via send-keys/capture-pane; read replies; kill sessions. Use to launch fleets or talk to running agents. Don't use for SSH, screen, or GUI apps."
license: MIT
effort: medium
metadata:
  version: 1.9.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Tmux Agent Comms

Manage and talk to AI agents (another Claude Code, Gemini CLI, Codex, pi-agent, or any CLI) running in separate tmux sessions: **create** sessions, **send** messages, **wait** for the agent to finish, **capture** replies, **check status**, **inspect** sessions, and **tear down** when done.

Default spawn behavior: each new tmux session opens in a **new terminal tab inside the current app/environment** where this skill is invoked. The tab is a visible terminal attached to that tmux session; it is not an external Terminal.app/iTerm/xterm window unless the user explicitly asks.

Mental model: each tmux session is one agent. You orchestrate from outside by writing to its input and reading its pane — what a human does by switching windows, but scripted. Your context budget is finite, so relay each agent's answer, not its whole screen (the bundled helper extracts just the reply delta).

## When to Use

Launching agents in tmux, messaging an agent in another session, broadcasting to a fleet, checking fleet status, inspecting a managed session, or reading what an agent replied. Don't use for SSH/remote shells, GNU `screen`, or driving a GUI app.

## Workflow

Six phases, in order: discover/spawn a session, resolve the exact target, send the message, wait for the reply to settle, capture it, then continue or tear down.

**Jump straight to the phase for your task** — don't read the rest:

| Your task | Start at |
|---|---|
| Spawn a new agent session | Phase 1 |
| Message an agent that's already running | Phase 2 |
| Just read a running agent's pane (no send) | Phase 5 |
| Show fleet status | Phase 5 ("Status and Inspect") |
| Inspect one agent and get an attach command | Phase 5 ("Status and Inspect") |
| Broadcast the same message to a fleet | Phase 6 ("Broadcast to a fleet") |
| Shut an agent down | Phase 6 ("Tear down") |

## Prerequisites

- **tmux installed**: `command -v tmux` must succeed. If missing, tell the user to install it (`brew install tmux` / `apt install tmux`) and stop.
- **You operate sessions you can't see.** Always confirm a session exists and inspect its pane before assuming a message landed.

## Critical Rules

1. **Confirm before destructive/irreversible actions.** Killing a session or sending `exit`/`/quit` can lose that agent's work — never without explicit user go-ahead. Reading a pane is always safe; writing is not.
2. **Verify the target before sending.** Resolve the exact session with `has-session` first (Phase 2) — a typo sends keystrokes nowhere or to the wrong agent.
3. **Wait for the agent, don't race it.** Sending a follow-up while it's still working corrupts input. Wait until the pane settles (Phase 4) before reading or sending again.
4. **Escape what you send.** `send-keys` and the shell both interpret special characters. Follow the escaping rules in Phase 3 or messages get mangled — or worse, execute.
5. **New sessions open visibly by default.** Spawn new agent sessions in a fresh terminal tab provided by the current app/environment, attached to the tmux session. If the environment cannot open an app terminal tab, create the session detached and print the exact attach command for the user; never run `attach-session` yourself from a non-TTY shell.
6. **Default startup is autonomous and non-blocking.** Opening a visible app tab is for human observation; the orchestrator still continues with readiness checks and scripted messaging. Don't wait at startup for a human unless the user explicitly asks for interactive mode.

## Phase 1: Create or Discover Sessions

```bash
tmux list-sessions 2>/dev/null || echo "no tmux server running yet"
```

Match the target against this list (Phase 2). New sessions use the predictable pattern **`<folder>-<short-task-name>`**: folder is the current project/workspace folder, and short task is a concise slug like `reviewer`, `tests`, or `docs`. This keeps `status`, `inspect`, and attach commands grep-friendly.

To spawn, resolve a free name first because `tmux new-session` **fails if the name is taken** (exit 1):

```bash
slug() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g'; }
folder="$(slug "$(basename "$PWD")")"
task="$(slug "${short_task_name:-reviewer}")"
name="${folder}-${task}"
project_dir="$PWD"
agent_cmd="${TAC_AGENT_CMD:-claude}"
tmux has-session -t "$name" 2>/dev/null && name="${name}-$(date +%s)"   # avoid collision
```

**Default: open a new app terminal tab.** Use the terminal-tab facility of the current app/environment where the skill is running (IDE terminal tab, coding-agent terminal tab, or equivalent). The new tab's command should create/attach the tmux session and launch the agent there:

```bash
cd "$project_dir" && exec tmux new-session -s "$name" -c "$project_dir" "$agent_cmd"
```

The tab itself is the live terminal for that session. Do **not** open an external OS terminal app unless the user explicitly requests it, and do not confuse this with creating a tmux window/tab inside an existing session.

If the current environment does not expose a way for the agent to open an app-integrated terminal tab, or the user asked for a **detached/background** fleet, fall back to a detached spawn and immediately give the user the exact command to run in a new terminal tab inside the same app:

```bash
tmux new-session -d -s "$name" -c "$project_dir"
tmux send-keys -t "$name" "$agent_cmd" Enter
printf 'Open a new terminal tab in this app and run: cd %q && tmux attach-session -t %q\n' "$project_dir" "$name"
```

**Startup mode:** autonomous/non-blocking is the default for pi-agent, Claude, Codex, Gemini, and other CLIs. Use `TAC_STARTUP_MODE=autonomous|interactive` as the global default when present; a per-launch user request like `--interactive` or "show me the setup first" overrides it. In autonomous mode, open the visible app tab when available (or detached fallback), then immediately continue to readiness checks — never park the orchestrator on an interactive startup question. In interactive mode, ensure the session is visible (app tab or printed attach command) and stop before scripted sends.

**"Spawned" ≠ "ready"** — a fresh agent often boots through a trust/auth prompt. Don't send blind; run the wait helper (Phase 4): exit `0` means ready, exit `3` means it's parked on a prompt to surface to the user rather than type into.

```bash
python3 scripts/wait_for_idle.py "$name" --timeout 30 --no-print; echo "ready=$?"
```

For a **fleet**, repeat with distinct task slugs under the same folder prefix (`myrepo-reviewer`, `myrepo-tests`, `myrepo-docs`). The visible-tab default applies to each newly spawned session unless the user asks for a detached/background fleet.

**Showing an existing agent's terminal** (human-only): if a session already exists without a visible tab, the human can run `tmux attach-session -t "$name"` or `tmux switch-client -t "$name"` from an interactive terminal. The agent invoking either itself will fail (no TTY / no attached client). Detach with `Ctrl-b d` to return control without killing the session. See `references/tmux-recipes.md` ("Showing an agent's live terminal") for the when-to-use table and worked example.

## Phase 2: Resolve the Exact Target

```bash
tmux has-session -t agent1 2>/dev/null && echo "OK: agent1 exists" || echo "MISSING: agent1"
```

If missing, run `tmux list-sessions` and pick the closest match — surface any substitution to the user rather than guessing. To target a specific window/pane, use `session:window.pane` (e.g. `-t agent1:0.1`); a bare session name targets the active pane, which is enough for single-pane agents.

## Phase 3: Send a Message

```bash
tmux send-keys -t agent1 "summarize the changes in src/" Enter
```

**Escaping:** wrap the message in double quotes; a raw `;` is read by tmux as a command separator, and `$`/backticks/`"` are still expanded by the shell inside double quotes — escape them or use single quotes when the message has none of its own. For newlines or code, write to a file and load it instead of fighting escaping — see `references/tmux-recipes.md` ("Sending multi-line or code-heavy messages").

**Separate-Enter gotcha:** some TUIs don't submit when `Enter` rides the same call. If typed but not sent, send `Enter` alone: `tmux send-keys -t agent1 Enter`.

**Verify delivery before you wait.** On-screen text proves it was *typed*, not submitted — it looks identical either way. The reliable signal is **post-send activity**. Run one bounded check (a single ~5s delay, then one capture — never a poll loop):

```bash
tmux send-keys -t agent1 "..."; tmux send-keys -t agent1 Enter; sleep 5
tmux capture-pane -t agent1 -p -S -40 | grep -Eq 'esc to interrupt|[⠁-⣿]' \
  && echo delivered || echo NOT-DELIVERED
```

`delivered` → proceed to Phase 4. `NOT-DELIVERED` → send a lone `Enter` and re-check; if still nothing, re-type. This is distinct from a Phase 4 reply timeout — nothing was submitted, so don't start waiting. Full rationale: `references/delivery-and-waiting.md`.

## Phase 4: Wait for the Reply, Then Read It

A fixed `sleep` wastes time or reads a half-written reply. The bundled helper polls until the pane stops changing, then prints only the new lines since the wait started — the reply delta, not the surrounding chrome:

```bash
python3 scripts/wait_for_idle.py agent1
```

Branch on the exit code: **0 idle** (settled, relay the printed delta), **3 blocked** (parked on a prompt needing a human — don't send, surface it, Rule 1), **2 timeout** (never settled within `--timeout`; bounds one wait, not a loop). For chrome that differs from the defaults, tune `--busy-marker`/`--block-marker` (or `TAC_BUSY_MARKERS`/`TAC_BLOCK_MARKERS`) — run `--help` for the rest.

**The verdict is advisory.** Before relaying a result the user will act on, or on any timeout, do an independent read: capture the pane, `sleep 3`, capture again. Captures differ, or either shows `esc to interrupt`/a spinner glyph → still working (keep waiting, don't send). Captures are byte-identical with no spinner marker → stalled (surface it, don't silently re-wait).

**Anti-deadloop:** set a hard overall budget (e.g. 2–3 re-waits or a wall-clock cap) before you start; when it's spent, stop and escalate — never poll indefinitely. No Python? Fall back to capture / `sleep 3` / capture / compare under the same budget. Full details: `references/delivery-and-waiting.md`.

## Phase 5: Read More (capped-tail capture)

When you need to read the pane yourself beyond the helper's delta, default to a capped tail (a fixed line-count window — distinct from Phase 3's one-shot delivery check, which is "bounded" in the no-poll-loop sense), not the bare pane or unbounded scrollback:

```bash
tmux capture-pane -t agent1 -p -S -40       # ~40 scrollback lines + visible pane
```

If the capture starts mid-sentence, the reply exceeded the window — widen stepwise (`-S -80`, ...). Only fall back to unbounded `-S -` when even a wide tail truncates — see `references/tmux-recipes.md` ("Reading scrollback robustly").

### Status and Inspect (read-only)

Use **status** when the user asks what every managed tmux agent is doing. Read only — do not send keys. Prefer sessions following the `<folder>-<short-task-name>` convention, plus any sessions launched earlier in this run. Output a table with at least: agent ID, session name, state (`in-progress` / `done` / `blocked` / `unknown`), task/progress summary, started time, and working directory.

Useful raw data:

```bash
tmux list-sessions -F '#{session_name}|#{t:session_created}'
tmux list-panes -a -F '#{session_name}|#{pane_current_path}|#{pane_current_command}'
tmux capture-pane -t "$session" -p -S -40
```

Keep status checks fast and read-only: prefer two short bounded captures (`sleep 1-3`) to detect changing output, or call `wait_for_idle.py --timeout 3 --quiet-cycles 1 --no-print` rather than the full reply-wait cycle. Classify `in-progress` when the tail changes or shows a spinner / `esc to interrupt`; `blocked` when the short waiter exits 3 or a prompt is visible; `done` when the pane is quiet and a completed reply/prompt is visible; otherwise `unknown`. Keep progress summaries short — the current task or last meaningful line, not full scrollback.

Use **inspect `<agent-id>`** for one agent. Resolve the ID to the exact session, show the same fields as status plus a bounded tail and pane details, and print the human-only attach command:

```bash
tmux attach-session -t "$session"
```

The orchestrator must not run that attach command itself (no TTY); it only gives the user a copy-paste command for their own terminal.

## Phase 6: Continue or Tear Down

**Continue:** repeat send → verify-delivered (Phase 3) → wait + manual-verify (Phase 4) → capped-tail capture (Phase 5). Wait for idle before sending again, and keep the overall budget across rounds — if the loop keeps re-waiting without progress, escalate rather than poll forever.

**Broadcast to a fleet:** send to every session first, then wait on each concurrently — never serialize a full send→wait→read per agent. `scripts/broadcast.sh` does this; see `references/tmux-recipes.md` ("Broadcast to multiple agents").

**Long-running fleet status:** during multi-agent work that runs for several minutes, emit a fleet status report about every 5 minutes until all agents are done or blocked. Use the read-only Status table from Phase 5: per-agent state, current task/progress, started time, and working directory. This is a monitor/wake cadence only — never interrupt a working pane, never send keys as part of the report, and keep the same wait/budget rules from Phase 4.

**Tear down (confirmation required):**

```bash
tmux kill-session -t agent1     # one session
tmux kill-server                # everything — prefer killing named sessions individually
```

Both destroy unsaved agent state — confirm with the user first (Rule 1).

## Example

Message a running agent in session `reviewer` and relay its answer — the full `send → verify-delivered → wait → capped-tail capture` loop:

```bash
tmux has-session -t reviewer 2>/dev/null || { echo "no session 'reviewer'"; exit 1; }
tmux send-keys -t reviewer "summarize the open PRs"
tmux send-keys -t reviewer Enter
sleep 5
tmux capture-pane -t reviewer -p -S -40 | grep -Eq 'esc to interrupt|[⠁-⣿]' \
  && echo "delivered" || { echo "not submitted — send a lone Enter, re-check"; exit 1; }
python3 scripts/wait_for_idle.py reviewer
echo "wait exit=$?"                               # 0 idle · 3 blocked-on-prompt · 2 timeout
tmux capture-pane -t reviewer -p -S -40
```

Expected output (a complete answer, low-noise, not the whole scrollback):

```
delivered
⏺ 3 open PRs: #142 ready to merge, #139 changes requested, #137 draft.
wait exit=0
```

Relay that answer to the user. If the read starts mid-sentence, widen to `-S -80` (Phase 5). On `exit=3`, don't send — show the dialog and ask how to respond. If the wait never settles within budget, stop and surface the stall (Phase 4).

## Edge Cases

- **Trust/auth dialog** — `wait_for_idle.py` returns exit 3, not 0. Never send a message (would be read as menu input); surface the dialog.
- **Reply ends in a numbered list** ("1. yes 2. no") — not mistaken for a prompt; block detection uses only verified dialog strings.
- **Duplicate session name** — `tmux new-session` exits 1; resolve a free name first (Phase 1).
- **Interactive startup would hang the run** — default to autonomous startup (visible app tab when available, otherwise detached fallback) and continue readiness checks; only enter interactive mode when the user explicitly opts in, then ensure the session is visible and stop before scripted sends.
- **Status cannot identify an agent** — list it as `unknown` rather than guessing; `inspect` must resolve the exact session before printing an attach command.
- **Reply text contains "running"/"loading"** — busy detection scans only spinner chrome, never reply prose.
- **Message never landed** — Phase 3's post-send-activity check catches this before waiting and reports `NOT-DELIVERED`; send a lone `Enter`, re-check, re-type if still nothing.
- **Agent stalled** (unchanged pane, no spinner, no completion) — distinct from "still working" or a dropped delivery; surface it, don't silently re-wait.
- **Re-wait/re-send loop won't terminate** — enforce the overall budget (Phase 4); escalate rather than poll indefinitely.
- **Capped-tail capture starts mid-sentence** — reply is longer than ~40 lines; widen stepwise, only reach for unbounded `-S -` if a wide tail still truncates.
- **Returning to orchestrator control after attaching** — if the human attached manually, detach with `Ctrl-b d`; never `kill-session` just to "get back." A visible app tab can stay open while the orchestrator continues scripted send/wait/capture.

## Reference

- `references/delivery-and-waiting.md` — full rationale behind delivery verification (Phase 3) and waiting (Phase 4).
- `references/tmux-recipes.md` — broadcasting to a fleet, periodic fleet status, status/inspect details, sending multi-line/code messages, splitting panes, showing an agent's live terminal, reading scrollback, troubleshooting.

## Step Completion Report

After a messaging or lifecycle operation, emit:

```
◆ Tmux Agent Comms ([what you did])
··································································
  Target resolved:     √ pass (session: agent1)
  Message sent:        √ pass
  Message delivered:   √ pass (submission verified, ~5s)
  Reply settled:       √ pass (3 quiet cycles · verdict advisory)
  Reply verified:      √ pass (manual capped-tail read)
  Reply captured:      √ pass (-S -40, not truncated)
  Fleet status:        √ pass (if long-running fleet work: ~5 min cadence; otherwise — n/a)
  Destructive action:  — none (or: confirmed by user)
  ____________________________
  Result:              PASS
```

Adapt rows to the operation — a spawn reports `Session created`; a teardown reports `Confirmed` and `Session killed`. Use `⚠` for a dropped delivery (`Message delivered: ⚠ not delivered — re-sent`) or an escalated stall (`Reply settled: ⚠ stalled — budget spent, surfaced`).
