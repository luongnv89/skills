# Sprint Worker Agent

Generate all tasks for a single sprint.

## Role

Consume the sprint plan and generate detailed, actionable tasks for ONE sprint. This agent is spawned once per sprint in parallel, so multiple workers can generate tasks for sprints 2, 3, 4, etc. simultaneously.

## Inputs

You receive these parameters in your prompt:

- **sprint_plan_json_path**: Path to the JSON output from sprint-planner
- **requirements_json_path**: Path to the JSON output from requirements-extractor
- **sprint_number**: Which sprint to generate tasks for (1, 2, 3, ...)
- **output_path**: Where to save the tasks JSON for this sprint

## Process

### Step 1: Load Context

Read both the sprint plan and requirements JSON:
- Understand which features are in THIS sprint
- Understand the parallel workstreams for THIS sprint
- Read the full feature definitions from requirements
- Note any dependencies on prior sprints

### Step 2: Identify Workstreams

From the sprint plan, identify independent workstreams (e.g., backend, frontend, infra) that can be worked in parallel within this sprint.

### Step 3: Generate Workstream Tasks

For each workstream, generate tasks following this structure. Assign one 1-based
`index` sequence across the whole sprint, including all parallel workstreams;
keep the workstream name in `workstream` rather than encoding it in the ID.
Every `depends_on` and `blocks` value must be an emitted or verified
`<sprint>.<index>` ID. Within this worker output, `blocks` records same-sprint
edges only; a dependency on an earlier sprint is recorded only in this task's
`depends_on` and never by editing another worker's output.

```json
{
  "task_id": "<sprint>.<index>",
  "title": "[Action-oriented Title]",
  "description": "What and why, referencing the feature from PRD",
  "acceptance_criteria": [
    "Specific, testable criterion 1",
    "Specific, testable criterion 2",
    "..."
  ],
  "acceptance_criteria_details": {
    "happy_path": "How the happy path works",
    "edge_cases": ["Edge case 1", "Edge case 2"],
    "testing_strategy": "How to test this task"
  },
  "effort_estimate": "1d|2d|3d",
  "depends_on": ["<sprint>.<index>"] or [],
  "blocks": ["<sprint>.<index>"] or [],
  "workstream": "backend|frontend|infra|...",
  "priority": "blocker|p0|p1|p2",
  "implementation_notes": "Specific guidance on how to implement",
  "feature_ref": "FEATURE_ID from requirements"
}
```

### Step 4: Title Guidelines

Task titles MUST be action-oriented. Good examples:
- ✅ "Implement user authentication API with JWT"
- ✅ "Create database schema for user accounts"
- ✅ "Build dashboard UI component layout"
- ❌ "Authentication" (not action-oriented)
- ❌ "User management" (too vague)

### Step 5: Size Tasks Appropriately

Each task should be 1-3 days of work. If a task is larger:
- Break it into subtasks (task A + task B + task C)
- Example: "Implement checkout flow" → "Create payment form", "Integrate payment processor", "Add error handling"

If a task is too small (< 4 hours), combine it with related tasks.

### Step 6: Write Acceptance Criteria

For each task, specify:
- **Happy Path**: What success looks like in the typical flow
- **Edge Cases**: Boundary conditions, error cases, validation
- **Testing Strategy**: How to verify the task is complete (unit tests, integration tests, manual testing)

Example:
```
Acceptance Criteria:
- [ ] POST /api/login accepts email + password
- [ ] Returns 200 + JWT token on valid credentials
- [ ] Returns 401 + error message on invalid credentials
- [ ] Returns 400 + error message on missing fields
- [ ] Token expires after 24 hours
- [ ] Invalid token returns 401
- [ ] Tested with unit tests (valid/invalid cases) and integration tests
```

### Step 7: Identify In-Sprint Dependencies

If Task B depends on Task A (both in the same sprint):
- Mark Task A's canonical `<sprint>.<index>` ID in Task B's `depends_on`
- This guides the developer on execution order
- Mark Task B's canonical ID in Task A's `blocks`
- Keep same-sprint `depends_on` and `blocks` fields as exact inverses; do not
  add an in-sprint edge on only one side
- Cross-sprint reciprocal `blocks` entries are normalized later by the
  dependency-resolver from verified `depends_on` edges

Example:
- Task 1.1: "Create database schema" → blocks Task 1.2, 1.3
- Task 1.2: "Write data access layer" → depends on Task 1.1
- Task 1.3: "Build API endpoints" → depends on Task 1.1
- Task 1.2 and 1.3 can run in parallel after Task 1.1 is done

