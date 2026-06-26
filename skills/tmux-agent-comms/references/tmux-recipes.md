# Tmux Agent Comms — Recipes & Troubleshooting

Patterns the SKILL.md points to when a task goes beyond the basic send → wait → capture loop. Read the relevant section when you hit that case; you don't need all of it at once.

## Broadcast to multiple agents

Send one instruction to a fleet and collect each reply. Use the bundled script — it sends to every session first, then waits on all of them **concurrently** (each reply settles in its own background process), so wall-clock is the slowest single agent, not the sum:

```bash
TAC_TIMEOUT=180 bash scripts/broadcast.sh "pull latest main and report status" reviewer tests docs
```

It prints one labeled block per agent with the reply delta and a state tag (`idle` / `TIMEOUT` / `BLOCKED`), and exits non-zero if any agent timed out or is blocked. `TAC_WAIT_ARGS` passes extra flags to the waiter (e.g. `TAC_WAIT_ARGS=--full`).

**Wait for boot before the first broadcast.** Freshly spawned agents may still be on a splash or trust prompt. Confirm each is ready first (exit 0, not 3):

```bash
for s in reviewer tests docs; do python3 scripts/wait_for_idle.py "$s" --timeout 30 --no-print; echo "$s ready=$?"; done
```

If `broadcast.sh` is unavailable, fan the message out in one loop, then wait in a **second** loop (never one combined loop — that serializes the waits behind each send).

## Sending multi-line or code-heavy messages

Escaping breaks down fast with newlines, quotes, `$`, and backticks. Two robust options:

**Option A — paste-buffer load (preferred for blocks of text/code).** Write the message to a file, load it into a tmux paste buffer, then paste it into the target and submit:

```bash
cat > /tmp/agent_msg.txt <<'EOF'
Refactor this function and explain the change:

    def f(x): return x*2
EOF
tmux load-buffer /tmp/agent_msg.txt
tmux paste-buffer -t agent1
tmux send-keys -t agent1 Enter
```

The single-quoted heredoc (`<<'EOF'`) prevents the shell from expanding `$`/backticks in the body. `paste-buffer` inserts the text literally — no per-character escaping needed.

**Option B — `send-keys -l` (literal).** `-l` tells tmux to treat the argument literally rather than as key names, which avoids tmux-level interpretation (still mind shell quoting):

```bash
tmux send-keys -t agent1 -l 'price is $5; see file.txt'
tmux send-keys -t agent1 Enter
```

For anything with newlines, prefer Option A.

## Splitting a session into panes

To watch an agent and a log side by side, or run two agents in one session, split the window. Note the pane index in the target (`session:window.pane`).

```bash
tmux split-window -t agent1 -h        # horizontal split (side by side)
tmux send-keys -t agent1:0.1 "gemini" Enter   # launch a second agent in pane 1
tmux capture-pane -t agent1:0.1 -p    # read just that pane
```

List panes and their indices with `tmux list-panes -t agent1`.

## Reading scrollback robustly

The **default** read for a full reply is a bounded tail — `-S -40`, which returns ~40 lines of scrollback plus the visible pane — see SKILL.md Phase 5. This section is the **expand** case: a reply long enough that the bounded tail truncated (the capture starts mid-sentence). Widen the window stepwise rather than jumping straight to the whole history:

```bash
tmux capture-pane -t agent1 -p -S -80       # widen the tail when ~40 lines truncates
tmux capture-pane -t agent1 -p -S -500      # last 500 lines, for a very long reply
tmux capture-pane -t agent1 -p -S -          # entire scrollback — last resort, can be large
```

`-S -` (start at the very top of history) grabs everything — useful when you genuinely don't know how long the reply was, but it floods the capture with old turns and chrome, so reach for it **only** when even a wide tail truncates. Keep captures bounded by default and increase the window only as far as needed. The bundled `wait_for_idle.py` accepts `--scrollback N` to factor history into its stability check.

## Stripping TUI chrome from a capture

Agent TUIs surround the answer with box-drawing characters, prompts, and status bars. When relaying to the user, quote the substantive lines, not the frame. If you need a rough programmatic trim, drop lines that are only box characters:

```bash
tmux capture-pane -t agent1 -p | grep -vE '^[[:space:]]*[─━│┃┌┐└┘├┤┬┴┼╭╮╯╰]*[[:space:]]*$'
```

This is best-effort — always sanity-check the result rather than trusting it blindly.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Message typed but never submitted | TUI didn't accept `Enter` in the same call | Send `Enter` as its own `send-keys` call (SKILL.md Phase 3) |
| Delivery check says `delivered` but no reply ever comes | Checked that the text is *present*, not that it was *submitted* — `capture-pane` shows input-box text and transcript text identically | Verify **submission**, not presence: after send+5s, confirm post-send activity (spinner / `esc to interrupt`) or that the input line cleared. Don't gate on `grep -qF "<text>"` alone (SKILL.md Phase 3) |
| Message present on screen but unsubmitted (sitting in input box) | `Enter` rode in the same call and wasn't accepted | Phase 3 check reports this as `UNSUBMITTED` (text present, no activity). Send a lone `Enter`, re-check — distinct from a dropped keystroke and from a reply timeout |
| Message never reached the agent (dropped) | Keystroke dropped / busy pane swallowed input | Phase 3 check reports this as `DROPPED` (text absent). Re-type, re-check; report **distinctly** from a reply timeout — nothing was submitted |
| `can't find session` / nothing happens | Wrong or non-existent target | `tmux has-session -t <name>`; then `tmux list-sessions` to find the real name |
| Captured pane is empty or all chrome | Read too early, or wrong pane | Re-run `wait_for_idle.py`; check pane index with `tmux list-panes` |
| Reply cut off | Bounded-tail window too small for this reply | Widen the tail stepwise — `-S -80`, then larger; unbounded `-S -` only as last resort (SKILL.md Phase 5; "Reading scrollback robustly" above) |
| `;` or `$...` came out wrong / executed | Shell/tmux interpreted special chars | Quote the message; use `send-keys -l` or paste-buffer (see above) |
| Agent stuck on a yes/no or trust prompt | It's waiting for a keypress, not a typed line | `wait_for_idle.py` flags this as exit 3 (BLOCKED) for known dialogs. Send the exact key it expects (e.g. `tmux send-keys -t agent1 "1" Enter`), but confirm with the user first for any permission/trust prompt |
| Can't tell if the agent is stuck or still working | Trusting the helper's exit code without a look | Verdict is advisory — read the pane yourself (`-S -40`). Spinner / changing tail = working (wait); unchanged + no spinner + no completion = stalled (surface to user). SKILL.md Phase 4 |
| `wait_for_idle.py` times out repeatedly | Agent genuinely slow, or a persistent spinner | Raise `--timeout` for a single wait; if a static UI element matches a busy marker, fall back to the manual capture-compare loop. Bound the **overall** re-wait/re-send loop and escalate when the budget is spent — never poll forever (SKILL.md Phase 4) |
| New session dies immediately | Agent binary not found in that shell | Launch the agent manually once to see the error; ensure it's on PATH in a login shell |

## Safety reminders

- Reading panes is always safe. **Writing** to a pane can disrupt or destroy another agent's in-progress work — get user confirmation for anything beyond a benign message.
- `kill-session` / `kill-server` lose unsaved agent state. Kill individual named sessions over `kill-server` unless a full reset is explicitly wanted.
- Never relay a captured pane that may contain secrets (API keys, tokens) without the user's awareness — captures include whatever is on screen.
