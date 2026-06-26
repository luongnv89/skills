---
name: tmux-agent-comms
description: "Manage AI agents in tmux: spawn or kill sessions and message any CLI agent (Claude Code, Gemini, etc.) via send-keys/capture-pane, then read its reply. Use to launch a fleet or talk to a running agent. Don't use for SSH, GNU screen, or GUI apps."
license: MIT
effort: medium
metadata:
  version: 1.2.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Tmux Agent Comms

Manage and talk to AI agents (another Claude Code, Gemini CLI, or any CLI) running in separate tmux sessions. This skill covers the full loop: **create** sessions for agents, **send** them messages, **wait** for them to finish thinking, **capture** their replies, and **tear down** sessions when done.

The mental model: each tmux session is one agent. You orchestrate them from the outside by writing to their input and reading their pane — exactly what a human would do by switching windows, but scripted. Because the orchestrating agent's context budget is finite, relay each agent's answer, not its whole screen (the bundled helper extracts just the reply).

## When to Use

Use this when the user wants to launch agents in tmux, message an agent running in another session, broadcast to a fleet, or read what an agent replied. Don't use it for SSH/remote shells, GNU `screen`, or driving a GUI app.

## Workflow

Quick start: the six phases below run in order — discover/spawn a session, resolve the exact target, send the message, wait for the reply to settle, capture it, then continue or tear down. Read only the phase you need.

## Prerequisites

- **tmux installed**: `command -v tmux` must succeed. If missing, tell the user to install it (`brew install tmux` / `apt install tmux`) and stop — do not fake it with background shells.
- **A terminal multiplexer model**: you operate sessions you can't see. Always confirm a session exists and inspect its pane before assuming a message landed.

## Critical Rules

1. **Confirm before destructive or irreversible actions.** Killing a session, sending `exit`/`/quit`, or piping shell commands into another agent's prompt can lose that agent's work. Never do these without the user's explicit go-ahead. Reading a pane is always safe; writing to one is not.
2. **Verify the target before sending.** A typo'd session name silently sends keystrokes nowhere (or to the wrong agent). Always resolve the exact target with `has-session` first (Phase 2).
3. **Wait for the agent, don't race it.** Agents take seconds to respond. Sending a follow-up while the target is still working corrupts its input. Always wait until the pane output settles (Phase 4) before reading a reply or sending again.
4. **Escape what you send.** `send-keys` interprets `;` as a command separator and the shell interprets `$`, backticks, and quotes. Mishandled, your message gets mangled or — worse — executes. Follow the escaping rules in Phase 3.

## Phase 1: Create or Discover Sessions

You either attach to agents that already exist or spin up new ones.

### List existing sessions

```bash
tmux list-sessions 2>/dev/null || echo "no tmux server running yet"
```

This shows every running session by name. Match the user's target against this list (see Phase 2).

### Spawn a new agent session

`tmux new-session` **fails if the name is already taken** (exit 1, "duplicate session"). So check first and pick a free name, then create a **detached** session (`-d`, `-s <name>`) and launch the agent in a second step (lets the shell initialize before the agent starts):

```bash
name=agent1
tmux has-session -t "$name" 2>/dev/null && name="${name}-$(date +%s)"   # avoid collision
tmux new-session -d -s "$name" -c /path/to/project   # -c sets the working dir
tmux send-keys -t "$name" "claude" Enter
```

Replace `claude` with whatever launches the target agent (`gemini`, `claude --resume`, etc.).

**"Spawned" ≠ "ready."** A fresh agent boots through a splash, and often a **trust/auth prompt that needs a keypress** before its input box works. Don't fire the first message blind. Run the wait helper (Phase 4): exit `0` means the input box is ready, exit `3` means it's parked on a prompt you must surface to the user (e.g. "Do you trust this folder?") rather than typing into.

```bash
python3 scripts/wait_for_idle.py "$name" --timeout 30 --no-print; echo "ready=$?"
```

To launch a **fleet**, repeat with distinct job-named sessions (`reviewer`, `tests`, `docs`) so later messages are self-documenting.

## Phase 2: Resolve the Exact Target

Before sending anything, confirm the session exists. `has-session` exits non-zero if it doesn't:

```bash
tmux has-session -t agent1 2>/dev/null && echo "OK: agent1 exists" || echo "MISSING: agent1"
```

If the exact name is missing, run `tmux list-sessions` and pick the closest match — but surface the substitution to the user rather than guessing silently.

**Targeting precision.** `-t agent1` targets the session's active pane. To hit a specific window or pane, use `session:window.pane`, e.g. `-t agent1:0.1`. For single-pane agent sessions (the common case), the bare session name is enough.

## Phase 3: Send a Message

```bash
tmux send-keys -t agent1 "summarize the changes in src/" Enter
```

`send-keys` types the string into the target's input, and the trailing `Enter` submits it.

**Escaping — this is where messages break:**

