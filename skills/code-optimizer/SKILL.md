---
name: code-optimizer
description: Analyze code for performance issues and suggest optimizations. Use when users ask to "optimize this code", "find performance issues", "improve performance", "check for memory leaks", "review code efficiency", or want to identify bottlenecks, algorithmic improvements, caching opportunities, or concurrency problems.
license: MIT
metadata:
  version: 1.2.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
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
