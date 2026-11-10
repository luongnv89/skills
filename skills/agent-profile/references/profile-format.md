# Profiles, run folders, errors

Read in Steps 2, 3 and 6.

## Storage

| Scope   | File                                                     | Wins when names clash |
| ------- | -------------------------------------------------------- | --------------------- |
| global  | `$XDG_CONFIG_HOME/agent-profile/profiles.json` (default `~/.config/agent-profile/profiles.json`) | no |
| project | `.agent-profiles.json` at the git root (or the current directory outside git) | yes: `list` marks it "overrides global" |

Both files have the shape `{"version": 1, "profiles": {"<name>": {…}}}`. Writes are
atomic (temp file, then rename). Neither file ever holds a credential, so a project file
may be committed; it names mcc or Codex profiles, which are local to one machine, so most
teams keep it in `.gitignore`.

## Profile fields

| Field             | Example              | Notes                                                         |
| ----------------- | -------------------- | ------------------------------------------------------------- |
| `harness`         | `claude`             | an adapter id from `harnesses.md`                             |
| `harness_profile` | `twmaisie`           | optional; must have been detected when saved                  |
| `model`           | `sonnet`             | as detected, or typed                                         |
| `provider`        | `opencode-cli`       | pi only                                                       |
| `typed_model`     | `false`              | `true` when the id was typed, not detected                    |
| `thinking`        | `low`                | optional; absent means the harness default                    |
| `permissions`     | `edits`              | `ask`, `edits` or `full`                                      |
| `harness_version` | `2.1.322 (Claude Code)` | the version detected when saved                            |
| `created`, `updated` | ISO 8601 UTC      |                                                               |

Names: 1–40 characters, lowercase letters, digits and hyphens, starting with a letter or
digit.

**Brief** (one line per profile in `list`):
`cc-sonnet — claude/twmaisie · sonnet · thinking low · permissions edits · global`

## Run folder

`$XDG_CACHE_HOME/agent-profile/runs/<YYYYMMDD-HHMMSS>-<profile>/` (default under
`~/.cache`):

| File          | Holds                                                     |
| ------------- | --------------------------------------------------------- |
| `prompt.md`   | the task, copied at run time                              |
| `command.json`| profile brief, cwd, argv, stdin, notes                    |
| `output.log`  | stdout and stderr of the harness                          |
| `child.pid`, `runner.pid` | the harness and, in background mode, the runner |
| `result.json` | `status` (done, failed, timeout, failed-to-start), `exit_code`, `duration_s`, `finished` |

A timeout sends SIGTERM to the harness's process group, then SIGKILL after 10 s.

## Errors

The script prints `agent_profile: error: <what, which input, how to fix>` on stderr.
Exit 2 is bad input, exit 1 is a runtime failure.

| Message starts with                     | Do                                                            |
| --------------------------------------- | ------------------------------------------------------------- |
| `no profile named`                      | show the saved names it lists; offer Step 3                   |
| `harness … is not installed`            | the CLI was removed since the profile was saved: offer another profile or a new one |
| `model … is not in … list`              | the harness lists models and this one is not there: re-ask the model from the list |
| `… pass --typed-model`                  | confirm with the user that they typed this id, then re-run with the flag |
| `thinking … is not valid` / `does not support thinking` | re-ask the thinking question from the detected levels |
| `a … profile named … exists`            | ask replace or rename                                         |
| `untested adapter: … does not mention`  | stop; show the message; suggest updating the adapter (rule 7) |
| `… runs with full permissions`          | ask the full-permission question (Step 5), then pass `--confirm-full` |
| `… is not valid JSON`                   | show the file path; ask the user to fix or move it            |

## Edge cases

- **No harness installed:** `detect` shows every adapter as not installed. Stop, and
  name the CLIs the skill supports.
- **The model list fails** (`models_error`): show the error. Offer `Type a model id` only
  when `models_complete` is false; otherwise ask the user to fix the harness first.
- **A saved profile whose harness version changed:** run as usual; mention the old and
  new version in Step 5's notes.
- **Background run with no `result.json` and a dead runner:** `status` reports `lost`;
  show the log tail and say the result is unknown.
- **The user asks to run without confirming:** Step 5 still shows the command; the
  confirmation can be one word, but it cannot be skipped.
- **Several tasks at once:** run them one at a time, or each in its own worktree in
  Background mode, one run folder each.