- Wrap the message in **double quotes** so the shell keeps it as one argument.
- A literal `;` inside an unquoted argument is read by tmux as a command separator. Quoting prevents this; when in doubt, keep messages free of raw `;`.
- `$`, backticks, and `"` inside double quotes are still expanded/interpreted by the shell. Escape them (`\$`, `` \` ``, `\"`) or use single quotes for the whole message when it contains no single quote of its own.
- For any message with newlines, complex quoting, or code, **write it to a file and load it** instead of fighting escaping — see `references/tmux-recipes.md` ("Sending multi-line or code-heavy messages").

**The separate-Enter gotcha.** Some TUIs (including some Claude Code states) don't submit when `Enter` rides along in the same `send-keys` call. If a message types but doesn't send, send the Enter on its own:

```bash
tmux send-keys -t agent1 "your message"
tmux send-keys -t agent1 Enter
```

## Phase 4: Wait for the Reply, Then Read It

A fixed `sleep` either wastes time or reads a half-written reply. The bundled helper polls until the pane stops changing, then prints **only the new lines since the wait started** — the agent's answer, not the surrounding 24 lines of box-drawing and status bars. Relaying deltas instead of full frames is the main token saving over a multi-turn conversation.

```bash
python3 scripts/wait_for_idle.py agent1
```

It returns one of three states — **branch on the exit code:**

- **0 — idle:** settled and ready. Its stdout is the reply delta; relay that to the user.
- **3 — blocked:** settled but parked on a prompt that needs a human (trust/auth dialog). It prints the full pane so you can show the dialog. **Do not send a message** — it would be read as menu input. Surface it and ask the user how to respond (Rule 1).
- **2 — timeout:** never settled (agent still working or genuinely stuck). Raise `--timeout` or inspect the pane.

Content stability is the universal signal (works for any CLI agent); spinner chrome (`esc to interrupt`) and dialog text only refine the verdict. For an agent whose chrome differs, add markers with `--busy-marker`/`--block-marker` or the `TAC_BUSY_MARKERS`/`TAC_BLOCK_MARKERS` env vars — no code edit. Other flags: `--timeout`, `--quiet-cycles`, `--interval`, `--full` (print the whole pane), `--scrollback N`. Run with `--help` for details.

If you can't run the script (no Python, restricted env), fall back to a manual loop: capture (below), `sleep 3`, capture again, compare. Matching captures with no spinner = done. A spinner or `esc to interrupt` still showing → wait and re-capture; **don't send a new message yet** (Rule 3).

## Phase 5: Read More (scrollback / full pane)

The helper already relays the delta. Reach for raw `capture-pane` when you need the **full** pane or history — e.g. a long reply that scrolled off:

```bash
tmux capture-pane -t agent1 -p              # full visible pane
tmux capture-pane -t agent1 -p -S -200      # + 200 lines of scrollback
```

Relay the agent's answer, not the surrounding TUI chrome. If a capture is mostly box-drawing, increase scrollback or re-check that the agent actually replied.

## Phase 6: Continue or Tear Down

**Continue the conversation:** repeat Phase 3 → Phase 4. Each round, wait for idle (exit 0) before sending again.

**Broadcast to a fleet:** send the message to **every** session first, then wait on each — never serialize a full send→wait→read per agent, or a slow agent stalls the rest. The bundled `scripts/broadcast.sh` does this; see `references/tmux-recipes.md` ("Broadcast to multiple agents").

**Tear down (confirmation required):** when the user is done with an agent, kill its session:

```bash
tmux kill-session -t agent1
```

To stop everything (all sessions and the tmux server):

```bash
tmux kill-server
```

Both destroy unsaved agent state — confirm with the user first (Rule 1). Prefer killing named sessions individually over `kill-server` unless the user explicitly wants a full reset.

## Example

For example, to message a running agent in session `reviewer` and relay its answer (a typical send → wait → read example):

```bash
tmux has-session -t reviewer 2>/dev/null || { echo "no session 'reviewer'"; exit 1; }
tmux send-keys -t reviewer "summarize the open PRs"
tmux send-keys -t reviewer Enter
python3 scripts/wait_for_idle.py reviewer        # blocks until idle, prints the reply delta
echo "wait exit=$?"                              # 0 idle · 3 blocked-on-prompt · 2 timeout
```

Expected output (the delta — the agent's answer, not the full pane):

```
⏺ 3 open PRs: #142 ready to merge, #139 changes requested, #137 draft.
wait exit=0
```

Relay that answer to the user. On `exit=3`, do not send — show the dialog and ask the user how to respond.

## Edge Cases

- **Agent on a trust/auth dialog** (e.g. a fresh Gemini in an untrusted dir) — `wait_for_idle.py` returns exit 3, not 0. Never send a message; the keystrokes would be read as menu input. Surface the dialog.
- **Reply ends in a numbered list** ("1. yes 2. no") — handled: block detection uses only verified dialog strings, so a normal reply is not mistaken for a prompt.
- **Duplicate session name** — `tmux new-session` exits 1 ("duplicate session"); resolve a free name first (Phase 1).
- **Agent reply contains "running"/"loading"/"…"** — handled: busy detection scans only spinner *chrome* in the last lines, never reply prose.

## Reference

Read `references/tmux-recipes.md` for: broadcasting to a fleet, sending multi-line/code messages safely, splitting a session into panes, reading scrollback robustly, and a troubleshooting table (message didn't send, pane empty, session not found, agent stuck on a prompt).

## Step Completion Report

After a messaging or lifecycle operation, emit:

```
◆ Tmux Agent Comms ([what you did])
··································································
  Target resolved:     √ pass (session: agent1)
  Message sent:        √ pass
  Reply settled:       √ pass (3 quiet cycles)
  Reply captured:      √ pass
  Destructive action:  — none (or: confirmed by user)
  ____________________________
  Result:              PASS
```

Adapt rows to the operation — a spawn reports `Session created`; a teardown reports `Confirmed` and `Session killed`.
