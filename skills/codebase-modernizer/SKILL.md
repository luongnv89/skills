---
name: codebase-modernizer
description: "Audit a stale, inherited, or messy codebase — deps, bugs, security, tests, CI, docs, UI/UX — then emit a phased, testable modernization plan. Read-only: plans upgrades, never applies them. Not for single-PR review, PRD-to-tasks, or UX-only audits."
license: MIT
effort: max
metadata:
  version: 1.2.2
  author: "Luong NGUYEN <luongnv89@gmail.com>"
  architecture: "orchestrator (baseline gate → parallel dimension audits → evidence report → phased sprint plan → validation)"
---

# Codebase Modernizer

For a codebase you are returning to after a long gap, or one that has drifted through many
unoptimized changes. It audits the whole repo across every applicable dimension, then converts the
findings into a **phased, sprint-sized, testable plan** for producing a better, up-to-date version.

Produces exactly two files in the target repo root:

| File | Contents |
|---|---|
| `MODERNIZATION_REPORT.md` | Baseline evidence + every finding, severity-ranked, each citing `path:line` |
| `MODERNIZATION_PLAN.md` | Phases → sprints → tasks → milestones, every task closing named findings |

## Read-only contract

This skill **never modifies source code, dependencies, lockfiles, or configuration** — no tracked
file's content changes. On a clean tree that is `git diff --stat` empty. On a stale, already-dirty
tree, `git status --porcelain` and `git diff` after the run must match a snapshot taken before it
(declared artifacts set aside). It runs read-only probes and writes the two report files above. Two
kinds of *new* file may also appear, and both must be enumerated in the report's Artifacts section:
a **declared delegate artifact** (`CODE_REVIEW.md`, from `code-review` mode `review`) and **probe
byproducts** (build dirs some dependency probes create, such as `obj/`, `.dart_tool/`, `target/`,
`.gradle/`). Nothing else.

- Dependency upgrades become **planned tasks with migration steps** — never `npm update`, `ncu -u`,
  `cargo update`, `poetry update`, or any equivalent. A blind bulk upgrade on a stale tree produces a
  broken build and an unreviewable diff, which is exactly what the plan exists to prevent.
- Refactors, dead-code removal, and test generation are **planned**, not applied. Applying them is
  the delegate skills' job, run later against the plan.
- Agent environment files (`CLAUDE.md`, `AGENTS.md`) are **planned** via `/agent-config create` or
  `/agent-config update` in the plan's Pre step — never created or rewritten during the audit.
- If the user asks mid-run to start fixing, finish the report and plan first, then hand off to the
  delegate skill named in that task.

## Leading terms

Used throughout this skill and its references with these exact meanings:

- **baseline-green** — the recorded state where the project builds and its test suite runs to a known
  pass rate. Established in Phase 0; every P0–P4 task's acceptance criteria require it to hold. Pre
  is exempt when the baseline is RED — restore-green stays on P0 / Sprint 0.
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
Phase 3, after the audit is recorded — and because HEAD moves, re-record the commit SHA and
re-verify every citation still resolves. A citation that no longer resolves means the audit is
stale: say so and re-run rather than publishing a report pointing at the wrong lines.

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

Resolve all nine branches in `references/scope-detection.md` **before Phase 0** — target path, repo
size, Agent-tool availability, Bash availability, Skill-tool availability, UI presence, app
runnability, ecosystems, and any user dimension filter. Each is a real branch in the workflow, not a
preference. Two of them change what is obtainable at all, so check them early:

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
  records and record `Path: delegated`. `code-review` mode `review` writes its own `CODE_REVIEW.md`,
  a **declared artifact** that must be listed in the report's Artifacts section. Never let
  `dont-make-me-think` enter its **Redesign Mode, which edits UI source files** — ask for the
  usability review only and decline any offer to apply fixes.
- **Inline** (`CLEAN`, `DEAD`, `TEST`, `CI`, `SEC`, `DOCS`) — these delegates **write**, so invoking
  one during an audit would break the read-only contract. Never do it. Audit the dimension with its
  checklist in `references/dimension-map.md`, record `Path: inline`, and name that skill as the
  invocation in the plan task that does the work. Here `inline` is the expected path, not a
  degradation — do not report it as a limitation. The plan's Pre step likewise names
  `/agent-config create|update` and never runs it.

Read `references/delegation-policy.md` before Phase 2 for exact invocation args, artifact handling,
and the Skill-tool-unavailable fallback (which *is* reduced depth).

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

**When there is no test command**, the baseline-green assertion every **P0–P4** task carries falls
back to the build: P0–P4 tasks before the P0 suite-creation task assert `<build command>` succeeds;
every later P0–P4 task asserts the suite that task established. Do not apply this fallback to Pre.

**Completion criteria:** every row of the baseline table in `references/baseline.md` holds a recorded
value or an explicit **Not Assessed** with a reason; the overall verdict is `GREEN`, `AMBER`, or
`RED`; every value cites the command that produced it.

### Phase 1 — Inventory and dimension selection

Detect stack, ecosystems, UI presence, repo size, and entry points. Produce the dimension worklist:
each of the 10 dimensions marked **audit** or **Not Assessed + reason**. Confirm the worklist with
the user only if the dimension filter is ambiguous; otherwise proceed.

**Completion criteria:** all 10 dimensions have a disposition; every ecosystem with a manifest is
listed; repo-size branch and Agent-tool branch are both resolved and stated.

### Phase 2 — Dimension audits

