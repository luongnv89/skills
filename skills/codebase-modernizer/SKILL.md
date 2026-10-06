---
name: codebase-modernizer
description: "Audit a stale, inherited, or messy codebase — deps, bugs, security, tests, CI, docs, UI/UX — then emit a phased, testable modernization plan. Read-only: plans upgrades, never applies them. Not for single-PR review, PRD-to-tasks, or UX-only audits."
license: MIT
effort: max
dependencies:
  - code-review
  - dont-make-me-think
metadata:
  version: 1.4.0
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

This skill **invokes** the two skills declared in frontmatter `dependencies`: `code-review` (modes
`review` and `perf`, for `BUG` and `PERF`) and `dont-make-me-think` (`UX`). Run this before Phase 0,
the first phase that probes anything. Discovery acquires nothing:

```bash
if command -v asm >/dev/null && asm deps --help >/dev/null 2>&1; then
  asm deps discover codebase-modernizer --json || echo "discover failed; acquire at first use" >&2
  printf 'cm_session=%s\n' "codebase-modernizer-$(date +%s)-$$"   # record it; reuse it verbatim
else
  echo "asm deps unavailable: npm install -g agent-skill-manager@latest" >&2
fi
```

1. If the block prints `asm deps unavailable`, record every delegated dimension **Not Assessed —
   skill unavailable**, skip steps 2–5, and continue.
2. When Phase 2 first reaches `BUG` or `PERF`, run
   `asm deps acquire code-review --session <cm_session> --json`. When it first reaches `UX`, run the
   same command for `dont-make-me-think`. Never acquire for a dimension that is Not Assessed.
3. If the acquire exits 0, pass its returned `skillMdPath` to the dimension worker as
   `delegate_skill_md`. Read that path directly.
4. If the acquire exits non-zero, print the install hint in `references/delegation-policy.md`
   (*Missing dependency*). Record **Not Assessed — skill unavailable** for `BUG` and `PERF`
   (`code-review`) or `UX` (`dont-make-me-think`), continue, and name it in Limitations. A missing
   dependency is **fail-soft**, not fatal.
5. **Release in `finally`.** If any acquire ran, run
   `asm deps release --session <cm_session> --json` once at every terminal outcome (after Phase 5,
   on a stop, or on an error), before the final report. Put a failed release under `Uncertainty:`.

Lease-owned copies live outside the target repo, so they are not target artifacts. The six *inline*
dimensions name their skill in a plan task and never invoke it, so they need no dependency entry.

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
Phase 3, after the audit is recorded. Because HEAD moves, re-record the commit SHA and re-verify
every citation. If any citation no longer resolves, stop with `Result: BLOCKED — audit stale after
sync` and re-run the audit.

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
branch in the workflow, not a preference. Check these two first, because they change what is
obtainable at all:

- **No Bash** → record the whole baseline **Not Assessed — no shell**, audit only what static
  reading supports, and never fabricate a verdict.
- **No UI detected** → UI/UX dimensions are **Not Assessed — no UI detected**. Never invent UX
  findings.

If a branch was not checked, take its restrictive side.

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

- **Invoked** (`BUG`, `PERF`, `UX`) — normalize the output into finding records and record
  `Path: delegated`. Never let `dont-make-me-think` enter its **Redesign Mode, which edits UI
  source files**.
- **Inline** (`CLEAN`, `DEAD`, `TEST`, `CI`, `SEC`, `DOCS`) — these delegates **write**, so never
  invoke one during the audit. Audit the dimension with its checklist in
  `references/dimension-map.md`, record `Path: inline`, and name that skill in the plan task.
  `inline` is the expected path, not a degradation.

Read `references/delegation-policy.md` before Phase 2. It holds the invocation args, the
`CODE_REVIEW.md` declared-artifact handling, the review-only rule for `dont-make-me-think`, the
`/agent-config` Pre-step rule, and the Skill-tool-unavailable fallback (which *is* reduced depth).

## Workflow

### Phase 0 — Baseline (gate)

