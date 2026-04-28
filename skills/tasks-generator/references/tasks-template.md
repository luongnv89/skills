# Tasks Template

## Table of Contents
1. [Concrete Reviewable Shape](#concrete-reviewable-shape)
2. [Overview](#overview)
3. [Dependencies Map](#dependencies-map)
4. [Sprint Sections](#sprint-sections)
5. [Backlog](#backlog)
6. [Ambiguous Requirements](#ambiguous-requirements)
7. [Final Agent Message](#final-agent-message)

---

## Concrete Reviewable Shape

A reviewer-friendly minimal example of the generated `tasks.md`:

```markdown
# Development Tasks — <Project Name>

Source PRD: ./prd.md
Generated: 2026-04-28

## Sprint Overview

| Sprint | Phase           | Focus                          | Task Count |
|--------|-----------------|--------------------------------|------------|
| 1      | POC             | Core differentiating feature   | 5          |
| 2      | MVP Foundation  | Auth, data models              | 8          |
| 3      | MVP Completion  | UI/UX, integration             | 7          |
| 4      | Full Features   | Enhancements, polish           | 6          |

## Sprint 1 — POC

### Task 1.1: Implement core ranking algorithm

**Description**: Build the scoring function described in PRD §3.2 — the
single feature that proves the product hypothesis.

**Acceptance Criteria**:
- [ ] Given input `X`, function returns score within `[0, 1]`.
- [ ] Unit tests cover empty input, max input, and a typical input.
- [ ] Latency under 50ms for inputs up to 1k items.

**Dependencies**: None

**Effort**: 2-3 days (M)

**PRD Reference**: §3.2 Ranking

### Task 1.2: ...

## Dependency Table

| Task   | Depends On  | Blocks      | Wave |
|--------|-------------|-------------|------|
| 1.1    | None        | 1.2, 2.1    | 1    |
| 1.2    | 1.1         | 2.3         | 2    |
| 2.1    | 1.1         | 2.2, 3.1    | 2    |

## Critical Path

`1.1 → 2.1 → 2.2 → 3.1 → 3.4` (estimated 11-14 days)

## Flagged Ambiguities

- PRD §4.1 leaves the rate-limit value unspecified — assumed 60 req/min, confirm with PM.
- PRD §5 mentions "social login" without listing providers — assumed Google + GitHub.
```

---

## Final Agent Message

The agent's final message after a successful run should look like:

```
✅ tasks.md generated at <path>
Sprints: 4 | Tasks: 26 | Critical path: 5 tasks (~12 days)
GitHub: https://github.com/<owner>/<repo>/blob/main/<dir>/tasks.md
README updated: https://github.com/<owner>/<repo>/blob/main/README.md
Commit: <sha>
Next: review Sprint 1 / Wave 1 tasks before kickoff.
```

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
