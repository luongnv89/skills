---
name: opencode-handoff
description: "Resume a limit-blocked OpenCode session in a fresh sandbox: same project and agent setup, no host OpenCode config/token/key, attached in a tmux panel. Don't use for one-shot sandbox tasks (opencode-sandbox), opencode.ai (opencode-runner), or Herdr."
license: MIT
compatibility: "Requires Docker on PATH and running, plus the opencode-sandbox skill at v2.1.0 or newer. The tmux panel additionally needs `tmux`; without it the skill prints the attach command instead."
effort: medium
metadata:
  version: 1.0.4
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# OpenCode Handoff

You hit the OpenCode usage limit mid-task. This skill gives you a new local
OpenCode profile for the **same project** with the **same agent setup**,
deliberately leaves the host's OpenCode config, token, and key behind, and
opens it in a **new tmux panel**.

The credential exclusion is the point, not a side effect. Anonymous/free models
may work without an account, and authentication is optional when the selected
provider requires it. A fresh local profile does not guarantee a fresh provider,
model, account, network, or service allowance.

This skill **composes** two others rather than reimplementing them:

| Concern | Owned by |
|---|---|
| Container lifecycle, mounts, credentials | `opencode-sandbox` (`run_opencode.sh`) |
| Panel mechanics | `tmux-agent-comms` (Phase 1 — create/discover) |
| Credential boundary + wiring the two together | this skill |

## When to Use

- OpenCode reports a usage or rate limit and you want to keep going now
- You want a second OpenCode session on the same project under a different
  account, without disturbing the host session
- You want a disposable OpenCode environment that cannot spend the host account

Do **not** use it to run a one-shot task in a container (that is
`opencode-sandbox`), to call opencode.ai's hosted models (`opencode-runner`), or
to manage Herdr panes (`herdr-agent-comms`).

## Repo Sync Before Edits (mandatory)

The container edits the project tree through the `/workspace` mount, and it only
sees what is on disk at `docker run` time. Sync **before** launching:

```bash
branch="$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD)"
git -C "$PROJECT_DIR" fetch origin && git -C "$PROJECT_DIR" pull --rebase origin "$branch"
```

If the tree is dirty: stash (`-u`), sync, pop. If `origin` is missing or the
rebase conflicts, stop and ask the user — never rebase blind on a dirty tree.

Because the handoff container writes to the same working tree as the host
session, decide with the user which session owns the tree before starting work
in both.

## What crosses into the container, and what does not

This is the whole design. Read `references/credential-boundary.md` before
changing any mount.

| Host path | In container | Why |
|---|---|---|
| the project dir | `/workspace` (rw) | the work itself, including its `.agents/` |
| `~/.agents` | `/root/.agents` (ro) | the global skill library |
| `~/.config/opencode/skills` | `/root/.config/opencode/skills` (ro) | skill wiring — see below |
| `~/.ssh`, `~/.config/gh`, `GH_TOKEN`, `~/.gitconfig` | mounted (opt out) | so `git push` / `gh pr` still work |
| `~/.config/opencode` (the rest) | **absent** | `service.json` holds a `password` |
| `~/.local/share/opencode` | **absent** | `auth.json` holds `opencode.key` |

`~/.config/opencode/skills/<name>` entries are **relative** symlinks
(`../../../.agents/skills/<name>`). Mounting that one subdirectory at the same
depth alongside `~/.agents` makes them resolve inside the container with no
rewriting, while everything else in `~/.config/opencode` — including the
credential — stays on the host.

Project-local `.agents/` needs no special handling: it arrives with the project
mount at the same relative path it occupies on the host, so OpenCode's
project-local discovery behaves in the container exactly as it does outside.

## Workflow

### Step 1 — Confirm the project and sync

Resolve the project directory (default: the repo you are in) and run the
**Repo Sync** above. Confirm the target with the user if it is not obvious.

### Step 2 — Create the container and open the panel

One invocation does both. Call it by **absolute path** — the script lives next
to this SKILL.md, not in the project:

```bash
bash /path/to/opencode-handoff/scripts/handoff.sh --project /path/to/project
```

It resolves `opencode-sandbox`'s `run_opencode.sh` from the sibling skill (then
`~/.claude/skills`, then `~/.agents/skills`), **verifies that script supports
`--no-opencode-config` and `--with-agents`**, and errors out if it does not — an
older sandbox would silently mount the host credentials, which is the one
failure this skill must never ship.