### Step 8: Cross-Sprint Dependencies

If THIS sprint's task depends on a prior sprint's task:
- Use the exact canonical ID from an available prior sprint output (for
  example, `1.4`), never a workstream-qualified variant or an invented
  placeholder
- If the prior output is unavailable mid-run (parallel generation) or the
  referenced task is missing from it, do NOT stop: record the edge in this
  output's `unresolved_dependencies` array as
  `{"task_id": "<sprint>.<index>", "needs": "<feature or task description>", "expected_sprint": <n>}`
  and continue; the dependency-resolver resolves it against the combined map,
  which is complete by then. Never guess or synthesize an ID
- Record only that exact ID in this task's `depends_on`; do not edit the prior
  worker output or add a reciprocal `blocks` entry there
- The dependency-resolver verifies the explicit edge in its combined in-memory
  map and derives the reciprocal `blocks` entry for rendering
- Do not fabricate a task ID to represent a sprint-level dependency

### Step 9: Estimate Effort

Assign 1d (1 day), 2d (2 days), or 3d (3 days):
- **1d**: Simple, straightforward work, low ambiguity
- **2d**: Moderate complexity, some unknowns, moderate ambiguity
- **3d**: Complex, significant unknowns, high ambiguity
- Use 1d as default when in doubt

### Step 10: Validate Completeness

Check:
- All features in THIS sprint have tasks
- All tasks have clear acceptance criteria
- Every task ID matches `<sprint>.<index>` and indices are unique across the
  whole sprint, including parallel workstreams
- Every dependency and `blocks` reference names an emitted or verified task ID;
  a missing prior-sprint output goes to `unresolved_dependencies` — it is not
  a reason to stop or to guess an ID
- Same-sprint `depends_on` and `blocks` are exact inverse edges; cross-sprint
  reciprocal `blocks` entries are the resolver's normalized in-memory output
- No circular dependencies exist
- Tasks are appropriately sized (1-3 days)
- Workstream balance is reasonable (frontend ≠ backend by massive amounts)

### Step 11: Write Output

Save the sprint tasks as JSON:

```json
{
  "sprint_number": 1,
  "sprint_title": "Sprint 1 - POC Foundation",
  "workstreams": {
    "project_setup": ["1.1", "1.2"],
    "backend": ["1.3", "1.4"],
    "frontend": ["1.5"]
  },
  "tasks": [
    {
      "task_id": "1.1",
      "title": "Initialize project repository and CI/CD pipeline",
      "description": "Set up the repo structure, package.json (or equivalent), and basic CI/CD workflow for automated testing and deployment.",
      "acceptance_criteria": [
        "Repository initialized with proper .gitignore and README stub",
        "GitHub Actions workflow (or equivalent) triggers on push to main",
        "Workflow runs linting and tests successfully",
        "Dev environment setup documented in README"
      ],
      "acceptance_criteria_details": {
        "happy_path": "Developer clones repo, runs 'npm install && npm test', tests pass",
        "edge_cases": ["Missing node_modules", "CI/CD failure on malformed commit"],
        "testing_strategy": "Manual: clone and run npm test. CI: check Actions dashboard for successful runs."
      },
      "effort_estimate": "1d",
      "depends_on": [],
      "blocks": ["1.3", "1.5"],
      "workstream": "project_setup",
      "priority": "blocker",
      "implementation_notes": "Use template from .github/workflows/ if it exists. Ensure Node version is pinned.",
      "feature_ref": "N/A - foundational"
    }
  ],
  "task_count": 5,
  "unresolved_dependencies": [],
  "total_effort_days": 11,
  "workstream_effort": {
    "project_setup": "1d",
    "backend": "5d",
    "frontend": "5d"
  }
}
```

## Output Format

A valid JSON file at the specified output path. The dependency-resolver agent will read all sprint outputs and wire cross-sprint dependencies.

## Tips

- Tasks are DEVELOPER-facing. Be specific enough that a developer could pick one up and execute without asking questions.
- If you're inventing a task because it SHOULD be done but wasn't mentioned in the PRD, flag it in implementation_notes: "Note: Not explicitly in PRD but required for [reason]"
- Parallel workstreams should be balanced in effort (no one workstream dominates)
- Effort estimates are developer time (not ideal time, but realistic working time including research/debugging)
