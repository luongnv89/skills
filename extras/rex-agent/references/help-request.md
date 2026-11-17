# Help Request

The full help summary printed on `help`, `--help`, `/rex-agent help`, or any plain question about what the skill does or how to drive it.

```text
rex-agent — build and control an AI-agent fleet in your Rex window.

WHAT YOU CAN ASK FOR
  spawn      "spin up agents named tests and docs beside my pane"
  message    "ask reviewer to summarize the open PRs"
  read       "show me what tests said"      (reads only, sends nothing)
  status     "what is my fleet doing right now?"
  broadcast  "tell every agent to pull latest main"
  steer      "focus the docs pane so I can type in it"
  teardown   "shut the fleet down"          (asks before closing anything)
  handoff    "keep driving this run when your context fills up"
  help       this summary

HOW IT BEHAVES
  Your pane stays the orchestrator and is never closed by accident.
  Workers land as equal-width columns in that same tab, not new tabs.
  New agents mirror yours: same harness, model, thinking level and launch
  flags, unless you name something else. An inherited permission bypass
  is announced before any agent starts.
  Agent state comes from the program status each agent CLI reports to Rex.
  A prompt aimed at a busy, blocked or unverifiable agent is refused
  before anything is typed.
  Every prompt waits for its own turn to settle, and blocked, stalled or
  timed-out agents are reported rather than silently retried.
  Dialogs are left for you: it focuses the pane and never answers them.
  Closing panes, tabs or sessions needs your approval; it never stops the
  Rex server.

WHAT IT NEEDS
  The rex CLI on PATH, a running Rex server (`rex whoami`), and this
  session inside a Rex terminal (REX_SESSION and REX_BLOCK set). Workers
  must report OSC 7501 program status: Claude Code, Codex 0.163+, pi and
  Gemini CLI do; opencode does not.
  Not for Herdr (use herdr-agent) or tmux (use tmux-agent-comms). For
  everyday Rex tabs and splits, `rex skill show` prints Rex's own guide.
```
