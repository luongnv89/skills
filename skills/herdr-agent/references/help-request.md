# Help Request

The full help summary printed on `help`, `--help`, `/herdr-agent help`, or any plain question about what the skill does or how to drive it.

```text
herdr-agent — build and control an AI-agent fleet in your Herdr tab.

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
  A prompt aimed at a busy or blocked agent is refused before it is sent.
  Every send waits for a settled state, and blocked, stalled or timed-out
  agents are reported rather than silently retried.
  Closing panes, tabs, workspaces or the server needs your approval.

WHAT IT NEEDS
  herdr 0.9.0 or later on PATH, a running server (`herdr status`), and this
  session inside a Herdr pane (HERDR_ENV=1). Default same-kind launches need
  the server's `pane process-info` API to return full argv.
  Not for tmux or GNU screen — use tmux-agent-comms there.
```
