---
name: tasks-generator
description: "Generate development tasks from a PRD file with sprint-based planning. Use when users ask to create tasks from PRD, break down the PRD, generate sprint tasks, or want to convert product requirements into actionable development tasks. Creates/updates tasks.md and always reports GitHub links to changed files. Don't use for writing a PRD, authoring a TAD, or executing tasks (see openspec-task-loop)."
effort: max
license: MIT
metadata:
  version: 1.1.2
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Tasks Generator

Transform PRD documents into structured, sprint-based development tasks with dependency analysis.

## Environment Check

Before running this skill, verify:
- [ ] The project has a PRD file (prd.md or similar)
- [ ] You have write access to the project directory
- [ ] The project is a git repository with a remote
- [ ] You can run bash commands in the project directory

If any check fails, the skill will stop and ask for clarification.

## Subagent Architecture

This skill uses a **Staged Pipeline (E) + Parallel Workers (B)** architecture:

```
Phase 1: Requirements Extraction
  ↓ (requirements-extractor agent)
  ↓
Phase 2-3: Sprint Planning
  ↓ (sprint-planner agent)
  ↓
Phase 4-5: Parallel Sprint Task Generation
  ├→ (sprint-worker agents, spawned in parallel — one per sprint)
  ├→ sprint 1 tasks
  ├→ sprint 2 tasks
  ├→ sprint 3 tasks
  └→ ...
  ↓
Phase 6: Cross-Sprint Dependency Resolution
  ↓ (dependency-resolver agent)
  ↓
Final Output: tasks.md with all tasks and dependencies
```

**Agents**:
1. `agents/requirements-extractor.md` — Reads PRD + supporting docs, produces structured feature list
2. `agents/sprint-planner.md` — Defines sprint scope (POC, MVP, full features), produces sprint plan
3. `agents/sprint-worker.md` — Generates tasks for ONE sprint (runs in parallel, one per sprint)
4. `agents/dependency-resolver.md` — Wires cross-sprint dependencies, produces final tasks.md

**Key Insight**: Per-sprint task generation is parallelizable. Large PRDs produce 30-80 tasks across 4+ sprints. Sprint tasks are not fully independent — Sprint 2 depends on Sprint 1 output — so the dependency-resolver does a final pass to wire cross-sprint relationships.

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

## Input

Preferred: PRD file path provided in `$ARGUMENTS`.

Auto-pick mode (if `$ARGUMENTS` is empty):
1. Reuse the most recent project folder/path from this chat/session.
2. If unavailable, use env var `IDEAS_ROOT` when present.
3. Else check shared marker file `~/.config/ideas-root.txt`.
4. Backward compatibility fallback: `~/.openclaw/ideas-root.txt`.
5. If still unavailable, ask the user to provide the path or set `IDEAS_ROOT`.
6. Use `<project>/prd.md`.
7. If multiple candidates are plausible, ask user to choose.

## Pre-checks

1. Resolve `PRD_PATH` (from `$ARGUMENTS` or auto-pick mode) and verify it exists
2. Check for existing `tasks.md` in the same directory - create backup if exists: `tasks_backup_YYYY_MM_DD_HHMMSS.md`
3. Look for supporting docs in same directory: `tad.md`, `ux_design.md`, `brand_kit.md`

## Workflow

### Phase 1: Extract Requirements

From PRD, extract:
- Core features and value proposition
- User stories and personas
- Functional requirements
- Non-functional requirements (performance, security)
- Technical constraints and dependencies

### Phase 2: Define Development Phases

**POC (Proof of Concept):**
- Single most important feature proving core value
- Minimal implementation, 1-2 sprints

**MVP (Minimum Viable Product):**
- Essential features for first release
- Core user workflows

**Full Features:**
- Remaining enhancements
- Nice-to-haves and polish

### Phase 3: Create Sprint Plan

| Sprint | Focus | Scope |
|--------|-------|-------|
| Sprint 1 | POC | Core differentiating feature |
| Sprint 2 | MVP Foundation | Auth, data models, primary workflows |
| Sprint 3 | MVP Completion | UI/UX, integration, validation |
| Sprint 4+ | Full Features | Enhancements, optimization, polish |

### Phase 4: Analyze Dependencies

1. **Map Dependencies**: For each task, identify "Depends On" and "Blocks"
2. **Group Parallel Tasks**: Assign tasks to execution waves
3. **Calculate Critical Path**: Longest dependency chain = minimum duration
4. **Validate**: Check for circular dependencies, broken references

### Phase 5: Generate tasks.md

Create `tasks.md` in same directory as PRD. See [references/tasks-template.md](references/tasks-template.md) for full template.

## Task Format

Each task must include:

```markdown
### Task X.Y: [Action-oriented Title]

**Description**: What and why, referencing PRD

**Acceptance Criteria**:
- [ ] Specific, testable condition 1
- [ ] Specific, testable condition 2

**Dependencies**: None / Task X.X

**PRD Reference**: [Section]
```

## Task Guidelines

- **Title**: Action-oriented (e.g., "Implement user authentication API")
- **Size**: 1-3 days of work; break larger features
- **Criteria**: Cover happy path and edge cases
- **Dependencies**: List prerequisites and external dependencies

## Quality Checks

Before finalizing:
- [ ] All PRD requirements addressed
- [ ] Each task links to PRD
- [ ] No circular dependencies
- [ ] Clear MVP vs post-MVP distinction
- [ ] Ambiguous requirements flagged
- [ ] All tasks in dependency table
- [ ] Critical path identified

## README Maintenance (ideas repo)

After writing `tasks.md`, if the PRD lives inside an `ideas` repo, update the repo README ideas table:
- Preferred: `cd` to the repo root and run `python3 scripts/update_readme_ideas_index.py` (if it exists)
- Fallback: update `README.md` manually (ensure Tasks status becomes ✅ for that idea)

## Commit and push (mandatory)

- Commit immediately after updates.
- Push immediately to remote.
- If push is rejected: `git fetch origin && git rebase origin/main && git push`.

Do not ask for additional push permission once this skill is invoked.

## Reporting with GitHub links (mandatory)
When reporting completion, include:
- GitHub link to `tasks.md`
- GitHub link to `README.md` when it was updated
- Commit hash

Link format (derive `<owner>/<repo>` from `git remote get-url origin`):
- `https://github.com/<owner>/<repo>/blob/main/<relative-path>`

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

**Requirements phase checks:** `PRD parsed`, `Features extracted`, `Constraints identified`

**Sprint Planning phase checks:** `Phases defined`, `Stories created`, `Dependencies mapped`

**Generation phase checks:** `tasks.md written`, `Sprint breakdown complete`, `Estimates assigned`

**Output phase checks:** `README updated`, `Committed`, `Links reported`

## Output Summary

After generating, provide:
1. File location
2. Sprint overview (count, tasks per sprint)
3. MVP scope summary
4. Dependency analysis (waves, critical path, bottlenecks)
5. Flagged ambiguous requirements
6. Next steps: Review Sprint 1 and Wave 1 tasks first
