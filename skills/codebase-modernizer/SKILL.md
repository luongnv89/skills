---
name: codebase-modernizer
description: "Audit a stale, inherited, or messy codebase — deps, bugs, security, tests, CI, docs, UI/UX — then emit a phased, testable modernization plan. Read-only: plans upgrades, never applies them. Not for single-PR review, PRD-to-tasks, or UX-only audits."
license: MIT
effort: max
metadata:
  version: 1.3.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
  architecture: "orchestrator (baseline gate → parallel dimension audits → evidence report → phased sprint plan → validation)"
---

# Codebase Modernizer

For a codebase you are returning to after a long gap, or one that has drifted through many
unoptimized changes. It audits every applicable dimension, then converts the findings into a
**phased, sprint-sized, testable plan** for a better, up-to-date version.

Produces exactly two files in the target repo root:

| File | Contents |
|---|---|
| `MODERNIZATION_REPORT.md` | Baseline evidence + every finding, severity-ranked, each citing `path:line` |
| `MODERNIZATION_PLAN.md` | Phases → sprints → tasks → milestones, every task closing named findings |

## Read-only contract

This skill **never modifies source code, dependencies, lockfiles, or configuration** — no tracked
file's content changes. On a clean tree that is `git diff --stat` empty. On a stale, already-dirty
tree, `git status --porcelain` and `git diff` after the run must match a snapshot taken before it
(declared artifacts set aside). Beyond the two reports, only two kinds of *new* file may appear,
both enumerated in the report's Artifacts section: a **declared delegate artifact**
(`CODE_REVIEW.md`, from `code-review` mode `review`) and **probe byproducts** (build dirs such as
`obj/`, `.dart_tool/`, `target/`, `.gradle/`). Nothing else.

- Dependency upgrades become **planned tasks with migration steps** — never `npm update`, `ncu -u`,
  `cargo update`, `poetry update`, or any equivalent. A blind bulk upgrade on a stale tree produces a
  broken build and an unreviewable diff, which is exactly what the plan exists to prevent.
- Refactors, dead-code removal, and test generation are **planned**, not applied. Applying them is
  the delegate skills' job, run later against the plan.
- Agent environment files (`CLAUDE.md`, `AGENTS.md`) are **planned** via `/agent-config create` or
  `/agent-config update` in the plan's Pre step — never created or rewritten during the audit.
- If the user asks mid-run to start fixing, finish the report and plan first, then hand off to the
  delegate skill named in that task.

## Dependency Preflight (mandatory)

This skill **invokes** two other skills during the audit: `code-review` (modes `review` and `perf`)
and `dont-make-me-think` (`UX`). Resolve both **before Phase 0**, the first phase that probes
anything:

```bash
npm install -g agent-skill-manager                                     # only if `asm` is missing
asm install code-review -p claude --yes
asm install dont-make-me-think -p claude --yes
asm list -p claude --json | grep -E 'code-review|dont-make-me-think'   # verify
```

`-p claude` is not decoration: `asm install` refuses to guess a provider non-interactively, `--yes`
does not cover that choice, and naming the same provider in the verification stops an install under
a different tool from reporting success.

A dependency that stays missing is **fail-soft**, not fatal: record that dimension **Not Assessed —
skill unavailable**, continue, and name it in Limitations. The six *inline* dimensions below name
their skill in a plan task and never invoke it, so they need no preflight.

## Leading terms

Used throughout this skill and its references with these exact meanings:

- **baseline-green** — the recorded state where the project builds and its test suite runs to a known
  pass rate. Established in Phase 0; every P0–P4 task must assert it still holds. Pre is exempt when
  the baseline is RED — restore-green stays on P0 / Sprint 0.
- **finding record** — one normalized issue row with a stable **finding ID** (`F-<DIM>-<NNN>`, e.g.
  `F-DEP-003`). The report lists them; the plan's tasks close them by ID.
- **Not Assessed** — an explicit report verdict for a dimension that could not be checked (no tool,
  no UI, no network). Never replaced by a guess.
- **fail-soft** — probe whether a tool exists before using it; on absence, record **Not Assessed**
  with the reason and continue. A missing tool never aborts the run.
- **upgrade wave** — one batch of dependency upgrades that ships and is verified together:
  security patches → patch/minor batch → each major on its own.

## Repo Sync Before Edits (mandatory)

**Default: do not sync.** This skill merges nothing and commits nothing — it writes two untracked
report files. Rebasing mid-audit can pull in a year of upstream commits, invalidating every
`path:line` citation and the recorded SHA. Audit the tree as you found it.

**Sync only when the user asks for the reports committed or pushed.** Then sync at the *start* of
Phase 3, after the audit is recorded; because HEAD moves, re-record the commit SHA and re-verify
every citation. One that no longer resolves means the audit is stale — say so and re-run.

