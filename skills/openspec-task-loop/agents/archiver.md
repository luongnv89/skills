---
name: archiver
description: Merge spec deltas into main specs, move change to archive, update parent tasks.md
role: Archive & Transition Handler
version: 1.1.0
---

# Archiver Agent

Complete the task cycle by merging spec artifacts into main openspec/specs, archiving the change folder, and updating parent project tasks.md.

## Input

```json
{
  "task_id": "2.3",
  "change_id": "task-2-3-pin-crud",
  "change_path": "openspec/changes/task-2-3-pin-crud/",
  "parent_tasks_md": "tasks.md",
  "verification_passed": true,
  "verification_report": { ... }
}
```

## Process

### Step 1: Merge Spec Deltas

Read spec artifacts from `openspec/changes/task-2-3-pin-crud/specs/`:

1. **Extract capability specs**: Any new `spec.md` files under `specs/[capability]/`
2. **Check for collisions**: Does `openspec/specs/[capability]/` already exist?
3. **Merge or create**:
   - If new capability: Move spec to `openspec/specs/[capability]/spec.md`
   - If existing capability: Review for conflicts, merge if compatible, or create versioned spec

Example:

```
# Before
openspec/
  ├── changes/task-2-3-pin-crud/
  │   └── specs/pin-crud/spec.md  <- New
  └── specs/
      └── auth/spec.md

# After
openspec/
  ├── changes/task-2-3-pin-crud/  <- Still exists, not deleted
  └── specs/
      ├── auth/spec.md
      └── pin-crud/spec.md  <- Merged from change
```

Output merge results:

```json
{
  "spec_merges": [
    {
      "source": "openspec/changes/task-2-3-pin-crud/specs/pin-crud/spec.md",
      "destination": "openspec/specs/pin-crud/spec.md",
      "action": "created",
      "conflicts": []
    }
  ],
  "merge_status": "success"
}
```

### Step 2: Create Archive Entry

Create timestamped archive folder:

```
openspec/changes/archive/
  └── 2026-03-24-task-2-3-pin-crud/
      ├── proposal.md
      ├── design.md
      ├── tasks.md
      ├── specs/
      │   └── pin-crud/spec.md
      └── ARCHIVE_NOTE.md
```

Create ARCHIVE_NOTE.md:

```markdown
# Archive Note: task-2-3-pin-crud

**Archived**: 2026-03-24 12:15:00 UTC
**Task ID**: 2.3
**Status**: Completed

## Summary

Implemented full CRUD operations for pins with strict user ownership scope.

### What Changed
- Added `pins` table migration with user_id ownership
- Implemented 5 API endpoints (POST, GET, PATCH, DELETE, GET by ID)
- Added ownership validation middleware
- 15 unit tests + 8 integration tests (all passing)

### Files Modified
- src/api/pins.ts (new)
- src/db/migrations/001_create_pins.sql (new)
- tests/api/pins.test.ts (new)
- src/middleware/auth.ts (updated - ownership check)

### Specs Created
- openspec/specs/pin-crud/spec.md

### Verification
- Scope: atomic ✓
- Acceptance Criteria: 6/6 satisfied ✓
- Spec-Test Alignment: 8/8 aligned ✓
- Code Quality: passed ✓

### Next Steps
- Deploy to staging environment
- Run smoke tests
- Deploy to production
- Update user documentation
```

### Step 3: Update Parent tasks.md

Read project's main `tasks.md` and find task 2.3:

```markdown
# Project Tasks

## Phase 2: Core Features

### Task 2.3: Pin CRUD Operations
- Status: ✅ COMPLETED
- Spec: openspec/specs/pin-crud/spec.md
- Archive: openspec/changes/archive/2026-03-24-task-2-3-pin-crud/
- Completion Date: 2026-03-24
- Lead: [Agent]

**Changes**:
- Added pins API with Create, Read, Update, Delete
- Added ownership validation
- 23 tests (unit + integration)
```

Update markers:
- Change status to ✅ COMPLETED or similar
- Add completion date
- Add archive path reference
- Add spec path reference

Output update:

```json
{
  "parent_tasks_md": "tasks.md",
  "task_id": "2.3",
  "status_updated": "completed",
  "changes_made": [
    "Updated task 2.3 status to ✅ COMPLETED",
    "Added archive path: openspec/changes/archive/2026-03-24-task-2-3-pin-crud/",
    "Added spec path: openspec/specs/pin-crud/spec.md",
    "Added completion date: 2026-03-24"
  ]
}
```

### Step 4: Cleanup and Validation

1. **Verify no orphaned files**: Are all change artifacts merged or archived?
2. **Check for dangling references**: Do any specs reference non-existent files?
3. **Commit readiness**: Are all changes in staging area?

Output:

```json
{
  "cleanup": {
    "orphaned_files": [],
    "dangling_references": [],
    "uncommitted_changes": [
      "openspec/specs/pin-crud/spec.md",
      "openspec/changes/archive/2026-03-24-task-2-3-pin-crud/",
      "tasks.md"
    ],
    "ready_to_commit": true
  }
}
```

### Step 5: Git Operations

Prepare for commit:

1. **Stage archival changes**: Git add openspec/, tasks.md
2. **Create commit message**:

```
feat(pin-crud): implement CRUD operations with ownership scope

- Add pins table migration
- Implement Create, Read, Update, Delete endpoints
- Add ownership validation middleware
- 23 tests (unit + integration), all passing

Closes #2.3
```

3. **Note commit hash** for final report

Output:

```json
{
  "git_operations": {
    "staged_files": [
      "openspec/specs/pin-crud/spec.md",
      "openspec/changes/archive/2026-03-24-task-2-3-pin-crud/ARCHIVE_NOTE.md",
      "tasks.md"
    ],
    "commit_ready": true,
    "commit_message": "feat(pin-crud): implement CRUD operations with ownership scope\n\n- Add pins table migration\n- Implement Create, Read, Update, Delete endpoints\n- Add ownership validation middleware\n- 23 tests (unit + integration), all passing\n\nCloses #2.3"
  }
}
```

## Output Format

```json
{
  "task_id": "2.3",
  "change_id": "task-2-3-pin-crud",
  "archival_timestamp": "2026-03-24T12:15:00Z",
  "status": "archived",
  "actions_completed": {
    "spec_merge": "success",
    "archive_created": "openspec/changes/archive/2026-03-24-task-2-3-pin-crud/",
    "parent_tasks_updated": true,
    "cleanup_verified": true,
    "git_staged": true
  },
  "next_action": "commit_and_push",
  "commit_message_ready": true,
  "completion_summary": "Pin CRUD task completed and archived. Specs merged into main openspec/specs/. Ready to commit."
}
```

## Graceful Degradation

If git operations unavailable:
- Return archival completion status
- Provide commit message as text output
- Note: "Git operations skipped - manual commit required"

## Return to Main Skill

Pass archival results to openspec-task-loop SKILL.md.

- If successful: Task cycle complete
- Prompt user to commit and push
- Ready to select next task

## Next Task Selection

After archival:

```markdown
# Task Cycle Complete ✓

Archive: openspec/changes/archive/2026-03-24-task-2-3-pin-crud/
Specs: openspec/specs/pin-crud/spec.md
Status: task-2-3-pin-crud ✅ COMPLETED

## What's Next?

Select the next task from tasks.md:
- [ ] 2.4: Pin Sharing with Collections
- [ ] 2.5: Pin Recommendations
- [ ] 3.1: Image Upload & Storage

Or run `/openspec-task-loop` to begin next task cycle.
```
