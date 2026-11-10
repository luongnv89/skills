# Harness adapters

Read in Step 3 (to explain each choice) and Step 5 (to explain the command). The script
(`scripts/agent_profile.py`, `ADAPTERS` and `build()`) is the source of truth; this file
explains it.

**Status.** `verified` means a real headless run through this skill succeeded on
2026-11-10 with the version shown. `untested` means the flags come from the CLI's
published docs. Before every run of an untested adapter, the script checks each flag it
uses against `<cli> --help` and refuses to run when one is missing.

| Harness  | CLI        | Status (version)        | Harness profiles                    | Models from                         | Thinking                                   |
| -------- | ---------- | ----------------------- | ----------------------------------- | ----------------------------------- | ------------------------------------------ |
| claude   | `claude`   | verified (2.1.322)      | mcc profiles (`mcc list --json`)    | aliases in `claude --help`, plus each mcc profile's model; any full model id may be typed | `--effort` levels parsed from `--help`     |
| pi       | `pi`       | verified (1.3.0)        | none                                | `pi --list-models` (with provider and thinking support) | `--thinking` levels from `--help`, only for models marked thinking |
| opencode | `opencode` | verified (2.2.6)        | none                                | `opencode models`                   | none listed; a `#variant` suffix may be typed into the model id |
| codex    | `codex`    | untested                | `[profiles.*]` in `~/.codex/config.toml` | none: type the id               | minimal, low, medium, high, xhigh (docs)   |
| droid    | `droid`    | untested                | none                                | none: type the id                   | off, low, medium, high (docs; model-dependent) |
| devin    | `devin`    | untested                | none                                | `devin models list --format json`   | none                                       |
| grok     | `grok`     | untested                | none                                | none: type the id                   | none (set in `~/.grok/config.toml`)        |
| gemini   | `gemini`   | untested                | none                                | none: type the id                   | none                                       |

## Permission modes

| Mode    | Meaning                                         | claude                              | pi            | opencode | codex                       | droid         | devin                      | grok      | gemini                   |
| ------- | ----------------------------------------------- | ----------------------------------- | ------------- | -------- | --------------------------- | ------------- | -------------------------- | --------- | ------------------------ |
| `ask`   | the harness's default; tools that need approval are refused in headless mode | (default)  | n/a           | (default) | `--sandbox read-only`       | (default)     | `--permission-mode normal` | (default) | (default)                |
| `edits` | file edits allowed without asking               | `--permission-mode acceptEdits`     | n/a           | n/a      | `--sandbox workspace-write` | `--auto low`  | `--permission-mode accept-edits` | n/a | `--approval-mode auto_edit` |
| `full`  | any command without asking                      | `--permission-mode bypassPermissions` | always (pi has no permission prompts) | `--auto` | `--sandbox danger-full-access` | `--auto high` | `--permission-mode dangerous` | `--yolo` | `--approval-mode yolo` |

`full` always needs the user's own yes for each run (SKILL.md rule 2).

## Headless command per harness

`<task>` is the prompt file's text passed as one argument; `< file` is the prompt file on
stdin. Neither goes through a shell.

| Harness  | Command                                                                                     |
| -------- | ------------------------------------------------------------------------------------------- |
| claude   | `claude -p --model M [--effort T] [perm] < file`; with a harness profile other than `default`: `mcc exec <profile> -- claude …` |
| pi       | `pi -p [--provider P] --model M [--thinking T] <task>`                                     |
| opencode | `opencode run --model M [--auto] <task>`                                                    |
| codex    | `codex exec --cd DIR --model M [--profile P] [--config model_reasoning_effort=T] [perm] - < file` |
| droid    | `droid exec --cwd DIR --model M [--reasoning-effort T] [perm] --file FILE`                  |
| devin    | `devin --print --prompt-file FILE --model M --respect-workspace-trust false [perm]`         |
| grok     | `grok -p <task> --model M [--yolo]`                                                         |
| gemini   | `gemini --model M [perm] --prompt <task>`                                                   |

## Notes

- **mcc:** a Claude Code profile is a separate config directory with its own login.
  `mcc exec <profile> -- <command>` runs the command with that profile's
  `CLAUDE_CONFIG_DIR`. The `default` profile is `~/.claude`.
- **opencode:** `opencode models` can fail once while its plugins start; the script
  retries once, then reports the error instead of a list.
- **pi:** the same model id can exist under several providers; the profile keeps the
  provider.

Sources for the untested adapters: Codex `codex exec` docs (developers.openai.com/codex),
Factory Droid CLI reference (docs.factory.com/droid-cli/cli-reference), Devin CLI commands
(docs.devin.ai/cli/reference/commands), Grok Build configuration guide
(github.com/xai-org/grok-build), Gemini CLI README (github.com/google-gemini/gemini-cli).
Re-verify an adapter by installing the CLI and running a real task through this skill,
then mark it `verified` here and in `ADAPTERS`.
