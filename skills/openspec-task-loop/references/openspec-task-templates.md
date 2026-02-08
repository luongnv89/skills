# OpenSpec Single-Task Templates

Use these templates when `/opsx:*` commands are unavailable and you need to apply OpenSpec manually.

## Folder Layout

```text
openspec/
  changes/
    <change-id>/
      .openspec.yaml
      proposal.md
      design.md
      tasks.md
      specs/
        <capability>/
          spec.md
```

---

## `.openspec.yaml`

```yaml
schema: spec-driven
createdAt: <ISO-8601>
changeId: <change-id>
sourceTask: <parent task id>
```

---

## `proposal.md`

```markdown
# Proposal: <change-id>

## Why
<Problem and user impact>

## Scope
- In scope:
  - <single-task scope>
- Out of scope:
  - <explicitly excluded items>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Risks
- <risk + mitigation>
```

---

## `specs/<capability>/spec.md`

```markdown
# <capability> Specification Delta

### Requirement: <name>
- The system SHALL <required behavior>.

#### Scenario: <happy path>
- GIVEN <state>
- WHEN <trigger>
- THEN <expected result>

#### Scenario: <edge/error path>
- GIVEN <state>
- WHEN <trigger>
- THEN <expected result>
```

---

## `design.md`

```markdown
# Design: <change-id>

## Approach
<How this task is implemented>

## Files Affected
- <path>: <reason>

## Decisions
- Decision: <what>
- Rationale: <why>
- Tradeoff: <cost>

## Validation Plan
- Unit/integration checks:
  - <check 1>
  - <check 2>
```

---

## `tasks.md`

```markdown
# Tasks: <change-id>

- [ ] 1. Implement <first concrete step>
- [ ] 2. Add/adjust tests for <scenario>
- [ ] 3. Run validation checks
- [ ] 4. Update docs/spec delta if behavior changed during implementation
```

---

## Archive Note (recommended)

Add to parent project log:

```markdown
- <date> Archived `<change-id>` for task `<task-id>`
  - Outcome: <what shipped>
  - Spec impact: <which capability/spec updated>
  - Verification: <tests/checks passed>
```
