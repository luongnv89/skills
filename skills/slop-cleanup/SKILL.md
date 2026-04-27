---
name: slop-cleanup
description: "Clean up a codebase by removing AI slop, dead code, weak types, duplication, defensive over-engineering, and legacy cruft using 8 parallel specialized subagents across two cleanup waves. Don't use for adding new features, performance tuning, or security-only audits."
effort: high
license: MIT
metadata:
  version: 1.1.0
  author: Luong NGUYEN <luongnv89@gmail.com>
  architecture: "subagent (Pattern B: Parallel Workers, 8 specialized cleaners)"
---

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

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Safety & Confirmation Gates

This skill **deletes and rewrites code aggressively**. That is the point. But because deletions are harder to reverse than additions, enforce these gates:

1. **Never run on uncommitted changes.** If `git status` is not clean, stop and ask the user to commit or stash.
2. **Create a dedicated cleanup branch** before any edits (e.g., `chore/slop-cleanup-YYYYMMDD`). Never work directly on `main`/`master`.
3. **One category per commit.** Each subagent's changes land in their own commit with a clear message. This makes individual categories revertible without losing the rest.
4. **Test gate between phases.** After each subagent completes, run the test suite and typecheck (if available). If tests fail, stop the pipeline and surface the failure — do not continue to the next subagent on a broken tree.
5. **Report before destructive deletion.** For subagents that delete code (unused code, legacy, duplicates), surface the deletion list to the user for approval when the deletion count exceeds 50 items or crosses module boundaries.

## Environment Check

Before starting:

1. **Detect language/stack** — read `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, etc. The subagents tailor tool choices (knip, madge, ts-prune, vulture, ruff, etc.) to the stack.
2. **Verify tooling** — if a subagent depends on a tool (knip for JS/TS unused code, madge for circular deps), confirm it's installed or can be run via `npx`. If not, fall back to manual analysis and note this in the report.
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

## Orchestration Workflow

### 1. Prepare

```bash
# Refuse if working tree is dirty
git diff-index --quiet HEAD -- || { echo "Commit or stash changes first"; exit 1; }

# Create cleanup branch
date_tag=$(date +%Y%m%d)
git checkout -b "chore/slop-cleanup-${date_tag}"
```

Detect the stack (language, package manager, test command, typecheck command) and write a one-line summary the user sees before dispatch begins.

### 2. Dispatch Wave 1 in parallel

Spawn subagents 3, 4, 5, and 8 in a single turn (multiple Agent tool calls in one message). Each receives:

- Absolute repo path
- Stack summary (language, tooling, test command)
- Instructions to write findings and edits to their own branch area and produce a per-category report at `.slop-cleanup/wave-1/<subagent>.md`
- Edit budget: each subagent may edit directly. They must commit their changes with a dedicated message prefixed with their category.

Wait for all four to finish. Run tests and typecheck. If anything broke, stop and report which subagent's commit introduced the failure (bisect by commit).

### 3. Dispatch Wave 2 in parallel

Spawn subagents 1, 2, 6, and 7. Same protocol — parallel dispatch, per-category reports at `.slop-cleanup/wave-2/<subagent>.md`, dedicated commits.

Wait for all four to finish. Run tests and typecheck. Stop on failure.

### 4. Assemble the final report

Read each subagent's category report and produce `SLOP_CLEANUP.md` at the repo root with this structure:

```markdown
# Slop Cleanup Report

**Branch:** chore/slop-cleanup-YYYYMMDD
**Commits:** N  (list with category and one-line summary)
**Tests:** ✓ passing  |  **Typecheck:** ✓ clean

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
```

### 5. Hand off to the user

Show the report path, the branch name, and summarize: *"Cleaned up N categories across M files, removed L lines, tests passing on branch X. Review `SLOP_CLEANUP.md` and merge when ready."*

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
  Typecheck after wave:    √ pass
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
  ____________________________
  Result:                        PARTIAL
```

```
◆ Final Report (step 3 of 3 — assembly)
··································································
  SLOP_CLEANUP.md written:   √ pass
  All commits have messages: √ pass
  Branch pushed:             √ pass
  Summary delivered to user: √ pass
  ____________________________
  Result:                    PASS
```

Use `√` for pass, `×` for fail. Keep the adapted check names specific to what actually ran.

## Expected Output

After a full run on a TypeScript monorepo, the final `SLOP_CLEANUP.md` summary looks like:

```markdown
# Slop Cleanup Report

**Branch:** chore/slop-cleanup-20260419
**Commits:** 8  (one per category)
**Tests:** passing  |  **Typecheck:** clean

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
```

And the terminal handoff message: "Cleaned up 8 categories across 43 files, removed 847 lines, tests passing on branch chore/slop-cleanup-20260419. Review `SLOP_CLEANUP.md` and merge when ready."

## Edge Cases

- **Dirty working tree at start**: Skill refuses to proceed and instructs the user to commit or stash before running.
- **No Agent tool available**: Falls back to running all 8 categories sequentially in a single conversation; warns user the process will be slower.
- **Required tool missing (e.g., knip not installed)**: Affected subagent falls back to grep-based manual cross-reference and notes degraded mode in its category report.
- **Tests fail after a wave**: Pipeline stops immediately; the failing commit is identified by bisect; subsequent waves do not run on a broken tree.
- **Subagent finds nothing in its category**: Records an empty findings table and moves on — not every codebase has every type of slop.
- **Deletion count exceeds 50 or crosses module boundaries**: Subagent surfaces the deletion list to the user for explicit approval before writing changes.
