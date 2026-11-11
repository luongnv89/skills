# Inherited launch profile — hc-agent

Read this before a spawn wave or a HANDOFF, or when the user wants a worker that differs from the main agent.

The **inherited launch profile** is the main agent's harness kind, model, thinking level, setup flags, and launch wrapper. The main agent is the one running this skill. Every worker, including a HANDOFF successor, starts on this profile unless the user names something else. `scripts/launch_profile.py` resolves the profile and, with `--start`, applies it.

## Resolve it once per spawn wave

```bash
python3 "$here/launch_profile.py" --main-model "$main_model" --main-thinking "$main_thinking"
```

Set `main_model` and `main_thinking` from your own runtime: the exact model ID and the thinking or effort level your harness gives you. If you cannot read one, leave it empty rather than guess. On Claude Code, leave `main_thinking` empty: the script reads `CLAUDE_EFFORT` itself when it runs inside the root terminal (`$HC_TERMINAL_ID` equals the root).

The command writes one summary line to stderr and the profile JSON to stdout. Relay the summary to the user before the first start, including any `⚠` or `warning:` line. Each `--start` resolves the profile again for that worker.

```text
Launch profile: claude (inherited from main) · model claude-opus-5-5 (self-report) · thinking max (env CLAUDE_EFFORT) · flags none (wrapper argv) · dropped 1 positional
```

## Where each field comes from

| Field | First source that yields a value |
|---|---|
| kind | `--kind` (user named one) → `hc get` `.status.app` (`claude-code` → `claude`) → the foreground process's argv0 |
| model | `--model` or a native model flag → `--main-model` → root argv → UNKNOWN |
| thinking | `--thinking` or a native flag → `--main-thinking` → `CLAUDE_EFFORT` (claude, inside root) → root argv → UNKNOWN |
| setup flags | root argv, filtered through the kind's allowlist |
| wrapper | the terminal's top-level `argv` up to and including `--` |
| folder | `--cwd "$project_dir"` (default: root's folder), applied by the `sh` folder wrapper |

**Root argv.** `hc get $HC_TERMINAL_ID` reports two argv lists. The top-level `argv` is what the terminal was started with, and may be a wrapper that picks the account, such as `["mcc", "run", "--", "<prompt>"]`. `foreground.argv` is the harness process itself, such as `["/…/claude", "<prompt>"]`.

- **Direct launch** (top-level argv0 is the harness, a node/bun script of it, or a shell the user typed into): the worker runs the foreground binary path (same install) plus flags parsed from the foreground argv.
- **Wrapper with `--`:** the worker keeps the wrapper prefix up to `--`, so it runs on the same account, and its flags come from the wrapper's own arguments after `--`. Flags the wrapper injects into the foreground process are not copied, because the wrapper adds them again.
- **Wrapper without `--`:** the profile aborts, because the wrapper's own arguments cannot be told from the harness's. `--without wrapper` launches the foreground binary directly and warns that the worker may use another account or config.

Wrapper handling was run live once, with `mcc run --` and Claude Code: the worker ran `mcc run -- --model <m> --effort <e>`, its harness process carried each flag once, and the root's prompt was not passed. Other wrappers, and a wrapper that injects a flag the worker also carries, are unverified. Name the wrapper under `Uncertainty:`.

**Positionals never carry over.** Both lists end with the root's own prompt (`/issue-resolver 469`). The strict parser drops every positional and names the count under `dropped`, so a worker is never handed the root's task.

**UNKNOWN applies only to model and thinking.** The worker starts on its config default, and the summary says `model UNKNOWN (worker uses its config default)`. Setup flags are security-relevant: unreadable root argv fails closed instead of being labeled UNKNOWN. Only `--without flags` permits that reduced-inheritance launch.

## The kind gate

A worker inherits model, thinking level, flags, and the wrapper only when its kind equals the main agent's **detected** kind. A worker of another kind starts as the bare binary name on PATH with that CLI's config defaults plus whatever the user named; `mcc run --` is a Claude Code wrapper and means nothing to `codex`.

If the main kind is unreadable, `--kind` selects the worker but establishes no inheritance relationship. The launch is refused unless `--without flags` explicitly selects reduced inheritance.

## Per-kind flag names

The same tables as herdr-agent and rex-agent, checked against the `--help` of claude 2.1.301, pi 1.3.0, and codex 0.162.1. A kind not in this table (gemini, opencode) inherits its kind only: pass its native flags after `--`, and never invent one.

| Kind | Model | Thinking | Setup flags carried from root argv |
|---|---|---|---|
| `claude` | `--model` | `--effort` | `--permission-mode`, skip-permissions switches, `--add-dir`, `--mcp-config`, `--strict-mcp-config`, `--settings`, `--setting-sources`, `--plugin-dir`, `--plugin-url`, `--agent`, `--agents`, tool allow/deny lists, system-prompt flags, `--fallback-model`, `--betas`, `--autocompact`, `--chrome`, `--ide`, `--bare`, `--safe-mode`, `--restricted` |
| `pi` | `--model` | `--thinking` | `--provider`, `--models`, tool, extension, skill, prompt-template and theme flags, system-prompt flags, `--session-dir`, `--no-session`, `--no-context-files`, `--approve`, `--offline`, advisor flags |
| `codex` | `--model` / `-m` | `--config model_reasoning_effort="…"` | `-c` overrides, `--profile`, `--sandbox`, `--ask-for-approval`, bypass switches, `--enable`, `--disable`, `--oss`, `--local-provider`, `--cd`, `--add-dir`, `--search` |

## What never carries over

- **Session and one-shot flags:** resume, continue, session IDs, fork, print mode and output format, session name, worktree, debug.
- **Positionals:** the root's prompt, a subcommand, and anything after a second `--`.
- **Credentials:** `pi --api-key` is dropped. Setup-flag values are never printed, because inline settings or MCP JSON can carry secrets.
- **Unrecognized flags:** dropped and named under `dropped`.
- **Environment:** `pane.split` takes no environment, so a worker gets the login environment hc gives every terminal, plus its own `HC_TERMINAL_ID`. Its role lives in `hc-agent.*` labels, not in an environment variable.

## Permission bypass is inherited and disclosed

`--dangerously-skip-permissions`, `--permission-mode bypassPermissions`, codex `--sandbox danger-full-access` or `--ask-for-approval never`, and pi `--approve` carry over like any setup flag. This gives a worker no access the orchestrator lacks, since the orchestrator can already type into any worker. Carrying them over is never silent: the summary prints `⚠ permission bypass inherited from main: …`, and that line must reach the user before the first start. `--without bypass` drops them; `--without flags` drops every inherited setup flag but the model and thinking. A posture set through the wrapper's own profile or shared settings reaches the worker through the wrapper or its config, and these options do not affect it.