Follow `references/baseline.md`. Record each of these with the command that produced it: build
status, test command and pass rate, coverage if obtainable, lint status, CI presence and last
result, runtime/toolchain versions in use.

A **RED** baseline (does not build, tests do not run, there is no suite, or the build could not be
probed at all) does **not** stop the audit. Record `Baseline: RED`, continue, and make restoring
baseline-green the plan's Sprint 0 — nothing downstream is verifiable without it.

**Probes must not mutate tracked files.** A tracked file a probe changes is a **finding**. The
snapshot procedure and the no-test-command fallback are in `references/baseline.md` (*Phase 0
rules: tracked files and the no-test-command fallback*).

**Completion criteria:** every row of the baseline table in `references/baseline.md` holds a recorded
value or an explicit **Not Assessed** with a reason; the overall verdict is `GREEN`, `AMBER`, or
`RED`; every value cites the command that produced it.

### Phase 1 — Inventory and dimension selection

Detect stack, ecosystems, UI presence, repo size, and entry points. Produce the dimension worklist:
each of the 10 dimensions marked **audit** or **Not Assessed + reason**. If a requested area maps to
no dimension ID, or to more than one, ask the user once which to audit. Otherwise proceed without
asking.

**Completion criteria:** all 10 dimensions have a disposition; every ecosystem with a manifest is
listed; repo-size branch and Agent-tool branch are both resolved and stated.

### Phase 2 — Dimension audits

**Read `references/delegation-policy.md` before invoking any delegated dimension.**

Run `DEP` first — its output feeds the plan's upgrade waves and often explains findings in other
dimensions. Then run the remaining audited dimensions. If the Repo size and Agent tool branches
select subagents, spawn one `agents/dimension-auditor.md` per dimension in parallel. Otherwise run
them inline, one at a time.

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

**Deduplicate before writing**, by the *Deduplication rule* in `references/report-template.md`.

**Completion criteria:** the file exists at the repo root; it contains the baseline table, a
dimension coverage table showing all 10 dispositions, and the full finding table; every finding has
ID, dimension, severity, evidence, and fix direction; the counts in the summary equal the rows in the
table.

### Phase 4 — Write MODERNIZATION_PLAN.md

Spawn `agents/plan-architect.md` with the report path (or run it inline when the Agent tool is
unavailable). It writes `MODERNIZATION_PLAN.md` from `references/plan-template.md`, using the fixed
skeleton: unconditional **Pre Agent environment** (`ME`), then **P0 Stabilize** (`M0`), **P1 Secure
& Patch** (`M1`), **P2 Modernize** (`M2`), **P3 Clean & Harden** (`M3`), and **P4 Polish** (`M4`).
Do not rename or renumber P0–P4. Each phase's goal and exit milestone are in
`references/plan-template.md` (*The fixed phase skeleton*). Phases split into sprints. Every task uses the `tasks-generator` task format so the plan interoperates
with that skill, plus a `Closes:` line naming finding IDs.

**Completion criteria:** Pre is present and ordered before P0; every `Critical` and `High` finding
is closed by ≥ 1 task; every task has ≥ 2 testable acceptance criteria; every P0–P4 task asserts
baseline-green still holds; the dependency table references only task IDs that exist and has no
cycles; the critical path is stated explicitly; Pre and each of P0–P4 have a milestone with a
measurable exit condition. `references/plan-template.md` carries the task-ID format, the Pre
create-vs-update rule, and the RED-baseline exemption.

### Phase 5 — Validation pass

1. Spawn `agents/plan-validator.md` with fresh context, giving it both output files and the repo.
   It verifies evidence citations resolve, severities are defensible, no finding is orphaned, no
   task invents work not traceable to a finding or a milestone, and the **stated critical path is
   actually the longest chain** in the dependency table.
2. Apply each `must-fix` correction it returns.
3. If round 1 returned any `must-fix`, re-run the validator once. **Never run a third round.**
4. Record each `must-fix` still open after round 2 in the report's Limitations, with a reason.

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

