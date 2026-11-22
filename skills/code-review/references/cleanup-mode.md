
# Slop Code Cleanup

Aggressively clean up a codebase by eliminating eight distinct categories of code quality problems. Orchestrates eight specialized subagents that each own one cleanup category, so each one stays focused, deep, and fast — and so they can run in parallel on independent slices of the problem.

The philosophy is simple: **a clean codebase has one clear way to do each thing.** Duplication, weak types, unused code, hidden errors, and legacy fallbacks all create multiple paths where one would do. This skill hunts down those extra paths and removes them.

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stop and ask the user to commit or stash first (Safety gate 1); do not stash on their behalf.

If `origin` is missing, pull is unavailable, or rebase conflicts occur, stop and ask the user before continuing.

## Safety & Confirmation Gates

This skill **deletes and rewrites code aggressively**. That is the point. But because deletions are harder to reverse than additions, enforce these gates:

1. **Never run on uncommitted changes.** If `git status` is not clean, stop and ask the user to commit or stash.
2. **Create a dedicated cleanup branch** before any edits (e.g., `chore/code-review-cleanup-YYYYMMDD`). Never work directly on `main`/`master`.
3. **Commits never mix categories.** Each subagent commits only its own category's changes, with its category prefix, so any category can be reverted without losing the rest.
4. **Test gate between waves.** After each wave finishes, run the test suite and typecheck (if available). If either fails, stop the pipeline and surface the failure — do not start the next wave on a broken tree. The gate also records the wave's test count before and after, and fails on a drop the deleted tests do not explain (*Test Count per Wave*).
5. **Report before destructive deletion.** For subagents that delete code (unused code, legacy, duplicates), surface the deletion list to the user for approval when the deletion count exceeds 50 items or crosses module boundaries.

## Environment Check

Before starting:

1. **Detect language/stack** — read `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, etc. The subagents tailor tool choices (knip, madge, ts-prune, vulture, ruff, etc.) to the stack.
2. **Verify tooling** — if a subagent depends on a tool (knip for JS/TS unused code, madge for circular deps), confirm it's already installed in the project or on PATH (e.g. `npx --no-install knip --version`). Don't download tools on the fly; if one is missing, fall back to manual analysis and note this in the report. These checks run in the orchestrator checkout, whose gitignored dependency dirs (`node_modules`, `.venv`) the subagents' fresh worktrees lack, so record the absolute path of each verified tool and of the test and typecheck commands' interpreters for the `tool_root` payload below.
3. **Determine scope** — full codebase vs. a subdirectory. Default to full unless the user specifies.
4. **Detect test/typecheck commands** — read scripts in `package.json`, `Makefile`, `pyproject.toml`, CI configs. These run between phases.

## Subagent Architecture

Eight specialized subagents, each focused on one cleanup category. They run in two **waves** because some categories produce findings that others need to reason about. Within a wave, subagents run in parallel.

```
┌─────────────────────────────────────────────┐
│  Main SKILL (Orchestrator)                  │
│  - Detect stack & tools                     │
│  - Create cleanup branch                    │
│  - Dispatch subagents in waves              │
│  - Run tests between waves                  │
│  - Assemble final report                    │
└──────────────┬──────────────────────────────┘
               │
     ┌─────────┴──────────┐
     │      Wave 1         │  (analyze + narrow edits, run in parallel)
     │                     │
     ▼                     ▼
 ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ Unused   │ │ Circular │ │ Weak     │ │ Slop/    │
 │ Code     │ │ Deps     │ │ Types    │ │ Comments │
 │ (knip)   │ │ (madge)  │ │          │ │          │
 └──────────┘ └──────────┘ └──────────┘ └──────────┘

               ↓ test + typecheck gate ↓

     ┌─────────────────────┐
     │      Wave 2         │  (structural, needs Wave 1 done first)
     │                     │
     ▼                     ▼
 ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ Dedupe/  │ │ Type     │ │ Defensive│ │ Legacy/  │
 │ DRY      │ │ Consol.  │ │ Prog.    │ │ Deprec.  │
 └──────────┘ └──────────┘ └──────────┘ └──────────┘

               ↓ test + typecheck gate ↓

        ┌──────────────────────┐
        │  Report Assembler    │
        │  SLOP_CLEANUP.md     │
        └──────────────────────┘