Options: `--name` / `--session` to override generated names, `--image` to pass a
different image through (default: `ghcr.io/luongnv89/devbox:latest`),
`--no-ssh` / `--no-github` to isolate the container from
GitHub, `--no-tmux` to skip the panel and just print the attach command, and
`--sandbox-script` to point at `run_opencode.sh` explicitly.

### Step 3 — Verify the boundary held

`handoff.sh` checks this itself and **refuses to hand over** if the host's
OpenCode config or data directory is bind-mounted, or if `auth.json` /
`service.json` exists under any OpenCode config/data path in the container
(`/root`, `/home/*`, and `/workspace`). Confirm you saw:

```
Credential boundary: OK (no OpenCode config, token, or key in the container).
Global agent setup: <N> skills under /root/.agents/skills.
```

A `Warning:` about `/root/.agents/skills` means the global setup did not mount —
the session will work but without your skills. Fix `~/.agents` on the host and
recreate rather than proceeding.

### Step 4 — Hand the panel to the user

Surface the printed session and attach command as a fenced block. OpenCode
starts with a fresh local profile; start it directly for anonymous/free models,
and log in only if the selected provider requires authentication:

```bash
tmux attach-session -t <SESSION_NAME>
# then, inside the panel:
opencode2
# If authentication is required:
opencode2 auth login
# (older images may use `opencode` instead)
```

Never run `tmux attach-session` yourself from a non-TTY tool
(`tmux-agent-comms`, Critical Rule). The session is created detached; attaching
is the human's step.

### Step 5 — Ask before removing the container

**Default is keep**, matching `opencode-sandbox`. The container holds the
user's new session; removing it ends their work. Ask once, naming it:

> Container `<CONTAINER_NAME>` is still running (tmux session
> `<SESSION_NAME>`). Remove it for cleanup?

- **Yes** → `docker rm -f "$CONTAINER_NAME"`, then `tmux kill-session -t "$SESSION_NAME"`
- **No** / no answer → leave both, and repeat the attach command

## Example

```bash
bash ~/.claude/skills/opencode-handoff/scripts/handoff.sh \
  --project ~/code/my-app
```

Expected output: the sandbox reports `opencode-config=0 agents=1`, then
`Credential boundary: OK`, `Global agent setup: 74 skills`, then
`SESSION_NAME=opencode-handoff-my-app-1788169556` with its
`tmux attach-session` line. The user attaches and starts `opencode2` with a
fresh local profile, optionally logging in when the selected provider requires
it (`opencode` is used on older images). The host session stays untouched; a
provider-side rate limit may still apply.

## Acceptance Criteria

- [ ] A container was created for the requested project, mounted at `/workspace`
- [ ] `/root/.agents/skills` is populated and
      `readlink -f /root/.config/opencode/skills/<any>` resolves under it
- [ ] `Credential boundary: OK` printed — no `auth.json` or `service.json`
      under any OpenCode config/data path in the container, and the host
      credential directories are not bind-mounted
- [ ] A **detached** tmux session was created and its `attach-session` line was
      shown to the user; the skill never attached to it itself
- [ ] Optional `opencode2 auth login` instructions were surfaced, not assumed
- [ ] The container was **not** removed unless the user confirmed

**Edge cases this skill accounts for:** an `opencode-sandbox` older than v2.1.0
(hard error, never a silent credential mount); `tmux` absent (warn, print the
`docker exec` line, still exit 0); a tmux session name collision (error, do not
reuse someone else's panel); a missing `~/.agents` (warn — the session works,
the skills do not); a dirty host tree before sync (stash `-u`, sync, pop); two
sessions writing one working tree (decide ownership before starting).

## Step Completion Report

```
◆ OpenCode Handoff
··································································
  Repo sync:             √ pass (fetch + rebase) | — n/a (clean, read-only)
  Sandbox script:        √ found, supports --no-opencode-config
  Container:             √ <name> running
  Agent setup:           √ <N> global skills, project .agents present
  Credential boundary:   √ no opencode config/token/key | × LEAK <path>
  Panel:                 √ tmux <session> (detached) | — n/a (no tmux)
  Login surfaced:        √ optional opencode2 auth login shown to user
  Container:             √ kept (<name>) | √ removed (user confirmed)
  ____________________________
  Result:               PASS | FAIL
```
