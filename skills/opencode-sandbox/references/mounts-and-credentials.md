# Mounts and credentials

## Credentials on by default (opt out to isolate)

`run_opencode.sh` mounts **`~/.ssh`** and GitHub auth (`~/.config/gh` plus
`GH_TOKEN`/`GITHUB_TOKEN` from `gh auth token`) **by default**, so `git
commit`, `git push`, `gh pr create`, and `gh pr merge` work inside the
container. `~/.gitconfig` is also on by default for commit authorship.

That is a real blast radius: an SSH key or `GH_TOKEN` reaches **every repo
and org that credential is scoped to**, not just the mounted project.
`--auto` will approve those actions without a prompt. Use this default when
the task is supposed to ship (push/PR/merge). For an untrusted or
read-only task, pass **`--no-ssh --no-github`** (and `--no-git-identity` if
you also do not want commits attributed as you).

Do not print the token. The script logs
`Credentials: ssh=1 github=1 gitconfig=1 opencode-config=1 agents=0`
(0 = off).

## Standard mounts

| Mount | Container path | When |
|---|---|---|
| project directory | `/workspace` | always — the task's target |
| `~/.config/opencode` | `/root/.config/opencode` | default on — OpenCode auth/config. Skip with `--no-opencode-config` (OpenCode then starts unauthenticated; see below) |
| `~/.ssh` | `/root/.ssh` | default on — `git push` over SSH. Skip with `--no-ssh` |
| `~/.config/gh` | `/root/.config/gh` | default on — `gh` CLI host login. Skip with `--no-github` |
| `GH_TOKEN` / `GITHUB_TOKEN` | env | default on — from `gh auth token` on the host. Skip with `--no-github` |
| `~/.gitconfig` (ro) | `/root/.gitconfig` | default on — commit authorship. Skip with `--no-git-identity` |
| `~/.claude` (ro) | `/root/.claude` | `--with-claude-skills` — task needs to read/follow a specific Claude Code skill |
| `~/.agents` (ro) | `/root/.agents` | `--with-agents`, or auto-added alongside `~/.claude` — see the symlink gotcha below |
| task file | `/scratch/<name>` | `--file PATH` — copied in, not bind-mounted; see SKILL.md → One-shot mode |

`run_opencode.sh` builds these automatically from its flags — read it before
reimplementing the logic by hand. The container is **kept by default**
(still running after the task) so the user can attach. Ask before
`docker rm`.

## The `~/.claude` symlink gotcha

Skills installed under `~/.claude/skills/<name>` are frequently symlinks to
`~/.agents/skills/<name>` (e.g. `~/.claude/skills/release-manager ->
../../.agents/skills/release-manager`). Mount `~/.claude` alone and the
symlink still shows up in `ls`, but resolving it inside the container fails —
the target lives outside every mounted path. The failure mode is confusing
because it looks like a permissions issue, not a missing mount:

```
$ ls /root/.claude/skills/release-manager/SKILL.md
ls: cannot access '/root/.claude/skills/release-manager/': No such file or directory
```

Fix: mount `~/.agents` read-only alongside `~/.claude` whenever both exist.
`run_opencode.sh --with-claude-skills` does this automatically — it's the
reason the flag checks for `~/.agents` at all, not just `~/.claude`. If a task
still can't read a skill file after both are mounted, the skill likely lives
somewhere else entirely (a plugin directory, a project-local
`.claude/skills/`) — check the real symlink target on the host with
`readlink ~/.claude/skills/<name>` before assuming the mount is wrong.

## Why `--auto` is required (and what credentials change)

`opencode run` requires `--auto` to run non-interactively — without it,
OpenCode blocks on a permission dialog with nothing attached to answer it,
and the container hangs until the process is killed. OpenCode's own `--help`
labels `--auto` "dangerous": it auto-approves every action the agent wants
to take.

With **default credentials** (`~/.ssh` + `GH_TOKEN`), that includes `git
push` and `gh pr create/merge` against every org those credentials can
reach. That is intended for ship-it tasks. It is **not** a sandbox against
GitHub — only against host paths you did not mount. For a task that must
not touch GitHub, pass `--no-ssh --no-github` so `--auto` cannot push.

`--auto` is still required in both modes; the mount list decides how far a
mistake can travel.


## Excluding OpenCode's own config (`--no-opencode-config`)

Every default run mounts `~/.config/opencode` so the container inherits the
host's OpenCode setup. That directory contains more than preferences:

| File | Contents |
|---|---|
| `service.json` | a `password` |
| `cli.json`, `tui.jsonc`, `opencode.jsonc` | preferences, plugin config |
| `skills/` | relative symlinks into `~/.agents/skills/` |

The account key itself lives elsewhere — `~/.local/share/opencode/auth.json`
(`opencode.key`) — and is never mounted by this script.

Pass `--no-opencode-config` for a container that must **not** inherit the host's
OpenCode identity, e.g. one meant to run on a separate account with its own
usage allowance. OpenCode inside then starts unauthenticated and needs its own
`opencode auth login`.

Because that also drops the `skills/` wiring, `--no-opencode-config`
`--with-agents` together re-mount just that subdirectory read-only:

```
-v ~/.agents:/root/.agents:ro
-v ~/.config/opencode/skills:/root/.config/opencode/skills:ro
```

The symlinks are relative (`../../../.agents/skills/<name>`), so at the mirrored
depth they resolve against the `~/.agents` mount with no rewriting, and
`/root/.config/opencode/` ends up containing only `skills`.

`--with-agents` is the narrower sibling of `--with-claude-skills`: it mounts
`~/.agents` alone, leaving `~/.claude` — and any Claude Code credentials under
it — on the host.
