<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Herdr Agent Comms

> Spawn, manage, and talk to AI agents as Herdr tabs — one project workspace, one tab per agent, messaging via the `herdr` CLI with status-aware waits.

## Highlights

- **Project workspace** — all agents for a repo share one Herdr workspace (sidebar rollup).
- **Tab per agent** — each sub-agent is a visible tab you can click or `herdr agent focus`.
- **Fleet spawn** — agent CLI + model + thinking + optional skills, then assign tasks in parallel.
- **Message & steer** — `pane run` / `agent send`, wait on `working` → `done`/`idle`, read transcripts.
- **Broadcast** — fan one instruction to many agents; concurrent waits.
- **Safe teardown** — close tabs/panes only after confirmation; never surprise `server stop`.

## When to Use

| Say this... | Skill will... |
|---|---|
| "Spin up 3 Herdr agents for this repo: reviewer, tests, docs" | Create/reuse project workspace, one tab each, launch agents |
| "Ask the reviewer agent what it found" | Resolve target, send, wait on status, relay reply |
| "Broadcast 'pull main' to all fleet agents" | Fan-out send + concurrent collect |
| "Jump me into the tests agent so I can steer" | `herdr agent focus tests` |

## How It Works

```mermaid
graph TD
    A["Ensure herdr server + project workspace"] --> B["Create tab per agent + launch CLI"]
    B --> C["Rename agent · wait idle · submit task"]
    C --> D["Send / broadcast via pane run"]
    D --> E["Wait agent-status done|idle"]
    E --> F["Read recent-unwrapped · relay"]
    F --> G["Focus to steer or tear down confirmed"]
    style A fill:#4CAF50,color:#fff
    style G fill:#2196F3,color:#fff
```

## Usage

```
/herdr-agent-comms
```

Or describe the goal in natural language — "launch a Herdr fleet", "message my Herdr reviewer tab".

## Popular Use Cases

### 1. Fleet with model/thinking/skill knobs

```
/herdr-agent-comms spin up 2 pi agents in this project:
- reviewer: model sonnet, thinking medium, skill code-review — review the last commit
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
- Agent CLIs on PATH (`pi`, `claude`, `codex`, …) as needed
- Optional: `herdr integration install <agent>` for better status

## Related

- Sibling skill: `tmux-agent-comms` (same workflow for plain tmux)
- Cheatsheet: https://luongnv.com/awesome-cheatsheets/cheatsheets/herdr/
- Docs: https://herdr.dev/docs/
