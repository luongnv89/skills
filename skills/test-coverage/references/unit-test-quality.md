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
- Never mock a whole module; spy on an object the code uses instead, or leave the gap (see *Integrity check*).

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

## Property tests

A property test states a rule that holds for every input and lets a library generate the inputs, so it reaches cases the writer's own examples miss. Write one only when both hold:

- **The project already has a property-testing library**: a manifest or lockfile declares it and Step 1's command can import it (Go's standard `testing/quick` is always present). Never add, install or upgrade one, or write it into a manifest, lockfile or requirements file, even when asked: the coverage tool stays the only manifest change, and a request for one goes under `Decision:`. Without one, cover the gap with example tests and name under `Uncertainty:` each property checked only by examples.
- **The code promises the property** in its docstring, types or name:

| Gap | Property | Example |
|---|---|---|
| Round-trip | Decoding what was encoded gives the input back | `decode(encode(x)) == x`, `parse(format(d)) == d` |
| Invariant | A fact true of every output | A sorted result is ordered and holds the same items; a clamped value is in range |
| Idempotency | Applying twice equals applying once | `normalize(normalize(s)) == normalize(s)` |
| Naive equivalence | The real code agrees with an obviously correct version | Binary search against a linear scan of the same list |

Write the naive version in the test, simpler than the code and independent of it (a linear scan, a brute-force loop); one that copies the code's logic is *Tautological* (see *Useless-test patterns*). A property that wrong code can also satisfy (a function that returns its input unchanged is idempotent) is paired with an example test that pins the real output.

**Deterministic.** Each property test fixes its seed, or derandomizes, in the test itself, so every run generates the same inputs:

| Library | In each test |
|---|---|
| Hypothesis (Python) | `@settings(derandomize=True, database=None, deadline=None)` on the test |
| fast-check (JS/TS) | `fc.assert(fc.property(...), { seed: 42 })` |
| `testing/quick` (Go) | `quick.Check(f, &quick.Config{Rand: rand.New(rand.NewSource(1))})` |
| gopter (Go) | `gopter.NewProperties(gopter.DefaultTestParametersWithSeed(1))` |
| proptest (Rust) | `#![proptest_config(ProptestConfig { rng_seed: RngSeed::Fixed(1), failure_persistence: None, ..ProptestConfig::default() })]` |

Never set it through shared config: a Hypothesis settings profile, `fc.configureGlobal`, an environment variable such as `PROPTEST_RNG_SEED`, or a runner flag. A library or installed version that takes its seed only from a flag or an environment variable is not used; write example tests. No saved failure database either (`database=None`, `failure_persistence: None`): a replayed failure makes the next run differ. Keep the library's default number of examples or fewer. Files the library generates (`.hypothesis/`) stay untracked and unstaged.

**Placement.** The *Integrity check* applies unchanged. In a pre-existing test file, a property test is a new test whose decorators, strategies and naive version sit in its decorator arguments or body, plus allowed imports; a strategy or helper shared by several tests goes in a new test file, defined as a function so nothing runs at import.

```python
@settings(derandomize=True, database=None, deadline=None)
@given(st.text(alphabet="ab"))
def test_rle_decode_reverses_encode(text):
    assert rle_decode(rle_encode(text)) == text
```

**Verification.** Step 4 treats a property test like any other. It runs alone twice; one that fails in only one run is flaky, and usually not derandomized. It is break-checked: a planted bug it still passes means the generated inputs never reach the bug or the property does not pin that behavior. Strengthen it once, by narrowing the strategy toward the branch (a two-letter alphabet makes long runs likely) or adding the boundary as an explicit case (`@example`), then repeat the check. One that fails all three times shows the library's shrunk counterexample as its failure output, and Step 4 decides which side is wrong as for any test.

## Sources of flakiness

| Cause | Fix |
|---|---|
| Reading the current time (`datetime.now()`, `Date.now()`, `time.Now()`), timezones | Inject a clock where the code accepts one; otherwise patch or freeze time as SKILL.md → Edge Cases says |
| Randomness | Use a generator the test creates with a fixed seed (`random.Random(0)`, `np.random.default_rng(0)`), or inject one; never seed the global generator. A property test seeds as *Property tests* says |
| `sleep()` waiting for async work | Await the event, or advance fake timers or a fake scheduler |
| Shared global or static state | Build a fresh fixture in each test |
| Test order dependence | Make each test build the state it needs. To expose it, run the file on its own and, where the runner has a built-in shuffle flag (`go test -shuffle=on`, `jest --randomize` on Jest 29.2+, `vitest --sequence.shuffle`), shuffled |
| Real ports or temp files | Use in-memory fakes, or a per-test temp dir (`tmp_path`, `t.TempDir()`) |
| A retry, rerun flag or skip marker | Never a fix: it hides the cause and teaches the next run to retry instead of looking for it. Fix the cause with a row above, or remove the new test and list it under `Uncertainty:` |

## Integrity check

Step 4 runs this before the commit and again on `<base>..HEAD` after it. It passes only when every pre-existing test (a test in a file tracked at the Step 0 base) still runs and checks exactly what it checked before. It is an allow-list: a change it does not allow fails the check, however harmless it looks.

