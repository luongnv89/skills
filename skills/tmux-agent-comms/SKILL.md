---
name: tmux-agent-comms
description: "Manage AI agents in tmux: spawn or kill sessions and message any CLI agent (Claude Code, Gemini, etc.) via send-keys/capture-pane, then read its reply. Use to launch a fleet or talk to a running agent. Don't use for SSH, GNU screen, or GUI apps."
license: MIT
effort: medium
metadata:
  version: 1.7.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Tmux Agent Comms

Manage and talk to AI agents (another Claude Code, Gemini CLI, or any CLI) running in separate tmux sessions: **create** sessions, **send** messages, **wait** for the agent to finish, **capture** replies, and **tear down** when done.

Mental model: each tmux session is one agent. You orchestrate from outside by writing to its input and reading its pane — what a human does by switching windows, but scripted. Your context budget is finite, so relay each agent's answer, not its whole screen (the bundled helper extracts just the reply delta).

## When to Use

Launching agents in tmux, messaging an agent in another session, broadcasting to a fleet, or reading what an agent replied. Don't use for SSH/remote shells, GNU `screen`, or driving a GUI app.

## Workflow

Six phases, in order: discover/spawn a session, resolve the exact target, send the message, wait for the reply to settle, capture it, then continue or tear down.

**Jump straight to the phase for your task** — don't read the rest:

| Your task | Start at |
|---|---|
| Spawn a new agent session | Phase 1 |
| Message an agent that's already running | Phase 2 |
| Just read a running agent's pane (no send) | Phase 5 |
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
5. **Attaching is opt-in, not a replacement.** Showing an agent's terminal (Phase 1) is for a human to drive by hand; it never replaces the default detached, scripted workflow.

## Phase 1: Create or Discover Sessions

```bash
tmux list-sessions 2>/dev/null || echo "no tmux server running yet"
```

Match the target against this list (Phase 2). To spawn: `tmux new-session` **fails if the name is taken** (exit 1), so check first, create **detached** (`-d -s <name>`), then launch the agent in a second step:

```bash
name=agent1
tmux has-session -t "$name" 2>/dev/null && name="${name}-$(date +%s)"   # avoid collision
tmux new-session -d -s "$name" -c /path/to/project
tmux send-keys -t "$name" "claude" Enter
```

Replace `claude` with whatever launches the target agent. **"Spawned" ≠ "ready"** — a fresh agent often boots through a trust/auth prompt. Don't send blind; run the wait helper (Phase 4): exit `0` means ready, exit `3` means it's parked on a prompt to surface to the user rather than type into.

```bash
python3 scripts/wait_for_idle.py "$name" --timeout 30 --no-print; echo "ready=$?"
```

For a **fleet**, repeat with distinct job-named sessions (`reviewer`, `tests`, `docs`).

**Showing the agent's terminal** (optional, human-only): `tmux attach-session -t "$name"` or `tmux switch-client -t "$name"`, run by the human in their own interactive terminal — the agent invoking either itself will fail (no TTY / no attached client). Detach with `Ctrl-b d` to return control without killing the session. See `references/tmux-recipes.md` ("Showing an agent's live terminal") for the when-to-use table and worked example.

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

## Phase 6: Continue or Tear Down

**Continue:** repeat send → verify-delivered (Phase 3) → wait + manual-verify (Phase 4) → capped-tail capture (Phase 5). Wait for idle before sending again, and keep the overall budget across rounds — if the loop keeps re-waiting without progress, escalate rather than poll forever.

**Broadcast to a fleet:** send to every session first, then wait on each concurrently — never serialize a full send→wait→read per agent. `scripts/broadcast.sh` does this; see `references/tmux-recipes.md` ("Broadcast to multiple agents").

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
- **Reply text contains "running"/"loading"** — busy detection scans only spinner chrome, never reply prose.
- **Message never landed** — Phase 3's post-send-activity check catches this before waiting and reports `NOT-DELIVERED`; send a lone `Enter`, re-check, re-type if still nothing.
- **Agent stalled** (unchanged pane, no spinner, no completion) — distinct from "still working" or a dropped delivery; surface it, don't silently re-wait.
- **Re-wait/re-send loop won't terminate** — enforce the overall budget (Phase 4); escalate rather than poll indefinitely.
- **Capped-tail capture starts mid-sentence** — reply is longer than ~40 lines; widen stepwise, only reach for unbounded `-S -` if a wide tail still truncates.
- **Returning to orchestrator control after attaching** — detach with `Ctrl-b d`; never `kill-session` just to "get back."

## Reference

- `references/delivery-and-waiting.md` — full rationale behind delivery verification (Phase 3) and waiting (Phase 4).
- `references/tmux-recipes.md` — broadcasting to a fleet, sending multi-line/code messages, splitting panes, showing an agent's live terminal, reading scrollback, troubleshooting.

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
  Destructive action:  — none (or: confirmed by user)
  ____________________________
  Result:              PASS
```

Adapt rows to the operation — a spawn reports `Session created`; a teardown reports `Confirmed` and `Session killed`. Use `⚠` for a dropped delivery (`Message delivered: ⚠ not delivered — re-sent`) or an escalated stall (`Reply settled: ⚠ stalled — budget spent, surfaced`).
