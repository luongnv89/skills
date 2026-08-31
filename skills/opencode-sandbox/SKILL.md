---
name: opencode-sandbox
description: "Run OpenCode in a docker-dev sandbox (SSH/gh on by default; --no-ssh/--no-github to isolate). Prints docker exec attach; kept until you confirm rm. Don't use for opencode.ai (opencode-runner), Herdr, or the app."
license: MIT
compatibility: "Requires Docker (Desktop or Engine) on PATH and running. Interactive mode additionally needs `cdev` (auto-installable from luongnv89/docker-dev) plus a pane-management skill (herdr-agent-comms or tmux-agent-comms)."
effort: medium
metadata:
  version: 2.1.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# OpenCode Sandbox

Run OpenCode inside a [luongnv89/docker-dev](https://github.com/luongnv89/docker-dev)
container for a local project. **SSH and GitHub auth are on by default**
(`~/.ssh`, `~/.config/gh`, `GH_TOKEN` from `gh auth token`) so `git commit`,
`git push`, `gh pr create`, and `gh pr merge` work in the container. Pass
`--no-ssh --no-github` when the task must not reach GitHub. Details:
`references/mounts-and-credentials.md`.

**Keep-by-default:** the container stays running after the task so the user
can attach a shell. Do not remove it unless they confirm (or they asked for
`--rm` up front).

## When to Use

- Run OpenCode against a project and let it commit, push, open, or merge a PR
  (`gh` / SSH available inside the container)
- OpenCode keeps hitting provider rate limits and the task needs a fresh
  container session
- The task must **not** touch GitHub — pass `--no-ssh --no-github` and review
  the host diff; push stays a separate step

## Repo Sync Before Edits (mandatory)

The container only sees whatever is on disk at `docker run` time — sync the
host repo *before* launching, not after:

```bash
branch="$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD)"
git -C "$PROJECT_DIR" fetch origin && git -C "$PROJECT_DIR" pull --rebase origin "$branch"
```

If the tree is dirty: stash (`-u`), sync, pop. If `origin` is missing or the
rebase conflicts, stop and ask the user before continuing.

Skip this step when the task is **read-only inspect** (list files, summarize)
and will not write the tree. Always sync when the container will edit files.

## Choose a mode

| Mode | Use when | Go to |
|---|---|---|
| **One-shot** (default) | Single task, no need to watch it work | "One-shot mode" below |
| **Interactive** | User wants to watch live or steer mid-task | `references/interactive-mode.md` |

Default to one-shot — it needs no pane-management skill, has no TUI-timing
gotchas, and its completion signal is a plain process exit code. Reach for
interactive mode only when the task genuinely needs a human in the loop
mid-run.

## One-shot mode

`scripts/run_opencode.sh` starts a named container (`sleep infinity` as PID 1
so it stays running), prints an attach command, then runs `opencode run --auto`
via `docker exec`. One exit code from OpenCode, output on stdout — no polling,
no TUI, no permission dialogs to click through (`--auto` handles them; see
`references/mounts-and-credentials.md` → _Why `--auto` is required_).

**The container is kept by default.** Do not pass `--rm` unless the user
already asked to throw the container away. After the run, ask them before
any `docker rm` (Step 4).

### Step 1 — Decide mounts

Every run mounts the project directory (`/workspace`). **On by default:**
`~/.config/opencode` (OpenCode's own auth — skip with `--no-opencode-config`),
`~/.ssh`, GitHub auth (`~/.config/gh` + `GH_TOKEN`), and `~/.gitconfig`. Opt
out when the user asks to isolate, or the task must not reach GitHub:

- `--no-ssh` — do not mount `~/.ssh`
- `--no-github` — do not mount `~/.config/gh` or inject `GH_TOKEN`
- `--no-git-identity` — do not mount `~/.gitconfig`
- `--no-opencode-config` — do not mount `~/.config/opencode`. OpenCode then
  starts unauthenticated (`opencode-handoff` builds on this). Combined with
  `--with-agents`, the script also mounts `~/.config/opencode/skills`
  read-only so its relative skill symlinks still resolve — and nothing else
  from that directory, including `service.json`. See
  `references/mounts-and-credentials.md`.

Add flags only for extras the task needs:

- `--with-claude-skills` — task must read/follow a **user-level** Claude Code
  skill living under `~/.claude/skills/` (mounts `~/.claude` **and**
  `~/.agents`, read-only — see the symlink gotcha in
  `references/mounts-and-credentials.md` before assuming one mount is
  enough). Skip this flag for a **project-local** skill/convention doc
  (e.g. `AGENTS.md`, `.claude/skills/` inside the repo itself, a
  CONTRIBUTING.md) — it's already inside `/workspace` via the project mount,
  no extra flag needed.
- `--with-agents` — mount `~/.agents` read-only **without** `~/.claude`. Use
  when the task needs the skill library but the container should not see
  Claude Code's own directory.

OpenCode has no native "skill" concept — mounting a directory only makes a
file *readable*, not *followed*. When using `--with-claude-skills`, the
`--message` must explicitly point OpenCode at it, e.g.: `"Read
/root/.claude/skills/<name>/SKILL.md and follow it as your playbook for this
task."`

Additional options accepted by `run_opencode.sh`: `--image IMAGE` to override
the default container image (`ghcr.io/luongnv89/u2604dev:latest`);
`--format FORMAT` to set `opencode run`'s output format (`default` or `json`;
default: `default`); `--name NAME` to set the container name (default:
`opencode-sandbox-<project>-<epoch>`); `--start-only` to create the container and
print the attach command without running OpenCode; `--exec-in NAME` to run
OpenCode in an already-started container; `--rm` to auto-remove the
container after OpenCode exits (opt-in — not the default).

### Step 2 — Start the container, show attach, then run OpenCode

Invoke the bundled script by **absolute path** — `scripts/run_opencode.sh`
next to this SKILL.md. Do not run `scripts/run_opencode.sh` from the
project directory; that file is not there.

**Two invocations**, so the user sees the attach command before OpenCode
blocks (a single `--project` + `--message` call also works, but the attach
line then sits in tool logs until OpenCode exits):

```bash
# 2a — create the keep-alive container, print attach, return immediately
bash /path/to/opencode-sandbox/scripts/run_opencode.sh \
  --project /path/to/project \
  --start-only \
  [--with-claude-skills] [--no-ssh] [--no-github]
```

Parse `CONTAINER_NAME=...` from stderr. Surface this to the user as a
fenced code block **now**, before step 2b:

```bash
docker exec -it <CONTAINER_NAME> zsh
```

```bash
# 2b — run OpenCode inside that container
bash /path/to/opencode-sandbox/scripts/run_opencode.sh \
  --project /path/to/project \
  --message "<task text>" \
  --exec-in "<CONTAINER_NAME>" \
  [--with-claude-skills] [--no-ssh] [--no-github]
```

For task text too long or complex for a shell argument, write it to a file
and attach it on **2b**:

```bash
bash /path/to/opencode-sandbox/scripts/run_opencode.sh \
  --project /path/to/project \
  --message "Follow the attached file's instructions exactly." \
  --file /path/to/task.txt \
  --exec-in "<CONTAINER_NAME>"
```

If `--exec-in` names a container that exists but is **stopped**, the script
runs `docker start` then execs. If the name does not exist, it errors —
do not `docker rm` a collision to "fix" it unless the user confirms.

`preflight.sh` (called automatically) checks the Docker daemon is running —
starting it on macOS if not — and pulls the image on first use. Both scripts
print a specific error with a fix on failure; read the message before
retrying blind. Common failures and fixes: `references/troubleshooting.md`.

**Completion criterion for this step:** step 2a exited 0 with a
`CONTAINER_NAME=` line; the attach command was shown to the user as a
fenced block *before* step 2b started; step 2b's OpenCode transcript then
ran.

### Step 3 — Verify before anything ships

**Completion criterion: exit code 0 from the `--exec-in` invocation, and the
printed transcript shows the task actually finished** (not a mid-task
rate-limit retry loop — see `references/troubleshooting.md` if it stalls).
Exit 0 means OpenCode finished without error; the container is still
running unless `--rm` was passed. It does **not** mean the change is
correct or safe to push.

Before treating the run as done:

1. `git -C "$PROJECT_DIR" status --short` and `git -C "$PROJECT_DIR" diff` — review every
   changed file, not just the ones the task description mentioned. A broad
   `git add <dir>/` stages backup/build artifacts (`.bak`, `.orig`, stray
   build output) just as readily as real changes — see
   `references/troubleshooting.md`.
2. If the task touched dependency files (`package.json`, lockfiles, etc.),
   diff them specifically for container-architecture leakage — a Linux
   binary promoted into a real (non-optional) dependency has shipped from
   this exact setup before. See `references/troubleshooting.md`.
3. Default credentials mean the container **can** `git push` / `gh pr`.
   Review `git status`/`diff` (and the GitHub result) anyway. If the user
   asked to isolate, you passed `--no-ssh --no-github` and push stays a
   **separate host step**.

### Step 4 — Ask before removing the container

**Default is keep.** Do not run `docker rm` (or pass `--rm`) unless the user
confirms they want the container gone.

After Step 3, ask once, naming the container:

> Container `<CONTAINER_NAME>` is still running. Attach with
> `docker exec -it <CONTAINER_NAME> zsh`. Remove it for cleanup?

- **Yes** → `docker rm -f "$CONTAINER_NAME"`, then confirm `docker container inspect "$CONTAINER_NAME"` fails.
- **No** / no answer → leave it running. Repeat the attach command so they
  still have a copy-paste line.
- **`--rm` was already passed** → the script removed it on exit; skip this
  step.

Do not treat leftover containers as a failure of the OpenCode task.

## Interactive mode

For watching OpenCode work live or steering it mid-task. Needs a real
pane/terminal the agent can repeatedly read and write — pair this skill with
**herdr-agent-comms** or **tmux-agent-comms** for the pane mechanics. Read
`references/interactive-mode.md` for what's specific to OpenCode-in-a-container
on top of those primitives: TUI readiness timing (sending too early drops the
message, or worse, a second premature send exits OpenCode entirely),
permission-dialog handling, and completion detection (container processes are
invisible to host-level agent-status tracking — poll the transcript or use a
sentinel string instead).

## Example

```bash
bash ~/.claude/skills/opencode-sandbox/scripts/run_opencode.sh \
  --project ~/code/my-app \
  --start-only
# → show the printed docker exec -it <name> zsh block to the user, then:
bash ~/.claude/skills/opencode-sandbox/scripts/run_opencode.sh \
  --project ~/code/my-app \
  --message "Add input validation to the signup form and run the test suite." \
  --exec-in "<CONTAINER_NAME>"
```

Expected output: 2a reports Docker/image ready and prints `CONTAINER_NAME=`
plus a copy-paste `docker exec -it <name> zsh` block, then returns. The
user can paste that into another terminal immediately. 2b streams OpenCode's
task transcript and exits `0`. The container is **still running**. Back on
the host, `git -C ~/code/my-app diff` shows the validation change and its
test — nothing else. Then ask the user whether to `docker rm -f <name>`.
If the transcript instead shows a rate-limit retry loop, treat the run as
unfinished (see `references/troubleshooting.md`), not as a pass.

## Acceptance Criteria

- [ ] `run_opencode.sh` exits `0`, and the transcript shows the task actually
      completed (not a stalled rate-limit retry)
- [ ] A copy-paste attach command (`docker exec -it <container-name> zsh`)
      was shown to the user
- [ ] The container was **not** removed unless the user confirmed cleanup
      (or they requested `--rm` up front)
- [ ] `git -C "$PROJECT_DIR" status --short` and `git -C "$PROJECT_DIR" diff` were reviewed on
      the host before anything is committed or pushed
- [ ] SSH (`~/.ssh`) and GitHub auth (`GH_TOKEN` / `~/.config/gh`) were
      mounted unless the user asked to isolate (`--no-ssh --no-github`)
- [ ] Dependency-file diffs (`package.json`, lockfiles) were checked for
      container-only binaries before treating the run as safe to merge

**Edge cases this skill accounts for:** a dirty host repo before sync (stash
`-u`, sync, pop); an already-running container from a prior task (name
collision — see `references/troubleshooting.md`); a leftover kept container
the user declined to remove (leave it; do not `docker rm` on your own); a
TUI message sent before the interactive pane finishes booting, which drops
the message or exits OpenCode entirely (see `references/interactive-mode.md`).

## Step Completion Report

```
◆ OpenCode Sandbox (one-shot run)
··································································
  Docker daemon:         √ pass (docker info)
  Image ready:           √ pass (ghcr.io/luongnv89/u2604dev:latest)
  Mounts:                √ workspace, opencode config, ssh, gh, gitconfig [+ claude skills]
  Credentials:           √ ssh+gh on | √ --no-ssh --no-github (isolated)
  Attach command:        √ docker exec -it <name> zsh shown
  Task exit code:        √ 0 | × <N> — <error from output>
  Host diff reviewed:    √ pass (git status/diff checked) | — n/a (no changes)
  Container:             √ kept (<name>) | √ removed (user confirmed) | √ --rm
  ____________________________
  Result:               PASS | FAIL
```

Adapt for interactive mode: replace `Task exit code` with `Sentinel/transcript
completion` and add `Permission dialogs handled` if any appeared. `Container`
is still kept-until-confirmed unless the user asked to auto-remove.