Read every change against the base, staged and unstaged together, with renames split and no diff drivers: `git diff --no-ext-diff --no-textconv --no-color --no-renames --text -U0 <base>`, plus the new files from `git status --porcelain --untracked-files=all`. Leave paths on the pre-sync list out of the check (they are the user's work, which this run never writes to) and name them under `Uncertainty:`, since the suite ran with them.

**Every new test, fixture and helper**, in any file, restores everything it changes and leaves shared state as it found it. An unrestored assignment to a module global, another module's attribute, or the environment fails the check. Python's `monkeypatch` and `with patch(...)` restore themselves. These do not, so restore them in the same test (`try`/`finally`) or a fixture only the new tests use: `patch(...).start()` needs `stop()`, Jest and Vitest `spyOn` needs `mockRestore()` unless the config already sets `restoreMocks`, fake timers need `useRealTimers()`, `vi.stubGlobal` and `vi.stubEnv` need `vi.unstubAllGlobals()` and `vi.unstubAllEnvs()`, `jest.replaceProperty` needs `restore()`. Seeding the global random generator counts as changing shared state. The run adds no module mock (`vi.mock`, `vi.doMock`, `jest.mock`, `jest.doMock`, `jest.unstable_mockModule`, Bun `mock.module`, a `__mocks__` file, a patched `sys.modules` entry): depending on hoisting and the runner's isolation settings, one reaches tests outside the new one. A gap that needs one stays untested and goes under `Uncertainty:`. A class body holds only definitions, and no code runs at import or package load beyond imports, constants and definitions: no autouse or session-wide fixture, no Go `func init()`, and no package-level `var` that calls anything beyond a side-effect-free constructor such as `errors.New` or `regexp.MustCompile`.

**A pre-existing test file may change only like this:**

- **Added lines** belong to a new test whose name is not defined in the file (or Go package) at the base, together with its body and blank separator lines, or to an import below (with blank lines between import groups). A new test goes after every existing test in the file: after the last one at top level (before a trailing `if __name__ == "__main__":` block), or at the end of a test container (a test class, a `describe` block, a Rust `#[cfg(test)]` module) that holds no later existing test. Never inside an existing test's body. No other added line: no module-level statement, fixture, assignment, build tag, or line inside an existing test.
- **An import**: an existing one extended from the same module, every original name and alias kept unchanged, at least one name added; or a new import line. Neither may bind a name the file already binds or a builtin name, and neither is a star import. Either may be wrapped over several lines (a parenthesised Python import, JavaScript braces, a Go import block replacing a single import, a rustfmt `use` tree).
- **Removed lines** only from such an import, or the last line re-added unchanged because a final newline was added. Outside Python, a line in that import block may come back with only the whitespace the project's formatter changed (gofmt alignment).

A pre-existing test file that is deleted, renamed or moved fails the check. A new row in an existing table test is an edit of that test: add a new test instead. Keep each file's line endings; rewriting CRLF as LF changes every line.

**A new file** holds only new tests and the fixtures and helpers they alone use, under the rule above. Its test names may not repeat a pre-existing test's name in the same Go package.

**Never changed or added:** test-selection config and anything that passes runner options: `conftest.py`, `pytest.ini`, `pytest.toml`, `tox.ini`, `setup.cfg`, the test sections of `pyproject.toml` or `package.json` (including its `scripts`), `jest.config.*`, `vitest.config.*`, a Makefile or CI workflow, `.gitattributes`, a Go `TestMain`. The run sets no environment variable and installs nothing but the coverage tool (SKILL.md → Edge Cases), which is the only manifest change allowed. Files the test and coverage tools generate (`.coverage`, caches), left untracked and unstaged, are not changes.

These markers never appear in an added line. Match them as the test framework's API (a decorator, call, attribute or option), not inside a name, a comment, or another library's method:

| Stack | Never added |
|---|---|
| Python | `pytest.mark.skip`, `skipif`, `xfail`, `flaky`, `pytestmark`, `pytest.skip(`, `unittest.skip`, `reruns`, `__test__ = False` |
| JavaScript/TypeScript | `.skip`, `.only`, `.todo`, `xit`, `xdescribe`, `fit`, `fdescribe`, `jest.retryTimes`, a `retry` option |
| Go | `t.Skip`, `TestMain`, a `testing.Short()` guard, a `//go:build` line |
| Rust | `#[ignore]` |

If the check fails after the commit, push nothing: report `PARTIAL — existing test changed` with the line, and leave the commit for the user to inspect.

## Reading a test result

A solo run, a break check and the base check below are judged by the test's own reported result (passed, failed, error), never by the command's exit status, so a coverage threshold missed by a run of a few tests changes nothing. A run in which the test was not collected or did not execute gives **no result**.

## Failing pre-existing tests

When a test that passed at baseline fails in Step 4, decide at the base, never on the branch:

1. `git worktree add --detach <dir outside the repo> <base>`, and run that test there alone by its test id with Step 1's command and the same dependency versions: point to the original checkout's interpreter, virtualenv or installed dependencies, or let Step 1's command build them from the lockfile (for JavaScript, symlink the original `node_modules` or run `npm ci`). A command that would fetch other versions gives no result. Run it up to three times and stop at the first failure.
2. It fails there the same way it failed on the branch (for a failed assertion, the same assert statement, whose line number may shift by lines this run added above it; otherwise the same exception type; numbers in the message may differ) → a **pre-existing flake**: put it and its visible cause under `Decision:`; it does not block the commit, and the `Result:` names it. A later failure of the same test in this run keeps this decision.
3. It passes all three times, fails another way (a file the scratch checkout lacks, an import error), or gives no result → **this run broke it**: report `PARTIAL` and name it, even if it passes alone on the branch. A flake that fails one run in three still passes three runs in a row about a third of the time and is blamed here; that errs on the safe side, since nothing is committed.
4. Remove the worktree with `git worktree remove --force` in every outcome, then confirm `git worktree list` no longer shows it.

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
