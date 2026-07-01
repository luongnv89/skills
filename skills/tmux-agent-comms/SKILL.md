---
name: tmux-agent-comms
description: "Manage AI agents in tmux: spawn or kill sessions and message any CLI agent (Claude Code, Gemini, etc.) via send-keys/capture-pane, then read its reply. Use to launch a fleet or talk to a running agent. Don't use for SSH, GNU screen, or GUI apps."
license: MIT
effort: medium
metadata:
  version: 1.5.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Tmux Agent Comms

Manage and talk to AI agents (another Claude Code, Gemini CLI, or any CLI) running in separate tmux sessions. Covers the full loop: **create** sessions, **send** messages, **wait** for the agent to finish, **capture** replies, and **tear down** when done.

The mental model: each tmux session is one agent. You orchestrate from outside by writing to its input and reading its pane — what a human does by switching windows, but scripted. Because your context budget is finite, relay each agent's answer, not its whole screen (the bundled helper extracts just the reply).

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
5. **Attaching is opt-in, not a replacement.** Showing an agent's terminal (Phase 1) is an alternative for a human to drive by hand; it does not replace the default detached, scripted workflow — don't attach unless the user wants to see or steer the live UI.

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

### Show the agent's terminal (optional)

The default workflow stays detached — you drive the agent with `send-keys`/`capture-pane` and never open its terminal. If the user wants to *see* the live CLI (a trust/auth prompt, debugging, or hands-on steering), there are two commands, and **who runs which matters**:

```bash
tmux attach-session -t "$name"     # HUMAN runs this in their own interactive terminal
tmux switch-client -t "$name"      # agent can run this itself, if it is already a tmux client ($TMUX set)
```

`attach-session` needs a controlling TTY. If you (the agent) invoke it through a non-interactive Bash tool, it fails with `open terminal failed: not a terminal` — it does not open anything. Never run `attach-session` yourself; instead tell the human the exact command to type in their own terminal. `switch-client` is different: it's a control-mode command that reuses your *own* existing tmux client, so it's safe for you to run it yourself when you're already inside a tmux client (`$TMUX` is set) and want to hand your own view over.

Detach with `Ctrl-b d` (default prefix + `d`) to return control to the orchestrator without killing the session. This is opt-in and does not replace the default detached flow — see `references/tmux-recipes.md` ("Showing an agent's live terminal") for the when-to-use guidance, the correct command for each starting context, and a worked example that names the exact session attached to.

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

