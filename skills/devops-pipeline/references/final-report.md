# Final Report — devops-pipeline

Print the final report once per run, after the last Step Completion Report. The step reports score each check; the final report tells the user what changed, what proves it, what is still unknown, and what they must decide.

A **repository write** is any of: writing or merging `.pre-commit-config.yaml`, a workflow file, or `scripts/e2e_test.sh`; creating a `<file>.bak`; or running `pre-commit install`.

## Four required parts, in this order

1. **`Result:`** — the status word first, then one line on what changed or was found.
   - `COMPLETE` — every requested file was written or merged with the user's confirmation, both hook types are installed, and every Step 4 command exited 0. An audit-only run that writes nothing is `COMPLETE` when every Acceptance Criteria item was checked against the existing files.
   - `PARTIAL — <reason>` — the run made at least one repository write, and then one of these happened: `pre-commit validate-config` failed, a Step 4 command exited non-zero, or the user declined a merge or a new file. A check demoted to a later lane under the 60-second rule does not make the run partial; list it under `Uncertainty:`.
   - `BLOCKED — <reason>` — the run stopped before its first repository write: `pre-commit` is not installed, the stack is undetected and the user gave no answer, `origin` is missing and the user did not approve a local-only setup, or Repo Sync hit a conflict.
2. **`Evidence:`** — only checks that ran, each with its command or file and the observed result: the detected stack, each file written or merged (with its `.bak` path), the `validate-config` exit code, the exit code of each `pre-commit run` stage, the two `pre-commit install` calls, and the `scripts/e2e_test.sh` exit code for a CLI project. In an audit-only run, list each Acceptance Criteria item with pass or fail and the file that shows it. Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts. Always state that the GitHub Actions workflow was not run: the bypass guard, matrix, and deploy jobs first run on the next pull request or push. Also list each foreign hook moved to `<hook>.legacy`, each check demoted with its measured time, each failing hook left open, and each tool or stack choice the user did not confirm.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` Pending approvals include: confirming a merge diff, deleting a `<file>.bak`, deleting a `<hook>.legacy`, and deciding how to fix a failing hook. Name each other remaining user action on its own line, such as committing the new files and opening a pull request to exercise CI.

Map the step report to the status: `Result: PASS` → `COMPLETE`; `PARTIAL` → `PARTIAL`; `FAIL` → `BLOCKED` when no repository write happened, otherwise `PARTIAL`.

## Example: a complete setup

```text
Result: COMPLETE — pre-commit hooks and a lean CI workflow added for a Python CLI
Evidence:
  Stack: Python 3.12, uv, ruff + mypy + pytest; CLI with 4 subcommands (from --help)
  Wrote: .pre-commit-config.yaml (new), .github/workflows/ci.yml (new), scripts/e2e_test.sh (new)
  pre-commit validate-config: exit 0
  pre-commit run --all-files: exit 0 (ruff, ruff-format, mypy, pytest-fast)
  pre-commit run --all-files --hook-stage pre-push: exit 0 (pytest-full, e2e-cli)
  pre-commit install; pre-commit install --hook-type pre-push: both hooks installed
  bash scripts/e2e_test.sh: exit 0
Uncertainty:
  ci.yml has not run on GitHub; the bypass guard and matrix first run on the next pull request.
Decision: No approval needed.
  Remaining action: commit the three files and open a pull request to exercise CI.
```

## Example: a run that stopped before any write

```text
Result: BLOCKED — pre-commit is not installed; no file was written
Evidence:
  command -v pre-commit: not found
  Stack: Node 20, pnpm, eslint + prettier + vitest (from package.json)
Uncertainty: none
Decision: No approval needed.
  Remaining action: install pre-commit (pip install pre-commit or brew install pre-commit), then re-run.
```

## Reader checks

A run's final report passes review when a reader can:

1. **Find the main result** — the first line gives the status and what changed, without reading hook output.
2. **Separate facts from assumptions** — verified claims name the command that ran; untested behavior, such as the CI workflow, is under `Uncertainty:`.
3. **Trace each claim** — each file and check under `Evidence:` names its path or command and its exit code. A passing commit stage does not imply the push stage passed.
4. **See the next decision** — `Decision:` names the approval needed, or states `No approval needed.`, and lists each remaining user action.

Human understanding stays unconfirmed until a user answers these checks. Agent inspection alone cannot confirm it.
