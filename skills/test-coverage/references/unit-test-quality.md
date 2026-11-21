# Unit test quality

Read this before Step 3 writes the first test. A unit test has one job: fail only when the code it covers is broken, and say why in seconds. A flaky or assertion-free test raises the coverage number while lowering trust in the suite, so every new test meets the rules below.

## Rules

| Property | Rule | Check on each new test |
|---|---|---|
| Deterministic | Same input, same result, on every run | It reads no wall clock or timezone, uses no unseeded randomness, and never calls `sleep()` |
| Isolated | No network, real database, real port, shared file path, or shared global state. Where the existing unit tests already use a test-database or local-server fixture, reuse it | It passes when run on its own, offline, and in any order |
| Fast | Milliseconds per test, so the whole suite runs on every commit | It makes no network or external-service calls and does no waiting; a per-test temp dir is fine. A test that needs more is an integration test, which this skill does not write |
| Focused | One behavior per test | Its name alone says what broke |
| Behavior, not implementation | Assert on return values, raised errors, and observable effects: state, output, and calls to a faked boundary | It asserts nothing about private methods, private attributes, or internal call order |
| Honest | It passes because the code works, never because it was retried, skipped or because an existing test was changed | It carries no skip, `xfail`, retry decorator or rerun flag, and no test that existed before the run was edited to make room for it |

## Fakes and boundaries

- Use real objects for in-process collaborators.
- Replace the network, databases, the clock, and randomness with fakes, stubs, or injected dependencies. Give file access a per-test temp dir.
- When the project wraps a third-party API in its own interface, fake that interface, not the library.

## Layout and naming

Follow the layout and naming style of the project's existing tests. Where the project has no convention, lay each test out as Arrange / Act / Assert and name it for the unit, the scenario, and the expected result. Example in pytest; adapt it to the detected stack:

```python
def test_parse_packet_rejects_truncated_header():
    # Arrange
    raw = bytes.fromhex("4500")  # too short for an IPv4 header

    # Act / Assert
    with pytest.raises(MalformedPacketError):
        parse_packet(raw)
```

## Sources of flakiness

| Cause | Fix |
|---|---|
| Reading the current time (`datetime.now()`, `Date.now()`, `time.Now()`), timezones | Inject a clock where the code accepts one; otherwise patch or freeze time as SKILL.md → Edge Cases says |
| Randomness | Seed it, or inject the generator |
| `sleep()` waiting for async work | Await the event, or advance fake timers or a fake scheduler |
| Shared global or static state | Build a fresh fixture in each test |
| Test order dependence | Make each test build the state it needs. To expose it, run the file on its own and, where the runner has a built-in shuffle flag (`go test -shuffle=on`, `jest --randomize` on Jest 29.2+, `vitest --sequence.shuffle`), shuffled |
| Real ports or temp files | Use in-memory fakes, or a per-test temp dir (`tmp_path`, `t.TempDir()`) |
| A retry, rerun flag or skip marker | Never a fix: it hides the cause and teaches the next run to retry instead of looking for it. Fix the cause with a row above, or remove the new test and list it under `Uncertainty:` |

## Integrity check

Step 4 runs this before the commit and again on `<base>..HEAD` after it. It passes only when every pre-existing test (a test in a file tracked at the Step 0 base) still runs and checks exactly what it checked before. It is an allow-list: a change it does not allow fails the check, however harmless it looks.

