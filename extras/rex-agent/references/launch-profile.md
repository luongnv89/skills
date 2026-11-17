# Inherited launch profile — rex-agent

Read this before a spawn wave or a HANDOFF, or when the user wants a worker that differs from the main agent.

The **inherited launch profile** is the main agent's harness kind, model, thinking level, and setup flags. The main agent is the one running this skill. Every worker, including a HANDOFF successor, starts on this profile unless the user names something else. `scripts/launch_profile.py` resolves the profile and, with `--start`, applies it.

## Resolve it once per spawn wave

```bash
python3 "$here/launch_profile.py" --main-model "$main_model" --main-thinking "$main_thinking"
```

Set `main_model` and `main_thinking` from your own runtime: the exact model ID and the thinking or effort level your harness gives you. If you cannot read one, leave it empty rather than guess. On Claude Code, leave `main_thinking` empty: the script reads `CLAUDE_EFFORT` itself when it runs inside the root block (`$REX_BLOCK` equals the root).

The command writes one summary line to stderr and the profile JSON to stdout. Relay the summary to the user before the first start, including any `⚠` or `warning:` line. Each `--start` resolves the profile again for that worker. If the user changes your model or thinking level mid-run, update `main_model` and `main_thinking` before the next wave.

```text
Launch profile: claude (inherited from main) · model claude-opus-5-5 (self-report) · thinking max (env CLAUDE_EFFORT) · flags none (root argv)
```

## Where each field comes from

| Field | First source that yields a value |
|---|---|
| kind | `--kind` (user named one) → the root record's `app` (`claude-code` → `claude`) → the root process's `argv0` or `script` |
| model | `--model` or a native model flag → `--main-model` → root argv → UNKNOWN |
| thinking | `--thinking` or a native flag → `--main-thinking` → `CLAUDE_EFFORT` (claude, inside root) → root argv → UNKNOWN |
| setup flags | root argv, filtered through the kind's allowlist |
| cwd and config | `--cwd "$project_dir"`; the worker loads the same settings, MCP config, context files, and skills as main |

The main agent's own report ranks above argv because argv only records launch-time values. A live check found the main agent at effort `max` while its config default was `medium`, so a worker started bare would have run at `medium`.

**Root argv** is read from the kernel, never from Rex, because Rex's `process` method reports only `argv0`. The source is `/proc/<pid>/cmdline` on Linux and `sysctl KERN_PROCARGS2` on macOS, for the root block's foreground pid. It is read only when `rex whoami` reports a local `unix:` endpoint: with a remote server the pid belongs to another machine.

**UNKNOWN applies only to model and thinking.** The worker starts on its config default, and the summary says `model UNKNOWN (worker uses its config default)`. Setup flags are security-relevant: unreadable root argv, or a remote server, fails closed instead of being labeled UNKNOWN. Only `--without flags` permits that reduced-inheritance launch.

## The kind gate

A worker inherits model, thinking level, and flags only when its kind equals the main agent's **detected** kind. If the user names a different kind, the worker gets that CLI's config defaults plus whatever the user named. A Claude model ID or effort level means nothing to `pi` or `codex`, so `--main-model` and `--main-thinking` are ignored across kinds.

If the main kind is unreadable, `--kind` selects the worker but establishes no inheritance relationship. The launch is refused unless `--without flags` explicitly selects reduced inheritance; then only worker-specific `--model`, `--thinking`, or native flags apply.

## Per-kind flag names

Checked against the `--help` of claude 2.1.301, pi 1.3.0, and codex 0.162.1. A kind not in this table (gemini, opencode) inherits its kind only: pass its native flags after `--`, and never invent one.

| Kind | Model | Thinking | Setup flags carried from root argv |
|---|---|---|---|
| `claude` | `--model` | `--effort` | `--permission-mode`, skip-permissions switches, `--add-dir`, `--mcp-config`, `--strict-mcp-config`, `--settings`, `--setting-sources`, `--plugin-dir`, `--plugin-url`, `--agent`, `--agents`, tool allow/deny lists, system-prompt flags, `--fallback-model`, `--betas`, `--autocompact`, `--chrome`, `--ide`, `--bare`, `--safe-mode`, `--restricted` |
| `pi` | `--model` | `--thinking` | `--provider`, `--models`, tool, extension, skill, prompt-template and theme flags, system-prompt flags, `--session-dir`, `--no-session`, `--no-context-files`, `--approve`, `--offline`, advisor flags |
| `codex` | `--model` / `-m` | `--config model_reasoning_effort="…"` | `-c` overrides, `--profile`, `--sandbox`, `--ask-for-approval`, bypass switches, `--enable`, `--disable`, `--oss`, `--local-provider`, `--cd`, `--add-dir`, `--search` |

`--model` and `--thinking` hold a user-named value and map to the flag in this table; they are never translated between kinds. To support another kind, add a table to `launch_profile.py` after reading that CLI's `--help`.

## What never carries over

- **Session and one-shot flags:** resume, continue, session IDs, fork, print mode and output format, session name, worktree, debug.
- **Positionals:** an initial prompt, a subcommand such as `codex resume`, and anything after `--`.
- **Credentials:** `pi --api-key` is dropped. Setup-flag values are never printed, because inline settings or MCP JSON can carry secrets, and they never pass through a shell prompt or its history: `--start` hands them to the block as separate argv words.
- **Unrecognized flags:** dropped and named under `dropped`, so a flag added by a newer CLI shows up in the summary instead of being passed along silently.
- **Environment:** the worker gets the user's interactive shell environment plus `REX_AGENT_ROLE=<name>`. Rex sets the worker's own `REX_SESSION` and `REX_BLOCK`. Session IDs and tokens stay in the main agent's process.

## Permission bypass is inherited and disclosed

The main agent's permission settings are part of its setup. `--dangerously-skip-permissions`, `--permission-mode bypassPermissions`, codex `--sandbox danger-full-access` or `--ask-for-approval never`, and pi `--approve` all carry over. This gives a worker no access the orchestrator lacks, since the orchestrator can already type into any worker block. Without them, every worker would stop at a permission dialog that Rule 7 says only the human may answer.

Carrying them over is never silent. The summary prints `⚠ permission bypass inherited from main: …`, and that line must reach the user before the first start. If the user wants workers without it, pass `--without bypass`. `--without flags` drops every inherited setup flag but keeps a model and thinking level recoverable from self-report, environment, or readable argv. A permission posture set through shared settings, such as `defaultMode`, reaches the worker through its config and is not affected by these options.

## When a start fails

- **Exit 1, program exited:** the CLI rejected a flag or crashed. The message prints the block's last screen lines; fix or `--without` the offending field, and start again. The failed block stays open (`--keep-open`) and is an orphan: ask before closing it.
- **Exit 1, timeout:** no `idle` record arrived in time. A dialog that reports nothing (a login, an update prompt) or a CLI without program status looks like this. Capture the block; never type into it.
- **Exit 1, error at boot:** the worker reported `error` (for example an invalid API key); the message carries its text. Fix the cause before starting again.
- **Exit 3:** the worker reported `blocked` at boot (trust, auth, question). Focus it and let the human answer.
- **Exit 1 before any split:** the profile failed to resolve. Nothing was created.
