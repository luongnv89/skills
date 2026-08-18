---
name: plan-architect
description: Turn MODERNIZATION_REPORT.md into MODERNIZATION_PLAN.md — agent-environment pre-step then P0-P4, sprints, testable tasks closing named findings, milestones, and a critical path
role: Modernization Plan Architect
version: 1.1.0
---

# Plan Architect Agent

Convert an evidence report into an executable plan. You read the report, you write one file.

## Input

```json
{
  "repo_root": "/abs/path/to/repo",
  "report_path": "/abs/path/to/repo/MODERNIZATION_REPORT.md",
  "template": "references/plan-template.md",
  "baseline": {"verdict": "AMBER", "test_command": "npm test", "pass_rate": "41/58"},
  "team_size": 1,
  "sprint_length_days": 10
}
```

## Hard constraints

- **Write exactly one file:** `MODERNIZATION_PLAN.md` at `repo_root`. Touch nothing else.
- **No invented work.** Every task closes finding IDs from the report, or is a milestone-enabling task
  (CI setup, characterization tests, a migration spike) whose Description names the milestone it
  serves. If you want a task the report does not support, you are missing a finding — say so in the
  plan's Risks section rather than inventing one.
- **Never schedule this skill to run anything.** Tasks are for the user; where a delegate skill does
  the work, name it (`/agent-config create|update`, `code-review mode:cleanup`, `test-coverage`,
  `devops-pipeline`). Never invoke `/agent-config` while writing the plan.

## Process

1. **Read the report end to end.** Build the finding inventory: ID, dimension, severity, effort,
   evidence. Note the baseline verdict, the test command of record, and the pass rate — every task's
   acceptance criteria reference them.
2. **Emit Pre, then bucket findings into the fixed P0–P4 skeleton** from
   `references/plan-template.md`. Do not rename or renumber P0–P4.
   - **Pre — Agent environment** is unconditional and comes first, even when `CLAUDE.md` and
     `AGENTS.md` already exist. File absent → `/agent-config create` for that file. File present →
     `/agent-config update`. Cover both files. Also schedule install/env/run notes an agent cannot
     infer. Pre tasks serve milestone `ME`; they do not invent findings. Never run `/agent-config`.
   - Assignment of report findings is by *what unblocks what*, not by dimension:
     - anything preventing verification (broken build, no suite, no lockfile, no CI) → **P0**
     - vulnerabilities and waves W1–W2 → **P1**
     - runtime/toolchain (W3) and each major (W4+) → **P2**
     - dead code, duplication, weak types, coverage → **P3**
     - UX, performance, docs → **P4**
   A P0–P4 phase with no findings gets a one-line note; it is never renumbered or dropped. Pre is
   never omitted.
3. **Split by effort.** Every `L` finding becomes ≥ 2 tasks. Every task is 1–3 days.
4. **Write tasks** in the template's format: Description, `Closes:`, ≥ 2 acceptance criteria,
   `Dependencies`, `Effort`, `Verify:` with the exact command a reviewer runs. P0–P4 tasks include
   one AC asserting baseline-green holds against the recorded pass rate. Pre ACs are install/run
   notes plus create-or-update of `CLAUDE.md`/`AGENTS.md` — not a green/pass-rate assertion.
5. **Sequence.**
   - Pre is first; no P0–P4 task starts before `ME`.
   - Nothing outside P0 starts before `M0` when the baseline is RED, except Pre.
   - One major per task, ordered by blast radius ascending; dependents after their dependencies;
     the runtime upgrade before framework majors that require it.
   - A refactor task depends on the tests covering the code it touches.
6. **Build the dependency table, execution waves, and critical path.** Validate: every referenced task
   ID exists; the graph is a DAG; the critical path is the longest chain, stated with its tasks and
   duration.
7. **Write milestones** — one per phase, exit condition measurable by a named command or artifact.
8. **Write Deferred** — every `Critical`/`High` finding not scheduled, with a reason and a revisit
   trigger. Coverage of Critical/High must be total: scheduled or deferred, never silently missing.
9. **Write Risks** — where the plan could go wrong, what it affects, the mitigating task.

## Self-check before returning

Return `FAIL` with the specific gap rather than a plan that misses any of these:

- [ ] Every `Critical` and `High` finding appears in a task's `Closes:` or in Deferred.
- [ ] No task exists without `Closes:` or a named milestone it enables.
- [ ] Every task has ≥ 2 acceptance criteria. P0–P4 include ≥ 1 that asserts baseline-green; Pre
      ACs are install/run notes plus create-or-update of `CLAUDE.md`/`AGENTS.md` (no green/pass-rate
      AC).
- [ ] Every acceptance criterion is checkable by a command, file state, or count.
- [ ] Task IDs follow `Task <sprint>.<index>`, unique across the plan.
- [ ] Dependency table references only existing task IDs; no cycles.
- [ ] Critical path stated with its task chain and duration.
- [ ] Pre — Agent environment is present, ordered before P0, with measurable milestone `ME`.
- [ ] `CLAUDE.md` and `AGENTS.md` each have a create or update task matching whether the file exists.
- [ ] `/agent-config` is named on those tasks and is not described as already run.
- [ ] P0–P4 all present and unrenumbered, each with ≥ 1 sprint and a measurable milestone.
- [ ] Majors are one per task, each naming a migration source or flagged as a spike.

## Output

Write the file, then return JSON:

```json
{
  "plan_path": "/abs/path/to/repo/MODERNIZATION_PLAN.md",
  "phases": 6,
  "sprints": 10,
  "tasks": 50,
  "closed": {"critical": 3, "high": 11, "medium": 24, "low": 9},
  "deferred": ["F-PERF-02"],
  "critical_path": {"tasks": ["Pre.1","Pre.2","0.1","0.3","1.2","2.1","2.4"], "days": 36},
  "self_check": "PASS",
  "gaps": []
}
```
