---
name: test-coverage
description: "Generate unit tests for untested branches and edge cases. Use when coverage is low, CI flags gaps, or a release needs hardening. Not for integration/E2E suites, framework migrations, or fixing production bugs."
license: MIT
effort: low
metadata:
  version: 1.5.0
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

Review the low-coverage code for:
- Logical branches (if/else, switch), state transitions, and side effects
- Error paths and invalid input, where real bugs often live
- Boundary values: empty, null, zero, min, max, and off-by-one
- Normal paths that no existing test covers

### 3. Write Tests

1. Read `references/unit-test-quality.md`.
2. Write tests for the Step 2 gaps with the test framework for the detected [Stack](#stack-detect-before-step-1-of-workflow), following that file's rules: deterministic, isolated, fast, one behavior per test, and assertions on behavior rather than implementation.
3. Check each new test against the file's four self-check questions. Rewrite any test that fails one.

### 4. Verify Improvement

1. Run the full test suite. If a previously passing test now fails, report PARTIAL and name it. If a new test fails, run it on its own twice more. If it passes in either solo run, it is flaky: handle it as in item 2. Only if it fails all three times, read the failure and decide which side is wrong:
   - **The test is wrong** (bad setup, or an expectation the code never promised): fix the test, then rerun.
   - **The code is wrong** (the test checks behavior that the code's docstring, types, or name promise): this is a suspected bug. Remove the test, and any import or fixture only it used, then rerun item 1. Do not change production code, and do not loosen the assertion to match the code. Report the bug under `Decision:` with the test's code and failure output. The run can still be `COMPLETE`; name the bug in the `Result:` line. That test becomes the regression test for the fix.
   - **You cannot tell which side is wrong**: treat it as a suspected bug.
2. Run only the new tests on their own, twice (for example `pytest tests/test_parser.py`, `go test ./internal/store -count=1 -run '^TestKey'`, `cargo test key_`). If a new test fails in either run, it depends on test order, shared state, or timing. Fix it once from the flakiness table in `references/unit-test-quality.md` and repeat items 1 and 2. If it still fails, remove it and list it under `Uncertainty:`.
3. Run the same coverage command as Step 1.
4. Compare the new total with the Step 1 baseline. If it is not strictly higher, report PARTIAL and list the Step 2 gaps that are still untested.
5. If the full suite passed in item 1 and the new test files passed in item 2, commit the new tests on the feature branch with a message that records the before/after coverage percentages and the files newly covered. Stage each test file this run wrote by explicit path (`git add tests/test_parser.py`); never `git add -A`, `git add .` or `git commit -a`, which would sweep in user work Repo Sync restored. Never stage a path on the pre-sync list. Stage a changed manifest or lockfile (*Coverage tool not installed*) only with its reason in the commit message. Check `git diff --cached --name-only` before committing. Under `Uncertainty:`, list each changed file left unstaged, or every new test file when the commit is skipped (failed suite or regression).
6. Print the final report. It opens with `Result:` — `COMPLETE`, `PARTIAL — reason`, or `BLOCKED — reason` — followed by:
   - `Evidence:` the commands that ran, with before/after totals, pass/fail counts, and the item 2 rerun result
   - `Uncertainty:` what was not checked (e.g., excluded paths, CI not run, covered lines without output assertions)
   - `Decision:` the action that needs approval, or `No approval needed`, then any remaining user action (e.g., push the branch, open a PR)
   - The number of new test cases and the files with the biggest coverage gains

## Expected Output

After a successful run on a Python project, the final verification report shows:

```
Result:       COMPLETE — coverage 61% → 84%, all tests pass
Evidence:     pytest --cov=. --cov-report=term-missing (before): 61% (47/77 statements), 47 passed
              same command (after): 84% (65/77 statements), 56 passed, 0 failed
              9 new tests run on their own, twice: 9 passed both runs
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
- [ ] Every new test asserts on a return value, a raised error, or an observable effect. A test that only executes code does not count.
- [ ] No new test uses the network, the wall clock, unseeded randomness, or `sleep()`, or a real database other than a test-database fixture the existing unit tests already use.
- [ ] The full test suite passes locally before committing (`npm test`, `pytest`, `go test ./...`, etc.), and the new tests pass when run on their own, twice.
- [ ] A new test that exposed a suspected bug is left out of the commit and reported under `Decision:`. No assertion was loosened to match the code.
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
- **Async / concurrent code paths**: Use the framework's async test utilities (for example `pytest-asyncio` or Jest fake timers). Never use a bare sync wrapper, and never `sleep()` to wait for async work.
- **Code reads the clock, randomness, or global state directly**: Patch it with a tool the test framework ships: pytest `monkeypatch` on the name the module under test imports, `jest.spyOn` or `vi.spyOn`, or Jest or Vitest fake timers for time. If no such tool reaches it, do not refactor production code to add a seam. Leave that gap untested and list it under `Uncertainty:`.

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

**Test Writing phase checks:** `Tests written`, `Self-check passed`, `No network, DB, clock, randomness, or sleep`, `Framework conventions followed`

**Verification phase checks:** `Tests pass`, `New tests pass on their own`, `Coverage improved`, `No regressions`

## Guidelines

- Follow the project's existing test patterns and naming conventions.
- Add new tests to the file that already tests the unit. If none exists, place them where the project's unit tests live: alongside the source (Go `_test.go`, a Rust `#[cfg(test)]` module) or in its unit-test directory. Never add them to an integration or E2E suite.
