---
name: code-optimizer
description: "Analyze code for performance bottlenecks, memory leaks, and algorithmic inefficiencies. Use when asked to optimize, find bottlenecks, or improve efficiency. Don't use for bug-hunting code review, security audits, or refactoring without a perf goal."
license: MIT
effort: medium
metadata:
  version: 1.3.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Code Optimization

Analyze code for performance issues following this priority order:

## Analysis Priorities

1. **Performance bottlenecks** - O(n²) operations, inefficient loops, unnecessary iterations
2. **Memory leaks** - unreleased resources, circular references, growing collections
3. **Algorithm improvements** - better algorithms or data structures for the use case
4. **Caching opportunities** - repeated computations, redundant I/O, memoization candidates
5. **Concurrency issues** - race conditions, deadlocks, thread safety problems

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

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

## Workflow

### Prerequisites

Before making any changes:
1. Check the current branch - if already on a feature branch for this task, skip
2. Check the repo for branch naming conventions (e.g., `feat/`, `feature/`, etc.)
3. Create and switch to a new branch following the repo's convention, or fallback to: `feat/optimize-<target>`
   - Example: `feat/optimize-api-handlers`

### 1. Analysis

1. Read the target code file(s) or directory
2. Identify language, framework, and runtime context (Node.js, CPython, browser, etc.)
3. Analyze for each priority category in order
4. For each issue found, estimate the performance impact (e.g., "reduces API response from ~500ms to ~50ms")
5. Report findings sorted by severity (Critical first)

### 2. Apply Fixes

1. Present the optimization report to the user
2. On approval, apply fixes starting with Critical/High severity
3. Run existing tests after each change to verify no regressions
4. If no tests exist, warn the user before applying changes

## Response Format

For each issue found:

```
### [Severity] Issue Title
**Location**: file:line_number
**Category**: Performance | Memory | Algorithm | Caching | Concurrency

**Problem**: Brief explanation of the issue

**Impact**: Why this matters (performance cost, resource usage, etc.)

**Fix**:
[Code example showing the optimized version]
```

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Prerequisites** — checks: `Branch setup`, `Naming convention detected`, `Feature branch created`

**Phase: Analysis** — checks: `Issue detection`, `Priority categories covered`, `Impact estimated`, `Findings sorted by severity`

**Phase: Apply Fixes** — checks: `Fix application`, `User approval obtained`, `Existing tests run`, `No regressions introduced`

**Phase: Verify** — checks: `Performance verified`, `Test suite passes`, `Critical issues resolved`, `Warnings documented`

## Severity Levels

- **Critical**: Causes crashes, severe memory leaks, or O(n³)+ complexity
- **High**: Significant performance impact (O(n²), blocking operations, resource exhaustion)
- **Medium**: Noticeable impact under load (redundant operations, suboptimal algorithms)
- **Low**: Minor improvements (micro-optimizations, style improvements with perf benefit)

## Language-Specific Checks

### JavaScript/TypeScript
- Array methods inside loops (map/filter/find in forEach)
- Missing async/await causing blocking
- Event listener leaks
- Unbounded arrays/objects

### Python
- List comprehensions vs generator expressions for large data
- Global interpreter lock considerations
- Context manager usage for resources
- N+1 query patterns

### Go
- Goroutine leaks (unbounded `go func()` without context cancellation)
- Unnecessary allocations in hot paths (use `sync.Pool`, pre-allocate slices)
- String concatenation in loops (use `strings.Builder`)
- Missing `defer` for resource cleanup

### Rust
- Unnecessary cloning (use references or `Cow<>` instead)
- Lock contention with `Mutex` when `RwLock` would suffice
- Unbounded `Vec` growth without `with_capacity`
- Blocking operations in async contexts

### Java
- Autoboxing in tight loops (use primitive types)
- String concatenation with `+` in loops (use `StringBuilder`)
- Synchronized blocks that are too broad
- Stream API misuse (unnecessary intermediate collections)

