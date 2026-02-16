---
name: test-coverage
version: 1.2.0
description: Expand unit test coverage by targeting untested branches and edge cases. Use when users ask to "increase test coverage", "add more tests", "expand unit tests", "cover edge cases", "improve test coverage", or want to identify and fill gaps in existing test suites. Adapts to project's testing framework.
---

# Test Coverage Expander

Expand unit test coverage by targeting untested branches and edge cases.

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
