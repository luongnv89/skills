# MODERNIZATION_PLAN.md Template

Written at the target repo root in Phase 4, derived entirely from `MODERNIZATION_REPORT.md`. The task
format matches `tasks-generator` so the plan interoperates with that skill; the additions are the
`Closes:` line and the baseline-green acceptance criterion.

## The fixed phase skeleton

Phases are always P0–P4 in this order. A phase with no findings collapses to a one-line "nothing
found in this phase" note — it is never renumbered or dropped, because the ordering is the argument:
you cannot verify an upgrade without a baseline, and you should not modernize on top of a known
vulnerability.

| Phase | Goal | Exit milestone |
|---|---|---|
| **P0 Stabilize** | build green, tests runnable, lockfile committed, CI running the suite | `M0` — baseline-green reproducible in CI from a clean checkout |
| **P1 Secure & Patch** | close vulnerabilities, ship waves W1–W2 | `M1` — zero known High/Critical advisories; patch/minor current |
| **P2 Modernize** | runtime/toolchain upgrade (W3), then one major per task (W4+) | `M2` — every major current or deferred with written rationale |
| **P3 Clean & Harden** | dead code, duplication, weak types, coverage to target | `M3` — coverage ≥ target; duplication below threshold; zero `any` in the named scope |
| **P4 Polish** | UI/UX, performance, docs alignment | `M4` — UX findings closed; perf budget met; docs match code |

### Binding M3 and M4 — required, not optional

"Coverage ≥ target" is not a milestone until *target* is a number. Derive each from the Phase 0
baseline; never leave a placeholder in the written plan:

| Value | How to bind it |
|---|---|
| Coverage target | baseline coverage + 20 percentage points, floored at 60%. If coverage was **Not Assessed**, the target is "a coverage tool is configured and reports a number" — measurement before improvement |
| Duplication threshold | baseline duplication if a tool measured it; otherwise "no logic block repeated ≥ 3 times survives in the `DEAD` findings" |
| Weak-type scope | the specific directories where `DEAD` found `any`/`interface{}` — name them |
| Perf budget | the metric a `PERF` finding cites (bundle size, p95 latency, query count) with its measured value as the ceiling. If `PERF` found nothing measurable, drop the perf clause from M4 rather than inventing a budget |

If a value cannot be bound from evidence, say so in the milestone and make binding it the phase's
first task. An unbindable milestone is a planning failure, not a formatting one.

Sprint sizing: 5–10 tasks per sprint, one to two weeks of work for one developer. Split a phase into
multiple sprints when it exceeds that; a phase always has at least one sprint.

## Template

````markdown
# Modernization Plan — <project name>

Derived from [`MODERNIZATION_REPORT.md`](./MODERNIZATION_REPORT.md) · **Baseline at audit:** <verdict>
**Test command of record:** `<command>` · **Pass rate at audit:** `<41/58>`

Every task's acceptance criteria include *"`<test command>` passes at ≥ the recorded rate"*. That is
what makes this plan testable rather than aspirational.

## At a glance

| Phase | Sprints | Tasks | Closes | Milestone |
|---|---|---|---|---|
| P0 Stabilize | 1 | 6 | 4 Critical | M0 |
| P1 Secure & Patch | 2 | 11 | 3 Critical, 8 High | M1 |
| P2 Modernize | 3 | 14 | 6 High | M2 |
| P3 Clean & Harden | 2 | 12 | 18 Medium | M3 |
| P4 Polish | 1 | 8 | 9 Low | M4 |

**Critical path:** Task 0.1 → 0.3 → 1.2 → 2.1 → 2.4 (<N> days). Nothing in P2 starts before M0.

## Phase P0 — Stabilize

**Goal:** <one line> · **Milestone M0:** <measurable exit condition>

### Sprint 0 — <name>

#### Task 0.1: <Action-oriented title>

**Description**: What and why, referencing the finding.

**Closes**: `F-TEST-01`, `F-CI-02`

**Acceptance Criteria**:
- [ ] <specific, checkable condition — a command, a file state, or a count>
- [ ] `<test command>` passes at ≥ 41/58 (baseline-green holds)

