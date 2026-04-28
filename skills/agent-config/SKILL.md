---
name: agent-config
description: "Create or update CLAUDE.md and AGENTS.md files following official best practices. Use when asked to create, audit, or improve agent config files (CLAUDE.md, AGENTS.md). Don't use for README/contributor docs or non-Claude IDE plugins."
license: MIT
effort: medium
metadata:
  version: 1.2.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

## When to Use

Use when the user asks to create, update, audit, or improve `CLAUDE.md` or `AGENTS.md`. Skip for generic README or contributor-doc work.

## Prerequisites

- Run inside a git repo with `origin` set; the skill **requires** a clean tree before destructive edits.
- Tools: `git`, file write access to the target path.
- Confirm whether the user wants `CLAUDE.md`, `AGENTS.md`, or both before writing.

## Repo Sync Before Edits (mandatory)

Sync the current branch with remote before any create/update/delete. This is a destructive workflow — always **dry-run first** with `git fetch` (read-only) and inspect status before pulling.

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin                       # dry-run: read-only preview
git status                             # validate clean tree
git pull --rebase origin "$branch"     # only after confirmation
```

If the working tree is dirty, **back up via stash** before syncing:

```bash
git stash push -u -m "pre-sync-backup"  # backup
git fetch origin && git pull --rebase origin "$branch"
git stash pop                            # restore
```

If `origin` is missing, rebase conflicts occur, or stash pop fails, **stop and confirm** with the user before continuing. Never overwrite an existing `CLAUDE.md` / `AGENTS.md` without first reading it and showing a diff.

## User Input

```text
$ARGUMENTS
```

Recognised inputs: `create`, `update`, `audit`, or a path (e.g., `src/api/CLAUDE.md`).

## Step 1: Determine Target File

If unspecified, ask which file:

- **CLAUDE.md** — project context loaded each conversation: bash commands Claude can't guess, code-style overrides, test runners, repo etiquette, env quirks, gotchas.
- **AGENTS.md** — subagent definitions: tool permissions, model preferences, focused single-domain instructions.

## CLAUDE.md Guidelines

CLAUDE.md gives Claude persistent context **it cannot infer from code alone**.

### Include vs Exclude

| Include | Exclude |
|-----------|-----------|
| Bash commands Claude cannot guess | Anything Claude can figure out from code |
| Code style rules that differ from defaults | Standard language conventions |
| Testing instructions and preferred runners | Detailed API docs (link instead) |
| Repository etiquette (branch naming, PRs) | Information that changes frequently |
| Architectural decisions specific to project | Long explanations or tutorials |
| Developer environment quirks (env vars) | File-by-file codebase descriptions |
| Common gotchas or non-obvious behaviors | Self-evident practices like "write clean code" |

See `references/anti-patterns.md` for the full quality test and failure modes.

### Example Format

```markdown
# Code style
- Use ES modules (import/export), not CommonJS (require)
- Destructure imports when possible

# Workflow
- Typecheck after a series of code changes
- Prefer single-test runs over the full suite for performance
```

### File Locations

- `~/.claude/CLAUDE.md` — applies to all sessions
- `./CLAUDE.md` — checked into git, shared with team
- `CLAUDE.local.md` — gitignored personal overrides
- Parent dirs (monorepos) and child dirs (on-demand) both load

### Import Syntax

```markdown
See @README.md and @package.json.
- Git workflow: @docs/git-instructions.md
```

### Emphasis

Add **IMPORTANT** or **YOU MUST** for critical rules to improve adherence.

## AGENTS.md Guidelines

Subagents run in their own context with restricted tools.

### Definition Format

```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: opus
---
You are a senior security engineer. Review for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Auth/authorization flaws
- Secrets in code
Provide line references and concrete fixes.
```

**Required**: `name`, `description`, `tools`. **Optional**: `model`.

Best practices: single-domain focus, specific scope, concrete output format, minimum tool surface.

## Token Efficiency Block (always inject)

**Always** append the block from `references/token-efficiency-block.md` to every generated `CLAUDE.md` / `AGENTS.md`. This is non-negotiable — it protects the agent's context window and budget.

## Optional Blocks (only when requested)

If the user asks for orchestration rigor or stricter coding rules, copy verbatim the relevant block from `references/optional-blocks.md` (Workflow Orchestration / Mandatory Coding Discipline). Do not inject blindly.

## Execution Flow

### `create` (default)

1. Ask which file type if unspecified.
2. Analyze project: existing files, stack, README, package manifests.
3. Draft following guidelines + inject token-efficiency block.
4. If user said "apply now", write directly; otherwise present draft.
5. Finalize at the right path.

### `update`

1. Read existing file (do not skip — used to compute diff).
2. Audit against guidelines.
3. Identify content to remove, condense, or add.
4. Apply if asked, else show diff.

### `audit`

1. Read existing file.
2. Report: content quality, anti-patterns, useful-vs-redundant ratio, recommendations.
3. **Do NOT modify the file** — report only.

## Step Completion Reports

After each major step, output:

```
◆ [Step Name] ([step N of M])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Use `√` for pass, `×` for fail. Adapt check names per step.

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] Target file path confirmed (CLAUDE.md, AGENTS.md, or explicit path).
- [ ] Repo synced clean OR user explicitly authorised proceeding without sync.
- [ ] Token-efficiency block present in the generated/updated file (verify by grep `## Token Efficiency`).
- [ ] No anti-pattern from `references/anti-patterns.md` appears in the new content.
- [ ] For `audit`: no file was modified (verify with `git diff --stat`).
- [ ] Final step-completion report emitted with `Result: PASS`.

## Expected Output

**For `create` / `update`:** writes one file at the chosen path. Example tail of the file:

```markdown
## Token Efficiency
- Never re-read files you just wrote or edited. You know the contents.
- Never re-run commands to "verify" unless the outcome was uncertain.
... (rest of token-efficiency block)
```

Followed by a step-completion report ending in `Result: PASS`.

**For `audit`:** prints a markdown report (no file writes), e.g.:

```
◆ Audit (step 1 of 1)
  Content quality:    √ pass — 12 useful lines, 3 redundant
  Anti-patterns:      × fail — found 2 (generic style rules)
  Token block:        × fail — missing
  Result:             PARTIAL
```

## Edge Cases

- **No existing CLAUDE.md and `update` requested** → fall back to `create`, confirm with user first.
- **Both root and child `CLAUDE.md` exist** → ask which scope to edit; never silently overwrite both.
- **Dirty working tree** → stash backup before sync; if `stash pop` conflicts, stop and ask.
- **Missing `origin`** → skip sync, warn user, require explicit confirmation to proceed.
- **User pastes raw `$ARGUMENTS`** with no recognised verb → ask which mode (create/update/audit).
- **Generated file would exceed 500 lines** → reject; CLAUDE.md must stay terse, link out instead.

## Anti-Patterns to Avoid

See `references/anti-patterns.md` for the full list (style rules linters cover, generic advice, file-by-file dumps, etc.).