### General
- Premature optimization warnings (only flag if genuinely impactful)
- Database query patterns (N+1, missing indexes)
- I/O in hot paths

## Error Handling

### No obvious performance issues found
**Solution:** Report that the code is already well-optimized. Suggest profiling with runtime tools (e.g., `perf`, Chrome DevTools, `py-spy`) to find runtime-specific bottlenecks.

### Target file is too large (>2000 lines)
**Solution:** Ask the user to specify which functions or sections to focus on. Analyze the most performance-critical paths first.

### Optimization breaks existing tests
**Solution:** Revert the change immediately. Re-examine the optimization and adjust the approach to preserve existing behavior.

## Acceptance Criteria

A run is acceptable only when all of the following are verifiable:

- Produces an optimization report grouped by severity (Critical, High, Medium, Low) — assert at least one severity bucket appears or the "no issues found" branch fires.
- Each reported issue includes `Location`, `Category`, `Problem`, `Impact`, and `Fix` — verify by checking the rendered template fields are non-empty.
- Impact statement includes a quantitative estimate (e.g., "~500ms → ~50ms", "O(n²) → O(n log n)") — assert the Impact line contains a number, complexity class, or before/after pair.
- Fixes are applied only after explicit user approval — verify the agent emits an approval prompt before any `Edit`/`Write` tool call.
- Existing tests run after each applied fix and the result is reported — verify a test command was executed and its pass/fail status is logged.
- A feature branch following the repo convention is checked out before edits — verify with `git rev-parse --abbrev-ref HEAD` matching `feat/*` or repo equivalent.
- Each phase emits a Step Completion Report block with `Result: PASS | FAIL | PARTIAL` — assert the block is present in the transcript.

## Expected Output

Given a Node.js file `src/api/handlers.js` with an N+1 query in `listUsers()`, the skill should emit:

```
◆ Analysis (step 1 of 3 — src/api/handlers.js)
··································································
  Issue detection:           √ pass (3 issues found)
  Priority categories:       √ pass (Performance, Caching covered)
  Impact estimated:          √ pass
  Findings sorted:           √ pass
  Criteria:                  4/4 met
  ____________________________
  Result:                    PASS

### [Critical] N+1 query in listUsers
**Location**: src/api/handlers.js:42
**Category**: Performance

**Problem**: `users.forEach(u => db.query(...))` issues one query per user.

**Impact**: For 1000 users, ~1000 round-trips (~2000ms) → 1 batched query (~50ms). 40x speedup.

**Fix**:
\`\`\`js
const ids = users.map(u => u.id);
const rows = await db.query('SELECT * FROM orders WHERE user_id = ANY($1)', [ids]);
\`\`\`
```

Expected result: a markdown report with one block per issue, sorted Critical → Low, followed by a phase completion report. See `docs/README.md` for a longer end-to-end example.

## Edge Cases

- **No performance issues found**: emit a "code is already well-optimized" note and recommend runtime profiling tools (`perf`, `py-spy`, Chrome DevTools) — do NOT invent low-severity findings to fill the report.
- **File exceeds 2000 lines**: stop and ask the user which functions/sections to focus on; do not silently truncate.
- **Tests are absent**: warn the user before applying any fix and require explicit confirmation; never apply changes silently.
- **Optimization regresses tests**: revert the specific change immediately via `git checkout -- <file>` after `git diff` confirms the scope and the user confirms the revert; never force-push, and back up the diff with `git stash` before discarding so work is recoverable.
- **Repo lacks `origin` or rebase fails**: stop and ask the user to confirm before any recovery; run `git status` and `git stash --dry-run`-style inspection first, take a backup branch (`git branch backup/pre-recovery`), and never run destructive `reset --hard` or `rm` without explicit confirmation.
- **Mixed-language project**: analyze each language with its own checklist; do not apply JavaScript heuristics to Python code.
- **Premature optimization candidates**: skip micro-optimizations unless a measurable hot path is identified — flag them as Low only when a profile or benchmark backs the claim.