```

**Why two waves?** Wave 1 subagents do pure cleanup — removing things that are clearly wrong. Their results shrink the surface area for Wave 2, which restructures what remains (deduplication, type consolidation, legacy collapse). Running Wave 2 first would mean merging duplicates that later get deleted as unused, wasting work.

## Subagent Specifications

Each subagent has its own prompt file in `agents/`. The orchestrator spawns them via the Agent tool (`subagent_type: general-purpose`) with their prompt file as context.

| # | Wave | Subagent | Prompt file | Scope |
|---|------|----------|-------------|-------|
| 1 | 2 | Deduplicator | `agents/deduplicator.md` | Extract shared code; apply DRY only where it reduces complexity |
| 2 | 2 | Type Consolidator | `agents/type-consolidator.md` | Merge duplicate type/interface/struct definitions into shared modules |
| 3 | 1 | Unused Code Killer | `agents/unused-code-killer.md` | Find and delete unreferenced code using knip/ts-prune/vulture/etc. |
| 4 | 1 | Circular Dep Untangler | `agents/circular-dep-untangler.md` | Detect and break circular dependencies using madge/dep-cruiser |
| 5 | 1 | Weak Type Strengthener | `agents/weak-type-strengthener.md` | Replace `any`/`unknown`/`interface{}`/`Object` with specific types |
| 6 | 2 | Defensive Programming Remover | `agents/defensive-programming-remover.md` | Remove try/catch, fallbacks, and null-checks that hide errors |
| 7 | 2 | Legacy Code Remover | `agents/legacy-code-remover.md` | Delete deprecated, fallback, and duplicated-by-migration code paths |
| 8 | 1 | Slop Comment Cleaner | `agents/slop-comment-cleaner.md` | Remove AI-generated fluff, stubs, work-in-motion comments, LARP |

## Test Count per Wave

Cleaner subagents delete the tests of the code they delete, so a wave's test gate can pass on fewer tests than the wave started with. Each wave records its test count before and after, so the checks that judge a wave never shrink without a record.

- **The count** is the number of tests the test command reports it ran (passed, failed and skipped together, each parametrized case as the runner counts it), read from the runner's summary. If the runner prints no count, use its listing flag when it has one (`pytest --collect-only -q`, `go test -list .`, `cargo test -- --list`). If neither gives a number, the count is `unknown`, with the reason.
- **Before:** in *Prepare*, run the test command once on the cleanup branch before Wave 1 dispatches. Its count is Wave 1's before count. Wave 2's before count is Wave 1's after count.
- **After:** the wave's test gate reads the count from the same run that decides pass or fail. A gate re-run after a deletion-cap re-dispatch replaces it.
- **Deleted tests:** every subagent that deletes a test function, case, parametrize row or test file lists each one in its category report under `## Deleted Tests`: the test, its location, the deleted code it covered (symbol and location, or the reason it was deleted when its code stays, for example a duplicate merged), and the count it removes.
- **Check:** expected after count = before count − the counts listed under `## Deleted Tests` in the wave's category reports. An after count below that is an unexplained drop: the gate fails as a failing test would, so stop and name the before, after and listed counts. An after count above it is fine (a subagent may add tests). An `unknown` count never passes: the wave report marks `Test count` `×`, its result is `PARTIAL`, and `SLOP_CLEANUP.md` says `unknown` with the reason.

## Orchestration Workflow

### 1. Prepare

```bash
# Refuse if working tree is dirty
git diff-index --quiet HEAD -- || { echo "Commit or stash changes first"; exit 1; }

# Create cleanup branch
date_tag=$(date +%Y%m%d)
git checkout -b "chore/code-review-cleanup-${date_tag}"
```

Detect the stack (language, package manager, test command, typecheck command) and write a one-line summary the user sees before dispatch begins. Then run the test command once and record its count as Wave 1's before count (*Test Count per Wave*).

### 2. Dispatch Wave 1 in parallel

Spawn subagents 3, 4, 5, and 8 in a single turn (multiple Agent tool calls in one message). Each receives:

- `repo_path`: the subagent's own working directory (its isolated worktree); it never `cd`s to the orchestrator checkout, and it returns its absolute worktree path and branch with its result
- `base_sha`: the full SHA of the cleanup-branch tip at dispatch time (for a deletion-cap re-dispatch, the current tip). Before any edit the subagent checks that `git status --porcelain` is empty, runs `git reset --keep <base_sha>`, and confirms `git rev-parse HEAD` equals `base_sha`; on any mismatch it stops and returns an error without editing, since the Agent tool may create the worktree from `origin`'s default branch rather than the unpushed cleanup branch
- Stack summary (language, tooling, test command)
- `tool_root`: the orchestrator checkout's absolute path, with the absolute tool paths recorded in the Environment Check. The subagent runs its tools and its test and typecheck self-checks from `repo_path` by those absolute paths (e.g. `<tool_root>/node_modules/.bin/knip`, `<tool_root>/.venv/bin/python -m pytest`), and never symlinks or installs dependencies into its worktree: an untracked `node_modules` link blocks `git worktree remove`. A self-check that cannot start or cannot resolve a dependency in the worktree is an environment gap, not a regression: the subagent notes it in its report and keeps its edits instead of reverting them. The orchestrator's wave test gate is authoritative
- Instructions to produce a per-category report at `.slop-cleanup/wave-1/<subagent>.md`, listing every test it deletes under `## Deleted Tests` (*Test Count per Wave*), and never to stage or commit anything under `.slop-cleanup/`: reports stay untracked
- Isolation: spawn each subagent with `isolation: "worktree"`, pinned to `base_sha` as above; it edits and commits only there. After the wave, cherry-pick exactly the commits in `<base_sha>..<returned branch>`, oldest first (`git rev-list --reverse`), onto the cleanup branch one at a time (no merge commits). Then copy each worktree's `.slop-cleanup/wave-N/<subagent>.md` to the same `.slop-cleanup/wave-N/<subagent>.md` path in the orchestrator checkout, using the worktree path the subagent returned, so later waves and the final report can read it. Then run the wave's test gate, and once it passes, clean up the wave's worktrees (below).
- Edit budget: each subagent may edit directly. They must commit their changes with a dedicated message prefixed with their category.
- Deletion cap: if this category would delete more than 50 items or cross a module boundary, return the list without deleting.

Wait for all four to finish. Run tests and typecheck, and check the test count (*Test Count per Wave*). If anything broke or the count dropped without a listed deleted test, stop and report which subagent's commit introduced the failure (bisect by commit).

**A subagent that fails.** If a subagent errors, returns nothing, or reports that it stopped before finishing, cherry-pick none of its commits, since a partial category is not landed, and keep its worktree and branch if it has them. Finish the wave with the other subagents (cherry-picks, report copies, test gate, worktree cleanup), mark that category `× fail` in the wave report, then stop before the next wave: name the kept worktree and branch, and ask the user whether to re-dispatch that category from the current cleanup-branch tip or continue without it.

