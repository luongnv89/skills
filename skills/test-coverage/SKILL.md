---
name: test-coverage
description: "Generate unit tests for untested branches and edge cases. Use when coverage is low, CI flags gaps, or a release needs hardening. Not for integration/E2E suites, framework migrations, or fixing production bugs."
license: MIT
effort: low
metadata:
  version: 1.2.3
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Test Coverage Expander

Expand unit test coverage by targeting untested branches and edge cases.

## When to Use

- User asks to "increase test coverage", "add more tests", "expand unit tests", or "cover edge cases"
- A CI pipeline reports low coverage and the user wants it improved
- A code review flags untested error paths or boundary conditions
- The user wants to identify and fill gaps in an existing test suite before a release

## Instructions

1. Sync the branch with remote (see Repo Sync section below)
2. Create a feature branch for the new tests
3. Run the project's coverage tool to get a baseline report
4. Identify the lowest-coverage files and untested code paths
5. Write tests for error paths, boundary values, and missing branches
6. Re-run coverage to confirm improvement
7. Commit the new tests with a descriptive message

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

### 0. Create Feature Branch

Before making any changes:
1. Check the current branch - if already on a feature branch for this task, skip
2. Check the repo for branch naming conventions (e.g., `feat/`, `feature/`, etc.)
3. Create and switch to a new branch following the repo's convention, or fallback to: `feat/test-coverage`

### 1. Analyze Coverage

Detect the project's test runner and run the coverage report:
- **JavaScript/TypeScript**: `npx jest --coverage` or `npx vitest --coverage`
- **Python**: `pytest --cov=. --cov-report=term-missing`
- **Go**: `go test -coverprofile=coverage.out ./...`
- **Rust**: `cargo tarpaulin` or `cargo llvm-cov`

From the report, identify:
- Untested branches and code paths
- Low-coverage files/functions (prioritize files below 60%)
- Missing error handling tests

### 2. Identify Test Gaps

Review code for:
- Logical branches (if/else, switch)
- Error paths and exceptions
- Boundary values (min, max, zero, empty, null)
- Edge cases and corner cases
- State transitions and side effects

### 3. Write Tests

Use project's testing framework:
- **JavaScript/TypeScript**: Jest, Vitest, Mocha
- **Python**: pytest, unittest
- **Go**: testing, testify
- **Rust**: built-in test framework

Target scenarios:
- Error handling and exceptions
- Boundary conditions
- Null/undefined/empty inputs
- Concurrent/async edge cases

### 4. Verify Improvement

Run coverage again and confirm measurable increase. Report:
- Before/after coverage percentages
- Number of new test cases added
- Files with the biggest coverage gains

## Expected Output

After a successful run on a Python project, the final verification report shows:

```
Coverage before: 61% (47/77 statements)
Coverage after:  84% (65/77 statements)

New tests added: 9
Files improved:
  - src/parser.py        52% → 91%  (+7 tests: null input, empty string, unicode overflow)
  - src/auth.py          71% → 88%  (+2 tests: expired token, missing header)

All 56 tests passing. No regressions.
```

## Edge Cases

- **No test framework detected**: Skill checks `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` for test dependencies; if none found, asks the user which framework to use before writing any tests.
- **Coverage tool not installed**: Installs the appropriate tool (`pytest-cov`, `nyc`, `cargo tarpaulin`, etc.) and retries rather than failing silently.
- **Existing tests are already failing**: Does not add new tests until existing failures are resolved; reports the failing tests to the user first.
- **100% coverage already reached**: Reports this to the user and exits — no tests are added unnecessarily.
- **Generated code or vendored files in coverage report**: Excludes auto-generated and third-party directories from analysis to avoid writing tests for code the project does not own.
- **Async / concurrent code paths**: Uses framework-appropriate async test utilities (e.g., `pytest-asyncio`, `jest fakeTimers`) rather than bare sync wrappers.

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

**Branch Setup phase checks:** `Feature branch created`, `Base coverage measured`

**Analysis phase checks:** `Coverage report parsed`, `Gaps identified`, `Priority ranked`

**Test Writing phase checks:** `Tests written`, `Edge cases covered`, `Framework conventions followed`

**Verification phase checks:** `Tests pass`, `Coverage improved`, `No regressions`

## Error Handling

### No test framework detected
**Solution:** Check `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` for test dependencies. If none found, ask the user which framework to use and install it.

### Coverage tool not installed
**Solution:** Install the appropriate coverage tool (`nyc`, `pytest-cov`, etc.) and retry.

### Existing tests failing
**Solution:** Do not add new tests until existing failures are resolved. Report failing tests to the user first.

## Guidelines

- Follow existing test patterns and naming conventions
- Place test files alongside source or in the project's existing test directory
- Group related test cases logically
- Use descriptive test names that explain the scenario
- Do not mock what you do not own — prefer integration tests for external boundaries
