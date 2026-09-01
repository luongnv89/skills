# Credential Boundary — what crosses into the handoff container

The reason this skill exists. Every mount decision below was verified against a
real container; change one only with the same evidence.

## The two credentials that must never mount

| File | Key it holds | Default sandbox behavior |
|---|---|---|
| `~/.local/share/opencode/auth.json` | `opencode.type`, `opencode.key` | never mounted (outside `~/.config`) |
| `~/.config/opencode/service.json` | `password` | not mounted by handoff (sandbox mounts it only with `--with-opencode-config`) |

`opencode-sandbox` does not mount `~/.config/opencode` by default. It can mount
that host profile only when `--with-opencode-config` is requested, which is
wrong for this handoff. `handoff.sh` explicitly passes `--no-opencode-config`.

The container therefore gets a fresh local OpenCode profile with no host
credential. Anonymous/free models may work without login; `opencode2 auth login`
inside the panel is optional when the selected provider requires it (`opencode`
is the fallback on older images). A fresh local profile does not guarantee a
fresh provider-side allowance.

## The wiring problem, and why the subdirectory mount solves it

OpenCode discovers skills through `~/.config/opencode/skills/` — inside the
directory just excluded. Its entries are symlinks, and crucially they are
**relative**:

```
~/.config/opencode/skills/issue-creator -> ../../../.agents/skills/issue-creator
```

Three levels up from `.config/opencode/skills/` is `$HOME`, so the link resolves
to `~/.agents/skills/issue-creator`. Mount that one subdirectory at the mirrored
container depth, plus `~/.agents`, and the links resolve inside the container
untouched:

```bash
-v "$HOME/.agents:/root/.agents:ro"
-v "$HOME/.config/opencode/skills:/root/.config/opencode/skills:ro"
```

Verified in a real container:

```console
$ docker exec <name> readlink -f /root/.config/opencode/skills/issue-creator
/root/.agents/skills/issue-creator
$ docker exec <name> ls /root/.config/opencode/
skills
```

`/root/.config/opencode/` contains **only** `skills` — Docker created the parent
for the submount, so nothing else from the host's config directory exists there.

### Why not rebuild the symlinks in-container

`~/.config/opencode/skills` is a **curated subset** (9 entries) of
`~/.agents/skills` (76). Symlinking all 76 would change the user's setup rather
than reproduce it. Mounting the curated directory reproduces it exactly.

### Why the mount is read-only

The container must not be able to rewrite the host's skill wiring. This also
means project-local skills cannot be symlinked into that directory — which is
fine, see below.

## Project-local `.agents/`

Nothing extra is needed. `<project>/.agents/` arrives inside the `/workspace`
mount at the same path relative to the project root that it occupies on the
host, so whatever project-local discovery OpenCode performs on the host, it
performs identically in the container.

Deliberately **not** done: symlinking `/workspace/.agents/skills/*` into
`/root/.config/opencode/skills/`. The host does not wire them there either, so
doing it in the container would make the sandbox diverge from the session it is
supposed to mirror.

## What still mounts, and why

SSH (`~/.ssh`), GitHub (`~/.config/gh` + `GH_TOKEN`), and git identity
(`~/.gitconfig`) stay on by default, inherited from `opencode-sandbox`. The
handoff is meant to continue real work, which means committing and pushing.
These are *GitHub* credentials, not OpenCode ones — excluding them would not
affect the usage allowance and would break the workflow.

Pass `--no-ssh --no-github` when the handed-off task must not reach GitHub.

## The runtime check

Mount configuration is easy to get wrong and silent when it is. `handoff.sh`
asserts the boundary against the running container before opening the panel.
A probe (`docker exec true`) runs first so a dead container cannot look like
a clean boundary. Then two checks, both fail-closed:

1. **Mount sources.** After resolving realpaths, no bind-mount source may
   equal the host's `~/.config/opencode` or `~/.local/share/opencode`. The
   `skills/` subdirectory is a different source path, so it is allowed; a
   `skills/` directory that is actually a symlink to the parent is not.
2. **Credential filenames.** `find` for `auth.json` and `service.json` under
   every OpenCode config/data tree in the container (`/root`, `/home/*`,
   `/workspace`). That catches image leftovers, a project that *is* `$HOME`,
   and a leaked file inside the `skills/` submount, without flagging an
   unrelated `auth.json` elsewhere in the project.

Any hit refuses the handoff and tells the user how to inspect and remove the
container. A leak is a hard failure, never a warning: the user asked for a
session that cannot spend their account.
