# Edge Cases — herdr-agent

Read this when a target or the layout does not behave as the phase expects. Each line names the condition, then the action.

- `blocked`: focus the pane, notify, and request human action.
- `agent_not_found`: no detected agent in that pane — `agent start` it, or drop to the pane-surface fallback.
- `unknown` status: `herdr integration status`, then `herdr agent explain <target> --json` to see which rule matched.
- Name collision: suffix the requested name; never reuse an existing agent accidentally.
- More than four panes: warn that columns become cramped; change layout only with user approval.
- Unequal grid: rerun the equalizer and abort worker launch if it still fails.
- Wrong workspace or accidental tab: stop, preserve work, and ask before moving or closing panes.
- Successor never acks: HANDOFF failed — stay main, keep the fleet, and report the orphan pane before asking to close it.
- Root process-info has only `argv0`, no full `argv`: abort before splitting or starting; update/restart Herdr, or use `--without flags` only when reduced inheritance is intentional.
- A start times out after inheriting a flag: the CLI rejected it; read the pane for its message before retrying.
