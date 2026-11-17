# Profiles, run folders, errors

Read in Steps 2, 3 and 6.

## Storage

| Scope   | File                                                     | Wins when names clash |
| ------- | -------------------------------------------------------- | --------------------- |
| global  | `$XDG_CONFIG_HOME/agent-profile/profiles.json` (default `~/.config/agent-profile/profiles.json`) | no |
| project | `.agent-profiles.json` at the git root (or the current directory outside git) | yes: `list` marks it "overrides global" |

Both files have the shape `{"version": 1, "profiles": {"<name>": {…}}}`. A save or delete
holds a lock (one file per profile file under `~/.cache/agent-profile/locks/`, never in the
repo) and writes a unique temp file, then renames it. Neither file ever holds a credential.

A project file comes with the repo, so it is checked on load. An entry with a bad name, an
unknown harness, no model, a bad permission mode, or a model, thinking, provider or
harness profile value that starts with `-` or holds spaces is skipped with a warning
(`save` refuses the same values). At
`command`/`run` time every profile is checked again against what is installed. A model
no longer in a complete list, a harness profile or thinking level the harness does not
report, or a missing harness stops the run. Step 5's notes name a project profile's file so the user can check it.
Most teams keep `.agent-profiles.json` out of git, since mcc and Codex profile names are
local to one machine.

## Profile fields

| Field             | Example              | Notes                                                         |
| ----------------- | -------------------- | ------------------------------------------------------------- |
| `harness`         | `claude`             | an adapter id from `harnesses.md`                             |
| `harness_profile` | `twmaisie`           | must have been detected when saved; claude defaults to `default` |
| `model`           | `sonnet`             | as detected, typed, or `<listed>#<variant>` for opencode     |
| `provider`        | `opencode-cli`       | pi only                                                       |
| `variant`         | `high`               | opencode only, when the model has a `#variant`                |
| `typed_model`     | `false`              | `true` when the id was typed, not detected                    |
| `thinking`        | `low`                | optional; absent means the harness default                    |
| `permissions`     | `edits`              | `ask`, `edits` or `full`                                      |
| `harness_version` | `2.1.322`            | the version detected when saved; a later change shows in Step 5's notes |
| `created`, `updated` | ISO 8601 UTC      |                                                               |

Names: 1–40 characters, lowercase letters, digits and hyphens, starting with a letter or
digit.

**Brief** (one line per profile in `list`):
`cc-sonnet — claude/twmaisie · sonnet · thinking low · permissions edits · global`

## Run folder

`$XDG_CACHE_HOME/agent-profile/runs/<YYYYMMDD-HHMMSS>-<profile>-<6 hex>/` (default under
`~/.cache`). The random suffix keeps parallel runs of one profile apart.

| File          | Holds                                                     |
| ------------- | --------------------------------------------------------- |
| `prompt.md`   | the task, copied at run time                              |
| `command.json`| profile brief, cwd, argv, stdin, removed env vars, notes, timeout |
| `output.log`  | stdout and stderr of the harness                          |
| `runner.pid`, `child.pid` | the supervising script and the harness, each as `<pid> <start time>`. On Linux a pid is trusted only when its start time matches the live process (so `stop` never signals a reused pid); pids 0, 1 and negative values are never trusted. Without `/proc` (macOS) the start time cannot be checked |
| `result.json` | `status`, `exit_code`, `duration_s`, `finished`           |

| `status` / state  | Meaning                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `done`            | the harness exited 0                                               |
| `failed`          | the harness exited non-zero                                        |
| `timeout`         | the timeout passed; the harness's process group got SIGTERM, then SIGKILL after 10 s |
| `interrupted`     | the script got SIGTERM, SIGINT or SIGHUP (for example the shell tool's timeout) and stopped the harness |
| `stopped`         | `stop` ended it                                                    |
| `failed-to-start` | the harness could not be started                                   |
| `running`         | the runner is alive (no result yet)                                |
| `orphaned`        | the runner died and the harness still runs: use `stop`             |
| `lost`            | both are gone and no result was written                            |

Stopping a run (timeout, interrupt, `stop`) signals the harness's process group and every
descendant found through `/proc`, so a child that started its own session (opencode's
private server does) is ended too. A process that left the tree (re-parented to init)
cannot be found; opencode's shared background service is avoided with `--standalone` for
that reason. A refused `run` (bad profile, untested adapter) removes the run folder it
created.

## Errors

The script prints `agent_profile: error: <what, which input, how to fix>` on stderr.
Exit 2 is bad input, exit 1 is a runtime failure.

| Message starts with                     | Do                                                            |
| --------------------------------------- | ------------------------------------------------------------- |
| `no profile named`                      | show the saved names it lists; offer Step 3                   |
| `harness … is not installed`            | the CLI was removed since the profile was saved: offer another profile or a new one |
| `… could not list its models`           | show the probe error; ask the user to fix the harness, then detect again |
| `model … is not in … list` / `is no longer in` | re-ask the model from the detected list (or edit the profile) |
| `… pass --typed-model`                  | confirm with the user that they typed this id, then re-run with the flag |
| `thinking … is not valid` / `does not support thinking` | re-ask the thinking question from the detected levels |
| `a … profile named … exists`            | ask replace or rename                                         |
| `untested adapter: … does not mention`  | stop; show the message; suggest updating the adapter (rule 7) |
| `… no longer mentions …, which the '<mode>' mode needs` | a verified CLI changed its flags: stop, show the message, suggest re-verifying the adapter (rule 7) |
| `cannot check …'s flags`                | its help timed out or could not run: stop; ask the user to check the CLI, then retry |
| `… runs with full permissions`          | ask the full-permission question (Step 5), then pass `--confirm-full` |
| `the task is over … bytes`              | shorten the task, or use a harness that reads a file          |
| `… is not valid JSON` / `does not hold a profiles object` | show the file path; ask the user to fix or move it |
| `warning: skipping profile`             | mention the skipped entry and its file; the rest still work   |
| `run is not running`                    | nothing to stop; show `status`                                |

## Edge cases

- **No harness installed:** `detect` shows every adapter as not installed. Stop, and
  name the CLIs the skill supports.
- **A saved profile whose harness version changed:** run as usual; Step 5's notes show
  the old and new version.
- **Background run whose runner died:** `status` says `orphaned`; offer `stop`. With
  both gone and no result, `lost`: show the log tail and say the result is unknown.
- **The user asks to run without confirming:** Step 5 still shows the command; the
  confirmation can be one word, but it cannot be skipped.
- **Several tasks at once:** run each in its own worktree in Background mode; each run
  gets its own folder.
- **Codex outside a git repo:** the script adds `--skip-git-repo-check`, which must
  appear in `codex exec --help`.