**Verify delivery before you wait (don't skip this).** A keystroke can drop or an `Enter` can go unsubmitted, and you'd then wait on a reply that never comes. On-screen text only proves the message was *typed* — it looks identical whether submitted or parked in the input box. The reliable "submitted" signal is **post-send activity** (a spinner / `esc to interrupt`). After send, run a **bounded** check (one ~5s delay, then a single capture — never a poll loop) and grep the pane for that activity:

```bash
tmux send-keys -t agent1 "..."; tmux send-keys -t agent1 Enter; sleep 5
tmux capture-pane -t agent1 -p -S -40 | grep -Eq 'esc to interrupt|[⠁-⣿]' \
  && echo delivered || echo NOT-DELIVERED
```

- **`delivered`** — agent is busy → submitted → proceed to Phase 4.
- **`NOT-DELIVERED`** — no activity (usually the separate-Enter gotcha or a dropped keystroke). Send a lone `Enter` and re-check; if still nothing, re-type. Distinct from a Phase 4 reply timeout — nothing was submitted, so don't start waiting.

This is the `send → verify-delivered → wait → bounded-tail capture` loop. Trust the activity signal, not the text. Full rationale and the verbose branch logic: `references/delivery-and-waiting.md`.

## Phase 4: Wait for the Reply, Then Read It

A fixed `sleep` either wastes time or reads a half-written reply. The bundled helper polls until the pane stops changing, then prints **only the new lines since the wait started** — the agent's answer, not the surrounding 24 lines of box-drawing and status bars. Relaying deltas instead of full frames is the main token saving over a multi-turn conversation.

```bash
python3 scripts/wait_for_idle.py agent1
```

It returns one of three states — **branch on the exit code:**

- **0 — idle:** settled and ready. Its stdout is the reply delta; relay that to the user.
- **3 — blocked:** settled but parked on a prompt that needs a human (trust/auth dialog). It prints the full pane so you can show the dialog. **Do not send a message** — it would be read as menu input. Surface it and ask the user how to respond (Rule 1).
- **2 — timeout:** never settled within `--timeout` (agent still working, or genuinely stuck). This bounds **one** wait — it does not bound a loop that keeps re-waiting (see the anti-deadloop cap below).

Content stability is the universal signal (works for any CLI agent); spinner chrome and dialog text only refine the verdict. For an agent whose chrome differs, add markers with `--busy-marker`/`--block-marker` or the `TAC_BUSY_MARKERS`/`TAC_BLOCK_MARKERS` env vars — no code edit. Other flags: `--timeout`, `--quiet-cycles`, `--interval`, `--full`, `--scrollback N`; run `--help` for details.

**The verdict is advisory — verify it when it matters.** Exit 0 means *the pane stopped changing*, usually "done" but possibly a paused agent. Before relaying a result the user will act on, or on any exit-2 timeout, do an independent human-style read (`tmux capture-pane -t agent1 -p -S -40`, Phase 5): a spinner or a changing tail = **still working** (keep waiting, don't send — Rule 3); unchanged + no spinner + no completion = **stalled** (surface it, don't silently re-wait).

**Anti-deadloop — bound the whole loop, not just one wait.** `--timeout` caps a single call; the real risk is a re-wait / re-send loop that polls forever. Set a **hard overall budget** before you start — a small number of re-waits (e.g. 2–3) or a total wall-clock cap — and when it's spent, **stop and escalate to the user** with what you observed. Never poll indefinitely. Full details in `references/delivery-and-waiting.md`.

If you can't run the script (no Python, restricted env), fall back to a manual loop: capture (below), `sleep 3`, capture again, compare — under the same overall budget. Matching captures with no spinner = done. A spinner or `esc to interrupt` still showing → wait and re-capture; **don't send a new message yet** (Rule 3). If the budget runs out with no resolution, stop and surface it.

## Phase 5: Read More (bounded-tail capture)

The helper already relays the delta. When you need to read the pane yourself — to verify a verdict (Phase 4) or grab a full reply the delta clipped — **default to a bounded tail of ~20–40 lines**, not the bare visible pane and not the whole scrollback:

```bash
tmux capture-pane -t agent1 -p -S -40       # ~40 scrollback lines + the visible pane (a bounded tail)
```

`-S -40` returns ~40 lines of scrollback *plus* the visible pane (so ~40+ lines in a typical pane), enough that a reply which scrolled one screen up still comes through — while staying low-noise. This is the **default** read for a full reply, and it is deliberately **distinct from grabbing the whole pane / unbounded scrollback** (`-S -`), which floods the capture with old turns and TUI chrome.

**Tell when the tail truncated, and expand only then.** If the answer is longer than the window, the top of the capture starts mid-sentence (no clear start of the reply) or the first substantive line is cut off — that's the signal the reply exceeds the tail. Widen the window stepwise until the full reply is captured:

```bash
tmux capture-pane -t agent1 -p -S -80       # reply longer than ~40 lines → widen
```

Only fall back to unbounded scrollback (`-S -`) for an unusually long reply when even a wide tail truncates — see `references/tmux-recipes.md` ("Reading scrollback robustly") for that case. Relay the agent's answer, not the surrounding TUI chrome. If a capture is mostly box-drawing, re-check that the agent actually replied rather than blindly grabbing more.

## Phase 6: Continue or Tear Down

**Continue the conversation:** repeat the loop — send → verify-delivered (Phase 3) → wait, bounded + manual-verify (Phase 4) → bounded-tail capture (Phase 5). Each round, wait for idle (exit 0) before sending again, and keep the **overall budget** from Phase 4 across rounds: if the loop keeps re-waiting or re-sending without progress, stop and escalate to the user rather than polling forever.

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

For example, to message a running agent in session `reviewer` and relay its answer — the full `send → verify-delivered → wait → bounded-tail capture` loop:

```bash
tmux has-session -t reviewer 2>/dev/null || { echo "no session 'reviewer'"; exit 1; }
tmux send-keys -t reviewer "summarize the open PRs"
tmux send-keys -t reviewer Enter
sleep 5                                           # bounded delivery check (Phase 3)
tmux capture-pane -t reviewer -p -S -40 | grep -Eq 'esc to interrupt|[⠁-⣿]' \
  && echo "delivered" || { echo "not submitted — send a lone Enter, re-check"; exit 1; }
python3 scripts/wait_for_idle.py reviewer         # advisory: blocks until idle, prints the reply delta
echo "wait exit=$?"                               # 0 idle · 3 blocked-on-prompt · 2 timeout
tmux capture-pane -t reviewer -p -S -40           # bounded tail (~40 scrollback + visible pane), Phase 5
```

The delivery check here keys off **post-send activity** (the agent is now busy), which only appears once the message was accepted *and* submitted — see Phase 3 for the `delivered` / `NOT-DELIVERED` branch and the re-send remedy. Expected output (the bounded tail — a complete answer, low-noise, not the whole scrollback):

```
delivered
⏺ 3 open PRs: #142 ready to merge, #139 changes requested, #137 draft.
wait exit=0
```

Relay that answer to the user. If the bounded-tail read starts mid-sentence, widen to `-S -80` (Phase 5). If the message wasn't submitted, send a lone `Enter` and re-check — don't start waiting (Phase 3). On `exit=3`, do not send — show the dialog and ask the user how to respond. If the wait never settles within your overall budget, stop and surface the stall (Phase 4).

## Edge Cases

- **Agent on a trust/auth dialog** (e.g. a fresh Gemini in an untrusted dir) — `wait_for_idle.py` returns exit 3, not 0. Never send a message; the keystrokes would be read as menu input. Surface the dialog.
- **Reply ends in a numbered list** ("1. yes 2. no") — handled: block detection uses only verified dialog strings, so a normal reply is not mistaken for a prompt.
- **Duplicate session name** — `tmux new-session` exits 1 ("duplicate session"); resolve a free name first (Phase 1).
- **Agent reply contains "running"/"loading"/"…"** — handled: busy detection scans only spinner *chrome* in the last lines, never reply prose.
- **Message never landed** (dropped keystroke, unsubmitted `Enter`, input swallowed by a busy pane) — the Phase 3 check keys off *post-send activity*, not the mere presence of the text on screen, so it catches this **before** waiting and reports `NOT-DELIVERED`. The remedy covers every cause: send a lone `Enter`, re-check, then re-type if still nothing. Distinct from a reply timeout — nothing was submitted, so re-send rather than wait longer.
- **Agent stalled** (pane unchanged across reads, no spinner, no completion) — distinct from "still working" (spinner/`esc to interrupt` or a changing tail) and from a dropped delivery. Surface it; don't silently re-wait (Phase 4).
- **Re-wait/re-send loop won't terminate** — enforce the overall budget (Phase 4): cap total re-waits/wall-clock and escalate to the user; never poll indefinitely.
- **Bounded-tail capture starts mid-sentence** — the reply is longer than ~40 lines; widen stepwise (`-S -80`, …) and only reach for unbounded `-S -` if even a wide tail truncates (Phase 5).
- **Returning to orchestrator control after attaching** — detach with `Ctrl-b d` (default prefix + `d`); this leaves the session running so the scripted send-keys/capture-pane loop can resume. Never `kill-session` just to "get back" (Phase 1, "Show the agent's terminal").

## Reference

Read `references/delivery-and-waiting.md` for the full rationale behind delivery verification (Phase 3) and waiting (Phase 4).

Read `references/tmux-recipes.md` for: broadcasting to a fleet, sending multi-line/code messages safely, splitting a session into panes, showing an agent's live terminal, reading scrollback robustly, and a troubleshooting table.

## Step Completion Report

After a messaging or lifecycle operation, emit:

```
◆ Tmux Agent Comms ([what you did])
··································································
  Target resolved:     √ pass (session: agent1)
  Message sent:        √ pass
  Message delivered:   √ pass (submission verified, ~5s)
  Reply settled:       √ pass (3 quiet cycles · verdict advisory)
  Reply verified:      √ pass (manual bounded-tail read)
  Reply captured:      √ pass (-S -40, not truncated)
  Destructive action:  — none (or: confirmed by user)
  ____________________________
  Result:              PASS
```

Adapt rows to the operation — a spawn reports `Session created`; a teardown reports `Confirmed` and `Session killed`. Use `⚠` for a dropped delivery (`Message delivered: ⚠ not delivered — re-sent`) or a stall escalated to the user (`Reply settled: ⚠ stalled — budget spent, surfaced`).
