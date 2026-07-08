# Clean ATDD/TDD Checklist

Audit catalog distilled from the **bbv Clean ATDD/TDD Cheat Sheet V2.2** (Urs Enzler), pages 3–4.
Use this half to audit the **test suite and testability** of the code. Each item is a check: find the gap or smell, classify severity, cite `file:line`, propose the fix direction.

> If the codebase has **no automated tests at all**, that is a Critical finding (no safety net) — schedule "establish a test harness + characterization tests for risky logic" as a Phase 1 task before any non-trivial refactor.

---

## 1. Kinds of Automated Tests (is the right kind present?)

- **ATDD (Acceptance Test Driven Development)** — write an acceptance test first; covers a feature top-to-bottom delivering business value.
- **TDD (Test Driven Development)** — red → green → refactor; small unit steps.
- **DDT (Defect Driven Testing)** — write a failing test that reproduces a defect before fixing it.
- **POUTing (Plain Old Unit Testing)** — tests written after the code (e.g. for boundary cases). Use to *add* coverage, not to drive design.

*Check:* are bug fixes accompanied by a regression test (DDT)? Are features covered by acceptance tests (ATDD)?

## 2. Design for Testability

- **Constructor — simplicity** — objects must be easily creatable, or tests are slow/hard. *Heavy constructors → Major.*
- **Constructor — lifetime** — inject dependencies/config; don't construct longer-lived collaborators inside.
- **Abstraction layers at system boundaries** (DB, filesystem, web services, COM…) — enable mocking. *Untestable boundary → Major.*

---

## 3. Test Structure & Naming

- **Arrange–Act–Assert (AAA)** — every test follows it; never mix the three blocks. *Violations → Minor/Major.*
- **Test method naming** — name reflects what's tested: `FeatureWhenScenarioThenBehaviour`.
- **One assert / one concept per test** — a test checks one scenario.
- **SetUp/TearDown for infrastructure only** — not to hide test-relevant setup. *Major.*
- **Test naming of SUT variable** — always the same name (e.g. `testee`/`sut`) so the System Under Test is obvious.
- **Naming result values** — name the result consistently (e.g. `result`).
- **Anonymous variables** — same name for "don't care" inputs (e.g. `anonymousText`).

---

## 4. Unit Test Principles (FIRST-style)

- **Fast** — fast enough to run often (sub-second). *Slow unit tests → Major.*
- **Isolated** — no order dependency between tests. *Inter-test dependency → Major.*
- **Repeatable** — no assumed initial state, nothing left behind, no external-service dependency.
- **Self-validating** — red or green; no manual interpretation of output.
- **Timely** — written at the right time (TDD/DDT/POUTing).

---

## 5. Unit Test Smells (find and flag these)

| Smell | What to look for | Severity |
| --- | --- | --- |
| **Test not testing anything** | Passes even when the SUT is broken. | Critical |
| **Test needing excessive setup** | Dozens of lines to set up; SUT does too much. | Major |
| **Too large test / asserts for multiple scenarios** | One test asserting many unrelated things. | Major |
| **Checking internals** | Test reaches into private/protected members (reflection). | Major |
| **Test only runs on developer's machine** | Depends on local environment. | Major |
| **Test checks more than necessary** | Over-specified; breaks on unrelated changes. | Minor |
| **Irrelevant information** | Test contains data not needed to understand it. | Minor |
| **Chatty test** | Fills the console with text. | Minor |
| **Test swallowing exceptions** | Catches and lets the test pass anyway. | Major |
| **Conditional test logic** | `if`/loops inside a test → hard to read, unreliable. | Major |
| **Test logic in production code** | Test-only branches shipped in prod. | Major |
| **Erratic / flaky test** | Sometimes passes, sometimes fails (state/leftovers). | Critical |
| **Mixing stubbing & assertions** | Don't mix stub setup with the assert in the same block. | Minor |
| **Hidden test functionality** | Logic hidden in SetUp/base class instead of the test. | Major |
| **Bloated construction** | Long inline construction of dependencies; extract a builder/helper. | Minor |
| **Unclear fail reason** | No assert message; failure doesn't say what's wrong. | Minor |
| **Obsolete test** | Tests something no longer required but still referenced. | Minor |

### Test doubles (Fakes / Stubs / Spies / Mocks)

