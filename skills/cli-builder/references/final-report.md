# Final Report — cli-builder

Print the final report once per run, after the last Step Completion Report. The step reports score each check; the final report tells the user what was built, what proves it, what is still unknown, and what they must decide.

Format: plain text in the chat. Do not write a report file unless the user asks for one. If the user asks for a file, write the same four parts to the path they name.

A **file write** is any file this skill creates or modifies in the user's project: source files, tests, manifest entries (`pyproject.toml`, `package.json`, `Cargo.toml`, and similar), or packaging and completion scripts. Creating a git branch is not a file write.

## Four required parts, in this order

1. **`Result:`** — the status word first, then the tool name and one line on its command tree.
2. **`Evidence:`** — only checks that ran, each with its file or command and the observed result:
   - the branch name, or `no git repository`
   - each file created or modified
   - the CLI library chosen and the language detected
   - the visual style: `btop` with its styling library or zero-dependency module, or the style the user chose instead
   - each test command with its pass/fail counts (coverage only if the runner printed it)
   - each demo command with its exit code
   - each commit made, by short SHA and message

   Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts:
   - each task whose tests were recorded as `not run`, and why
   - each platform, shell, or Python/Node/Go version not tried
   - with the btop style: `styled output not viewed in a real terminal` and `light-background terminal not tried`, until the user confirms otherwise (`btop-style.md` → Verify)
   - each Phase 3 item skipped or declined (completions, config file, packaging)
   - each design or library choice the user did not confirm
   - `no git repository: no branch or commits` when Repo Sync was skipped

   Write `none` only when every item above is empty.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` Pending approvals include a proposed design change, continuing after a test command could not run, and how to fix a test that still fails after 3 attempts. Name each other remaining user action on its own line, such as pushing the branch or publishing the package.

After the four parts, print the usage quick-start (install command and 3-5 example invocations) and the next steps (suggested improvements, missing features, distribution TODO).

## Status rules

Apply the first rule that matches. SKILL.md Step 5 carries the same three rules.

| Order | Status | When |
|-------|--------|------|
| 1 | `BLOCKED — <reason>` | The run stopped before the first file write. |
| 2 | `PARTIAL — <reason>` | At least one file was written, and the run did not reach every approved task with every test command run and passing and every demo exiting 0. |
| 3 | `COMPLETE` | Every task in the approved plan is done, every test command ran and passed, and every demo exited 0. |

How each run outcome maps. Order 1 wins: any outcome reached before the first file write is `BLOCKED`, even when the table lists it as `PARTIAL`.

| Outcome | Status |
|---------|--------|
| Design or plan not approved, user ends the run | `BLOCKED` |
| No module to wrap and the user gives no answer | `BLOCKED` |
| Repo Sync conflict, or missing `origin` the user did not approve working around | `BLOCKED` |
| A test still fails after 3 fix attempts and the user stops | `PARTIAL` |
| A demo command still exits non-zero after 3 fix attempts and the user stops | `PARTIAL` |
| A test command could not run and the user approved continuing | `PARTIAL` |
| The user stops Step 4 before the last approved task | `PARTIAL` |
| A design change found in Step 4 awaits approval | `PARTIAL` |
| An approved Phase 3 task is not done | `PARTIAL` |
| The user declined Phase 3; Phases 1-2 done and all tests pass | `COMPLETE` |
| Not a git repository; every task done and all tests pass | `COMPLETE` (list it under `Uncertainty:`) |

Map a step report to the status: a step `Result: PASS` does not by itself make the run `COMPLETE`. A step `Result: FAIL` gives `BLOCKED` when no file was written, otherwise `PARTIAL`.

## Example: a complete run

```text
Result: COMPLETE — mylib CLI (Python, click) with subcommands run and info
Evidence:
  Branch: feat/cli-mylib-20260419-143200
  Language: Python (pyproject.toml); library: click; visual style: btop with rich
  Files created:
    cli/main.py          — entry point with argparse/click/typer wiring
    cli/commands/run.py  — "mylib run" subcommand
    cli/commands/info.py — "mylib info" subcommand
    tests/test_cli.py    — CLI smoke tests (help, version, run)
  Files modified:
    pyproject.toml       — updated with [project.scripts] entry point
  pytest: 8 passed, 0 failed
  Demo: mylib --help (exit 0), mylib --version (exit 0), mylib info (exit 0), env -u NO_COLOR FORCE_COLOR=1 mylib info (exit 0, ESC codes present)
  Commits: a1b2c3d feat(cli): add mylib CLI foundation; d4e5f6a feat(cli): add info command and JSON output
Uncertainty:
  Tested on macOS with Python 3.12 only.
  Styled output not viewed in a real terminal; light-background terminal not tried.
  Shell completions and packaging not built (Phase 3 declined).
Decision: No approval needed.
  Remaining action: review the branch and push it.

Usage quick-start:
  pip install -e .
  mylib --help
  mylib run --input data.csv --output results.json
  mylib info --format json

Next steps: add shell completions; publish to PyPI.
```

## Example: a run that stopped mid-execution

```text
Result: PARTIAL — deploy-tool CLI (Go, cobra): Phase 1 done, Phase 2 stopped at task 2.3
Evidence:
  Branch: feat/cli-deploy-tool-20260502-091500
  Files created: cmd/root.go, cmd/deploy.go, cmd/status.go, cmd/root_test.go
  go test ./...: 11 passed, 1 failed (TestStatusJSON: output key "state" missing)
  Demo (Phase 1): deploy-tool --help (exit 0), deploy-tool deploy --dry-run (exit 0)
  Commits: 9f8e7d6 feat(cli): add deploy-tool foundation
Uncertainty:
  Task 2.3 (status --format json) is not done; its test still fails after 3 fix attempts.
  Tasks 2.4-2.5 not started.
Decision: Choose how to fix TestStatusJSON: add "state" to the status API, or change the approved JSON schema.
  Remaining action: after the fix, re-run go test ./... and resume Step 4 at task 2.3.
```

## Reader checks

A run's final report passes review when a reader can:

1. **Find the main result** — the first line gives the status and the tool built, without reading test output.
2. **Separate facts from assumptions** — verified claims name the file or command that ran; untested platforms and tests recorded as `not run` are under `Uncertainty:`.
3. **Trace each claim** — each file and check under `Evidence:` names its path or command and its result. A passing Phase 1 does not imply Phase 2 passed.
4. **See the next decision** — `Decision:` names the approval needed, or states `No approval needed.`, and lists each remaining user action.

Human understanding stays unconfirmed until a user answers these checks. Agent inspection alone cannot confirm it.
