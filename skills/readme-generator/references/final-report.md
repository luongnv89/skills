# Final Report

The four-line block that ends every run, stops included. It follows the summary and never replaces it. `SKILL.md` → *Final Report* holds the `COMPLETE` example.

## Status

| Status | When |
|---|---|
| `COMPLETE` | `README.md` is written, the backup exists (Rewrite, Landing only), and every Step 4 check passes. `COMPLETE (no change)`: the README already passed and the user declined a rewrite |
| `PARTIAL` | `README.md` is written, but a Step 4 check still fails after the fix pass, or the landing section holds a `[placeholder]` marker |
| `BLOCKED` | Nothing was written: a required question went unanswered and the user ended the run, the repo sync stopped, or the request is out of scope |

A question that waits for the user's answer does not end the run.

## Fill rules

- `Result:` the status first, then what was written, the mode, and where the original is.
- `Evidence:` each landing-section command with its `path:line` source, the Step 4 result as `N/8` (`N/7` in Create mode), the section mapping count, and the sync line. Cite only checks that ran.
- `Uncertainty:` each assumption, labeled as an assumption; each output described rather than shown; each check not run. With none, write "None beyond the checks listed."
- `Decision:` the choice that waits on the user (a placeholder to fill, a registry name to confirm), or "No approval needed." Then name any remaining user action, such as reviewing the diff or deleting the backup.

## PARTIAL example

```text
Result: PARTIAL. Wrote README.md for tilemap (Create mode) with pitch, Install, Quick start, usage and license; the install command is a from-source placeholder.
Evidence: no install command in docs or release config; Quick start code from examples/basic.py:1-6 and its output from tests/test_render.py:14; Step 4 checks 7/7 passed (Create mode); sync: skipped (no git remote).
Uncertainty: Whether tilemap is published to PyPI is unknown; the install block is `git clone [placeholder — repository URL] && cd tilemap && pip install .`.
Decision: Confirm the repository URL, and whether `pip install tilemap` works, so the install line can be final.
```

## BLOCKED example

```text
Result: BLOCKED. README.md was not changed: the repo sync stopped on a rebase conflict.
Evidence: `git pull --rebase origin main` conflicted in README.md; ran `git rebase --abort` and `git stash pop`; README.md and the working tree match their state before the run.
Uncertainty: None beyond the checks listed.
Decision: Resolve the conflict with origin/main, or tell me to skip the sync, then re-run.
```

## Reader checks

Before you print the block, confirm these four checks:

1. **Result findable:** the first line states the status and what changed.
2. **Facts and assumptions separated:** each verified item names its check or source, and each assumption is labeled.
3. **Claims traceable:** each command and check cites a file and line or a command result.
4. **Next decision clear:** `Decision:` names the approval needed, or says none is needed, and names any remaining user action.

Agent checks cannot confirm that a human understood the report. Without a human reviewer's answer, label human understanding as unconfirmed.