**Dependencies**: None

**Effort**: S | M | L (1–3 days)

**Verify**: `<the exact command a reviewer runs to confirm this task is done>`

#### Task 0.2: …

## Phase P1 — Secure & Patch
## Phase P2 — Modernize
## Phase P3 — Clean & Harden
## Phase P4 — Polish

## Dependency table

| Task | Depends on | Blocks | Wave |
|---|---|---|---|
| 0.1 | — | 0.3, 1.1 | W0 |
| 1.1 | 0.1 | 2.1 | W1 |

## Execution waves

Tasks with no unmet dependencies, grouped by the round they can start in. Everything in a wave can
run in parallel.

| Wave | Tasks |
|---|---|
| 1 | 0.1, 0.2, 0.4 |
| 2 | 0.3, 0.5 |

## Milestones

| ID | Phase | Exit condition (measurable) | Verify with |
|---|---|---|---|
| M0 | P0 | clean checkout → build + suite green in CI | CI run link / `<command>` |
| M1 | P1 | `npm audit --json` reports 0 high+ advisories | `<command>` |

## Deferred and out of scope

Findings deliberately not scheduled, each with a reason. A deferred item is a decision, not an
oversight — this section is what makes the plan reviewable.

| ID | Severity | Why deferred | Revisit when |
|---|---|---|---|

## Risks

| Risk | Affects | Mitigation |
|---|---|---|
| No test coverage on <module>; refactor there is unverifiable | Tasks 3.2–3.4 | Task 3.1 adds characterization tests first |
````

## Rules for filling it

**Traceability**
- Every `Critical` and `High` finding is closed by ≥ 1 task, or appears in **Deferred** with a reason.
- Every task has a `Closes:` line naming finding IDs, or is a milestone-enabling task (CI setup,
  characterization tests) whose Description says which milestone it serves.
- No task invents work absent from the report.

**Testability**
- ≥ 2 acceptance criteria per task; at least one asserts baseline-green still holds.
- **When there is no test command at audit time** (RED baseline, no suite — a supported case), the
  baseline assertion falls back to the build: tasks scheduled *before* the P0 suite-creation task
  assert "`<build command>` succeeds"; every task *after* it asserts the suite that task established.
  State this substitution once at the top of the plan so the criteria are not silently weaker.
- Each criterion is checkable by a command, a file state, or a count — never "code is cleaner".
- The `Verify:` line gives the exact command a reviewer runs.

**Dependency upgrade tasks**
- One task per major bump. Never batch majors, and never mix a major with the patch/minor batch.
- Each major task names its **migration source** (Context7 doc, upstream guide, or CHANGELOG). If none
  was retrievable, the task's first acceptance criterion is producing it — labelled a spike.
- Order majors by blast radius ascending; a dependent's bump comes after its dependency's.
- Runtime/toolchain upgrade (W3) precedes framework majors that require it.

**Delegate tasks**
- The audit deliberately did not run the six skills that write (`code-review` modes `clean` and
  `cleanup`, `test-coverage`, `devops-pipeline`, `security-setup`, `doc-manager`). Where one of them
  does a task's work, the task names it and its exact invocation — e.g.
  `Verify: run /test-coverage on src/payments, then npm test`.
- The task still carries its own acceptance criteria. "Ran the skill" is not a criterion; what the
  skill was supposed to achieve is.

**Structure**
- Task IDs are `Task <sprint>.<index>`; sprint numbering runs continuously across phases (Sprint 0 in
  P0, Sprint 1–2 in P1, …) so IDs stay unique.
- The dependency table references only task IDs that exist, and contains no cycles.
- The critical path is stated explicitly with its task chain and duration.
- Every phase has a milestone whose exit condition is measurable by a stated command or artifact.

**Sequencing that must hold**
- Nothing outside P0 starts before `M0` when the baseline is RED.
- Refactor tasks in P3 depend on the tests that cover the code they touch.
- `code-review` mode `cleanup` appears as a P3 task the user runs — this skill never runs it.
