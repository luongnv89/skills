# Tasks Template

## Table of Contents
1. [Overview](#overview)
2. [Dependencies Map](#dependencies-map)
3. [Sprint Sections](#sprint-sections)
4. [Backlog](#backlog)
5. [Ambiguous Requirements](#ambiguous-requirements)

---

## Overview

```markdown
# Development Tasks

> Generated from: [prd.md filename]
> Generated on: [Current date]

## Overview

### Development Phases
- **POC**: [Brief description]
- **MVP**: [Brief description]
- **Full Release**: [Brief description]

### Key Dependencies
- [Critical dependencies or prerequisites]
```

---

## Dependencies Map

```markdown
## Dependencies Map

### Visual Dependency Graph

```
[Task 1.1] ─────┬──────────────────────────────> [Task 2.3]
               │
[Task 1.2] ────┴───> [Task 2.1] ───┬──> [Task 3.1] ──> [Task 4.1]
                                   │
[Task 1.3] ───> [Task 2.2] ────────┴──> [Task 3.2]
```

### Dependency Table

| Task ID | Task Title | Depends On | Blocks | Can Parallel With |
|---------|------------|------------|--------|-------------------|
| 1.1 | [Title] | None | 2.1, 2.3 | 1.2, 1.3 |
| 1.2 | [Title] | None | 2.1 | 1.1, 1.3 |
| 2.1 | [Title] | 1.1, 1.2 | 3.1 | 2.2 |

### Parallel Execution Groups

**Wave 1** (No dependencies - Start immediately):
- [ ] Task 1.1: [Title]
- [ ] Task 1.2: [Title]
- [ ] Task 1.3: [Title]

**Wave 2** (After Wave 1):
- [ ] Task 2.1: [Title] *(requires: 1.1, 1.2)*
- [ ] Task 2.2: [Title] *(requires: 1.3)*

**Wave 3** (After Wave 2):
- [ ] Task 3.1: [Title] *(requires: 2.1, 2.2)*

### Critical Path

```
[Task 1.2] → [Task 2.1] → [Task 3.1] → [Task 4.1]
```

**Critical Path Tasks**: 1.2 → 2.1 → 3.1 → 4.1
**Estimated Length**: [X tasks]

> ⚠️ Delays on critical path tasks directly impact project completion.
```

---

## Sprint Sections

```markdown
## Sprint 1: Proof of Concept (POC)

### Task 1.1: [Task Title]

**Description**: [Clear explanation of what and why, referencing PRD]

**Acceptance Criteria**:
- [ ] [Specific, testable condition 1]
- [ ] [Specific, testable condition 2]
- [ ] [Specific, testable condition 3]

**Dependencies**: [None / Task X.X]

**PRD Reference**: [Section or requirement]

---

### Task 1.2: [Task Title]
[Same format...]

---

## Sprint 2: MVP Foundation

### Task 2.1: [Task Title]
[Same format...]

---

## Sprint 3: MVP Completion

### Task 3.1: [Task Title]
[Same format...]

---

## Sprint 4: Feature Enhancement

### Task 4.1: [Task Title]
[Same format...]
```

---

## Backlog

```markdown
## Backlog: Future Iterations

### [Feature Name]
- [Brief description]
- [PRD reference if applicable]

### [Feature Name]
- [Brief description]
```

---

## Ambiguous Requirements

```markdown
## Ambiguous Requirements

> The following items from the PRD may need clarification:

| Requirement | What Needs Clarification |
|-------------|-------------------------|
| [Requirement] | [Question or ambiguity] |
| [Requirement] | [Question or ambiguity] |
```

---

## Technical Notes

```markdown
## Technical Notes

[Architecture decisions, implementation notes, or considerations from task planning]
```