**Read `references/delegation-policy.md` before invoking any delegated dimension** — it holds the
exact call for each, and the artifact handling that keeps the read-only contract intact.

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
row, kept by whichever dimension appears earlier in the delegate table above. Follow the
deduplication rule in `references/report-template.md` — it is what keeps the Summary counts equal to
the number of rows.

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

**Completion criteria:** Pre — Agent environment is present and ordered before P0, with create vs
update of `CLAUDE.md` and `AGENTS.md` matching file presence and `/agent-config` named not run;
every `Critical` and `High` finding is closed by ≥ 1 task; every task has ≥ 2 testable acceptance
criteria; every P0–P4 task asserts baseline-green still holds (Pre is exempt when the baseline is
RED — Pre ACs are install/run notes plus create-or-update of `CLAUDE.md`/`AGENTS.md`); task IDs follow `Task Pre.<index>` then
`Task <sprint>.<index>`; the dependency table references only task IDs that exist; no circular
dependencies; the critical path is stated explicitly; Pre and each of P0–P4 have a milestone with a
measurable exit condition.

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

The run is successful only if **all** hold:

- [ ] `MODERNIZATION_REPORT.md` and `MODERNIZATION_PLAN.md` both exist at the target repo root.
- [ ] **No tracked file's content changed** relative to the pre-run snapshot. On a clean tree,
      `git diff --stat` is empty. On a stale already-dirty tree, `git status --porcelain` and
      `git diff` match the snapshot taken before the run (declared artifacts set aside). This is
      the promise that matters: no source, manifest, lockfile, hook, workflow, test, or docs
      file was modified by the audit.
- [ ] Every new file in `git status --short` is either one of the two reports, a **declared delegate
      artifact** (`CODE_REVIEW.md`), or a probe byproduct listed in the report's Artifacts section.
      Anything else is a contract breach.
- [ ] The baseline table is complete with a `GREEN | AMBER | RED` verdict and per-row evidence.
- [ ] All 10 dimensions appear in the coverage table with `Audited` or `Not Assessed + reason`.
- [ ] Every finding record has a unique `F-<DIM>-<NNN>` ID, a severity, and `path:line` evidence
      (or manifest+version for `DEP`).
- [ ] Every `Critical` and `High` finding is closed by at least one task in the plan.
- [ ] The plan starts with the Agent-environment pre-step, then P0–P4, each with ≥ 1 sprint and a
      measurable milestone. Pre is present whether `CLAUDE.md` / `AGENTS.md` already exist (update)
      or not (create). `/agent-config` is named, never invoked.
- [ ] Every task has ≥ 2 testable acceptance criteria, explicit `Dependencies`, an effort estimate,
      and a `Closes:` line. P0–P4 tasks include a baseline-green assertion. Pre is exempt when the
      baseline is RED (install/run notes plus create-or-update of `CLAUDE.md`/`AGENTS.md`).
- [ ] The dependency table has no broken task IDs and no cycles; the critical path is stated.
- [ ] Major dependency bumps are one task each, never batched, each naming its migration source.
- [ ] Limitations section lists every **Not Assessed** dimension, missing tool, and degraded pass.

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

- **Not a git repo** — skip Repo Sync, state it in the report, still write both files.
- **Monorepo** — `scripts/dep_scan.sh` probes the repo root only; **re-run it once per package
  directory** and merge the results, one ecosystem row and `id_start` block per package. Never accept
  "Ecosystems detected: none" while nested manifests exist. Scope other dimensions to the packages
  the user names, or all of them if unspecified.
- **No manifest at all** (shell scripts, plain HTML) — `DEP` is **Not Assessed — no manifest**; the
  plan drops P2 to a single "no dependency surface" note rather than inventing upgrade tasks.
- **No network** — dependency *latest* versions are unobtainable; record installed versions only and
  mark currency **Not Assessed — offline**. Never guess a latest version.
- **Baseline RED** — audit continues; the plan's Sprint 0 is "restore baseline-green" and every later
  task depends on it.
- **Existing report files** — back them up as `MODERNIZATION_REPORT_backup_YYYY_MM_DD_HHMMSS.md`
  before overwriting.
- **Huge repo (> 2000 source files)** — audit by subsystem in priority order, cap the file set per
  dimension, and state in Limitations exactly what was not scanned. Never silently truncate.
- **User asks to apply fixes** — handled by the Read-only contract above: finish both files first,
  then hand off.

## Reference files

- `references/scope-detection.md` — the nine scope branches, detection, and resolution order.
- `references/delegation-policy.md` — invocation args, artifact handling, and fallbacks per path.
- `references/baseline.md` — Phase 0 probe protocol per stack, and the baseline evidence table.
- `references/dependency-audit.md` — per-ecosystem **fail-soft** probes, classification schema,
  **upgrade wave** rules, and migration-guide lookup for majors.
- `references/dimension-map.md` — the 10 dimensions: inline checklist, severity rubric, skip rules.
- `references/report-template.md` — `MODERNIZATION_REPORT.md` structure and the deduplication rule.
- `references/plan-template.md` — `MODERNIZATION_PLAN.md` structure and task format.
- `scripts/dep_scan.sh` — read-only ecosystem and dependency probe; prints a markdown summary.

Agents (spawn with the Agent tool; run inline if unavailable):

- `agents/dependency-auditor.md` — `DEP` dimension.
- `agents/dimension-auditor.md` — one delegated dimension per invocation.
- `agents/plan-architect.md` — report → `MODERNIZATION_PLAN.md`.
- `agents/plan-validator.md` — fresh-context validation of both outputs.
