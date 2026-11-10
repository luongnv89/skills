# Harness adapters

Read in Step 3 (to explain each choice) and Step 5 (to explain the command). The script
(`scripts/agent_profile.py`, `ADAPTERS` and `build()`) is the source of truth; this file
explains it.

**Status.** `verified` means a real headless run through this skill succeeded on
2026-11-10 with the version shown. `untested` means the flags come from the CLI's
published docs. Before every run of an untested adapter, the script checks each flag and
permission value it uses against `<cli> --help` as a whole token. It refuses to run when
one is missing.

| Harness  | CLI        | Status (version)        | Harness profiles                    | Models from                         | Thinking                                   |
| -------- | ---------- | ----------------------- | ----------------------------------- | ----------------------------------- | ------------------------------------------ |
| claude   | `claude`   | verified (2.1.322)      | mcc profiles (`mcc list --json`), always with `default` (`~/.claude`) | the aliases `claude --help` names, plus each mcc profile's model; other aliases and full ids may be typed | `--effort` levels parsed from `--help`; which levels a model honours is not reported |
| pi       | `pi`       | verified (1.3.0)        | none                                | `pi --list-models` (with provider and thinking support) | `--thinking` levels from `--help`, only for models marked thinking; a model's maximum is not reported |
| opencode | `opencode` | verified (2.2.6)        | none                                | `opencode models`                   | none listed; type `<listed model>#<variant>` |
| codex    | `codex`    | untested                | `[profiles.*]` in `~/.codex/config.toml` | none: type the id               | minimal, low, medium, high, xhigh (docs)   |
| droid    | `droid`    | untested                | none                                | none: type the id (`droid exec --help` lists them) | off, low, medium, high (docs; model-dependent) |
| devin    | `devin`    | untested                | none                                | `devin models list --format json`   | none                                       |
| grok     | `grok`     | untested                | none                                | none: type the id                   | none (set in `~/.grok/config.toml`)        |
| gemini   | `gemini`   | untested                | none                                | none: type the id                   | none                                       |

When a list probe fails (`models_complete: null`, shown as `LIST FAILED`), nothing can be
saved for that harness until a later detect lists the models. A failure never unlocks
typed ids.

## Permission modes

| Mode    | Meaning                              | claude                                | codex                          | droid         | devin                            | grok      | gemini                      |
| ------- | ------------------------------------ | ------------------------------------- | ------------------------------ | ------------- | -------------------------------- | --------- | --------------------------- |
| `ask`   | read-only in practice: anything not pre-approved is refused, since nobody answers prompts headless | `--permission-mode dontAsk` | `--sandbox read-only` | (default) | `--permission-mode normal` | (default) | (default) |
| `edits` | file edits allowed, commands refused | `--permission-mode acceptEdits`       | `--sandbox workspace-write`    | `--auto low`  | `--permission-mode accept-edits` | n/a       | `--approval-mode auto_edit` |
| `full`  | any command without asking           | `--permission-mode bypassPermissions` | `--sandbox danger-full-access` | `--auto high` | `--permission-mode dangerous`    | `--yolo`  | `--approval-mode yolo`      |

- **pi** and **opencode** offer only `full`. opencode's `run` allows tools by default:
  a profile without `--auto` still ran shell commands and wrote files, and
  `OPENCODE_CONFIG_CONTENT` permission rules were ignored (tested with 2.2.6). pi has no
  permission prompts, and its `--tools`/`--exclude-tools` flags denied even reads in
  testing (1.3.0). opencode `full` adds `--auto`.
- claude `ask` was verified: a write task under `dontAsk` created no file. Allow rules in
  the profile's own `settings.json` still apply.
- `full` always needs the user's own yes for each run (SKILL.md rule 2).

## Headless command per harness

The task is a file or stdin wherever the CLI allows it, so a task that starts with `-`
or is very long works. grok and gemini take it as an argument: a task over 100,000 bytes
is refused, and one starting with `-` gets a `Task:` line in front.

| Harness  | Command                                                                                     |
| -------- | ------------------------------------------------------------------------------------------- |
| claude   | `mcc exec <profile> -- claude -p --model M [--effort T] <perm> < file`; without mcc, only the `default` profile, run as `claude …` with `CLAUDE_CONFIG_DIR` removed |
| pi       | `pi -p [--provider P] --model M [--thinking T] -- @file`                                    |
| opencode | `opencode run --model M --auto --file file -- "Follow the instructions in the attached file."` |
| codex    | `codex exec --cd DIR --model M [--profile P] [--config model_reasoning_effort=T] <perm> [--skip-git-repo-check] - < file` (the last flag only outside a git repo) |
| droid    | `droid exec --cwd DIR --model M [--reasoning-effort T] [perm] --file file`                  |
| devin    | `devin --print --prompt-file file --model M --respect-workspace-trust false <perm>`         |
| grok     | `grok --model M [--yolo] -p <task>`                                                         |
| gemini   | `gemini --model M [perm] --prompt=<task>`                                                   |

Every run also sets `PWD` to the working directory: opencode takes its directory from
`$PWD`, and without it a run wrote its file where the script was started.

## Notes

- **mcc:** a Claude Code profile is a separate config directory with its own login.
  `mcc exec <profile> -- <command>` runs the command with that profile's
  `CLAUDE_CONFIG_DIR`. Running through `mcc exec default` keeps a delegated run on
  `~/.claude` even when the main agent itself runs under another mcc profile.
- **opencode:** `opencode models` can fail once while its plugins start; the script
  retries once, then reports the error.
- **pi:** the same model id can exist under several providers; the profile keeps the
  provider.

Sources for the untested adapters: Codex `codex exec` docs (developers.openai.com/codex),
Factory Droid CLI reference (docs.factory.com/droid-cli/cli-reference), Devin CLI commands
(docs.devin.ai/cli/reference/commands), Grok Build configuration guide
(github.com/xai-org/grok-build), Gemini CLI README (github.com/google-gemini/gemini-cli).
Re-verify an adapter by installing the CLI and running a real task through this skill,
then mark it `verified` here and in `ADAPTERS`.
