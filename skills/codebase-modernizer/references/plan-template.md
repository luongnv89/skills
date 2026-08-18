# MODERNIZATION_PLAN.md Template

Written at the target repo root in Phase 4, derived entirely from `MODERNIZATION_REPORT.md`. The task
format matches `tasks-generator` so the plan interoperates with that skill; the additions are the
`Closes:` line and the baseline-green acceptance criterion.

## The fixed phase skeleton

Every plan starts with an unconditional **Pre — Agent environment** step, then phases **P0–P4** in
this order. Do not rename, drop, or renumber P0–P4 to make room for Pre. A P0–P4 phase with no
findings collapses to a one-line "nothing found in this phase" note — it is never renumbered or
dropped, because the ordering is the argument: you cannot verify an upgrade without a baseline, and
you should not modernize on top of a known vulnerability. Pre is never collapsed away.

| Phase | Goal | Exit milestone |
|---|---|---|
| **Pre Agent environment** | project env an AI agent can use autonomously; `CLAUDE.md` and `AGENTS.md` created or improved | `ME` — both files exist at the repo root, document the recorded build/test commands, and are scheduled via `/agent-config` (not written during the audit) |
| **P0 Stabilize** | build green, tests runnable, lockfile committed, CI running the suite | `M0` — baseline-green reproducible in CI from a clean checkout |
| **P1 Secure & Patch** | close vulnerabilities, ship waves W1–W2 | `M1` — zero known High/Critical advisories; patch/minor current |
| **P2 Modernize** | runtime/toolchain upgrade (W3), then one major per task (W4+) | `M2` — every major current or deferred with written rationale |
| **P3 Clean & Harden** | dead code, duplication, weak types, coverage to target | `M3` — coverage ≥ target; duplication below threshold; zero `any` in the named scope |
| **P4 Polish** | UI/UX, performance, docs alignment | `M4` — UX findings closed; perf budget met; docs match code |

### Pre — Agent environment — required, not optional

Pre is planned work, never applied by this skill. It exists so a later agent can execute P0–P4
without unwritten human context. Put the detailed tasks here; do not invent `F-*` findings for it —
Pre tasks are milestone-enabling and serve `ME`.