When syncing, sync the current branch with remote — stash first if the tree is not clean:

```bash
git stash push -u -m "pre-sync"   # only when `git status --porcelain` is non-empty
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop                     # only if you stashed
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user
before continuing. A dirty tree is common on a neglected repo — never discard uncommitted work.

## Scope and branch selection

Resolve all nine branches in `references/scope-detection.md` **before Phase 0**. Each is a real
branch in the workflow, not a preference. Two change what is obtainable at all, so check them
early:

- **No Bash** → no baseline is obtainable; every Phase 0 probe is a shell command. Record the whole
  baseline **Not Assessed — no shell**, audit only what static reading supports, and never fabricate
  a verdict.
- **No UI detected** → UI/UX dimensions are **Not Assessed — no UI detected**. Never invent UX
  findings.

Never assume the permissive side of a branch you did not check.

## What this skill owns, and what it delegates

The finding-generators already exist. This skill's own contribution is **dependency and runtime
currency**, the **baseline gate**, and the **audit → plan bridge**. Everything else is delegated.

| Dim | Dimension | Audited by | Skip when |
|---|---|---|---|
| `DEP` | Dependency + runtime currency | **this skill** — `references/dependency-audit.md`, `scripts/dep_scan.sh` | no manifest found |
| `BUG` | Bugs, security holes, quality | **invoke** `code-review` mode `review` | never |
| `PERF` | Bottlenecks, leaks, algorithmic waste | **invoke** `code-review` mode `perf` | never |
| `UX` | Usability and UI flow | **invoke** `dont-make-me-think` | no UI detected |
| `CLEAN` | Readability vs Clean Code standards | inline — plan task runs `code-review` mode `clean` | never |
| `DEAD` | Dead code, duplication, slop, weak types | inline — plan task runs `code-review` mode `cleanup` | never |
| `TEST` | Untested branches and edge cases | inline — plan task runs `test-coverage` | never — an absent suite is itself a `Critical` finding |
| `CI` | Pipelines, pre-commit, quality gates | inline — plan task runs `devops-pipeline` | never |
| `SEC` | Secrets, dependency vulnerabilities | inline — plan task runs `security-setup` | never |
| `DOCS` | Docs drifted from code | inline — plan task runs `doc-manager` | never |

**Delegation policy — one rule: a delegate is invoked only if it changes no tracked file.**

- **Invoked** (`BUG`, `PERF`, `UX`) — these never touch source. Normalize their output into finding
  records and record `Path: delegated`. Never let `dont-make-me-think` enter its **Redesign Mode,
  which edits UI source files** — ask for the usability review only and decline any offer to apply
  fixes.
- **Inline** (`CLEAN`, `DEAD`, `TEST`, `CI`, `SEC`, `DOCS`) — these delegates **write**, so invoking
  one during an audit would break the read-only contract. Never do it. Audit the dimension with its
  checklist in `references/dimension-map.md`, record `Path: inline`, and name that skill as the
  invocation in the plan task that does the work. `inline` is the expected path, not a degradation.
  The plan's Pre step likewise names `/agent-config create|update` and never runs it.

Read `references/delegation-policy.md` before Phase 2 for exact invocation args, the `CODE_REVIEW.md`
declared-artifact handling, and the Skill-tool-unavailable fallback (which *is* reduced depth).

## Workflow

### Phase 0 — Baseline (gate)

Read `references/baseline.md` and follow it. Establish and record, with evidence:
build status, test command and pass rate, coverage if obtainable, lint status, CI presence and last
result, runtime/toolchain versions in use.

A **RED** baseline (does not build, tests do not run, there is no suite, or the build could not be
probed at all) does **not** stop the audit. Record `Baseline: RED`, continue, and make restoring
baseline-green the plan's Sprint 0 — nothing downstream is verifiable without it.

**Probes must not mutate tracked files.** Snapshot `git status --porcelain` before and after Phase 0.
Build and test commands can legitimately create build output, but any *tracked* file they change
(a rewritten lockfile, a newly written test snapshot) is a **finding**, not an accepted side effect —
report it and note that the probe was not reproducible. `references/baseline.md` gives the
non-mutating form of each command.

**When there is no test command**, the baseline-green assertion falls back to `<build command>`
succeeding until the P0 suite-creation task lands, and to that suite afterwards. Never apply the
fallback to Pre.

**Completion criteria:** every row of the baseline table in `references/baseline.md` holds a recorded
value or an explicit **Not Assessed** with a reason; the overall verdict is `GREEN`, `AMBER`, or
`RED`; every value cites the command that produced it.

### Phase 1 — Inventory and dimension selection

Detect stack, ecosystems, UI presence, repo size, and entry points. Produce the dimension worklist:
each of the 10 dimensions marked **audit** or **Not Assessed + reason**. Confirm it with the user
only if the dimension filter is ambiguous; otherwise proceed.

**Completion criteria:** all 10 dimensions have a disposition; every ecosystem with a manifest is
listed; repo-size branch and Agent-tool branch are both resolved and stated.

### Phase 2 — Dimension audits

**Read `references/delegation-policy.md` before invoking any delegated dimension.**

Run `DEP` first — its output feeds the plan's upgrade waves and often explains findings in other
dimensions. Then run the remaining audited dimensions, in parallel via `agents/dimension-auditor.md`
when the size branch calls for subagents, otherwise inline.

- `DEP` uses `agents/dependency-auditor.md` and `references/dependency-audit.md`, one invocation per
  ecosystem. All `DEP` findings share the `F-DEP-` prefix, so allocate each ecosystem a distinct
  `id_start` (1, 101, 201, …) **before** spawning them; gaps in the numbering are fine, collisions
  are not.
- All other dimensions use `agents/dimension-auditor.md` with that dimension's row from
  `references/dimension-map.md`. Each has its own prefix and numbers from 1, so they need no ID
  coordination.
- **No-fabrication rule:** every finding record cites `path:line` (or a manifest entry and version
  for `DEP`), or it is dropped. A dimension that produced nothing citable is **Not Assessed**, not
  "no issues found".

**Completion criteria:** every dimension marked *audit* in Phase 1 returned either ≥ 1 finding record
or an explicit "clean — checked X, found nothing" with the checks named; zero finding records lack
evidence; finding IDs are unique and follow `F-<DIM>-<NNN>`.

### Phase 3 — Write MODERNIZATION_REPORT.md

Merge all finding records into `MODERNIZATION_REPORT.md` using `references/report-template.md`.
Rank by severity: `Critical` → `High` → `Medium` → `Low`.

**Deduplicate before writing.** Two dimensions reporting the same `path:line` produce one counted
row, kept by whichever dimension appears earlier in the delegate table above. That rule is what
keeps the Summary counts equal to the number of rows.

**Completion criteria:** the file exists at the repo root; it contains the baseline table, a
dimension coverage table showing all 10 dispositions, and the full finding table; every finding has
ID, dimension, severity, evidence, and fix direction; the counts in the summary equal the rows in the
table.

### Phase 4 — Write MODERNIZATION_PLAN.md

Spawn `agents/plan-architect.md` with the report path (or run it inline when the Agent tool is
unavailable). It writes `MODERNIZATION_PLAN.md` from `references/plan-template.md`, using the fixed
skeleton (unconditional **Pre**, then **P0–P4** — do not rename or renumber P0–P4):

| Phase | Goal | Milestone |
|---|---|---|
| **Pre Agent environment** | env an AI agent can use autonomously; `CLAUDE.md` / `AGENTS.md` created or improved | `ME` — both files exist (create or update via planned `/agent-config`); recorded commands documented |
| **P0 Stabilize** | build green, tests runnable, lockfile committed, CI running | `M0` — baseline-green reproducible in CI |
| **P1 Secure & Patch** | vulnerabilities closed, security patch + patch/minor **upgrade waves** | `M1` — zero known High/Critical vulns; patch/minor current |
| **P2 Modernize** | each major dependency bump and runtime/toolchain upgrade, one task each | `M2` — every major current or deferred with written rationale |
| **P3 Clean & Harden** | dead code, duplication, weak types, test coverage to target | `M3` — coverage target met; duplication below stated threshold |
| **P4 Polish** | UI/UX, performance, docs alignment | `M4` — UX findings closed; perf budget met; docs match code |

Phases split into sprints. Every task uses the `tasks-generator` task format so the plan interoperates
with that skill, plus a `Closes:` line naming finding IDs.

**Completion criteria:** Pre is present and ordered before P0; every `Critical` and `High` finding
is closed by ≥ 1 task; every task has ≥ 2 testable acceptance criteria; every P0–P4 task asserts
baseline-green still holds; the dependency table references only task IDs that exist and has no
cycles; the critical path is stated explicitly; Pre and each of P0–P4 have a milestone with a
measurable exit condition. `references/plan-template.md` carries the task-ID format, the Pre
create-vs-update rule, and the RED-baseline exemption.

### Phase 5 — Validation pass

Spawn `agents/plan-validator.md` with fresh context, giving it both output files and the repo. It
verifies evidence citations resolve, severities are defensible, no finding is orphaned, no task
invents work not traceable to a finding or a milestone, and the **stated critical path is actually
the longest chain** in the dependency table.

Apply its corrections, then **re-run the validator — maximum 2 rounds.** Anything still open after
round 2 goes into the report's Limitations with a reason rather than looping further.

**Completion criteria:** the validator has run at least twice when round 1 returned any `must-fix`;
zero unresolved `must-fix` items remain, or each survivor is recorded in Limitations with a reason.

## Step Completion Reports

After each phase, emit:

```text
◆ [Phase Name] (phase N of 5 — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Per-phase check names:

- **Baseline:** `Build probed`, `Tests probed`, `Coverage probed`, `CI probed`, `Verdict recorded`
- **Inventory:** `Stack detected`, `Ecosystems listed`, `UI branch resolved`, `Worklist complete`
- **Audits:** `DEP complete`, `Delegated dims complete`, `Evidence cited`, `IDs unique`
- **Report:** `File written`, `Coverage table complete`, `Counts reconcile`
- **Plan:** `All Critical/High closed`, `Task format valid`, `No circular deps`, `Critical path stated`, `Milestones measurable`
- **Validation:** `Citations resolve`, `No orphan findings`, `Must-fix count 0`

Never report `PASS` while a phase completion criterion, required output file, or safety guardrail is
unresolved.

## Acceptance Criteria

The two bars that define this skill. The full run checklist — outputs, findings, and every plan
criterion — is `references/acceptance-criteria.md`; walk it before writing the report.

- [ ] **No tracked file's content changed** relative to the pre-run snapshot. On a clean tree,
      `git diff --stat` is empty. On a stale already-dirty tree, `git status --porcelain` and
      `git diff` match the snapshot taken before the run (declared artifacts set aside). No source,
      manifest, lockfile, hook, workflow, test, or docs file was modified by the audit.
- [ ] Every new file in `git status --short` is either one of the two reports, a **declared delegate
      artifact** (`CODE_REVIEW.md`), or a probe byproduct listed in the report's Artifacts section.
      Anything else is a contract breach.
- [ ] Both output files exist at the repo root and every criterion in
      `references/acceptance-criteria.md` holds.

If any criterion fails, report it as a `FAIL` row in the Step Completion Report and do not claim
success.

## Expected Output

```text
Target: /path/to/repo
Baseline: AMBER — builds; 41/58 tests pass; no coverage tool; CI absent
Dimensions: 8 audited, 2 Not Assessed (UX — no UI detected; PERF — out of requested scope)
Findings: 3 critical, 11 high, 24 medium, 9 low
Outputs: MODERNIZATION_REPORT.md, MODERNIZATION_PLAN.md
Plan: Pre + P0–P4, 10 sprints, 50 tasks — critical path Pre.1 → Pre.2 → 0.1 → 2.4
Validation: plan-validator PASS, 0 must-fix
Source files changed: 0
```

## Edge Cases

Two that change how the run is invoked or protect existing work. A user asking mid-run to apply
fixes is handled by the Read-only contract above. Every other case — not a git repo, no manifest,
no network, baseline RED, a huge repo, a narrowed dimension filter — is in
`references/edge-cases.md`, read when it arises.

- **Monorepo** — `scripts/dep_scan.sh` probes the repo root only; **re-run it once per package
  directory** and merge the results, one ecosystem row and `id_start` block per package. Never accept
  "Ecosystems detected: none" while nested manifests exist. Scope other dimensions to the packages
  the user names, or all of them if unspecified.
- **Existing report files** — back them up as `MODERNIZATION_REPORT_backup_YYYY_MM_DD_HHMMSS.md`
  before overwriting.

## Reference files

- `references/scope-detection.md` — the nine scope branches, detection, and resolution order.
- `references/delegation-policy.md` — invocation args, artifact handling, fallbacks per path.
- `references/baseline.md` — Phase 0 probe protocol per stack, and the baseline evidence table.
- `references/dependency-audit.md` — per-ecosystem **fail-soft** probes, classification schema,
  **upgrade wave** rules, and migration lookup for majors.
- `references/dimension-map.md` — the 10 dimensions: inline checklist, severity rubric, skip rules.
- `references/report-template.md` — report structure and the deduplication rule.
- `references/plan-template.md` — plan structure, task format, task-ID and Pre rules.
- `references/acceptance-criteria.md` — the full run checklist.
- `references/edge-cases.md` — the full edge-case list.
- `scripts/dep_scan.sh` — read-only ecosystem and dependency probe; prints a markdown summary.

Agents (spawn with the Agent tool; run inline if unavailable): `agents/dependency-auditor.md`
(`DEP`), `agents/dimension-auditor.md` (one delegated dimension per invocation),
`agents/plan-architect.md` (report → plan), `agents/plan-validator.md` (fresh-context validation).