Use the per-phase check names in `references/output-format.md`. Never report `PASS` while a phase
completion criterion, required output file, or safety guardrail is unresolved.

## Acceptance Criteria

Walk `references/acceptance-criteria.md` before writing the final report. It is the full run
checklist: outputs, the read-only contract, findings, the plan, and an understandable final report.
The two bars this skill exists to keep:

- [ ] **No tracked file's content changed** relative to the pre-run snapshot (*Read-only contract*).
- [ ] Every new file in `git status --short` is one of the two reports, a **declared delegate
      artifact** (`CODE_REVIEW.md`), or a probe byproduct listed in the report's Artifacts section.

If any criterion fails, report it as a `FAIL` row in the Step Completion Report and set `Result:` by
the rules below.

## Final report

End the run with one final report in chat. Its first four lines are fixed; field contents, the
outcome table, and the format rule are in `references/output-format.md`.

```text
Result: COMPLETE | PARTIAL — <reason> | BLOCKED — <reason>
Evidence: <checks that actually ran, and what each showed>
Uncertainty: <Not Assessed rows, degraded paths, untested items, labeled assumptions>
Decision: <approval needed, or "No approval needed."> Next: <remaining user action>
```

Set `Result:` with the first rule that matches:

1. **BLOCKED** — either output file is missing at the repo root, a tracked file's content changed
   during the run (even if restored), or the run stopped (sync conflict, stale citations, user
   stop).
2. **PARTIAL** — any of: a dimension is Not Assessed for an environment reason (no shell, offline,
   missing tool, missing skill); `BUG`, `PERF`, or `UX` ran inline at reduced depth; a huge-repo
   cap left paths unscanned; the read-only check could not run (not a git repo); a `must-fix`
   survived round 2; an acceptance criterion fails.
3. **COMPLETE** — every other run. A RED baseline, or Not Assessed because of no UI, no manifest,
   or the requested scope, is a finding or a scope choice, not a gap.

## Expected Output

```text
Result: COMPLETE — 47 findings; Pre + P0–P4 plan; 0 must-fix
Evidence: git status --porcelain and git diff match the pre-run snapshot; validator ran 1 round
Uncertainty: coverage Not Assessed (no coverage tool); no plan task was executed
Decision: No approval needed. Next: review MODERNIZATION_PLAN.md, then run Task Pre.1
```

The summary facts that follow these four lines (target, baseline, dimensions, findings, outputs,
plan, validation, source files changed) are in `references/output-format.md` (*Full example*).

## Edge Cases

Read `references/edge-cases.md` when a case arises: not a git repo, no manifest, no network,
baseline RED, a huge repo, a narrowed dimension filter, a **monorepo**, or **existing report
files**. A user asking mid-run to apply fixes is handled by the Read-only contract above.

## Reference files

Read each file only when its phase needs it; that keeps the agent's context budget for the audit.

- `references/scope-detection.md` — the nine scope branches, detection, and resolution order.
- `references/delegation-policy.md` — invocation args, artifact handling, fallbacks per path.
- `references/baseline.md` — Phase 0 probe protocol per stack, and the baseline evidence table.
- `references/dependency-audit.md` — per-ecosystem **fail-soft** probes, classification schema,
  **upgrade wave** rules, and migration lookup for majors.
- `references/dimension-map.md` — the 10 dimensions: inline checklist, severity rubric, skip rules.
- `references/report-template.md` — report structure and the deduplication rule.
- `references/plan-template.md` — plan structure, task format, task-ID and Pre rules.
- `references/acceptance-criteria.md` — the full run checklist.
- `references/output-format.md` — Step Completion Report checks, final-report fields, format rule.
- `references/edge-cases.md` — the full edge-case list.
- `scripts/dep_scan.sh` — read-only ecosystem and dependency probe; prints a markdown summary.

Agents (spawn with the Agent tool; run inline if unavailable): `agents/dependency-auditor.md`
(`DEP`), `agents/dimension-auditor.md` (one delegated dimension per invocation),
`agents/plan-architect.md` (report → plan), `agents/plan-validator.md` (fresh-context validation).
