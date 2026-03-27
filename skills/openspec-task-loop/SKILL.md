---
name: openspec-task-loop
description: Apply OpenSpec OPSX in a strict one-task-at-a-time loop. Use when the user asks to execute work as single-task changes, wants spec-first implementation per task, or says to use OpenSpec method for each task from a task list. Supports both native /opsx command environments and manual fallback by creating OpenSpec artifact files directly.
effort: medium
license: MIT
metadata:
  version: 1.1.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# OpenSpec Task Loop

## Subagent Architecture

This skill uses a strictly sequential pipeline of subagents, where each iteration accumulates context and depends on the previous step. **Pattern**: E (Staged Pipeline) + C (Review Loop).

### Agents

| Agent | Role | Trigger |
|-------|------|---------|
| **spec-scaffolder** | Create all OpenSpec artifacts (proposal.md, design.md, tasks.md, specs/) | After task selection |
| **implementer** | Implement scoped task, update checkboxes, run validation | After spec scaffolding |
| **verifier** | Independently check quality gate: scope atomicity, acceptance criteria, spec-to-test alignment | After implementation complete |
| **archiver** | Merge spec deltas, move to archive, update parent tasks.md | After verification passed |

### Sequential Dependency

- **No Parallelism**: Step N+1 depends on Step N completion
- **Context Accumulation**: Each agent reads previous artifacts and extends understanding
- **Quality Gates**: Verifier ensures each stage is solid before proceeding

**Why Sequential**: Multiple task iterations (5-10) degrade reasoning quality significantly without this staged approach. Each step builds confidence and catches issues early.

## Environment Check

Before executing:
1. Verify git access to repository
2. Confirm write permissions to openspec/ directory
3. Check for existing task lists in project root (tasks.md)
4. Ensure references/openspec-task-templates.md is available

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

## Overview

Run OpenSpec as **one task = one change**. Keep scope tight, generate artifacts, implement, verify, and archive before moving to the next task.

## Workflow Decision

1. **If `/opsx:*` commands are supported in the current coding tool**: use native OPSX flow.
2. **If not supported**: use manual fallback by creating files under `openspec/changes/<change-id>/`.

## Core Loop (Single Task)

For each selected task from `tasks.md`:

1. **Select exactly one task**
   - Keep one atomic unit of value (usually 1–3 dev days).
   - If too large, split before proceeding.

2. **Create a task-scoped change**
   - Use change id format: `task-<task-id>-<short-slug>` (example: `task-2-3-pin-crud`).

3. **Plan with OpenSpec artifacts**
   - `proposal.md`: intent, scope, acceptance criteria, out-of-scope.
   - `specs/.../spec.md`: requirements and GIVEN/WHEN/THEN scenarios.
   - `design.md`: implementation approach and tradeoffs.
   - `tasks.md`: implementation checklist for this single task.

4. **Implement only this task scope**
   - Do not include unrelated refactors.
   - Update checkboxes as work completes.

5. **Verify before archive**
   - Validate completeness, correctness, coherence.
   - Fix critical mismatches before archive.

6. **Archive and sync**
   - Merge delta specs if needed.
   - Archive change folder.
   - Mark the parent project task complete.

## Native OPSX Command Path

Use this sequence per task:

```text
/opsx:new task-<task-id>-<slug>
/opsx:ff <change-id>          # or /opsx:continue for stepwise control
/opsx:apply <change-id>
/opsx:verify <change-id>
/opsx:archive <change-id>
```

Rules:
- Prefer `/opsx:continue` when requirements are still unclear.
- Prefer `/opsx:ff` when scope is clear and small.
- If implementation reveals drift, update artifacts before continuing.

## Manual Fallback Path (No /opsx Support)

If slash commands are unavailable:

1. Ensure OpenSpec tree exists (`openspec/changes`, `openspec/specs`).
2. Scaffold one change folder with:
   - `proposal.md`
   - `design.md`
   - `tasks.md`
   - `specs/<capability>/spec.md`
3. Read `references/openspec-task-templates.md` before scaffolding task artifacts.
4. Implement task and update checkboxes.
5. Run local validation/tests.
6. Merge spec deltas into `openspec/specs/` and move change to `openspec/changes/archive/<date>-<change-id>/`.

## Quality Gate (must pass before archive)

- [ ] Scope remained single-task and atomic
- [ ] Acceptance criteria satisfied
- [ ] Spec scenarios reflected in tests or executable checks
- [ ] No unrelated files changed
- [ ] Parent `tasks.md` updated with completion state
- [ ] Archive note includes what changed and why

## Output Format for Updates

When reporting progress, use:

```markdown
Task: <id + title>
Change: <openspec change id>
Status: planning | implementing | verifying | archived
Done:
- ...
Next:
- ...
Risks/Notes:
- ...
```

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

### Selection (step 1 of 4)

```
◆ Selection (step 1 of 4 — task scoping)
··································································
  Task identified:        √ pass — task-2-3-pin-crud selected
  Scope bounded:          √ pass — 1-3 dev days, atomic unit
  Dependencies clear:     √ pass — no blockers in tasks.md
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Planning (step 2 of 4)

```
◆ Planning (step 2 of 4 — spec scaffolding)
··································································
  Spec artifacts created: √ pass — proposal.md, design.md, tasks.md, spec.md
  Implementation planned: √ pass — approach and tradeoffs documented
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

### Implementation (step 3 of 4)

```
◆ Implementation (step 3 of 4 — code delivery)
··································································
  Code written:           √ pass — all checkboxes updated
  Tests pass:             × fail — 1 unit test failing
  Scope respected:        √ pass — no unrelated files changed
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

### Archive (step 4 of 4)

```
◆ Archive (step 4 of 4 — completion and sync)
··································································
  Artifacts synced:       √ pass — specs merged into openspec/specs/
  Quality gate passed:    √ pass — all 6 criteria met
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

## Resources

- `references/openspec-task-templates.md` — proposal/spec/design/tasks templates for manual mode.
- `scripts/new_task_change.sh` — optional scaffold script for manual mode.
