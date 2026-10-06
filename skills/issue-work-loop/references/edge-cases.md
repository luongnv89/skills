# Edge Cases — /issue-work-loop

Each row is a situation the loop must handle rather than crash on. Exact stop and handoff blocks are in `error-messages.md`. Every stop still releases the dependency lease (SKILL.md → *Dependency Preflight*, step 4) and prints the final report with `Result: BLOCKED — {reason}`.

| Situation | Response |
|---|---|
| A dependency cannot be acquired | Stop before the repo sync; report every failed skill in one *Missing required skills* block |
| ISSUE implementer produces no unique open PR | If authoritative `already_resolved` with zero links, hand off `ALREADY_RESOLVED`; otherwise stop and report reason |
| Existing linked PR in ISSUE preflight | Confirm switch to PR mode; decline aborts |
| PR closed/not found | Stop before worker spawn |
| Explicit issue/PR mismatch | Stop and ask user to correct identifiers |
| Missing/contradictory reviewer verdict | One parse-only re-prompt, then fail ROUND |
| PR head changes during review/fix | Refresh; discard stale review/fix plan and review the current SHA |
| Fork/cross-repo push permission unavailable or uncertain | Review is allowed; stop before FIXER/push with handoff |
| Autonomous mode cannot be enabled or verified | Stop before dispatch with the per-harness recovery from `error-messages.md`; never substitute skip-permissions flags |
| Worker blocked | Surface trust/auth dialog; never type into it |
| Max rounds | Report all remaining FINDINGS; leave PR open |
