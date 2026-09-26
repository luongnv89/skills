# Dependency Resolver Agent

Wire cross-sprint dependencies and produce final task output.

## Role

Consume task outputs from all sprint-worker agents, validate dependencies, identify circular deps, compute the critical path, and produce the final tasks.md file with all tasks and their inter-sprint dependencies wired correctly.

## Inputs

You receive these parameters in your prompt:

- **sprint_tasks_dir**: Directory containing all sprint task JSON files (e.g., sprint_1.json, sprint_2.json, ...)
- **sprint_plan_json_path**: Path to the sprint plan JSON
- **requirements_json_path**: Path to the requirements JSON
- **prd_path**: Original PRD path
- **output_path**: Where to save the final tasks.md

## Process

### Step 1: Load All Sprint Tasks

Read all sprint JSON files from sprint_tasks_dir:
- Sprint 1 tasks
- Sprint 2 tasks
- Sprint 3 tasks
- (etc.)

Build an in-memory map of all tasks by task_id.

### Step 2: Load Dependencies Metadata

From sprint_plan_json, read the feature dependencies:
- Which features depend on which
- Use this to validate that sprint workers assigned tasks correctly to sprints

### Step 3: Validate Dependency References

Across all loaded sprint outputs:
- Require every task ID to match `<sprint>.<index>` and each sprint's indices
  to be unique across workstreams; keep `workstream` as a separate field
- Check that every `depends_on` and `blocks` reference names an emitted task ID;
  reject dangling or fabricated IDs
- For each `depends_on`, allow a same-sprint dependency or an existing task in
  an earlier sprint; reject unknown or later-sprint dependencies
- Build a normalized combined in-memory map: for every verified `depends_on`,
  derive the reciprocal `blocks` entry on the prerequisite task. Therefore
  `blocks` may point to the same or a later sprint, including edges absent from
  an individual parallel worker's output
- Do not create a dependency absent from an explicit worker `depends_on`; a
  derived reciprocal `blocks` entry is representation, not a new dependency
- Require normalized `depends_on` and `blocks` to be exact inverse edges
- Check for circular dependencies across the complete normalized graph
- If any invalid reference or cycle is found, report it with details

### Step 4: Map Feature Dependencies to Task Dependencies

Features have dependencies (from requirements). Map these to tasks:
- If Feature A depends on Feature B, connect tasks only when the referenced
  task IDs exist in the loaded sprint outputs
- Do NOT invent inter-task dependencies or placeholder task IDs; preserve the
  explicit edges supplied by sprint workers
- Describe sprint-level ordering conceptually without fabricating task-level
  edges

### Step 5: Identify Cross-Sprint Dependencies

Examine all `depends_on` references:
- If a task in Sprint N depends on a task in any earlier sprint, mark it as a
  cross-sprint dependency and preserve the exact canonical IDs
- Verify that every such reference resolves to an emitted prior-sprint task;
  never rewrite it to a guessed or workstream-qualified ID
- Resolve each entry in a sprint output's `unresolved_dependencies` against
  the combined map — all sprint outputs are loaded here, so a prerequisite a
  parallel worker could not see may exist now; wire it as an explicit
  `depends_on` edge when it resolves, otherwise surface it in the report
  (e.g., Assumptions Made) as unresolved rather than inventing an ID
- These are the "critical path" candidates

### Step 6: Run Deterministic Graph Analysis

After Steps 1–5 have loaded and normalized the worker records, pass the compact
`{"tasks": [...]}` graph to `scripts/analyze_dependencies.py`. Resolve that
script from this skill's installed directory to a quoted absolute path; never
build the path from issue text or another untrusted value. Use `--input -` with
the JSON on stdin, or `--input` with a quoted absolute JSON path. The exact
schema and output are in [../references/dependency-analysis.md](../references/dependency-analysis.md).

- Exit 0: consume `critical_path.task_ids`, `critical_path.effort_days`,
  `bottlenecks`, and the empty `cycles` list from the canonical JSON result.
- Exit 2: stop before rendering `tasks.md`; surface the stable stderr
  diagnostic and the offending graph contract. Do not repair the result by
  guessing or continue with partial output.
- The helper owns path sums, tie-breaking, derived blocks, direct-dependent
  counts, and cycle membership. The resolver owns feature coverage, task
  explanations, mitigation/parallel-opportunity judgments, and rendering.

### Step 7: Use Deterministic Bottleneck Results

Use the helper's sorted `bottlenecks` objects directly. A bottleneck is a task
with at least five distinct direct downstream dependents (outdegree); five
prerequisites listed by one task and transitive descendants do not qualify.
Include the helper's `direct_dependents` count in the human risk-analysis
narrative without recounting it in prose.

### Step 8: Handle Cycle Results

The helper validates every node, including disconnected and rootless components,
and reports one deterministic directed cycle witness. A cycle error is fatal:
do not render `tasks.md`, and do not label downstream residue as cyclic. The
resolver may explain which explicit `depends_on` edge must be removed, but it
must not override the helper's witness or invent a replacement dependency.

