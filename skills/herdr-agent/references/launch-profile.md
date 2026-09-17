# Inherited launch profile — herdr-agent

Read this before a spawn wave or a HANDOFF, or when the user wants a worker that differs from the main agent.

The **inherited launch profile** is the main agent's harness kind, model, thinking level and setup flags. The main agent is the one running this skill. Every worker, including a HANDOFF successor, starts on this profile unless the user names something else. `scripts/launch_profile.py` resolves the profile and applies it.

## Resolve it once per spawn wave

```bash
python3 "$here/launch_profile.py" --root-pane "$root_pane" \
  --main-model "$main_model" --main-thinking "$main_thinking"
```

Set `main_model` and `main_thinking` from your own runtime: the exact model ID and the thinking or effort level your harness gives you. If you cannot read one, leave it empty rather than guess. On Claude Code, leave `main_thinking` empty: the script reads `CLAUDE_EFFORT` itself when it runs inside the root pane.

The command writes one summary line to stderr and the profile JSON to stdout. Relay the summary to the user before the first split, including any `⚠` or `warning:` line. Each worker is then started with `--start` (see `spawn_sub` in `herdr-recipes.md`), which queries Herdr and the environment again for that worker. If the user changes your model or thinking level mid-run, update `main_model` and `main_thinking` before the next wave.

```text
Launch profile: claude (inherited from main) · model claude-opus-5[1m] (self-report) · thinking max (env CLAUDE_EFFORT) · flags none (root argv)
```

## Where each field comes from

| Field | First source that yields a value |
|---|---|
| kind | `--kind` (user named one) → main agent's kind from `herdr agent get <root_pane>` |
| model | `--model` or a native model flag (user named one) → `--main-model` → root pane argv → UNKNOWN |
| thinking | `--thinking` or a native flag → `--main-thinking` → `CLAUDE_EFFORT` (claude, inside root pane) → root argv → UNKNOWN |
| setup flags | root pane argv from `herdr pane process-info`, filtered through the kind's allowlist |
| cwd and config | `project_dir`; the worker loads the same settings, MCP config, context files and skills as main |

The main agent's own report ranks above argv because argv only records values from launch time, and the harness config can differ from both. A live check found the main agent running at effort `max` while `~/.claude/settings.json` said `medium`, so a worker started with no flags would have run at `medium`.

**UNKNOWN is not a failure.** The worker starts on its config default, and the summary says `model UNKNOWN (worker uses its config default)`. Report it and never guess a value.

## The kind gate

A worker inherits model, thinking level and flags only when its kind equals the main agent's kind. If the user names a different kind, the worker gets that CLI's config defaults plus whatever the user named. A Claude model ID or effort level means nothing to `pi` or `codex`, so `--main-model` and `--main-thinking` are ignored across kinds.

## Per-kind flag names

Checked against the `--help` output of claude 2.1.274, pi and codex 0.153.4. A kind that is not in this table inherits its kind only: pass its native flags after `--`, and never invent one.

| Kind | Model | Thinking | Setup flags carried from root argv |
|---|---|---|---|
| `claude` | `--model` | `--effort` | `--permission-mode`, skip-permissions switches, `--add-dir`, `--mcp-config`, `--strict-mcp-config`, `--settings`, `--setting-sources`, `--plugin-dir`, `--plugin-url`, `--agent`, `--agents`, tool allow/deny lists, system-prompt flags, `--fallback-model`, `--betas`, `--autocompact`, `--chrome`, `--ide`, `--bare`, `--safe-mode`, `--restricted` |
| `pi` | `--model` | `--thinking` | `--provider`, `--models`, tool, extension, skill, prompt-template and theme flags, system-prompt flags, `--session-dir`, `--no-session`, `--no-context-files`, `--approve`, `--offline`, advisor flags |
| `codex` | `--model` / `-m` | `--config model_reasoning_effort="…"` | `-c` overrides, `--profile`, `--sandbox`, `--ask-for-approval`, bypass switches, `--enable`, `--disable`, `--oss`, `--local-provider`, `--cd`, `--add-dir`, `--search` |

`--model` and `--thinking` hold a user-named value and are mapped to the flag in this table. They are never translated between kinds. To support another kind, add a table to `launch_profile.py` after reading that CLI's `--help`.

## What never carries over

- **Session and one-shot flags:** resume, continue, session IDs, fork, print mode and output format, session name, worktree, debug.
- **Positionals:** an initial prompt, a subcommand such as `codex resume`, and anything after `--`.
- **Credentials:** `pi --api-key` is dropped. Setup-flag values are never printed, because inline settings or MCP JSON can carry secrets.
- **Unrecognized flags:** dropped, and named under `dropped`, so a flag added by a newer CLI shows up in the summary instead of being passed along silently.
- **Environment:** the worker pane gets only `HERDR_ROLE`. Session IDs and tokens stay in the main agent's process.

## Permission bypass is inherited and disclosed

The main agent's permission settings are part of its setup. `--dangerously-skip-permissions`, `--permission-mode bypassPermissions`, codex `--sandbox danger-full-access` or `--ask-for-approval never`, and pi `--approve` all carry over. This gives a worker no access the orchestrator lacks, since the orchestrator can already run commands in any worker pane. Without them, every worker would stop at a permission dialog that Rule 7 says only the human may answer.

Carrying them over is never silent. The summary prints `⚠ permission bypass inherited from main: …`, and that line must reach the user before the first split. If the user wants workers without it, pass `--without bypass`. To drop every inherited setup flag but keep the model and thinking level, pass `--without flags`. A permission posture set through shared settings, such as `defaultMode`, reaches the worker through its config and is not affected by these options.

## When a start fails

A flag the CLI rejects makes the agent exit immediately. `herdr agent start` then waits out its whole timeout before it returns an error. `launch_profile.py` reports the failure and names the pane. Read the CLI's own message with `herdr pane read <pane> --source recent-unwrapped --lines 20`, fix or `--without` the offending field, and start again.