| Rule | How to fill it |
|---|---|
| Always present | Emit Pre even when `CLAUDE.md` and `AGENTS.md` already exist. Presence is not done. |
| Create vs improve | File **absent** → task names `/agent-config create` for that file. File **present** → task names `/agent-config update` (improve against agent-config's checklists). Cover **both** files, independently. |
| Broader env | Also schedule whatever an agent needs to install, configure, and run the repo: toolchain install, required env vars / `.env.example`, the recorded build and test commands, non-obvious repo etiquette. Fold these into Pre tasks; do not push them into P0. |
| Never invoke | Do **not** run `/agent-config` (or write `CLAUDE.md` / `AGENTS.md`) during the audit. Name the exact invocation on the task's `Verify:` line. |
| IDs | Sprint **Pre**, tasks `Task Pre.<index>` so P0 keeps Sprint 0 / `Task 0.<index>`. |
| Order | `ME` precedes every P0–P4 task. On a RED baseline, Pre is the only work allowed before `M0`. |
| RED baseline | Pre does **not** assert a green build or suite. Restore-green stays on P0 / Sprint 0. Pre ACs only require documented install/run notes and create-or-update of `CLAUDE.md` / `AGENTS.md`. |

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

Every P0–P4 task's acceptance criteria include *"`<test command>` passes at ≥ the recorded rate"*.
On a RED baseline, Pre omits that assertion — restoring green is P0 / Sprint 0, and Pre must
finish first. Pre ACs only require documented install/run notes and create-or-update of
`CLAUDE.md` / `AGENTS.md`.

## At a glance

| Phase | Sprints | Tasks | Closes | Milestone |
|---|---|---|---|---|
| Pre Agent environment | 1 | 3 | — (enables ME) | ME |
| P0 Stabilize | 1 | 6 | 4 Critical | M0 |
| P1 Secure & Patch | 2 | 11 | 3 Critical, 8 High | M1 |
| P2 Modernize | 3 | 14 | 6 High | M2 |
| P3 Clean & Harden | 2 | 12 | 18 Medium | M3 |
| P4 Polish | 1 | 8 | 9 Low | M4 |

**Critical path:** Task Pre.1 → 0.1 → 0.3 → 1.2 → 2.1 → 2.4 (<N> days). Nothing in P0 starts before ME. Nothing in P2 starts before M0.

## Phase Pre — Agent environment

**Goal:** <one line> · **Milestone ME:** <CLAUDE.md and AGENTS.md created or improved; recorded build/test commands documented>

### Sprint Pre — Agent-runnable environment

#### Task Pre.1: <Make the project environment agent-runnable>

**Description**: Install/configure notes, env vars, and the recorded build/test commands so an agent can proceed without unwritten context. Serves milestone ME.

**Closes**: — (milestone-enabling: ME)

**Acceptance Criteria**:
- [ ] Written notes cover toolchain install, required env vars / `.env.example`, and the recorded build/test commands
- [ ] A later agent can follow those notes from project files alone (commands may still be RED; restoring green is P0)

**Dependencies**: None

**Effort**: S | M | L (1–3 days)

**Verify**: `<the exact command a reviewer runs to confirm this task is done>`

#### Task Pre.2: <Create or improve CLAUDE.md>

**Description**: File absent → `/agent-config create` targeting `CLAUDE.md`. File present → `/agent-config update`. Serves milestone ME. Do not run the skill while planning.

**Closes**: — (milestone-enabling: ME)

**Acceptance Criteria**:
- [ ] `CLAUDE.md` exists at the repo root (create via `/agent-config` if absent)
- [ ] `CLAUDE.md` names the recorded build/test commands (improve via `/agent-config update` if already present)

**Dependencies**: Pre.1

**Effort**: S

**Verify**: run `/agent-config create` (or `update` if the file exists) targeting `CLAUDE.md`

#### Task Pre.3: <Create or improve AGENTS.md>

**Description**: File absent → `/agent-config create` targeting `AGENTS.md`. File present → `/agent-config update`. Serves milestone ME. Do not run the skill while planning.

**Closes**: — (milestone-enabling: ME)

**Acceptance Criteria**:
- [ ] `AGENTS.md` exists at the repo root (create) or is improved against agent-config checklists (update)
- [ ] `AGENTS.md` names the recorded build/test commands

**Dependencies**: Pre.1

**Effort**: S

**Verify**: run `/agent-config create` (or `update` if the file exists) targeting `AGENTS.md`

## Phase P0 — Stabilize

**Goal:** <one line> · **Milestone M0:** <measurable exit condition>

### Sprint 0 — <name>

#### Task 0.1: <Action-oriented title>

**Description**: What and why, referencing the finding.

**Closes**: `F-TEST-01`, `F-CI-02`

**Acceptance Criteria**:
- [ ] <specific, checkable condition — a command, a file state, or a count>
- [ ] `<test command>` passes at ≥ 41/58 (baseline-green holds)

**Dependencies**: Pre.2, Pre.3

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
| Pre.1 | — | Pre.2, Pre.3, 0.1 | W0 |
| 0.1 | Pre.2, Pre.3 | 0.3, 1.1 | W1 |
| 1.1 | 0.1 | 2.1 | W2 |

## Execution waves

Tasks with no unmet dependencies, grouped by the round they can start in. Everything in a wave can
run in parallel.

| Wave | Tasks |
|---|---|
| 1 | Pre.1 |
| 2 | Pre.2, Pre.3 |
| 3 | 0.1, 0.2, 0.4 |
| 4 | 0.3, 0.5 |

## Milestones

| ID | Phase | Exit condition (measurable) | Verify with |
|---|---|---|---|
| ME | Pre | `CLAUDE.md` and `AGENTS.md` exist (created or improved); recorded build/test commands documented | `test -f CLAUDE.md && test -f AGENTS.md` |
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
- ≥ 2 acceptance criteria per task. P0–P4 tasks include one that asserts baseline-green still holds.
  **Pre is exempt from the green-build/suite AC when the baseline is RED** — restoring that is P0 /
  Sprint 0, and no P0 work may start before `ME`. Pre ACs only require documented install/run notes
  and create-or-update of `CLAUDE.md` / `AGENTS.md`.
- **When there is no test command at audit time** (RED baseline, no suite — a supported case), the
  baseline assertion falls back to the build: **P0–P4** tasks scheduled *before* the P0 suite-creation
  task assert "`<build command>` succeeds"; every task *after* it asserts the suite that task
  established. Do not apply this fallback to Pre. State the substitution once at the top of the
  plan so the criteria are not silently weaker.
- Each criterion is checkable by a command, a file state, or a count — never "code is cleaner".
- The `Verify:` line gives the exact command a reviewer runs.

**Dependency upgrade tasks**
- One task per major bump. Never batch majors, and never mix a major with the patch/minor batch.
- Each major task names its **migration source** (Context7 doc, upstream guide, or CHANGELOG). If none
  was retrievable, the task's first acceptance criterion is producing it — labelled a spike.
- Order majors by blast radius ascending; a dependent's bump comes after its dependency's.
- Runtime/toolchain upgrade (W3) precedes framework majors that require it.

**Delegate tasks**
- The audit deliberately did not run the skills that write (`/agent-config create|update`,
  `code-review` modes `clean` and `cleanup`, `test-coverage`, `devops-pipeline`, `security-setup`,
  `doc-manager`). Where one of them does a task's work, the task names it and its exact invocation —
  e.g. `Verify: run /agent-config update targeting CLAUDE.md` or
  `Verify: run /test-coverage on src/payments, then npm test`.
- The task still carries its own acceptance criteria. "Ran the skill" is not a criterion; what the
  skill was supposed to achieve is.

**Structure**
- Pre uses `Task Pre.<index>` in Sprint Pre. After that, task IDs are `Task <sprint>.<index>`; sprint
  numbering runs continuously across P0–P4 (Sprint 0 in P0, Sprint 1–2 in P1, …) so IDs stay unique.
- The dependency table references only task IDs that exist, and contains no cycles.
- The critical path is stated explicitly with its task chain and duration.
- Every phase has a milestone whose exit condition is measurable by a stated command or artifact.

**Sequencing that must hold**
- Pre is first. No P0–P4 task starts before `ME`.
- Nothing outside P0 starts before `M0` when the baseline is RED, except Pre (which precedes P0).
- Refactor tasks in P3 depend on the tests that cover the code they touch.
- `code-review` mode `cleanup` appears as a P3 task the user runs — this skill never runs it.
- `/agent-config create|update` appears as Pre tasks the user runs — this skill never runs it.
