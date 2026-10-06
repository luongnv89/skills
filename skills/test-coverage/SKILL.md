---
name: test-coverage
description: "Generate unit tests for untested branches and edge cases. Use when coverage is low, CI flags gaps, or a release needs hardening. Not for integration/E2E suites, framework migrations, or fixing production bugs."
license: MIT
effort: low
metadata:
  version: 1.4.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Test Coverage Expander

Expand unit test coverage by targeting untested branches and edge cases.

## When to Use

- User asks to "increase test coverage", "add more tests", "expand unit tests", or "cover edge cases"
- A CI pipeline reports low coverage and the user wants it improved
- A code review flags untested error paths or boundary conditions
- The user wants to identify and fill gaps in an existing test suite before a release

## Stack (detect before Step 1 of Workflow)

Detect the project's language from its manifest file and use the matching commands throughout the Workflow below:

| Manifest | Stack | Coverage command | Test framework |
|---|---|---|---|
| `package.json` | JavaScript/TypeScript | `npx jest --coverage` or `npx vitest --coverage` | Jest, Vitest, Mocha |
| `pyproject.toml` | Python | `pytest --cov=. --cov-report=term-missing` | pytest, unittest |
| `go.mod` | Go | `go test -coverprofile=coverage.out ./...` | testing, testify |
| `Cargo.toml` | Rust | `cargo tarpaulin` or `cargo llvm-cov` | built-in test framework |

If none of these manifests is found, see [Edge Cases](#edge-cases) — "No test framework detected".

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote. First save `git status --porcelain` as the pre-sync list; Step 4 never stages those paths.

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
1. Run `git rev-parse --abbrev-ref HEAD`. If it prints a branch other than `main` or `master` that was created for this task, skip to Step 1.
2. Run `git branch -a` and note the prefix most existing branches use (e.g., `feat/`, `feature/`, `test/`).
3. Create and switch to a new branch with that prefix. If no prefix is in use, name it `feat/test-coverage`.

### 1. Analyze Coverage

Run the coverage command for the detected [Stack](#stack-detect-before-step-1-of-workflow) above. Record the total coverage percentage and the pass/fail counts as the baseline. If any test fails, stop here (see [Edge Cases](#edge-cases)).

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

Use the test framework for the detected [Stack](#stack-detect-before-step-1-of-workflow) above.

Target scenarios:
- Error handling and exceptions
- Boundary conditions
- Null/undefined/empty inputs
- Concurrent/async edge cases

### 4. Verify Improvement

1. Run the full test suite. If a new test fails, fix or remove it, then rerun. If a previously passing test now fails, report PARTIAL and name it.
2. Run the same coverage command as Step 1.
3. Compare the new total with the Step 1 baseline. If it is not strictly higher, report PARTIAL and list the Step 2 gaps that are still untested.
4. If the full suite passed in item 1, commit the new tests on the feature branch with a message that records the before/after coverage percentages and the files newly covered. Stage each test file this run wrote by explicit path (`git add tests/test_parser.py`); never `git add -A`, `git add .` or `git commit -a`, which would sweep in user work Repo Sync restored. Never stage a path on the pre-sync list. Stage a changed manifest or lockfile (*Coverage tool not installed*) only with its reason in the commit message. Check `git diff --cached --name-only` before committing. Under `Uncertainty:`, list each changed file left unstaged, or every new test file when the commit is skipped (failed suite or regression).
5. Print the final report. It opens with `Result:` — `COMPLETE`, `PARTIAL — reason`, or `BLOCKED — reason` — followed by:
   - `Evidence:` the commands that ran, with before/after totals and pass/fail counts
   - `Uncertainty:` what was not checked (e.g., excluded paths, CI not run, covered lines without output assertions)
   - `Decision:` the action that needs approval, or `No approval needed`, then any remaining user action (e.g., push the branch, open a PR)
   - The number of new test cases and the files with the biggest coverage gains

## Expected Output

After a successful run on a Python project, the final verification report shows:

```
Result:       COMPLETE — coverage 61% → 84%, all tests pass
Evidence:     pytest --cov=. --cov-report=term-missing (before): 61% (47/77 statements), 47 passed
              same command (after): 84% (65/77 statements), 56 passed, 0 failed
Uncertainty:  CI not run; src/vendor/ excluded from coverage
Decision:     No approval needed. Next: push feat/test-coverage and open a PR.

New tests added: 9
Files improved:
  - src/parser.py        52% → 91%  (+7 tests: null input, empty string, unicode overflow)
  - src/auth.py          71% → 88%  (+2 tests: expired token, missing header)
```

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] Coverage report exists from a runnable command for the detected stack (e.g., `jest --coverage`, `pytest --cov`, `go test -cover`).
- [ ] Post-run total coverage is strictly higher than the pre-run baseline — no test additions that fail to move the metric. A 100% baseline is the one exception (see Edge Cases).
- [ ] New tests target previously-untested branches, error paths, or boundary values — not duplicates of existing assertions.
- [ ] The full test suite passes locally before committing (`npm test`, `pytest`, `go test ./...`, etc.).
- [ ] All new tests live on a feature branch (e.g., `feat/test-coverage`), never on `main`/`master`.
- [ ] Commit message records the before/after coverage percentages and the files newly covered.
- [ ] The commit holds only files this run wrote, staged by explicit path.

If any item fails, the final report says `PARTIAL` or `BLOCKED` and names the reason.

The final report must also be understandable:

- The first line gives `COMPLETE`, `PARTIAL` or `BLOCKED` and the reason.
- `Evidence:` (commands run and their observed totals) is separate from `Uncertainty:` (assumptions and unchecked behavior).
- Each coverage number traces to a command output: the before/after totals and the per-file percentages.
- `Decision:` names the approval needed or says `No approval needed`, and names any remaining user action.

These are instruction checks. Without reviewer feedback, human understanding of the report stays unconfirmed; agent inspection cannot confirm it.

## Edge Cases

- **No test framework detected**: Skill checks `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` for test dependencies; if none found, asks the user which framework to use before writing any tests.
- **Coverage tool not installed**: If the coverage command fails because the tool is missing, install it as a dev dependency (`pytest-cov`, `nyc`, `cargo tarpaulin`, etc.) and rerun the command once. If it fails again, stop and report `BLOCKED` with the error output.
- **Existing tests are already failing**: If the Step 1 baseline run reports failing tests, do not write new tests. Stop and report `BLOCKED` with the names of the failing tests.
- **100% coverage already reached**: If the Step 1 baseline is 100%, add no tests. Report `COMPLETE` with the baseline as evidence and stop.
- **Generated code or vendored files in coverage report**: Leave auto-generated and third-party paths (e.g., `node_modules/`, `vendor/`, `dist/`, `build/`, files with a generated-code header) out of the Step 2 gap list, and list them under `Uncertainty:`.
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

## Guidelines

- Follow existing test patterns and naming conventions
- Place test files alongside source or in the project's existing test directory
- Group related test cases logically
- Use descriptive test names that explain the scenario
- Do not mock what you do not own — prefer real collaborators over mocks at external boundaries
