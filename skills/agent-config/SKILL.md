---
name: agent-config
description: "Create or update CLAUDE.md and AGENTS.md files following official best practices. Use when asked to create, audit, or improve agent config files (CLAUDE.md, AGENTS.md). Don't use for README/contributor docs or non-Claude IDE plugins."
license: MIT
effort: medium
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

## When to Use

Use when the user asks to create, update, audit, or improve `CLAUDE.md` or `AGENTS.md`. Skip for generic README or contributor-doc work.

## Core Principle

These files are **context, not enforced configuration**. They are loaded every session and the agent may still deviate.

- Short, specific, always-on facts go in the file.
- Multi-step procedures go in a **skill**.
- "Must never happen" goes in a `PreToolUse` **hook** plus permissions.
- "Verify the work" goes in **tests or CI**, not a sentence.

Write the constitution here; enforce the law somewhere else. Full rules and their sources: `references/official-standards.md`. Which layer owns a given instruction: `references/knowledge-routing.md`.

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

- **AGENTS.md** — the cross-agent source of truth, readable by any coding agent (Claude Code, Codex, others). A README *for agents*: setup, commands, layout, style deltas, tests, PR rules, security. Plain Markdown, no schema. Closest file wins, so nested copies override ancestors.
- **CLAUDE.md** — Claude-specific context loaded each conversation. When `AGENTS.md` already exists, `CLAUDE.md` opens with `@AGENTS.md` and carries only Claude-only extras — never a second copy of the same rules.

**Default when the user says "both":** write the content once into `AGENTS.md`, then a thin `CLAUDE.md` wrapper. Templates for both: `references/knowledge-routing.md`.

Subagent definition files (`.claude/agents/*.md`) are a different artifact and out of scope here — that is the `subagent-creator` skill's domain. Some repos, including this catalog, also keep subagent prompts inside their `AGENTS.md`; when the target file already uses that shape, preserve it and audit only the prose sections.

## Content Guidelines (both files)

These files give the agent persistent context **it cannot infer from code alone**.

**Size budget:** under **200 lines** per file (sweet spot 40–150); Codex's combined budget is 32 KiB. Past 200 lines, adherence measurably drops. When a file outgrows it: path-scope folder rules into `.claude/rules/*.md`, extract procedures into a skill, replace pasted docs with a pointer. Never use `@import` to save tokens.

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

Also pin what the model would otherwise guess wrong: the package manager (`pnpm`, not `npm`), the language version, the single-test command.

See `references/anti-patterns.md` for the full quality test and failure modes, and `references/claude-md-checklist.md` for the structural audit checklist (length budget, routing, enforceability, 5 required sections, drift).

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

- `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md` — personal defaults, all sessions. The user owns these; never rewrite one from a repo-scoped run.
- `./CLAUDE.md`, `./AGENTS.md` — checked into git, shared with the team, reviewed like code.
- `CLAUDE.local.md` / `AGENTS.override.md` — gitignored personal overrides.
- `.claude/rules/*.md` with a `paths:` key — load only when matching files are touched.
- Nested per-package files in monorepos; closest file wins.

### Imports and Emphasis

`@README.md`-style imports organize files but **do not shrink context** — imported files still load at launch. Reach for a path-scoped rule when the goal is fewer tokens.

Add **IMPORTANT** or **YOU MUST** only to true hard rules. Scattering them trains the model to ignore the markers.

## AGENTS.md Guidelines

`AGENTS.md` is the shared, agent-agnostic contract. Use this section order:

```markdown
## Project      — 2–4 sentences: what it is, invariants that must not break
## Commands     — install, dev, test (all / one), lint, types, adding a dep
## Layout       — package map, what may be edited, where tests live
## Conventions  — deltas from defaults only, one short example if needed
## Constraints  — never edit generated/, don't push to main unless asked
## Done when    — the exact lint/type/test commands that define completion
## Read when needed — pointers: billing → `docs/billing.md`
```

Every bullet must be a command, a pin, a constraint, or a pointer. One idea per bullet; no two bullets may contradict. Full templates, writing rules, and the maintenance feedback loop: `references/knowledge-routing.md`.

## Token Efficiency Block (always inject)

**Always** append the block from `references/token-efficiency-block.md` to every generated `CLAUDE.md` / `AGENTS.md`. This is non-negotiable — it protects the agent's context window and budget.

It is the one deliberate exception to "no general advice": these are always-on rules about how the agent works, not about the code, so the root file is the layer that owns them.

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

1. Read existing file. If both `AGENTS.md` and `CLAUDE.md` exist, read both — drift is only visible across the pair.
2. Walk every item in `references/claude-md-checklist.md` (length budget, content quality, routing, enforceability, 5 required sections, drift, final checks). Report each as pass / fail / N/A with a one-line reason.
3. Cross-check against `references/anti-patterns.md`.
4. **Route and enforce.** For every failing line, name where it belongs: a skill (procedure), a `.claude/rules/*.md` path-scoped file (folder-only), a `PreToolUse` hook plus permissions (must-never-happen), a test or CI (verification), or the user-level file (personal taste). A machine-checkable rule gets the gate **and** loses its prose.
5. Report: checklist results, anti-patterns found, routing recommendations, duplicated or contradicting rules, top recommendations.
6. **Do NOT modify the file** — report only. Suggest `/context` to confirm the file loads and `/doctor` to prune what the agent can infer.

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
- [ ] For `create` / `update`: result passes every section of `references/claude-md-checklist.md` (length budget, content quality, routing, enforceability, 5 required sections, drift).
- [ ] Generated/updated file is under 200 lines (verify with `wc -l`).
- [ ] No rule appears in both `AGENTS.md` and `CLAUDE.md`; when both exist, `CLAUDE.md` opens with `@AGENTS.md`.
- [ ] For `audit`: every checklist item is reported with pass / fail / N/A, each failing line carries a routing recommendation, and no file was modified (verify with `git diff --stat`).
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

**For `audit`:** prints a markdown report (no file writes) covering every checklist section, e.g.:

```
◆ Audit (step 1 of 1)
  Length budget:      √ pass — 64 lines
  Content quality:    × fail — 3 fluff lines ("be a senior engineer", motivational)
  Routing:            × fail — 12-line deploy runbook belongs in a skill
  Enforceability:     × fail — "never commit .env" has no PreToolUse hook
  5 required sections: × fail — missing "Hard rules" and "Done when"
  Drift:              × fail — 2 rules duplicated in AGENTS.md
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
- **AGENTS.md already exists and user asks for CLAUDE.md** → write the wrapper (`@AGENTS.md` + Claude-only extras), never a duplicate of the shared rules.
- **Target is a personal file (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`)** → audit and propose only; never rewrite a user's personal file from a repo-scoped run.
- **Monorepo** → propose nested per-package files rather than growing the root file.
- **Requested content is a multi-step procedure** → decline to inline it; propose a skill and leave a one-line pointer.
- **Generated file would exceed 200 lines** → reject; path-scope, extract to a skill, or link out instead.

## Anti-Patterns to Avoid

See `references/anti-patterns.md` for the full list (style rules linters cover, generic advice, file-by-file dumps, etc.).
