# Troubleshooting

## "No provider available"

```
Error: No provider available
```

Two distinct causes — check in this order:

1. **`~/.config/opencode` wasn't mounted, or the selected provider needs auth.**
   `opencode2 auth list` shows configured integrations (`opencode providers
   list` on older installs). An empty list can be normal for anonymous/free
   models; authenticate only if the selected provider requires it.
2. **Transient provider-side hiccup.** A run can fail with this exact error and
   an immediate retry may succeed. Retry once before treating it as a real
   failure.

## Rate limit stalls (free-tier `OpenCode Zen`)

```
Error from provider (Console): Provider rate limit exceeded [retrying in 6m 48s attempt #9]
```

This is a provider/service limit, not a Docker image or local-profile
problem. A new container or `--fresh-profile` only resets local OpenCode state;
it does not reset provider-, model-, account-, network-, or service-side
quotas. In a recent reproduction, both a host-configured container and a
completely fresh profile stalled and recorded `provider.rate-limit` HTTP 429.
If a task stalls here for more than a couple of minutes:

- Stop the run instead of allowing an indefinite retry loop.
- Wait for the provider window to reset, or use `--model provider/model` with
  another authenticated/configured provider. Do not automatically rotate free
  models or claim that a fresh profile bypasses the limit.

## `cdev run --help` is missing `--mount-opencode` / `--preset`

The installed `cdev` predates those flags. Reinstall:

```bash
curl -fsSL https://raw.githubusercontent.com/luongnv89/docker-dev/main/install.sh | bash
```

This is safe to re-run — it clones/updates `~/.local/share/docker-dev` and
reinstalls the `~/.local/bin/cdev` shim. Only relevant to interactive mode
(`references/interactive-mode.md`); one-shot mode's `run_opencode.sh` uses
plain `docker run` and doesn't depend on `cdev` at all.

## Docker daemon unreachable after `preflight.sh` gives up

`preflight.sh` only knows how to auto-start Docker Desktop on macOS (`open -a
Docker`) and waits up to 60s. If it still fails:

- **macOS**: open Docker Desktop manually and watch it finish starting (cold
  start can exceed 60s on a loaded machine); re-run once `docker info`
  succeeds in a plain terminal.
- **Linux**: start the daemon per your distro (`systemctl start docker` or
  equivalent) — `preflight.sh` does not attempt this itself.

## `package.json`/lockfile pollution from building inside the container

If a task's job includes running the project's build/install inside the
container (a different architecture than the host — the images are
`linux/amd64` or `linux/arm64`, the host may be macOS), `npm install` can
promote a platform-specific optional dependency (e.g. `@esbuild/linux-arm64`)
into a **real, non-optional entry** in `package.json`, not just the lockfile.
This was observed directly: it would have shipped a Linux-only native binary
as a hard dependency for every consumer on every platform.

**Always diff `package.json` (not just the lockfile) after any container run
that touches dependencies**, before committing or pushing. If a
platform-specific package appears in `dependencies` that wasn't there before,
that's container-architecture leakage, not an intended change — revert it and
reproduce the intended change (e.g. a version bump) by hand or by reinstalling
on the host's native architecture instead.

## A broad `git add <dir>/` sweeps up backup or build artifacts

Observed directly: a task committed inside the container ran `git add
skills/opencode-sandbox/` and picked up `SKILL.md.bak` — a backup file a
prior tool run (`asm eval --fix`) had left on disk — into the commit. `git
add <dir>/` stages *everything* under that path, tracked intent or not; task
text asking for "the skill directory" doesn't distinguish source files from
incidental artifacts sitting next to them.

Before treating a commit made inside the container as done, check `git show
--stat HEAD` (or `git diff --cached` before the commit lands) for files the
task didn't actually intend to touch — `.bak`, `.orig`, `*.log`, build
output. If one snuck in, don't ship it: `git rm --cached <file>` and commit
the removal as a separate commit rather than amending (`git commit --amend`
rewrites a commit that may already be pushed or referenced elsewhere).

## A second run reuses a stale container `--name`

Both modes now pass an explicit `--name`. One-shot defaults to
`opencode-sandbox-<project>-<epoch>` (unique per invocation). Interactive must
do the same. If you reuse a name that is still in use — including a
**kept** container the user declined to remove — Docker fails: `docker:
Error response from daemon: Conflict. The container name "/..." is already
in use...`

`run_opencode.sh` detects this before `docker run` and prints a unique
`--name` (or `--exec-in` to reuse) as the first fix. `docker rm -f` is
mentioned last, and only if the user confirms destroying the kept
container.

## Leftover kept containers

Keep-by-default means `docker ps` will accumulate `opencode-sandbox-*`
containers (label `opencode-sandbox=1`). That is intended, not a leak to
silently fix. List them with:

```bash
docker ps -a --filter label=opencode-sandbox=1
```

Remove one only after the user confirms: `docker rm -f <name>`. `--rm` on
the `--exec-in` invocation restores auto-remove for that one run.

## Attach fails: container is not running

`docker exec` requires a running container. If the name exists in
`docker ps -a` but not `docker ps`:

```bash
docker start <container-name>
docker exec -it <container-name> zsh
```

`--exec-in` does the `docker start` itself before running OpenCode. Do not
create a second container, and do not `docker rm` the stopped one to "fix"
the attach.

## A pre-commit/test hook fails inside the container but passes standalone

If the project's test suite reads from the real user's config/state directory
(e.g. `~/.config/<app>`) rather than a fixture, and that directory exists on
the host with real accumulated data, tests can fail from **environment
contamination** — the real data overrides a bundled fixture the test expects.
This is a test-isolation bug in the target project, not something to fix by
mounting less: reproduce with an isolated `HOME` first to confirm

```bash
HOME=$(mktemp -d) <test command>
```

passes cleanly before concluding it's unrelated to your actual change, then
either run the real commit with that isolated `HOME`, or fix the test's
isolation if you own the project.
