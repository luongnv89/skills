# Knowledge Routing: which layer owns each instruction

Before writing a line into `AGENTS.md` or `CLAUDE.md`, decide whether the root file is its home at all. Most audit findings are routing errors, not wording errors.

## Routing table

| Kind of instruction | Home | Why |
|---|---|---|
| Always-on facts for any agent | Root `AGENTS.md` | Every agent loads it every session |
| Folder-only conventions | Nested `AGENTS.md`, or `.claude/rules/*.md` with `paths:` | Loads only when those files are touched |
| Claude-only lines (plan mode, hooks, `/commands`, skills, subagents, MCP tools) | A CLAUDE file that already exists or was requested; otherwise `.claude/rules/*.md` | Rules load alongside `AGENTS.md`, while a new `CLAUDE.md` would shadow it |
| Multi-step procedure | A skill (`SKILL.md`) | Its body loads only when invoked |
| Isolated research or audit | A subagent | It has its own context; only a summary returns |
| Must-never-happen stop | `PreToolUse` hook plus permissions | Doesn't depend on the model |
| Verification of work | Tests, CI, or a `PostToolUse` hook | "Please test" is a request; a gate is a gate |
| Claude commit trailers and attribution | The `attribution` and `includeGitInstructions` settings | A setting beats competing prose |
| Personal taste | `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.codex/AGENTS.md` | Not shared, and never rewritten by the repo agent |

The root file is the constitution. A 30-line deploy checklist inside it is a skill in the wrong place.

## File scopes

- **Shared source of truth**: the repo-root `AGENTS.md`, plus nested package files.
- **Claude wrapper**: a `CLAUDE.md` whose first line imports `AGENTS.md`, followed only by Claude-only lines. Write one only on request, or to un-shadow an existing `CLAUDE.md`.
- **Personal**: `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. The user writes these, and a repo-scoped run never rewrites them.
- **Local overrides**:
  - `CLAUDE.local.md` is gitignored and **shadows `AGENTS.md`** for its owner unless its first line is `@AGENTS.md`.
  - `AGENTS.override.md` is Codex-only, and *replaces* that directory's `AGENTS.md` for Codex.
- **Org policy**: a managed `CLAUDE.md`, or the `claudeMd` managed setting.

Commit the project files, review them like code, and give the root file an owner.

## The `CLAUDE.md` wrapper

Write it only on the migrate or wrapper branch, and never as a second copy of the rules:

```markdown
@AGENTS.md

## Claude Code
- Use plan mode for changes under `src/billing/`.
```

When no Claude-only lines remain, the wrapper is just the import line. In `.claude/CLAUDE.md`, the import reads `@../AGENTS.md`, because import paths resolve relative to the importing file.

## Maintaining it as a feedback loop

Add a rule only when one of these is true:

- the agent made the **same** mistake twice
- a review found a fact the agent should have known
- you typed the same correction in two consecutive sessions
- a new teammate would need it

Then:

- Check for duplicates and contradictions before keeping the edit.
- If a machine can check the rule, add a hook or a test and **delete the prose**.
- Batch updates: one bad session is noise, but two is a pattern.
- Re-prune periodically, since instructions lose value as models improve.