- **Isolate from environment** — use doubles to simulate dependencies.
- **Prefer a faking framework** for behavior-rich fakes; hand-written fakes for simple behavior reuse.
- **Don't check fakes' internals** instead of real outputs (excessive fake usage smell).
- **Excessive fake usage** — if a test needs many mocks, the SUT likely does too much (SRP). *Major.*

---

## 6. TDD Principles

- **A test checks one feature.**
- **Tiny steps** — add a little test, then a little code.
- **Keep tests simple** — if a test gets complicated, split the SUT (SRP).
- **Prefer state verification to behavior verification** unless there's no state to verify.
- **Test domain-specific language** — helper methods/classes to make tests read simply.

## 7. TDD Process Smells

- **Using code coverage as a goal** — use it to find missing tests, not as a driving target.
- **No green bar in the last ~10 minutes** — steps too big; commit smaller.
- **Not running the test before writing production code** — you can't trust a test you never saw fail.
- **Not spending enough time on refactoring** — refactoring is the investment in future change.
- **Skipping something too easy / too hard to test** — both hide problems; too-hard-to-test signals a design issue. *Major.*
- **Organizing tests around methods, not behavior** — test scenarios, not getters/setters in isolation. *Major.*

---

## 8. Red / Green Bar Patterns (TDD rhythm — recommend in remediation tasks)

**Red bar patterns (pick the next test):**
- **One step test** — pick a test you're confident you can implement and that maximizes learning.
- **Partial test** — write a not-fully-correct test that brings you a step closer, then extend.
- **Another test** — note new test ideas on a TO-DO list; don't lose focus on the current one.
- **Learning test** — test an external component to confirm it behaves as expected.

**Green bar patterns (get to green):**
- **Fake it ('til you make it)** — return a constant first, refactor toward real later.
- **Triangulate — drive abstraction** — write the test with at least two sample data sets, then abstract.
- **Obvious implementation** — if it's trivial, just implement it; if it stumbles, step back to small steps.
- **One to many — drive collection operations** — implement for one element first, then for the collection.

---

## 9. Acceptance Test Driven Development (ATDD)

- **Use acceptance tests to drive your TDD tests** — let acceptance tests guide unit-level TDD.
- **A user acceptance test** covers a complete feature top-to-bottom delivering business value.
- **Automated ATDD** — for regression and executable specifications.
- **Component acceptance tests** — per logical component or subsystem, combinable without losing coverage.
- **Simulate system boundaries** (UI, DB, filesystem, external services) to check acceptance cases.
- **Avoid acceptance-test spree** — write acceptance tests only for real scenarios; cover exceptional/theoretical cases with unit tests instead.

### ATDD/TDD cycle (the loop remediation should restore)

Acceptance criteria → examples → acceptance-test skeleton → initial design (spike if needed) → refactor → write acceptance test → run → make failure reason obvious → per-class TDD inner loop (write a minimal test < 10 min → run → make failure obvious → write minimal code → run all → clean up < 10 min) → repeat until all examples pass.

---

## 10. Test Pyramid (is the shape right?)

From base (many, automated, fast) to top (few, manual, slow):

1. **Unit Tests** — the broad base.
2. **Acceptance Tests** — drive development.
3. **System & Constraint Tests** — constraint test = test for non-functional requirements.
4. **Exploratory Testing** — find gaps.
5. **Other / manual** — tests not practical to automate.

*Check:* an **inverted pyramid** (many slow end-to-end tests, few unit tests) is a Major finding — slow feedback, brittle suite.

---

## 11. Continuous Integration

- **Pre-commit check** — run all unit + acceptance tests for code worked on before committing.
- **Post-commit check** — CI runs all unit + acceptance tests on every commit.
- **Communicate failed integration to the whole team** — get blocking failures resolved fast.
- **Build staging** — split the CI workflow into stages to reduce feedback time.
- **Automatically build an installer** for the test system as often as possible.
- **Continuous deployment** — install to a test environment on every commit; automate production deployment.

*Check:* no CI, or tests not run on every commit → Major.

---

**Bibliography:** *Test Driven Development: By Example* (Kent Beck); *ATDD by Example* (Markus Gärtner); *The Art of Unit Testing* (Roy Osherove); *xUnit Test Patterns* (Gerard Meszaros).
