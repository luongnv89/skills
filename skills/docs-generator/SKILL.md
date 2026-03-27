---
name: docs-generator
description: Restructure project documentation for clarity and accessibility. Use when users ask to "organize docs", "generate documentation", "improve doc structure", "restructure README", or need to reorganize scattered documentation into a coherent structure. Analyzes project type and creates appropriate documentation hierarchy.
effort: low
license: MIT
metadata:
  version: 1.2.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Documentation Generator

Restructure and organize project documentation for clarity and accessibility.

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

**Phase: Branch Setup** — checks: `Branch creation`, `Project analysis`

**Phase: Project Analysis** — checks: `Project analysis`, `Doc restructure`

**Phase: Documentation Restructure** — checks: `Doc restructure`, `Diagram creation`, `Validation pass`

**Phase: Validation** — checks: `Validation pass`, `Branch creation`, `Diagram creation`

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
