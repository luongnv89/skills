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

## Self-check

Ask these four questions of each new test before Step 4. Rewrite a test that fails any of them:

1. Would it fail if the behavior it covers broke? A test that only runs the code, or asserts only that a result is not null, fails this question.
2. Would it keep passing through a refactor that preserves the behavior?
3. Can it run alone, offline, and in any order?
4. Does its failure message point at the cause? Use the framework's comparison assertions so a failure shows expected against actual. In Go, put the input, `got`, and `want` in the `t.Errorf` message.

Coverage is a signal, not a target. A line executed by a test with no meaningful assertion counts as covered but is still untested, and 100% coverage with weak assertions proves nothing.
