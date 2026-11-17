# Fix reference: fixer

Load this file only as the fixer's input slice. `UT` means `python3 <skill-dir>/scripts/user_test.py`.

Contents: 1 Complexity · 2 Never auto-fixed · 3 Procedure · 4 Build and test · 5 Checkpoints · 6 Recording the result

## 1. Complexity

Confirm the tester's estimate once you know the root cause.

| Complexity | All of these hold |
|---|---|
| simple | root cause found; 1 file; at most 20 changed lines; nothing changes beyond the fix |
| medium | root cause found and reproducible; at most 5 files; at most 150 changed lines; one feature or layer |
| complex | anything else, or any item in §2 |

Count changed lines with `UT checkpoint diff`. Over the bound: restore the checkpoint and return `complex`.

## 2. Never auto-fixed

These are always `complex`. Return them without editing; the main agent puts them in the plan.

- Database schema changes, migrations, data backfills.
- Authentication, sessions, permissions, payments, cryptography, secrets.
- Adding, removing or upgrading a dependency; build, CI or infrastructure configuration.
- A public contract change: API request or response shape, a removed or renamed CLI flag. Rejecting invalid input with a 4xx error and a clear message is not a contract change.
- Any finding in the `security` category.
- Building a missing feature, beyond wiring an existing handler.
- A UX change that needs a product or design decision: copy tone, layout redesign, colors, a new flow.
- A change that makes existing tests expect different behavior.

## 3. Procedure

Input: run dir, the finding JSON, project root, the baseline build and test commands, the attempt number, env notes, and on attempt 2 the verifier's observation.

1. Read the finding. Locate the code: search for the on-screen text, route, endpoint or command named in `where` (`grep -rn`), then follow the call path.
2. Write the root cause as one sentence. If you cannot find it after about 20 tool calls, stop and return `complex: root cause unclear`.
3. Decide the complexity with §1 and §2. If it is complex, return without editing.
4. Run `UT checkpoint save --run-dir <run_dir> --fix <id> <file>...` for every file you will edit or create, before the first edit. Before touching another file later, `save` it too.
5. Make the smallest change that removes the root cause. Match the surrounding code's style. Do not refactor, rename, reformat, or touch dependencies.
6. Add a regression test only when the project already tests that module and the test fits the existing pattern in about 30 lines. Checkpoint the test file first.
7. Run `UT checkpoint diff --run-dir <run_dir> --fix <id>`. Check the bound in §1. If you decide the finding is complex after editing, run `UT checkpoint restore --run-dir <run_dir> --fix <id>` before you return.
8. Run the build and tests (§4). On a failure, correct it once. If it still fails, run `UT checkpoint restore --run-dir <run_dir> --fix <id>` and return `failed`.
9. Record the result (§6).
10. Return one line: `<id> built: <summary>`, `<id> complex: <reason>`, or `<id> failed: <reason>`.

Never commit, push, stash, run `git checkout -- .`, `git reset`, or `git clean`, or delete a file this fix did not create. Never edit files under `.user-test/` except through `UT`. Never ask the user a question; return `complex` with the question as the reason.

## 4. Build and test

```bash
UT build-check --run-dir <run_dir> --label <id>-a<attempt> --build "<build cmd>" --test "<test cmd>"
```

- Build: the project's build or typecheck command from `run.json` `checks.baseline`. A project with no build step (plain Python or JavaScript): compile-check each changed file instead (`python3 -m py_compile <file>`, `node --check <file>`) and pass that as `--build`.
- Tests: the baseline test command. If the full suite takes more than about 5 minutes, run only the changed module's tests and say so in `tests.result`.
- A new failure is a test that passed in `checks.baseline` and fails now. Compare the test names in the logs under `<run_dir>/logs/`, not only the `tail`. Record the count as `tests.new_failures`; `report` rejects a fixed finding without `"new_failures": 0`.
- No test suite: record `"result": "no test suite"`.

## 5. Checkpoints

- `checkpoint save` copies each listed file into `<run_dir>/checkpoints/<id>/files/` and records files that do not exist yet as new. Saving the same path twice keeps the first copy.
- `checkpoint restore` copies the saved files back with a fresh modification time and deletes the files this fix created. It touches nothing else, so earlier fixes and the user's uncommitted work outside those files survive.
- `checkpoint diff` writes `<run_dir>/checkpoints/<id>/fix.diff` and prints the changed line count.

## 6. Recording the result

```bash
UT update --run-dir <run_dir> --finding <id> --json '{
  "complexity": "simple",
  "complexity_reason": "One missing check in create_todo()",
  "fix": {"attempts": 1, "files": ["server.py"], "diff": "checkpoints/todos-1/fix.diff",
          "root_cause": "create_todo() stores the title without checking it",
          "summary": "Reject empty or whitespace-only titles with HTTP 400",
          "build": {"cmd": "python3 -m py_compile server.py", "exit": 0},
          "tests": {"cmd": "python3 -m unittest -q", "exit": 0, "new_failures": 0, "result": "8 passed"},
          "regression_test": "tests/test_server.py::test_rejects_blank_title"}
}'
```

For a `complex` result, record only `complexity` and `complexity_reason`.
