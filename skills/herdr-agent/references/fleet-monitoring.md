# Fleet monitoring, status, and reporting (Herdr)

Rationale for Phase 6 of `herdr-agent`. Three surfaces, three audiences:
the snapshot answers *you*, metadata badges answer *the human glancing at the
sidebar*, and notifications interrupt them when something actually needs them.

## One call, whole fleet

```bash
python3 "$here/fleet_status.py" --tab "$root_tab"
python3 "$here/fleet_status.py" --tab "$root_tab" --json          # machine-readable
python3 "$here/fleet_status.py" --tab "$root_tab" --fail-on-blocked
```

It wraps `herdr api snapshot`, which returns the entire live session — version
and protocol, focused workspace/tab/pane ids, workspace, tab and pane records,
per-tab layout snapshots, and every agent record — in **one** socket round trip.

Why that matters for a fleet:

- **Cost is flat.** One `herdr` invocation for 2 agents or 12. Per-agent
  `herdr agent get` costs N process spawns and N round trips.
- **The view is consistent.** N separate reads can observe agent A before B
  changed state and report a fleet that never existed at any instant.
- **It sees agent-less panes.** `--panes` includes panes whose process Herdr
  does not recognize, which is exactly where a silently dead worker hides.

Rows sort by attention: `blocked` first, then `done`, `working`, `idle`,
`unknown`. `--fail-on-blocked` exits 3 so a monitoring loop can branch without
parsing the table.

Read a single agent with `herdr agent get <target>` only when you need one
target's current revision. Never poll it in a loop — use `herdr agent wait`.

## Badge each worker so the human can read the fleet

`herdr pane report-metadata` writes **display-only** fields that Herdr renders
in the sidebar. It never affects semantic state, waits, notifications or
rollups, so badging is always safe.

```bash
python3 "$here/badge.py" reviewer \
  --title "Review PR 412" \
  --display-agent "Claude: review" \
  --state-label working="reading the diff" \
  --state-label done="findings ready" \
  --token role=review --token phase=working \
  --ttl-ms 3600000
```

The wrapper exists because `report-metadata` takes a pane id while fleet
bookkeeping runs on agent names; it resolves either form.

What each field buys you:

| Field | Effect |
|---|---|
| `--title` | Replaces the pane title in the sidebar with the assigned job |
| `--display-agent` | Replaces the visible agent name (all workers otherwise read "claude") |
| `--state-label STATUS=TEXT` | Task-specific wording for one status; keys must be `idle`, `working`, `blocked`, `done`, `unknown` |
| `--token NAME=VALUE` | Arbitrary named value, renderable as `$NAME` in Agent rows and returned by `pane get` / `agent get` |
| `--ttl-ms N` | Expiry, 1 to 86400000 ms. Omit for "until replaced or the pane closes" |

Server-enforced caps: 80 characters per title, display name, state label and
token value; at most 16 token keys per report and 32 retained per pane; token
names are 1–32 ASCII letters, digits, underscores or hyphens; a pane accepts
sequenced reports from at most 32 distinct sources for its whole lifetime, and
clearing does not release a slot. `badge.py` reports under one fixed source for
that reason — do not invent a new source per call.

Token maps are patches: a value sets a key, JSON null clears it, omitted keys
stay. Clear with `herdr pane report-metadata <pane> --source ... --clear-token NAME`.

Workspace-level rollups use the same contract via
`herdr workspace report-metadata <workspace_id> --source ID --token NAME=VALUE`,
rendered as `$NAME` in Space rows. Use it for a fleet-wide counter such as
`--token fleet="3 working, 1 blocked"`.

Badging is display only. `fleet_status.py` still reports semantic
`agent_status`, and a badge that says `phase=done` next to a `working` status
means your bookkeeping drifted, not that the agent finished.

## Interrupt the human only when they are needed

```bash
herdr notification show "Fleet done" --body "reviewer and tests settled" --sound done
herdr notification show "Agent blocked" --body "reviewer needs a trust decision" --sound request
```

`--position` takes `top-left`, `top-right`, `bottom-left`, `bottom-right`;
`--sound` takes `none`, `done`, or `request`.

Send one when a run finishes, when an agent goes `blocked`, and when a HANDOFF
completes. Do not send one per relayed reply — a notification the human learns
to ignore is worse than none.

`herdr agent focus <name>` is the companion move: it puts the pane in front of
them. Focus also marks that agent's completion seen, which flips `done` to
`idle`. Focus for a blocker, not to show off a finished reply.

## What the human's own client already shows

Herdr's sidebar rolls agent state up per workspace on its own, and
`terminal_title_stripped` on each record carries whatever the agent CLI last
advertised as its title — for Claude Code, a short summary of the current turn.
`fleet_status.py` falls back to it when no badge title is set, so a fleet is
readable even before you badge anything.

## The run report

Report every target, including the ones that did not run. An agent missing from
the report reads as success.

```text
Fleet: PARTIAL
Root kept: w26:p1
Workers: reviewer=settled, tests=settled, docs=BLOCKED
Layout: 4 equal-width columns
Replies: 2 captured, 1 blocked, 0 timed out
```

Every worker ends in exactly one of: settled, blocked, stalled, timed out,
failed, or skipped-unsafe. Take those outcomes from `broadcast.sh`'s per-target
lines and the closing `fleet_status.py` call, not from memory of what you sent.
