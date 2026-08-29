<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# OpenCode Docker Dev

> Run OpenCode sandboxed inside a luongnv89/docker-dev container — isolated from host SSH keys and GitHub tokens by construction. The container is kept by default so you can attach a shell.

## Highlights

- One-shot mode uses **`--start-only` then `--exec-in`**: a named keep-alive container, a copy-paste `docker exec -it <name> zsh` attach command *before* OpenCode runs, then `opencode run --auto` via `docker exec` — a plain exit code, no TUI to drive or permission dialogs to click through
- Container is **kept by default**; the agent asks before `docker rm`. Pass `--rm` only when you already want it gone
- Never mounts `~/.ssh` or injects a GitHub token — by design, not by discipline. Tasks that need push/publish access stop before that step; a human does it on the host afterward
- Handles the `~/.claude` → `~/.agents` symlink gotcha automatically when mounting Claude Code skills into the container
- Interactive mode (pairs with herdr-agent-comms or tmux-agent-comms) documents the OpenCode-specific TUI timing and permission-dialog quirks discovered while building this skill

## When to Use

| Say this...                                                        | Skill will...                                                                 |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| "Run OpenCode on this project without giving it my SSH key"        | Set up mounts, run `opencode run --auto` in a container, verify the diff      |
| "OpenCode keeps hitting rate limits, try it in a fresh container"   | Launch a fresh container session against the same task (kept until you confirm cleanup) |
| "Use the docker-dev repo to run OpenCode on this repo"              | Preflight Docker, build mounts, run the task, report exit code + diff         |

## How It Works

```mermaid
graph TD
    A["Decide mode: one-shot or interactive"] --> B["Decide mounts: workspace + opencode config, plus skills/git-identity if needed"]
    B --> C["preflight.sh: Docker running, image pulled"]
    C --> D["--start-only: kept container + attach command"]
    D --> E["--exec-in: opencode run --auto"]
    E --> F["Review git diff on host, then ask before docker rm"]
    style A fill:#4CAF50,color:#fff
    style F fill:#2196F3,color:#fff
```

## Usage

Model-invoked — ask to run OpenCode sandboxed, isolated from credentials, or in a fresh container to dodge rate limits, and the skill applies itself.

## Resources

| Path                                        | Description                                                                 |
| -------------------------------------------- | ----------------------------------------------------------------------------- |
| `scripts/preflight.sh`                       | Ensures Docker is running and the image is pulled                            |
| `scripts/run_opencode.sh`                    | `--start-only` then `--exec-in`: kept container, attach command, `opencode run --auto` |
| `references/mounts-and-credentials.md`       | The credential redline, standard mounts, and the `~/.claude` symlink gotcha  |
| `references/interactive-mode.md`             | TUI readiness timing, permission dialogs, completion detection               |
| `references/troubleshooting.md`              | Provider errors, rate limits, outdated `cdev`, dependency-file leakage       |

## Output

A completed OpenCode task run against the mounted project directory, a
copy-paste `docker exec -it <name> zsh` attach command, a prompt asking
whether to remove the kept container, plus a Step Completion Report showing
mounts used, exit code, attach shown, container kept/removed, and whether
the host diff was reviewed before anything ships. One-shot mode's raw
output is whatever `opencode run` printed (or JSON events, with
`--format json`).
