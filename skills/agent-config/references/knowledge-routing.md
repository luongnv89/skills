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

### A rule the user asks for

Add it as asked, through the targeted edit. The evidence bar below does not apply: the user's request is the approval. Still check it for duplicates and contradictions, and route it with the table above.

### A rule the agent proposes

A rule you propose yourself, from a repeated mistake, a review, an audit finding or a session's corrections, is written only when it passes all four checks. One bad session is noise; two is a pattern.

1. **Two occurrences.** Cite at least two separate occurrences of the same miss, each with its location: a PR or commit SHA plus `path:line`, or a session's command and its output. Two occurrences in the same PR or session count once.
2. **A checkable trigger.** State the trigger as something a diff or a command can show: a path glob, an added or removed line matching a pattern, or a command and the result that means the rule was broken. "Write cleaner code" has no trigger, so it fails.
3. **A disprove check.** Try to prove the rule wrong before keeping it. Run the trigger against both cited occurrences: it must fire on each. Then run it against recent clean changes, such as the last 10 merged commits on the default branch that are not occurrences (`git log --first-parent -n 10`): it must fire on none. Show the commands and what they returned.
4. **Human approval.** Show the rule with its evidence, and write it only after the user approves (Step 4, *Show before writing*). An unattended run writes nothing and lists the rule as a candidate.

A rule that fails a check is reported as a **candidate**, never written, naming the check it failed (for example `1 occurrence found`, `no diff-checkable trigger`, `fires on 3 clean commits`).

### A rule broken again

A rule is not a lock. When a cited occurrence happened after the rule was already in the file (`git log -S '<rule text>' -- AGENTS.md` dates it), the prose has failed once. Don't reword it or add emphasis: propose a hook (`PreToolUse` plus permissions for a must-never stop) or a test or CI check that enforces the same trigger, and, once that gate exists, delete the prose.

If a machine can check any rule, add a hook or a test and **delete the prose**.

### When to re-prune

Instructions lose value as models improve, so re-run the prune pass (SKILL.md Step 3, step 2) over the whole file when either of these happens:

- **A model or agent upgrade**: the user reports moving to a new model, or to a new major version of Claude Code, Codex or Cursor.
- **The file nears its size limit**: it reaches 150 lines (the top of the 40–150 sweet spot; the hard limit is 200), or all instruction files together pass 28 KiB of Codex's 32 KiB.

A targeted edit that finds either trigger still makes only the requested change, and reports `re-prune due` with the reason and its prune candidates.
