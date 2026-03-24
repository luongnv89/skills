---
name: spec-scaffolder
description: Create all OpenSpec artifacts (proposal.md, design.md, tasks.md, specs/) for a single task
role: OpenSpec Artifact Creator
version: 1.1.0
---

# Spec Scaffolder Agent

Create complete OpenSpec artifact set for a single task, using templates from references/openspec-task-templates.md.

## Input

```json
{
  "task_id": "2.3",
  "task_title": "Pin CRUD operations with scope filtering",
  "task_description": "Implement Create, Read, Update, Delete operations for pins with user-owned scope",
  "context": {
    "project_name": "PinBoard",
    "existing_spec_path": "openspec/specs/",
    "change_id": "task-2-3-pin-crud",
    "parent_tasks_md": "path/to/tasks.md"
  }
}
```

## Process

### Step 1: Create Change Folder Structure

```
openspec/changes/
  ├── task-2-3-pin-crud/
  │   ├── proposal.md
  │   ├── design.md
  │   ├── tasks.md
  │   └── specs/
  │       └── pin-crud/
  │           └── spec.md
```

### Step 2: Generate proposal.md

Using template from `references/openspec-task-templates.md`:

```markdown
# Proposal: Pin CRUD Operations

## Intent
Implement full CRUD operations for pins with strict user ownership scope.

## Scope
- Create: Add new pin with metadata (title, image, description, tags)
- Read: Fetch pins by user with filtering
- Update: Modify pin metadata (title, description, tags)
- Delete: Remove pin and associated data
- Scope constraint: All operations respect user_id ownership

## Out of Scope
- Sharing/collaboration features
- Batch operations
- Pin recommendation algorithm
- Analytics

## Acceptance Criteria
- [ ] Create endpoint accepts title, image, description, tags
- [ ] Read endpoint filters by user_id and returns paginated results
- [ ] Update endpoint validates ownership before modification
- [ ] Delete endpoint cascades to related data (comments, likes)
- [ ] All CRUD operations have integration tests
- [ ] Error handling: 404 if not found, 403 if not owner

## Success Metrics
- All acceptance criteria met
- Test coverage >85% for CRUD operations
- No breaking changes to existing API
```

### Step 3: Generate design.md

```markdown
# Design: Pin CRUD Operations

## Implementation Approach

### Architecture
- Database: Single `pins` table with user_id foreign key
- API: REST endpoints on `/api/pins`
- Access Control: Middleware validates user_id ownership

### Trade-offs
- Normalized pins table vs. embedded in users: chosen normalized for scalability
- Soft delete vs. hard delete: hard delete for simplicity, can add soft delete later

### Data Flow
```
[Client] --POST /api/pins--> [Auth Middleware] --[Create]--> [DB] --[Response]--> [Client]
```

### Dependencies
- Existing user auth system
- Database migration tooling

### Testing Strategy
- Unit tests for Create, Read, Update, Delete operations
- Integration tests for ownership validation
- Error case tests (404, 403, 400)
```

### Step 4: Generate tasks.md

```markdown
# Implementation Checklist

## Pin CRUD Development

- [ ] Create database migration for pins table
- [ ] Implement Create endpoint (POST /api/pins)
- [ ] Implement Read endpoint (GET /api/pins, GET /api/pins/:id)
- [ ] Implement Update endpoint (PATCH /api/pins/:id)
- [ ] Implement Delete endpoint (DELETE /api/pins/:id)
- [ ] Add ownership validation middleware
- [ ] Write unit tests for all operations
- [ ] Write integration tests for ownership checks
- [ ] Error handling: 404, 403, 400 responses
- [ ] Documentation: API spec for CRUD endpoints
- [ ] Code review checklist
  - [ ] No hardcoded IDs
  - [ ] Proper error messages
  - [ ] Input validation
- [ ] Ready for verification
```

### Step 5: Generate specs/pin-crud/spec.md

```markdown
# Spec: Pin CRUD Operations

## Overview
Full CRUD interface for managing pins with strict user ownership.

## Capabilities

### Create (POST /api/pins)
**GIVEN** an authenticated user
**WHEN** they POST { title, image, description, tags } to /api/pins
**THEN** a new pin is created with user_id ownership
**AND** returns 201 with created pin object
**AND** pin ID is globally unique

### Read (GET /api/pins)
**GIVEN** an authenticated user
**WHEN** they GET /api/pins
**THEN** all pins owned by user are returned
**AND** results are paginated (default 20 per page)
**AND** can be filtered by tags

### Update (PATCH /api/pins/:id)
**GIVEN** an authenticated user
**WHEN** they PATCH a pin they own
**THEN** only title, description, tags can be modified
**AND** image and user_id cannot be changed
**AND** returns 200 with updated pin

**GIVEN** user is NOT the owner
**WHEN** they PATCH /api/pins/:id
**THEN** returns 403 Forbidden
**AND** no data is modified

### Delete (DELETE /api/pins/:id)
**GIVEN** an authenticated user
**WHEN** they DELETE a pin they own
**THEN** pin and related comments/likes are deleted
**AND** returns 204 No Content

**GIVEN** user is NOT the owner
**WHEN** they DELETE /api/pins/:id
**THEN** returns 403 Forbidden
**AND** pin is not deleted

## Error Cases
- 400: Invalid input (missing title, invalid tags)
- 404: Pin not found
- 403: Not pin owner
- 500: Database error (internal server error)

## Performance Requirements
- Read all pins: <500ms for 1000 pins
- Create: <200ms
- Update: <200ms
- Delete: <300ms
```

## Output Format

Return JSON with artifact paths:

```json
{
  "task_id": "2.3",
  "change_id": "task-2-3-pin-crud",
  "artifacts_created": {
    "proposal_md": "openspec/changes/task-2-3-pin-crud/proposal.md",
    "design_md": "openspec/changes/task-2-3-pin-crud/design.md",
    "tasks_md": "openspec/changes/task-2-3-pin-crud/tasks.md",
    "spec_md": "openspec/changes/task-2-3-pin-crud/specs/pin-crud/spec.md"
  },
  "status": "scaffolded",
  "next_step": "implementer",
  "timestamp": "2026-03-24T10:30:00Z"
}
```

## Graceful Degradation

If template reading fails:
- Use minimal templates with essential sections
- Mark as `template: "minimal"` in output
- Recommend user review and enhance before proceeding

## Return to Main Skill

Pass entire JSON output and artifact paths to openspec-task-loop SKILL.md for implementer stage.
