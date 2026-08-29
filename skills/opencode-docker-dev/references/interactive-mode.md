# Interactive mode

Use this when the user wants to **watch OpenCode work live** or **steer it
mid-task** — things one-shot mode (`opencode run --auto`) can't do, since it's
a single fire-and-forget process with no way to send a follow-up.

Interactive mode drives OpenCode's full-screen TUI, which needs a real
terminal/pty that stays alive across multiple reads and writes. This skill
does not implement pane management itself — pair it with whichever
pane-management skill is available in the session:

- **herdr-agent-comms** — if `herdr` is on PATH and its server is running
- **tmux-agent-comms** — if using plain tmux instead

Use that skill's split/send/wait/read primitives to drive the pane. The
material below is what's specific to OpenCode running *inside a container*
on top of those primitives — none of it is pane-management mechanics.

## Setup: same mounts, `cdev` instead of plain `docker run`

Interactive mode benefits from `cdev` (the docker-dev repo's launcher CLI)
over a raw `docker run`, because it gives you a persistent zsh shell to work
from between OpenCode invocations, plus the same mount flags this skill's
`run_opencode.sh` builds by hand.

**Check the installed `cdev` is current before relying on its flags** — an
old version silently lacks `--mount-opencode`/`--preset`:

```bash
command -v cdev || curl -fsSL https://raw.githubusercontent.com/luongnv89/docker-dev/main/install.sh | bash
cdev run --help | grep -q -- --mount-opencode || curl -fsSL https://raw.githubusercontent.com/luongnv89/docker-dev/main/install.sh | bash
```

Then launch a **kept** container (no `--rm`) with a unique name, print the
attach command, and exec a shell into it for the pane (adapt to whichever
pane skill is active — this is the plain-docker equivalent `cdev run`
performs):

```bash
# Unique name, e.g. opencode-dev-<project>-$(date +%s)
docker run -d --name <container-name> --label opencode-docker-dev=1 \
  -v "$PROJECT_DIR:/workspace" \
  -v "$HOME/.config/opencode:/root/.config/opencode" \
  [-v "$HOME/.claude:/root/.claude:ro" -v "$HOME/.agents:/root/.agents:ro"] \
  [-v "$HOME/.gitconfig:/root/.gitconfig:ro"] \
  -w /workspace \
  ghcr.io/luongnv89/u2604dev:latest sleep infinity
```

As soon as that returns, surface this copy-paste block to the user (do not
wait until OpenCode finishes):

```bash
docker exec -it <container-name> zsh
```

Drive the pane with a second `docker exec -it <container-name> zsh` (or
`opencode` inside that shell). The keep-alive `sleep infinity` is PID 1, so
closing OpenCode does not tear the container down.

**This is the complete mount list — the four `-v` lines above (project,
opencode config, optional skills, optional git identity) plus nothing else.**
Do not extend it with `-v ~/.ssh:...` or `-e GH_TOKEN=...` even under
pressure ("just this once," "the user explicitly approved it in chat") — the
credential redline in `references/mounts-and-credentials.md` applies
identically here, and Claude Code's own permission classifier independently
blocks both of these when attempted directly. If a task genuinely needs
push/publish access, stop and hand it back to the user as their own,
separate, manually-run command — don't try to satisfy it by editing this
template.

## Gotcha 1 — wait for the full ready screen before sending

OpenCode's TUI takes a few seconds to render. Sending text too early has two
failure modes, both observed directly:

- The send is silently dropped — the input never reaches the text box.
- A **second** premature send exits OpenCode back to the shell entirely
  (observed twice in testing: the app just quits, no error).

Before the first send, read the pane and confirm **both** are visible:

- The `Ask anything...` placeholder text
- The build/provider status line at the bottom (e.g. `Build · <model> ·
  OpenCode Zen`)

If only a partial render shows (e.g. just the ASCII logo), wait and re-read —
don't send yet. After launching `opencode`, a `sleep 6`–`8` before the first
read-and-check is a reasonable starting point; always verify by reading the
pane rather than trusting a fixed sleep alone.

## Gotcha 2 — verify the send landed

After sending, re-read the pane and confirm the state actually changed (a
spinner, "esc interrupt", or a permission dialog) rather than assuming one
send always works. If the screen still shows the idle placeholder, the send
was dropped — resend once. Do not send a second time reflexively without
checking first; that's what triggers the exit-back-to-shell failure mode
above.

## Gotcha 3 — permission dialogs

The first time OpenCode touches a new mounted path it hasn't seen yet (e.g. a
scratch directory), it shows an in-TUI dialog:

```
△ Permission required
  ← Access external directory /scratch

  Allow once   Allow always   Reject
```

This is expected and benign for any path this skill's own setup mounted.
Detect it by reading the pane for `Permission required`, confirm `Allow once`
is the highlighted option (read with ANSI formatting if the pane-management
skill supports it), and confirm it. If a dialog appears for a path you did
**not** intentionally mount, stop and check the mount list — don't reflexively
approve.

## Gotcha 4 — multi-line or long tasks

Don't pipe multi-line text directly into the TUI input. Write the task to a
file inside a mounted scratch directory — **not** inside `/workspace`, which
would dirty the project's git status with a stray file — and send a short
instruction instead: `Read the file /scratch/task.txt and follow its
instructions exactly.`

## Gotcha 5 — completion detection doesn't cross the container boundary

Host-level agent/process detection (e.g. herdr's agent-status tracking) sees
the container's shell process, not what's running inside it — OpenCode inside
a container reads as an unrecognized process, not `idle`/`working`/`done`.
Detect completion by:

1. Polling the pane transcript directly on a timer, and/or
2. Asking the task prompt to print a unique sentinel string as its last line
   when finished (e.g. `After finishing, print exactly: TASK_DONE_<random>`),
   and matching for that string in the transcript.

Don't rely on any external "agent is idle" signal for work happening inside
the container — it won't fire.

## Cleanup

**Keep-by-default** — same as one-shot. Do not `docker rm` unless the user
confirms. Closing the pane or exiting OpenCode leaves the container
running (`sleep infinity`). After the task, ask:

> Container `<container-name>` is still running. Attach with
> `docker exec -it <container-name> zsh`. Remove it for cleanup?

If they say yes: `docker rm -f <container-name>` and close the pane per the
pane-management skill's own teardown. If they say no, leave it and repeat
the attach command.
