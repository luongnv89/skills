# The /issue-creator bridge

Exactly how plan tasks reach the tracker. Read this in Phase 4. `/issue-creator` owns every issue
body; this skill owns what it is handed, the labels applied afterwards, and the verification that the
result matches the plan.

## Why the bridge is shaped this way

`/issue-creator`'s **Output Contract** forbids *skill-generated* codebase analysis in an issue body —
no predicted affected files, no root cause, no implementation hints. It does preserve
*reporter-supplied* technical detail verbatim inside the Reporter Context blockquote.

A plan task is reporter-supplied: a human-reviewed document already exists, and this skill relays it.
So the whole task block is passed **verbatim** and lands in Reporter Context intact — paths, `Verify:`
commands, and finding IDs included. What stays forbidden is this skill adding anything the plan does
not say. That is the **plan-faithful** rule, and it is what keeps the bridge contract-clean.

## Step 1 — The epic (Create mode)

Invoke `/issue-creator` once with intent text built only from the plan header and milestone table:

```text
Epic: Modernize acme-api — Pre + P0–P4

Track the implementation of MODERNIZATION_PLAN.md, derived from MODERNIZATION_REPORT.md.

Baseline at audit: AMBER — builds; 41/58 tests pass; CI absent
Test command of record: `npm test` (pass rate 41/58)

Phases: Pre Agent environment · P0 Stabilize · P1 Secure & Patch · P2 Modernize ·
P3 Clean & Harden · P4 Polish — 10 sprints, 50 tasks.

Done when every milestone exit condition holds:
- ME — CLAUDE.md and AGENTS.md exist; recorded build/test commands documented
- M0 — baseline-green reproducible in CI from a clean checkout
- M1 — zero known High/Critical advisories; patch/minor current
- M2 — every major current or deferred with written rationale
- M3 — coverage ≥ 62%; no logic block repeated ≥ 3 times; zero `any` in src/api
- M4 — UX findings closed; bundle ≤ 480 KB; docs match code
```

The milestone exit conditions become the epic's acceptance criteria — whole-effort outcome, per IDD
SPEC §2.1. Then `gh issue edit <epic> --add-label epic`.

**The intent text must end with the plan-binding marker block** — this is not optional, and it is
what makes the epic findable on a re-run:

```text
<!-- plan-to-issues:plan=<plan_path> -->
<!-- plan-dashboard:start -->
<!-- plan-dashboard:end -->
```

Creating the epic without it reintroduces the duplicate-epic bug: an interruption during Step 3
leaves an epic that the next run cannot recognise, and it files a second one. Follow SKILL.md
Phase 3 steps 2-4 in full — including the post-create verification — rather than stopping at the
label.

## Step 2 — One batch document per phase

Build one document per plan phase and invoke:

```text
/issue-creator <batch document> --parent <epic>
```

`--parent` makes `/issue-creator` append `Part of #<epic>` to every child body. Each item is a `##`
heading (a heading starts a new batch item), and the item body is the plan task, copied:

```markdown
## 0.1: Commit the lockfile and restore the build

Type: improvement
Priority: high
Effort: S
Labels: phase:p0, improvement, dim:dep, priority:high
Plan task: 0.1 — Sprint 0 · Phase P0 Stabilize · MODERNIZATION_PLAN.md

Description: The repository ships no lockfile, so no two installs resolve the same tree.
Restore a committed lockfile and a reproducible install.

Acceptance criteria:
- [ ] `package-lock.json` is committed at the repo root
- [ ] `npm ci` succeeds from a clean checkout
- [ ] `npm test` passes at ≥ 41/58 (baseline-green holds)

Dependencies: Pre.2, Pre.3
Closes: F-DEP-003, F-CI-002
Verify: `rm -rf node_modules && npm ci && npm test`
```

Rules that make the batch reversible into a dashboard:

- **Title prefix is load-bearing.** `<task-id>: <imperative title>`. It is the only reliable
  task-id → issue-number map, since `/issue-creator` assigns numbers.
- **`Plan task:` line is the durable marker.** It survives into Reporter Context and is what
  **idempotent re-run** greps for.
- **One batch per phase.** 5–15 items per call. Rate limits, per-phase progress, and resumption all
  come from this bound. Split a phase over 15 tasks into per-sprint batches.
- **Batch mode never blocks.** `/issue-creator` skips its clarification step in batch mode and marks
  low-confidence fields `(needs review)`. That is expected; do not pre-answer for it.
- **Duplicate warnings are surfaced, not auto-resolved.** `/issue-creator`'s duplicate detector may
  flag an existing issue. Show it and let the user decide — a modernization backlog legitimately
  resembles older stale issues.

## Step 3 — Map created issues back to plan tasks

`/issue-creator` prints `✓ Created issue #N: <title>` per item. Parse the `<task-id>:` prefix out of
each title to build `task_id → issue_number`. Then confirm against the tracker rather than the
transcript:

```bash
gh issue list --state all --limit 500 --json number,title,labels,body \
  --jq '[.[] | select(.body | test("Part of #<epic>\\b"))] | map({number,title,labels:[.labels[].name]})'
```

Filter locally rather than with `--search "Part of #100 in:body"`: GitHub's search tokenizer drops
the `#`, so that query silently matches issues mentioning `100` and misses others. A local `select`
on the fetched body is exact.

A created issue whose title lost its prefix is **unmapped**: repair it and re-read. **Source** the
title out of the worklist — never retype the plan text into the assignment, which is a shell literal
and parses `` ` ``/`$(…)` just as an argument would (SKILL.md -> *Prompt Injection Boundary*):

```bash
title="$(jq -r --arg id "$task_id" '.tasks[] | select(.id == $id) | "\($id): \(.title)"' worklist.json)"
gh issue edit <n> --title "$title"
```

`gh` has no `--title-file`, so this variable form is the only safe way to pass a plan-derived title.

An unmapped issue silently excluded from the dashboard is the failure mode this check exists to
prevent.

## Step 4 — Label pass

Apply the computed **label set** per issue (`references/labels.md` → *Applying labels*), then re-read
labels to confirm. Additive only.

## Step 5 — Dependency pass

Run once, after every phase is filed, so cross-phase dependencies resolve to real numbers.

For each task with `depends_on`, translate ids to issue numbers and append a marker line to that
child's body (read-modify-write, preserving the fetched body verbatim):

```text
Depends on #103, #104
```

`Depends on #N` is scope-independent of `Part of #<epic>` and answers a different question: `Part of`
says the child serves the epic's outcome, `Depends on` says it cannot merge first (IDD SPEC §2.1).
`/auto-pilot`'s merge gate reads `Depends on` only, which is why the pass is worth the extra edits.

- Skip children with no dependencies — most of the backlog gets no edit.
- A dependency id absent from the map is skipped and reported as `⚠ unknown dep <id>`; never emit a
  `#0` or a guessed number.
- Cross-repo references are out of scope: emit bare `#N` only.
- Verify by re-reading the body and confirming the marker line is present.

## Fallback

There is none. If `/issue-creator` is unavailable, Phase 0 stops the run and prints the install
block from `references/preflight.md` — `asm` command included.
Filing bodies with raw `gh issue create` would produce issues that skip the normalized template,
duplicate detection, and Reporter Context — a backlog `/issue-resolver` and `/issue-triage` then read
inconsistently.
