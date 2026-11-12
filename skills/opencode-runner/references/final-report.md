# Final Report — opencode-runner

Print the final report once per run, after Phase 6 cleanup. A run that stops before `opencode run` starts skips Phases 4–6 and prints it directly. The step reports score each phase; the final report tells the human what happened, what proves it, what is still unknown, and what they must decide. Use concise text: a run is a quick operation, so it needs no table, diagram or HTML report.

## Four required parts, in this order

1. **`Result:`** — the status word first, then one line on what happened.
   - `COMPLETE` — the last poll showed `exit=0` and Phase 6 Step 4 printed `cleanup=complete`.
   - `PARTIAL — <reason>` — `opencode run` started, and after that one of these happened: `exit=` was non-zero or `none`, the user approved a kill after a stall, timeout or poll cap, or Phase 6 Step 4 printed `cleanup=incomplete`.
   - `BLOCKED — <reason>` — the run stopped before `opencode run` started: opencode is not installed, opencode does not start after the upgrade, no free-tier eligible model is available, or the user cancelled at the Phase 3 confirmation.
2. **`Evidence:`** — only checks that ran, each with its command and observed result: `opencode --version`, the model chosen from `opencode models`, the last `status()` line (`status=`, `exit=`, `bytes=`), `git status --porcelain` when the working directory is a git repository, and the Phase 6 Step 4 `cleanup=` line. Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts. The skill never reviews or tests opencode's changes, so `exit=0` and a list of changed files prove that opencode finished and touched those files, not that the change is correct. Mark the file list as opencode's own claim when no `git status --porcelain` ran. Note that free models on OpenCode Zen may use the submitted data for model improvement. Write `none` only when nothing applies.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` Pending approvals include: retrying with the next free model, keeping a stalled run alive, and installing or repairing opencode. Name any other remaining user action on its own line, such as reviewing the changed files before committing them.

The step reports do not set the status on their own. A run that stopped in Phases 1–3 is `BLOCKED`. A run that reached Phase 4 is `COMPLETE` or `PARTIAL` by the `exit=` and `cleanup=` rules above. A Phase 1 step report that is `PARTIAL` only because `opencode upgrade` failed, while `opencode --version` still works, does not stop the run; list the failed upgrade under `Uncertainty:`.

## Example: a successful run

```text
Result: COMPLETE — opencode added a retry decorator to utils/http.py and updated its tests
Evidence:
  opencode --version: 1.2.3, exit 0
  model: opencode/deepseek-v4-flash-free (user accepted the default)
  last poll: status=done exit=0 bytes=7982
  git status --porcelain: M utils/http.py, M tests/test_http.py
  cleanup: cleanup=complete
Uncertainty: The changes were not reviewed or tested by this skill; exit 0 shows only that opencode finished.
Decision: No approval needed.
  Remaining action: review the diff and run the tests before committing.
```

## Example: a run that stopped before opencode started

```text
Result: BLOCKED — no free cloud model available
Evidence:
  opencode --version: 1.2.3, exit 0
  opencode models: 14 models listed, 0 free-tier eligible in opencode/*
Uncertainty: none
Decision: Approve one of: check provider auth with `opencode auth list`, or name a model to use.
```

## Reader checks

A final report passes review when a reader can:

1. **Find the main result** — the first line gives the status and what happened, without reading the log.
2. **Separate facts from assumptions** — each verified claim names its command or observed value; opencode's own claims and untested changes sit under `Uncertainty:`.
3. **Trace every claim** — each outcome points to its evidence: `exit=0` does not stand in for a correct change, and a killed run does not stand in for a cleaned-up one.
4. **See the next decision** — `Decision:` names the approval needed, or states `No approval needed.`, and lists any remaining user action.

Human understanding stays unconfirmed until a user answers these checks. Agent inspection alone cannot confirm it.
