# Help Request

The full help summary printed on `help`, `--help`, `/hc-agent help`, or any plain question about what the skill does or how to drive it.

```text
hc-agent — build and control an AI-agent fleet in your Herdr desktop app tab.

WHAT YOU CAN ASK FOR
  spawn      "spin up agents named tests and docs beside my pane"
  message    "ask reviewer to summarize the open PRs"
  read       "show me what tests said"      (reads only, sends nothing)
  status     "what is my fleet doing right now?"
  broadcast  "tell every agent to pull latest main"
  steer      "show me the docs agent so I can type in it"
  teardown   "shut the fleet down"          (asks before closing anything)
  handoff    "keep driving this run when your context fills up"
  help       this summary

HOW IT BEHAVES
  Your pane stays the orchestrator and is never closed by accident.
  Workers land as splits to the right in that same tab, not new tabs,
  and focus goes back to the pane you were in after each split. The app
  sizes the columns; this skill does not resize panes.
  New agents mirror yours: same harness, model, thinking level, launch
  flags and launch wrapper (such as mcc run --), unless you name
  something else. Your own prompt never carries over. An inherited
  permission bypass is announced before any agent starts.
  Agent state comes from the OSC 7501 status each agent CLI reports to hc.
  A prompt aimed at a busy, blocked or silent agent is refused before
  anything is typed.
  Every prompt waits for its own turn to settle, and blocked, stalled or
  timed-out agents are reported rather than silently retried.
  Dialogs are left for you: it shows the agent and never answers them.
  Closing panes needs your approval, and only workers it started are
  closed; it never stops the app or the hc core.
  It never calls the herdr TUI CLI.

WHAT IT NEEDS
  The Herdr desktop app's hc and herdr-app CLIs on PATH, and this session
  inside one of the app's terminals (HC_TERMINAL_ID set, shown in the
  window). Workers must report OSC 7501 status: Claude Code does.
  Observed with hc 0.1.20 and Herdr.app 0.1.15 on macOS.
  Not for the Herdr TUI (HERDR_ENV=1: use herdr-agent), Rex (rex-agent)
  or tmux (tmux-agent-comms). What differs from herdr-agent, and what is
  unavailable in the app: references/app-vs-tui.md.
```
