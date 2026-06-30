# Delivery Verification & Waiting — the full rationale

The deep "why" behind SKILL.md Phases 3 and 4. The SKILL.md gives you the commands and the branch logic; read this when you need to understand *why* a step is shaped the way it is, or when a check behaves unexpectedly.

## Why "text on screen" does not prove a message was submitted

After `send-keys`, the message text appears in `capture-pane` whether it was **submitted** or is merely **typed and still parked in the input box** — both render as the same characters. So "the text is on screen" only proves it was typed, not sent. Reading the message text back out of the pane to confirm delivery is therefore unreliable: a single capture can't tell "echoed in the transcript" from "still parked in the input box."

The one signal that reliably means *submitted* is **post-send activity**: once the agent accepts the message it starts working (a spinner / `esc to interrupt`). That is why the Phase 3 delivery check keys off activity, not text presence.

### The bounded delivery check (one fixed wait, then one capture)

```bash
tmux send-keys -t agent1 "summarize the changes in src/"
tmux send-keys -t agent1 Enter
sleep 5                                          # bounded: one fixed wait, ~5s
pane=$(tmux capture-pane -t agent1 -p -S -40)    # ~40 scrollback lines + visible pane
if printf '%s\n' "$pane" | grep -Eq 'esc to interrupt|[⠁-⣿]'; then
  echo "delivered"          # agent is working → input was accepted and submitted
else
  echo "NOT-DELIVERED"      # no activity → it didn't land; re-send
fi
```

Keep this **bounded** — one short fixed delay, then a single capture. Never a poll loop here; that can hang. The reply-settling poll belongs to Phase 4, not the delivery check.

### The two outcomes (neither is a reply timeout)

- **`delivered`** — the agent is busy (spinner / `esc to interrupt`), which only appears once the message was accepted *and* submitted → proceed to Phase 4.
- **`NOT-DELIVERED`** — no post-send activity. Usually the separate-Enter gotcha (the message typed but the `Enter` didn't submit) or a dropped/swallowed keystroke. The fix covers both: **send a lone `Enter`** (`tmux send-keys -t agent1 Enter`) and re-check once — a no-op if it was already submitted; if there's still nothing, **re-type** the message. Report this **distinctly** from a Phase 4 reply timeout: nothing was submitted, so don't start waiting until it lands.

If your agent's spinner glyphs differ, key the check off its busy marker (the same `--busy-marker` / `TAC_BUSY_MARKERS` vocabulary Phase 4 uses) rather than `esc to interrupt` alone.

## Why the helper's verdict is advisory

`wait_for_idle.py` exit 0 means *the pane stopped changing*, which is usually "done" but can also be a paused agent or a UI that quiesced mid-task. Content stability is the universal signal (works for any CLI agent); spinner chrome (`esc to interrupt`) and dialog text only refine the verdict.

When the verdict matters (before relaying a result the user will act on, or on any exit-2 timeout), do an **independent, human-style read** — capture the pane yourself and look at the actual content — rather than trusting the exit code alone:

```bash
tmux capture-pane -t agent1 -p -S -40        # bounded tail: ~40 scrollback lines + visible pane
```

This distinguishes the third failure mode (a stalled agent) from a working one — separate from a dropped delivery (Phase 3) and a reply timeout (exit 2):

- **Still working:** a spinner / `esc to interrupt` is showing, or the tail differs from a capture you took moments ago → keep waiting; **don't send a new message yet**.
- **Stuck / stalled:** the pane is unchanged across reads, with no spinner and no completion (no prompt returned, answer never finished) → it won't resolve on its own. Surface it to the user; do not silently re-wait.

## Anti-deadloop — bound the whole loop, not just one wait

`--timeout` caps a **single** call; the real risk is a re-wait / re-send loop (Phase 4 and Phase 6 "Continue") that polls forever. Set a **hard overall budget** before you start — a small number of re-waits (e.g. 2–3) or a total wall-clock cap — and when it's spent, **stop and escalate to the user** with what you observed (last capture, how long you waited). Never poll indefinitely and never auto-re-send past the cap; an agent that hasn't settled within the budget is a stall to report, not a loop to keep running.

### Manual fallback (no Python / restricted env)

Capture, `sleep 3`, capture again, compare — under the same overall budget. Matching captures with no spinner = done. A spinner or `esc to interrupt` still showing → wait and re-capture; **don't send a new message yet**. If the budget runs out with no resolution, stop and surface it.
