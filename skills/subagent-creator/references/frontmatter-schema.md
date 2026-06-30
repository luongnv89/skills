# Subagent frontmatter schema

The YAML frontmatter at the top of a `.claude/agents/<name>.md` (or `~/.claude/agents/<name>.md`) file. Two required fields; everything else is optional. **Reach for the common fields first** — most good subagents use only the first four.

## File location and precedence

A subagent file lives in one of these, highest priority first:

1. `--agents` CLI flag (JSON, session-only) — highest
2. `.claude/agents/` — project-level, version-controlled, team-shared
3. `~/.claude/agents/` — user-level, personal, cross-project
4. Plugin `agents/` folders — lowest

In a monorepo with nested `.claude/agents/` dirs, the one closest to the working directory wins. When the same `name` exists at multiple levels, the higher-priority one overrides.

## Common fields — use these first

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `name` | **yes** | string | Lowercase letters/digits/hyphens, no consecutive hyphens. Must match the filename stem. |
| `description` | **yes** | string | The primary trigger. When to invoke + what it does. Add `Use PROACTIVELY` or `MUST BE USED` to encourage auto-delegation. Quote it (it usually contains `:` or `,`). |
| `tools` | no | CSV | Tools the agent may use. **Omit to inherit ALL tools.** Least privilege: list only what's needed. |
| `model` | no | string | `inherit` \| `sonnet` \| `opus` \| `haiku` (or a full model ID). Defaults to the subagent model if omitted. `inherit` uses the caller's model. |

A minimal, complete subagent:

```yaml
---
name: code-reviewer
description: "Expert code review specialist. Use PROACTIVELY after writing or changing code. Reviews for security, bugs, and quality."
tools: Read, Grep, Glob, Bash
model: inherit
---
```

### `tools` — least-privilege patterns

| Agent kind | Suggested tools | Rationale |
|------------|-----------------|-----------|
| Analysis / review / audit (read-only) | `Read, Grep, Glob` | Can't mutate anything. Safest default for reviewers. |
| Search / explore | `Read, Grep, Glob, Bash` | Read-only Bash for `ls`/`find`/`git log`. |
| Worker that edits code | `Read, Edit, Write, Bash, Grep, Glob` | Needs write + run. Justify each. |
| General-purpose | *(omit `tools`)* | Inherits everything. Only when the agent genuinely needs broad access. |

**Scope `Bash` when you can** — `tools: Read, Bash(npm:*), Bash(git:*)` restricts Bash to `npm …` and `git …` commands (one pattern per entry). Conditional patterns (`Bash(test:*)`) narrow the blast radius of an edit-capable agent.

## Advanced fields — verify before using

These appeared in the source reference but are **version-dependent** and easy to get wrong or stale. Use one only when the job clearly needs it, and confirm it's supported in the user's Claude Code version (`/agents` or `claude agents` will surface what's honored). Don't sprinkle them in by default.

| Field | Type | What it does | When to reach for it |
|-------|------|--------------|----------------------|
| `disallowedTools` | CSV | Explicitly forbid tools even if otherwise inherited. | Lock a near-general agent out of a dangerous tool. |
| `permissionMode` | string | `default` \| `acceptEdits` \| `dontAsk` \| `bypassPermissions` \| `plan`. Controls the edit-approval workflow. | Rarely. `bypassPermissions` is dangerous — avoid unless deliberate. |
| `maxTurns` | int | Hard cap on agentic iterations. | Bound a long-running or runaway agent. |
| `skills` | CSV | Skills auto-injected into the agent at startup. | The agent depends on a specific skill's discipline. |
| `mcpServers` | YAML map | MCP server definitions for the agent. | The agent needs a specific external data source. |
| `memory` | string | `user` \| `project` \| `local`. Persists `MEMORY.md` across sessions (first ~200 lines auto-load; Read/Write/Edit auto-enabled). | A research/assistant agent that should accumulate knowledge. |
| `background` | bool | Run as a background task by default. | Long jobs the user shouldn't block on. |
| `effort` | string | `low` \| `medium` \| `high` \| `max`. Reasoning strength. | Cheap mechanical agent (`low`) vs. hard reasoning (`max`). |
| `isolation` | string | `worktree` runs the agent in an isolated git worktree on its own branch. | Parallel agents that would otherwise conflict on files. Expensive. |
| `initialPrompt` | string | Auto-submitted first turn when run as a main agent. | Session-wide agents (`claude --agent <name>`). |
| `context` | string | `fork` inherits the parent's full conversation instead of a clean slate. | Exploring an alternative approach without losing current context. |
| `hooks` | YAML | Component-scoped lifecycle hooks (e.g. a `PreToolUse` command). | Enforce a guard (lint, security check) around the agent's tool use. |

**Rule of thumb:** if you can't say in one sentence why the agent needs an advanced field, leave it out. A subagent with just `name` + `description` + `tools` + `model` is the norm, not the exception.

### Plugin restriction

Subagents shipped inside a **plugin** may **not** use `hooks`, `mcpServers`, or `permissionMode` (privilege-escalation guard). If you're authoring a plugin-bundled agent, restrict yourself to the common fields plus the safe advanced ones.

## `--agents` CLI (JSON) form

The same definition, session-only, via flag. `prompt` here is the system-prompt body:

```bash
claude --agents '{
  "reviewer": {
    "description": "Expert code reviewer. Use proactively after changes.",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Bash"],
    "model": "sonnet"
  }
}'
```

Keys: `description` (required), `prompt` (required), `tools` (optional array), `model` (optional). No frontmatter file needed; lasts the session.