Read every change against the base, staged and unstaged together, with renames split and no diff drivers: `git diff --no-ext-diff --no-textconv --no-color --no-renames --text -U0 <base>`, plus the new files from `git status --porcelain --untracked-files=all`. Leave paths on the pre-sync list out of the check (they are the user's work, which this run never writes to) and name them under `Uncertainty:`, since the suite ran with them.

**A pre-existing test file may change only like this:**

- **Added lines** belong to a new top-level test (function, class, or `#[test]` item) whose name is not defined anywhere in the file at the base, together with its body, or to an import below. No other added line: no module-level statement, fixture, assignment, build tag, or line inside an existing test.
- **An extended import**: the same module, every original name and alias kept unchanged, at least one name added, and no added name already bound in the file. It may be rewrapped over several lines (a parenthesised Python import, JavaScript braces, a Go import block replacing a single import, a rustfmt `use` tree). A new import line follows the same rule: it binds no name the file already binds.
- **Removed lines** only from such an import, or the last line re-added unchanged because a final newline was added. Outside Python, a line in that import block may come back with only the whitespace the project's formatter changed (gofmt alignment).

A pre-existing test file that is deleted, renamed or moved fails the check. A new row in an existing table test is an edit of that test: add a new test function instead. Keep each file's line endings; rewriting CRLF as LF changes every line.

**A new file** may hold tests, plus fixtures and helpers that only those tests use and that restore everything they change. It may not run code at import time beyond imports, constants and definitions, define an autouse or session-wide fixture, patch shared state for other tests, or reuse a pre-existing test's name.

**Never changed or added:** test-selection config and anything that passes runner options: `conftest.py`, `pytest.ini`, `pytest.toml`, `tox.ini`, `setup.cfg`, the test sections of `pyproject.toml` or `package.json` (including its `scripts`), `jest.config.*`, `vitest.config.*`, a Makefile or CI workflow, `.gitattributes`, a Go `TestMain`. A manifest may change only to add the coverage tool (SKILL.md → Edge Cases).

These markers never appear in an added line. Match them as code (a decorator, call, attribute or option), not inside a name or a comment:

| Stack | Never added |
|---|---|
| Python | `pytest.mark.skip`, `skipif`, `xfail`, `flaky`, `pytestmark`, `pytest.skip(`, `unittest.skip`, `reruns`, `__test__ = False` |
| JavaScript/TypeScript | `.skip`, `.only`, `.todo`, `xit`, `xdescribe`, `fit`, `fdescribe`, `jest.retryTimes`, a `retry` option |
| Go | `t.Skip`, `TestMain`, a `testing.Short()` guard, a `//go:build` line |
| Rust | `#[ignore]` |

If the check fails after the commit, push nothing: report `PARTIAL — existing test changed` with the line, and leave the commit for the user to inspect.

## Failing pre-existing tests

When a test that passed at baseline fails in Step 4, decide at the base, never on the branch:

1. `git worktree add --detach <scratch-dir> <base>`, then run that test there alone by its test id, three times, with Step 1's command.
2. It fails at least once there → a **pre-existing flake**: put it and its visible cause under `Decision:`; it does not block the commit.
3. It passes all three times there → **this run broke it**: report `PARTIAL` and name it, even if it passes alone on the branch. A rare flake can pass three times and be blamed here; that errs on the safe side, since nothing is committed.
4. Remove the worktree with `git worktree remove --force <scratch-dir>`.

## Self-check

Ask these five questions of each new test before Step 4. Rewrite a test that fails any of them:

1. Would it fail if the behavior it covers broke? A test that only runs the code, or asserts only that a result is not null, fails this question.
2. Would it keep passing through a refactor that preserves the behavior?
3. Can it run alone, offline, and in any order?
4. Does its failure message point at the cause? Use the framework's comparison assertions so a failure shows expected against actual. In Go, put the input, `got`, and `want` in the `t.Errorf` message.
5. Does it check something no existing test already checks? A test that repeats another test's assertion adds run time, not protection.

## Useless-test patterns

Each of these raises coverage without catching a bug. Delete or rewrite a new test that matches one:

| Pattern | Example | Instead |
|---|---|---|
| Tautological | Expected value computed with the same formula as the code: `assert price(x) == x * 1.2` | Hard-code the expected value from the spec: `assert price(100) == 120` |
| Tests the language or framework | A setter sets, the ORM saves, `list.append` appends | Skip it; cover the project logic that uses it |
| Mock-only | Every collaborator mocked, and the only assertion is that a mock was called | Assert on the returned value or resulting state; keep call assertions for a faked external boundary |
| Assertion-free | Runs the code and passes when nothing throws, or asserts only "not null" | Assert the exact value, error type, or effect |
| Duplicate | Same input and assertion as an existing test | Drop it, or pick an input from an untested partition or boundary |
| Private access | Calls a private method or reads a private field | Reach the branch through the public interface |

Coverage is a signal, not a target. A line executed by a test with no meaningful assertion counts as covered but is still untested, and 100% coverage with weak assertions proves nothing.
