# Optional Blocks (Workflow, Coding Discipline, Unit Tests)

Add these blocks to generated `CLAUDE.md` / `AGENTS.md` only when the user explicitly asks for orchestration rigor, stricter coding workflow rules, or unit-test rules. Insert each requested block above `## Token Efficiency`, which stays the last section; in a file without that section, append it at the end. Insert the coding-discipline block first, under a `## Coding Discipline` heading, so later blocks don't merge into its list.

## Workflow Orchestration (Balanced)

```markdown
## Workflow Orchestration (Balanced)
- For non-trivial tasks (3+ steps, architecture choices, or unclear dependencies), write a short plan first.
- If assumptions break, stop and re-plan before continuing.
- Use subagents strategically for parallel exploration; keep one focused goal per subagent.
- Do not mark tasks done without evidence (tests, logs, diffs, or output proof).
- Prefer elegant solutions for non-trivial work; keep simple fixes minimal.
- If logs/tests clearly show root cause, fix directly; ask only when risk or ambiguity is high.
- Capture lessons after corrections in durable docs to reduce repeat mistakes.

Core bias:
- Simplicity first
- Root-cause over patchwork
- Minimal-impact changes
```

## Mandatory Coding Discipline Block

```markdown
1. Before writing any code, describe your approach and wait for approval.
2. If the requirements I give you are ambiguous, ask clarifying questions before writing any code.
3. After you finish writing any code, list the edge cases and suggest test cases to cover them.
4. If a task requires changes to more than 3 files, stop and break it into smaller tasks first.
5. When there's a bug, start by writing a test that reproduces it, then fix it until the test passes.
6. Every time I correct you, reflect on what you did wrong and come up with a plan to never make the same mistake again.
```

## Unit Tests

If the coding-discipline block is in the file or requested in the same run, leave out this block's last line, because item 5 there already says it. Don't put CI setup from the same request (unit tests as the first, merge-blocking stage; JUnit XML results; a coverage threshold on changed lines) in this block, and don't edit CI config in this run: list those items under `Decision:` for the user (`knowledge-routing.md`).

```markdown
## Unit Tests
- Make each unit test fail only when the behavior it covers breaks, with a name or failure message that says what broke.
- Never read the wall clock or timezone, use unseeded randomness, or call `sleep()` in a unit test: inject a clock, seed or inject the generator, and await the event or use fake timers.
- Never touch the network, a real database, real ports, shared files, or shared global state in a unit test: use fakes, stubs, injected dependencies, fresh fixtures, and per-test temp dirs, so each test passes alone, in any order, and in parallel.
- Keep each unit test to milliseconds; a test that needs the network or a real database belongs in the integration suite.
- Test one behavior per test, laid out Arrange / Act / Assert, and name it for the scenario and expected result ("rejects a truncated header").
- Assert on return values, raised errors, and observable effects, never on private methods or internal call order.
- Cover the normal path, boundaries (empty, zero, max size, off-by-one), and invalid input and error paths.
- Never add a test only to raise coverage: a test without a meaningful assertion proves nothing.
- Fix a flaky test the day it appears, or ask before quarantining it; never re-run a failing pipeline until it passes.
- When fixing a bug, write the regression test first and watch it fail.
```

Insert verbatim — do not paraphrase. All three blocks are opt-in.
