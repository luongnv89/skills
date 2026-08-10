<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Herdr Agent Comms

> Tile **root + sub-agents** into **one grid tab** as equal-width columns — root stays put, workers stay the same size as root, messaging via the `herdr` CLI with status-aware waits.

## Highlights

- **Root + sub-agents grid** — every column, including root, is resized to equal width as sub-agents are added.
- **Root never replaced by accident** — the orchestrator pane stays put; only worker panes are closed on teardown.
- **Context handoff** — when the main agent's own window passes 50%, it spawns a successor orchestrator pane, hands over a compact fleet brief, and goes read-only so a long run never dies of a full context.
- **Fleet spawn** — agent CLI + model + thinking + optional skills, then assign tasks in parallel.
- **Message & steer** — `pane run` / `agent send`, wait on `working` → `done`/`idle`, read transcripts.
- **Broadcast** — fan one instruction to many agents; concurrent waits.
- **Safe teardown** — close sub-panes after confirmation; never surprise `server stop` or kill root.

## When to Use

| Say this... | Skill will... |
|---|---|
| "Spin up 2 Herdr agents beside me: reviewer and tests" | Build a grid in the root tab, launch agents in equal-width columns |
| "Ask the reviewer agent what it found" | Resolve target, send, wait on status, relay reply |
| "Broadcast 'pull main' to all fleet agents" | Fan-out send + concurrent collect |
| "Focus the tests pane so I can steer" | `herdr agent focus tests` |
| "Keep this fleet running even when you run out of context" | Hand the orchestrator role to a fresh `main-g2` pane with a compact brief |

## How It Works

```mermaid
graph TD
    A["Resolve root pane + tab + workspace"] --> B["next_grid_split · split rightmost + --equalize to equal width"]
    B --> C["Rename sub-pane · launch CLI · wait idle"]
    C --> D["Submit tasks · broadcast"]
    D --> E["Wait agent-status done|idle"]
    E --> F["Read recent-unwrapped · focus to steer"]
    style A fill:#4CAF50,color:#fff
    style F fill:#2196F3,color:#fff
```

## Usage

```
/herdr-agent-comms
```

Or describe the goal — "tile a reviewer agent with my pane", "launch a Herdr fleet grid beside me".

## Popular Use Cases

### 1. Root + sub-agents grid (default)

```
/herdr-agent-comms spin up 2 pi agents in a grid with my pane:
- reviewer: thinking medium — review the last commit
- tests: thinking low — propose a minimal test plan
```

### 2. Message a running agent

```
/herdr-agent-comms ask reviewer to summarize open risks; show me the reply
```

### 3. Steer live

```
/herdr-agent-comms focus the tests agent so I can type into it
```

## Requirements

- Herdr installed (`herdr --version`) and server running (`herdr status`)
- Prefer running the orchestrator **inside** Herdr (`HERDR_ENV=1`) so `$HERDR_PANE_ID` is the root
- Agent CLIs on PATH (`pi`, `claude`, `codex`, …) as needed
- Optional: `herdr integration install <agent>` for better status

## Related

- Sibling skill: `tmux-agent-comms` (same workflow for plain tmux)
- Cheatsheet: https://luongnv.com/awesome-cheatsheets/cheatsheets/herdr/
- Docs: https://herdr.dev/docs/
