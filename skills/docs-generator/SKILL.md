---
name: docs-generator
description: "Generate and restructure project documentation into a clear, accessible hierarchy. Use when asked to organize docs, generate documentation, improve doc structure, or restructure README. Don't use for API reference generation from code (JSDoc/Sphinx), authoring a landing page, or agent-config files like CLAUDE.md."
license: MIT
effort: low
metadata:
  version: 1.2.3
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Documentation Generator

Restructure and organize project documentation for clarity and accessibility.

## Prerequisites

This skill requires (validate each before starting; if any check fails, stop and ask the user):

- **Git working tree**: clean or stashable. Run `git status` first; if dirty, back up via `git stash push -u -m "pre-docs-sync"` before any sync that could rebase or overwrite local changes.
- **Tools required**: `git` >= 2.30, a Markdown-aware editor, and `mermaid-cli` (or a renderer) only if diagrams must be exported. Confirm availability with `git --version` and `command -v mmdc`.
- **Repo permissions**: read access for analysis; write access only when the user explicitly approves commits. For read-only repos, fall back to emitting a diff or inline summary instead of writing files.
- **Branch state**: an `origin` remote that is reachable (`git remote get-url origin`); if missing, do not attempt rebase/pull — ask the user.
- **Backups**: confirm the repo is pushed or otherwise backed up before any restructure that deletes or moves doc files. Pair every destructive `rm`/`git mv` with a prior `git status` check and explicit user confirmation; never run `git reset --hard`, `git push --force`, or `rm -rf` without a dry-run preview and user approval.
- **Safety defaults**: prefer dry-run previews (`git mv -n`, `rm -i`) and require user confirmation before any irreversible action.

If any prerequisite fails, halt and surface the blocker to the user rather than proceeding.

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Workflow

### 0. Create Feature Branch

Before making any changes:
1. Check the current branch - if already on a feature branch for this task, skip
2. Check the repo for branch naming conventions by running `git branch -r | head -20` (e.g., `feat/`, `feature/`, etc.)
3. Create and switch to a new branch following the repo's convention, or fallback to: `feat/docs-generator`

### 1. Analyze Project

Read the codebase to identify:
- **Project type**: Library, API, web app, CLI, microservices
- **Architecture**: Monorepo, multi-package, single module
- **User personas**: End users, developers, operators
- **Existing docs**: Scan for README files, docs/ folder, inline comments, docstrings
- **Gaps**: List what documentation exists vs. what is missing

### 2. Restructure Documentation

**Root README.md** - Streamline as entry point:
- Project overview and purpose
- Quickstart (install + first use)
- Modules/components summary with links
- License and contacts

**Component READMEs** - Add per module/package/service:
- Purpose and responsibilities
- Setup instructions
- Testing commands

**Centralize in `docs/`** - Organize by category (select applicable):
```
docs/
├── architecture.md      # System design, diagrams
├── api-reference.md     # Endpoints, authentication
├── database.md          # Schema, migrations
├── deployment.md        # Production setup
├── development.md       # Local setup, contribution
├── troubleshooting.md   # Common issues
└── user-guide.md        # End-user documentation
```

### 3. Create Diagrams

Use Mermaid for all visual documentation:
- Architecture diagrams
- Data flow diagrams
- Database schemas

### 4. Review and Validate

1. Verify all internal links resolve correctly
2. Check that code examples in docs are syntactically valid
3. Confirm no orphaned docs (files not linked from anywhere)
4. Present a summary of changes to the user before committing

Present changes to user for approval. Do not commit unless the user explicitly asks.

## Expected Output

After running this skill on a mid-size Node.js API project, you should see:
- A clean root `README.md` with project overview, quickstart, module links, and license
- Per-package `README.md` files for each service or library
- A `docs/` folder with relevant files such as `architecture.md`, `api-reference.md`, `deployment.md`, and `development.md`
- Mermaid diagrams embedded in architecture and data-flow docs
- A validation summary listing all internal links checked and any gaps found

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] Root `README.md` contains an overview, a quickstart (install + first use), and links to component or `docs/` files.
- [ ] A `docs/` directory exists with at least one of: `architecture.md`, `api-reference.md`, `deployment.md`, `development.md` — and only the files relevant to the project type.
- [ ] Every internal Markdown link resolves to an existing file (no broken `[text](path)` references).
- [ ] No orphaned files: every `docs/*.md` is reachable from `README.md` or another `docs/` page within one hop.
- [ ] Mermaid diagrams in architecture or data-flow docs render without syntax errors (`mmdc` validation if available).
- [ ] No commits land on `main`/`master`; all changes are on a feature branch following the repo's naming convention.

## Edge Cases

- **No existing documentation**: Skill generates from scratch using code analysis. Starts with `README.md` and adds `docs/` files based on project complexity.
- **Conflicting or outdated docs**: Flags conflicts to the user. Prefers code-derived information over stale docs; marks outdated sections for review.
- **Monorepo with many packages**: Limits per-package README creation to packages with actual public APIs or user-facing functionality; skips auto-generated or build-output packages.
- **Private or secret-adjacent content**: Never documents credentials, tokens, or internal-only endpoints beyond what already exists in code comments.
- **Read-only repository**: If git write access is unavailable, outputs documentation as a diff or inline summary rather than committing files.

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Branch Setup** — checks: `Branch creation`, `Repo sync`

**Phase: Project Analysis** — checks: `Project analysis`, `Gap identification`

**Phase: Documentation Restructure** — checks: `Doc restructure`, `Diagram creation`

**Phase: Validation** — checks: `Validation pass`, `Link verification`

## Error Handling

### No existing documentation found
**Solution:** Generate documentation from scratch based on code analysis. Start with README.md and add docs/ files based on project complexity.

### Conflicting or outdated docs
**Solution:** Flag conflicts to the user. Prefer code-derived information over stale docs. Mark outdated sections for user review.

## Guidelines

- Keep docs concise and scannable
- Adapt structure to project type (not all categories apply)
- Maintain cross-references between related docs
- Remove redundant or outdated content
- Preserve any existing docs that are still accurate