### Step 9: Check Coverage

Verify:
- All features from the requirements have tasks in the sprints
- All tasks reference a feature
- No tasks are orphaned (every task should map back to the feature list)

### Step 10: Generate tasks.md

Create the final markdown file that will be checked into the repo:

```markdown
# Tasks — [Project Name]

Generated: [ISO timestamp]
Total Tasks: [X]
Total Effort: [X days]
Critical Path: [X days]
Sprints: [X]

## Summary

- **POC Duration**: [X sprints] ([X days])
- **MVP Duration**: [X sprints] ([X days])
- **Full Features Duration**: [X+ sprints] ([X+ days])
- **Total Effort**: [X dev-days]

## Risk Analysis

### Bottlenecks
- **[TASK_ID]**: Blocks [X tasks], [Y workers can't proceed]
  - Mitigation: Start early, allocate senior dev

### Critical Path
The longest dependency chain is [X days]:
1. [TASK_ID]: [Title] ([effort])
2. [TASK_ID]: [Title] ([effort])
3. ...

Any delay to a critical path task delays the entire project by the same amount.

### Assumptions Made
[List any assumptions if the PRD was ambiguous]

---

## Sprint 1: [Title]

**Duration**: [X weeks]
**Phase**: [POC|MVP|Full Features]
**Total Effort**: [X days]

### Workstreams

#### Project Setup
- Task 1.1
- Task 1.2

#### Backend
- Task 1.3
- Task 1.4

#### Frontend
- Task 1.5

### Tasks

### Task 1.1: Initialize project repository and CI/CD pipeline

**Description**: Set up the repo structure, package.json (or equivalent), and basic CI/CD workflow for automated testing and deployment.

**Acceptance Criteria**:
- [ ] Repository initialized with proper .gitignore and README stub
- [ ] GitHub Actions workflow (or equivalent) triggers on push to main
- [ ] Workflow runs linting and tests successfully
- [ ] Dev environment setup documented in README

**Effort**: 1 day

**Dependencies**: None

**Blocks**: Task 1.3, Task 1.5

**PRD Reference**: Foundation for [feature name]

---

[Continue for all tasks, organized by sprint]

---

## Dependency Matrix

| Task ID | Title | Sprint | Depends On | Blocks | Effort |
|---------|-------|--------|-----------|--------|--------|
| 1.1 | Initialize repo | 1 | None | 1.3, 1.5 | 1d |
| 1.3 | Create DB schema | 1 | 1.1 | 1.4, 2.1 | 1d |
[...]

---

## Execution Guidance

### Sprint 1 Execution Order

**Week 1**:
- Day 1: Start Task 1.1 (blocks others, do first)
- Day 1-2 (parallel): Once setup is done, start Task 1.3 and Task 1.5 in parallel

### Cross-Sprint Dependencies

**Sprint 1 → Sprint 2**:
- All Sprint 2 backend tasks depend on Sprint 1 data model tasks (Task 1.3)
- All Sprint 2 frontend tasks depend on Sprint 1 API design (Task 1.4)

Start Sprint 2 immediately after Sprint 1 is complete to maintain momentum.

---

## Validation Checklist

- [ ] All PRD requirements mapped to tasks
- [ ] Each task has clear acceptance criteria
- [ ] No circular dependencies
- [ ] Effort estimates sum correctly per sprint
- [ ] Critical path is realistic
- [ ] Cross-sprint dependencies are clear
- [ ] Ambiguities from requirements are documented

---

## Next Steps

1. **Review Sprint 1 tasks** with the team
2. **Assign developers** to workstreams based on availability
3. **Lock the API interface** (between backend and frontend) before Sprint 2 starts
4. **Monitor critical path** — any delay to critical tasks delays the project
5. **Re-evaluate after Sprint 1** — actual effort may differ from estimates; adjust Sprint 2+ scope if needed
```

## Output Format

A complete markdown file at the specified output path. This file should be ready to check into the repo and share with the team.

## Quality Checks

Before finalizing:
- [ ] `analyze_dependencies.py` exited 0 and its canonical JSON result was consumed
- [ ] No circular dependencies detected
- [ ] All tasks in dependency table
- [ ] Critical path identified and documented from `critical_path`
- [ ] Bottlenecks noted with mitigation from `bottlenecks`
- [ ] Cross-sprint dependencies clear
- [ ] Effort estimates within reason (1-3 days per task)
- [ ] All PRD features covered

## Error Handling

If circular dependencies are detected:
- STOP and report them clearly
- DO NOT produce tasks.md
- Return a detailed error message with:
  - Which tasks form the cycle
  - Why the cycle exists
  - Recommendation: which dependency to remove

If coverage gaps exist (PRD features not in tasks):
- Report which features are missing
- These are likely ambiguous in the PRD or need the sprint-planner to revisit scope

## Tips

- The tasks.md file is developer-facing. Write it to be clear, complete, and actionable.
- Include examples and guidance where possible.
- The critical path is the most important insight — highlight it prominently.
- Cross-sprint dependencies should be visualized clearly so dependencies between sprints are obvious.