**Deletion-cap approval.** A subagent over the cap edits nothing and returns its deletion list. Finish the wave with the other subagents first (cherry-picks, report copies, test gate, worktree cleanup, including the capped subagent's worktree, which holds no commits). Then show the list to the user. On approval, re-dispatch that subagent with the approved list and `base_sha` set to the current tip, cherry-pick its commits, copy its report, re-run the wave's test gate, and clean up its worktree; on refusal, record the list as skipped deletions in its report. Only then start the next wave.

**Worktree cleanup.** After the copy and the passing test gate, for each worktree path and branch a subagent returned: confirm `git cherry <cleanup-branch> <branch>` prints no `+` lines (every commit landed), delete the copied report from that worktree (it is untracked and would block removal), run `git worktree remove <path>` without `--force`, then `git branch -D <branch>`. If any check or the removal fails, keep that worktree and branch and list them. When a wave stops early (test failure, cherry-pick conflict), keep all its worktrees and name them in the stop report.

### 3. Dispatch Wave 2 in parallel

Spawn subagents 1, 2, 6, and 7. Same protocol — parallel dispatch, `base_sha` set to the cleanup-branch tip after Wave 1's cherry-picks and passing test gate, per-category reports at `.slop-cleanup/wave-2/<subagent>.md`, dedicated commits. Pass `wave_1_reports` as absolute paths under the orchestrator checkout's `.slop-cleanup/wave-1/`, since the copied Wave 1 reports are not in the subagents' worktrees.

Wait for all four to finish. Run tests and typecheck, and check the test count. Stop on failure; otherwise clean up the wave's worktrees the same way.

### 4. Assemble the final report

Read each subagent's category report and produce `SLOP_CLEANUP.md` at the repo root with this structure. `## Deleted Tests` takes every row of every category report's `## Deleted Tests`, none dropped or merged, and the counts come from *Test Count per Wave*:

```markdown
# Slop Cleanup Report

**Branch:** chore/code-review-cleanup-YYYYMMDD
**Commits:** N  (list with category and one-line summary)
**Tests:** ✓ passing  |  **Typecheck:** ✓ clean
**Test count:** Wave 1: N → N (N deleted)  |  Wave 2: N → N (N deleted)
**Worktrees:** N removed  |  kept: path and branch of each, or none

## Summary
- Files deleted: N
- Lines removed: N
- Lines added: N
- Types consolidated: N
- Duplicates merged: N
- Try/catch removed: N
- Circular deps broken: N
- Weak types replaced: N
- Slop comments removed: N
- Tests deleted: N

## Deleted Tests
| Test | Location | Covered deleted code | Count | Category | Wave |
|------|----------|----------------------|-------|----------|------|
| test_format_legacy_date | tests/utils/test_date.py:12 | formatLegacyDate, src/utils/date.ts:45 | 1 | Unused code | 1 |

Write `None` when no test was deleted.

## By Category
### 1. Unused Code (subagent 3)
...one-line commit summary, then findings table with file/line/what/why...

### 2. Circular Dependencies (subagent 4)
...

### (etc for all 8 categories)

## Risk Flags
Anything each subagent flagged as "delete at your own risk" (external callers unknown, reflective access, dynamic imports).

## Next Steps
- Review the branch
- Run a full regression suite
- Merge or cherry-pick categories
- Inspect any kept worktrees, then remove them with `git worktree remove` and `git branch -D`
```

### 5. Hand off to the user

Show the report path, the branch name, the removed and kept worktrees, and summarize: *"Cleaned up N categories across M files, removed L lines, tests passing on branch X. Review `SLOP_CLEANUP.md` and merge when ready."*

## Graceful Degradation

- **No Agent tool available:** Run categories sequentially inline. Tell the user this will be slower and offer to narrow scope.
- **Tool missing (e.g., no knip):** The affected subagent falls back to grep + manual cross-reference. It notes the degraded mode in its report.
- **Tests fail after a wave:** Stop the pipeline. Do not start the next wave. Report which commit broke the build.
- **A subagent returns an empty finding list:** That's fine — some codebases really don't have slop in a given category. Record it in the report and move on.
- **Working tree was dirty at start:** Refuse and ask the user to commit or stash first.

## Writing Style for Edits

All subagents share these editing conventions:

- **Prefer deletion over rewriting.** If code isn't needed, remove it. Don't "refactor into a cleaner version" what should just be gone.
- **One change per commit within a category.** If a subagent makes multiple semantic changes, split them into multiple commits.
- **Explain the why in the commit message, not the code.** A commit message can say "Remove fallback for legacy v1 API (removed in #1234)". The code itself doesn't need a comment.
- **Do not add comments to explain the deletion.** No `// removed legacy handler`. The git log is the explanation.
- **No backwards-compatibility shims** unless the user explicitly asks for them. Clean means clean.
- **Trust the type system and framework guarantees.** If a value is declared non-null by a schema, don't add a `if (!x) throw` check.

## Step Completion Reports

After each wave and at the end, output a status report in this format:

```
◆ Wave 1 (step 1 of 3 — parallel cleanup)
··································································
  Unused code killer:      √ pass (removed 47 symbols, 12 files)
  Circular dep untangler:  √ pass (broke 3 cycles)
  Weak type strengthener:  √ pass (replaced 89 anys with specific types)
  Slop comment cleaner:    √ pass (removed 234 slop comments)
  Tests after wave:        √ pass
  Test count:              √ pass (412 → 405, 7 deleted tests listed)
  Typecheck after wave:    √ pass
  Worktrees removed:       √ pass (4 of 4)
  ____________________________
  Result:                  PASS
```

```
◆ Wave 2 (step 2 of 3 — structural consolidation)
··································································
  Deduplicator:                  √ pass (merged 18 duplicate blocks)
  Type consolidator:             √ pass (moved 23 types to shared/)
  Defensive programming remover: × fail — 3 tests broke, reverted
  Legacy code remover:           √ pass (deleted 2 fallback paths)
  Tests after wave:              × fail — blocked by defensive remover revert
  Test count:                    √ pass (405 → 403, 2 deleted tests listed)
  ____________________________
  Result:                        PARTIAL
```

```
◆ Final Report (step 3 of 3 — assembly)
··································································
  SLOP_CLEANUP.md written:   √ pass
  All commits have messages: √ pass
  Summary delivered to user: √ pass
  ____________________________
  Result:                    PASS
```

Use `√` for pass, `×` for fail. Keep the adapted check names specific to what actually ran.

## Expected Output

After a full run on a TypeScript monorepo, the final `SLOP_CLEANUP.md` summary looks like:

```markdown
# Slop Cleanup Report

**Branch:** chore/code-review-cleanup-20260419
**Commits:** 23  (across 8 categories)
**Tests:** passing  |  **Typecheck:** clean
**Test count:** Wave 1: 412 → 405 (7 deleted)  |  Wave 2: 405 → 401 (4 deleted)

## Summary
- Files deleted: 12
- Lines removed: 847
- Lines added: 134
- Types consolidated: 9
- Duplicates merged: 23
- Try/catch removed: 17
- Circular deps broken: 4
- Weak types replaced: 61
- Slop comments removed: 198
- Tests deleted: 11
```

And the terminal handoff message: "Cleaned up 8 categories across 43 files, removed 847 lines, tests passing on branch chore/code-review-cleanup-20260419. Review `SLOP_CLEANUP.md` and merge when ready."

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] Working tree is clean at start; the run is on a dedicated cleanup branch (e.g., `chore/code-review-cleanup-YYYYMMDD`), not on `main`/`master`.
- [ ] Every commit belongs to exactly one of the 8 cleanup categories and carries its prefix — never one monolithic commit.
- [ ] Test suite and typecheck pass between Wave 1 and Wave 2; the pipeline stops if either fails.
- [ ] Each wave recorded its test count before and after, and a drop the listed deleted tests do not explain stopped the pipeline.
- [ ] `SLOP_CLEANUP.md` lists every deleted test under `## Deleted Tests` with the deleted code it covered.
- [ ] Final `SLOP_CLEANUP.md` report exists and lists per-category counts (files touched, lines removed, deletions skipped).
- [ ] Deletions exceeding 50 items or crossing module boundaries were surfaced for user approval before being applied.
- [ ] Subagents missing their required tool (knip, madge, ts-prune, vulture, ruff) fall back to manual analysis and note "degraded mode" in their category report.

