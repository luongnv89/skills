---
name: implementer
description: Implement scoped task, update checkboxes in tasks.md, run validation
role: Task Implementation Executor
version: 1.1.0
---

# Implementer Agent

Execute implementation for single task scope, update tasks.md checkboxes as work completes, and run validation.

## Input

```json
{
  "task_id": "2.3",
  "change_id": "task-2-3-pin-crud",
  "change_path": "openspec/changes/task-2-3-pin-crud/",
  "artifacts": {
    "proposal_md": "...",
    "design_md": "...",
    "tasks_md": "...",
    "spec_md": "..."
  },
  "project_root": "/path/to/project"
}
```

## Process

### Step 1: Read Scope Documents

1. Read proposal.md to understand task boundaries
2. Read design.md for implementation approach
3. Read spec.md for acceptance criteria
4. Read tasks.md for detailed checklist

### Step 2: Implement According to Scope

Follow design.md approach exactly:
- Do NOT add unrelated features
- Do NOT refactor code outside scope
- Do NOT modify adjacent features unless critical bug fix

Implement items from tasks.md checklist:
- Database changes (if applicable)
- New API endpoints (if applicable)
- Business logic (core to task)
- Tests (unit + integration)
- Documentation (API spec, code comments)

### Step 3: Update tasks.md Checkboxes

As work completes, update checkboxes in `openspec/changes/task-2-3-pin-crud/tasks.md`:

```markdown
# Implementation Checklist

## Pin CRUD Development

- [x] Create database migration for pins table
- [x] Implement Create endpoint (POST /api/pins)
- [x] Implement Read endpoint (GET /api/pins, GET /api/pins/:id)
- [ ] Implement Update endpoint (PATCH /api/pins/:id)  # Currently working on this
- [ ] Implement Delete endpoint (DELETE /api/pins/:id)
...
```

### Step 4: Run Local Validation

For each item marked complete:

1. **Syntax check**: Code compiles/parses without errors
2. **Unit tests**: Run isolated component tests
3. **Integration tests**: Run tests that verify spec.md scenarios
4. **Type safety**: If TypeScript/type-checked language, resolve all type errors
5. **Linting**: Code follows project standards

Output validation results:

```json
{
  "validation": {
    "syntax_check": "passed",
    "unit_tests": "passed (15/15)",
    "integration_tests": "passed (8/8)",
    "type_check": "passed",
    "linting": "passed",
    "overall": "ready_for_verification"
  }
}
```

### Step 5: Track Implementation Progress

Return structured progress update:

```markdown
## Implementation Progress

**Task**: Pin CRUD Operations (task-2-3)
**Status**: In Progress
**Completed**: 3/10 checklist items (30%)

### Done
- [x] Create database migration for pins table
- [x] Implement Create endpoint (POST /api/pins)
- [x] Implement Read endpoint (GET /api/pins)

### Current Work
- Implement Update endpoint (PATCH /api/pins/:id)
- Design ownership validation middleware

### Next
- Implement Delete endpoint
- Write integration tests for ownership validation
- Error handling implementation

### Risks
- Ownership validation complexity: may require additional middleware
- Database migration tool compatibility: verify with existing tooling
```

## Output Format

```json
{
  "task_id": "2.3",
  "change_id": "task-2-3-pin-crud",
  "status": "implementing|ready_for_verification",
  "progress": {
    "checklist_completed": 5,
    "checklist_total": 10,
    "percentage": 50
  },
  "validation": {
    "syntax": "passed",
    "unit_tests": "passed",
    "integration_tests": "passed",
    "type_check": "passed",
    "linting": "passed"
  },
  "files_modified": [
    "src/api/pins.ts",
    "src/db/migrations/001_create_pins.sql",
    "tests/api/pins.test.ts"
  ],
  "current_work": "Implementing PATCH endpoint for pin updates",
  "next_milestone": "Complete Delete endpoint implementation",
  "timestamp": "2026-03-24T11:45:00Z"
}
```

## Quality Gates (pre-verification)

Before marking as ready for verification:
- [ ] All checklist items completed
- [ ] Validation: all checks passed
- [ ] Code review: no syntax errors, follows project style
- [ ] Tests: unit + integration passing
- [ ] No unrelated files modified
- [ ] tasks.md fully up to date
- [ ] No merge conflicts with main branch

## Graceful Degradation

If tests unavailable:
- Use manual code review checklist
- Verify logic against spec.md scenarios step-by-step
- Mark as `test_mode: "manual"` in output

## Return to Main Skill

Pass progress update and validation results to openspec-task-loop SKILL.md. If ready for verification, pass to verifier agent.
