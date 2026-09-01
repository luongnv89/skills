<!-- Human-facing catalog page. AI agents: skip this file; read ../SKILL.md instead. -->

# OpenCode Handoff

Hit the OpenCode usage limit mid-task? This skill gets you back to work in a
few minutes, on the same project, with the same skills — on a fresh allowance.

## What it does

1. Creates a Docker sandbox for your project, mounting the working tree and
   your global + project-local `.agents/` setup
2. Deliberately leaves your OpenCode config, token, and key on the host, so the
   container's OpenCode starts unauthenticated
3. Opens a detached tmux session attached to the container and hands you the
   `attach-session` line

You log in inside the panel with a different account and carry on.

## Usage

```
/opencode-handoff
```

Or call the script directly:

```bash
bash ~/.claude/skills/opencode-handoff/scripts/handoff.sh --project ~/code/my-app
```

Then:

```bash
tmux attach-session -t <session>
# inside the panel
opencode2 auth login
opencode2
# (older images may use `opencode` instead)
```

## Trigger phrases

- "I hit the OpenCode limit, get me a fresh session"
- "hand this project off to a new OpenCode sandbox"
- "continue this work with a fresh OpenCode usage limit"
- "same setup, new OpenCode account"

## Requirements

- Docker on PATH and running
- `opencode-sandbox` v2.1.0 or newer (this skill composes its container logic); the default image is `ghcr.io/luongnv89/devbox:latest`
- `tmux` for the panel — optional; without it you get the `docker exec` line

## Options

| Flag | Effect |
|---|---|
| `--project DIR` | project to hand off (required) |
| `--name` / `--session` | override the generated container / tmux names |
| `--image IMAGE` | use a different container image (default: `ghcr.io/luongnv89/devbox:latest`) |
| `--no-ssh` / `--no-github` | isolate the container from GitHub |
| `--no-tmux` | skip the panel, just print the attach command |
| `--sandbox-script PATH` | point at `run_opencode.sh` explicitly |

## What is not shared

Your OpenCode credentials. `~/.config/opencode/service.json` (a password) and
`~/.local/share/opencode/auth.json` (your key) never enter the container — the
skill verifies this at runtime and refuses to hand over if either appears.
SSH and GitHub auth *are* shared by default, so you can still commit and push.

## Related skills

- **opencode-sandbox** — run a one-shot OpenCode task in a container
- **opencode-runner** — offload work to opencode.ai's hosted free models
- **tmux-agent-comms** — the panel mechanics this skill builds on