## Edge Cases

- **Dirty working tree at start**: Skill refuses to proceed and instructs the user to commit or stash before running.
- **No Agent tool available**: Falls back to running all 8 categories sequentially in a single conversation; warns user the process will be slower.
- **Required tool missing (e.g., knip not installed)**: Affected subagent falls back to grep-based manual cross-reference and notes degraded mode in its category report.
- **Tests fail after a wave**: Pipeline stops immediately; the failing commit is identified by bisect; subsequent waves do not run on a broken tree.
- **Test count drops more than the listed deleted tests**: the wave's gate fails; the pipeline stops and names the before, after and listed counts.
- **Runner reports no test count**: the count is `unknown` with the reason; the wave report marks `Test count` `×` (`PARTIAL`) and `SLOP_CLEANUP.md` says so.
- **Subagent finds nothing in its category**: Records an empty findings table and moves on — not every codebase has every type of slop.
- **Deletion count exceeds 50 or crosses module boundaries**: the subagent returns the deletion list without applying it; once the rest of the wave has landed and passed its test gate, the orchestrator shows it to the user and re-dispatches with the approved list (*Deletion-cap approval*).
- **A subagent errors, returns nothing, or stops partway**: none of its commits are cherry-picked; the rest of the wave lands, then the pipeline stops before the next wave and asks the user (*A subagent that fails*).
- **A self-check can't run in a subagent's worktree** (no `node_modules` or `.venv` there): the subagent runs tools by absolute path under `tool_root`, notes any check that still can't run as an environment gap, and keeps its edits; the wave test gate in the orchestrator checkout decides.
- **Cherry-pick conflicts with an earlier category** (e.g., a modify/delete conflict): abort the cherry-pick, stop, name the two categories and the conflicting files, and ask the user.
