
# Code Optimization

Analyze code for performance issues following this priority order:

## Analysis Priorities

1. **Performance bottlenecks** - O(n²) operations, inefficient loops, unnecessary iterations
2. **Memory leaks** - unreleased resources, circular references, growing collections
3. **Algorithm improvements** - better algorithms or data structures for the use case
4. **Caching opportunities** - repeated computations, redundant I/O, memoization candidates
5. **Concurrency issues** - race conditions, deadlocks, thread safety problems

## Analysis Boundary (mandatory)

Performance analysis is source-read-only. Record `git rev-parse HEAD`, `git status`, and local
tracking observations without claiming remote freshness. Do not fetch, stash, pull, rebase,
checkout/switch, create or delete branches/worktrees, or mutate the index, refs, stash, branch,
or worktree during analysis. A named report artifact may be written only when this mode's output
contract specifies one; otherwise findings are report output, not source files.

Any source mutation is a separate, explicitly approved workflow. It must establish its own
freshness check and stash-first sync contract before edits; this mode never performs that work.

## Workflow

### Prerequisites

Before analysis:
1. Record the current `HEAD`, status, and local tracking observations without claiming remote freshness.
2. Confirm the target code, language, runtime context, and review scope.
3. Do not create or switch branches/worktrees; mutation belongs to the handoff below.

### 1. Analysis

1. Read the target code file(s) or directory
2. Identify language, framework, and runtime context (Node.js, CPython, browser, etc.)
3. Analyze for each priority category in order
4. For each issue found, estimate the performance impact (e.g., "reduces API response from ~500ms to ~50ms")
5. Report findings sorted by severity (Critical first)

### 2. Mutation Handoff (separate, explicit approval)

This mode stops after presenting the optimization report; it never applies fixes or creates or
switches branches. If the user separately approves a mutation workflow, that workflow must
re-check `HEAD`, status, and local tracking observations, detect incoming changes, and use its
stash-first sync contract before edits. It owns branch creation, source changes, per-fix tests,
security scans, and rollback. No mutation step may be inferred from this report or run as part of
performance analysis.

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

**Phase: Prerequisites** — checks: `Scope recorded`, `Tracking observation recorded`, `No mutation started`

**Phase: Analysis** — checks: `Issue detection`, `Priority categories covered`, `Impact estimated`, `Findings sorted by severity`

**Phase: Mutation Handoff** — checks: `Fix application deferred`, `User approval required`, `Freshness and stash-first contract`, `Existing tests required`, `No regressions requirement`, `Warnings documented`

## Severity Levels

- **Critical**: Causes crashes, severe memory leaks, or O(n³)+ complexity
- **High**: Significant performance impact (O(n²), blocking operations, resource exhaustion)
- **Medium**: Noticeable impact under load (redundant operations, suboptimal algorithms)
- **Low**: Minor improvements (micro-optimizations, style improvements with perf benefit)

## Language-Specific Checks

Read `references/language-checks.md` for the detected language's specific checks (covers JavaScript/TypeScript, Python, Go, Rust, Java, and general cross-language patterns) — load only the section matching the target code's language.

## Acceptance Criteria

A run is acceptable only when all of the following are verifiable:

- Produces an optimization report grouped by severity (Critical, High, Medium, Low) — assert at least one severity bucket appears or the "no issues found" branch fires.
- Each reported issue includes `Location`, `Category`, `Problem`, `Impact`, and `Fix` — verify by checking the rendered template fields are non-empty.
- Impact statement includes a quantitative estimate (e.g., "~500ms → ~50ms", "O(n²) → O(n log n)") — assert the Impact line contains a number, complexity class, or before/after pair.
- This mode applies no fixes; any separately approved mutation handoff requires explicit user approval before edits.
- A separately approved mutation workflow runs existing tests after each applied fix and reports the result; if no tests exist, it warns before applying changes.
- A separately approved mutation workflow checks out a feature branch following the repo convention before edits; this mode does not create or switch branches.
- The mutation handoff carries a fresh HEAD/status/tracking check and a stash-first sync contract.
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
- **Tests are absent**: the mutation handoff warns before applying any fix and requires explicit confirmation; this analysis mode never applies changes silently.
- **Optimization regresses tests**: the separately approved mutation workflow confirms the diff scope, preserves work through its stash-first recovery contract, and requires approval before reverting; this mode never runs checkout, stash, or discard operations.
- **Repo lacks `origin` or sync fails**: the mutation workflow stops before edits and reports the recovery path; performance analysis records its local observations and does not attempt recovery.
- **Mixed-language project**: analyze each language with its own checklist; do not apply JavaScript heuristics to Python code.
- **Premature optimization candidates**: skip micro-optimizations unless a measurable hot path is identified — flag them as Low only when a profile or benchmark backs the claim.
