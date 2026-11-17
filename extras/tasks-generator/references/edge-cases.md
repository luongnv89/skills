# Edge Cases

Handle each case below explicitly. The status column is the Final Report status when the run ends on that case (SKILL.md → *Final Report*).

| Case | Required behavior | Status if the run ends here |
|------|-------------------|-----------------------------|
| **`PRD_PATH` missing or empty** | Stop in Phase 1. Never invent requirements. The `Next step:` line suggests running `prd-generator` first. | `BLOCKED` |
| **No `$ARGUMENTS` and several candidate folders** | List the candidates and ask the user to choose. Never pick one silently. | `BLOCKED` (no answer) |
| **No `$ARGUMENTS` and no candidate** | Ask for the PRD path or for `IDEAS_ROOT` to be set. | `BLOCKED` (no answer) |
| **Existing `tasks.md`** | Copy it to `tasks_backup_YYYY_MM_DD_HHMMSS.md` before any change. If the backup is missing or empty, stop without writing. | `BLOCKED` (backup failed) |
| **No supporting documents** | Continue from the PRD alone. Name the missing `tad.md` on the `Uncertainty:` line. | not a stop |
| **`python3` unavailable** | Stop before Phase 5. Never compute the critical path or bottlenecks by hand. | `BLOCKED` |
| **No subagent tool** | Run each agent's instructions inline, in phase order, writing the same `WORK_DIR` files. | not a stop |
| **An agent returns no valid output twice** | Stop at that phase. Write no `tasks.md`. | `BLOCKED` |
| **`analyze_dependencies.py` exits 2 twice** | Stop before rendering. Quote the `error[graph-input]` line on the `Evidence:` line. If the cycle reflects a PRD question, put it on the `Decision:` line. | `BLOCKED` |
| **PRD too small for 15 tasks** | Do not pad with filler tasks. Write the tasks the PRD supports, flag the shortfall in the ambiguities section, and fail that criterion in Phase 6. | `PARTIAL` |
| **PRD too large for 80 tasks** | Merge tasks to stay at or under 80, or move the remainder to the Backlog section. | not a stop |
| **`PROJECT_DIR` not in a git repository** | Skip Repo Sync, Phase 7 and Phase 8. Note the skipped phases on the `Uncertainty:` line. | `COMPLETE` if all checks pass |
| **Git repository that is not an ideas repo** | Skip Phase 7. Never create `scripts/update_readme_ideas_index.py`. Phase 8 still commits. | not a stop |
| **No git remote `origin`** | Skip the Repo Sync fetch and pull and the Phase 8 push. Commit locally. The `Next step:` line tells the user how to add the remote (`git remote add origin <url>`). | `PARTIAL` |
| **Repo Sync conflict** | Abort the rebase, restore the stash when it applies cleanly, stop before writing and ask the user. | `BLOCKED` |
| **User declines the push** | Keep the local commit. Report the hash as `local only` and omit GitHub links. | `PARTIAL` |
| **Push rejected on a dirty tree** | Do not start the retry rebase. Name the uncommitted files on the `Uncertainty:` line. | `PARTIAL` |
| **Push rejected, retry rebase conflicts** | Run `git -C "$repo" rebase --abort`. Never force-push. | `PARTIAL` |
| **Push rejected twice** | After the one fetch-rebase-push retry fails, stop. Never force-push. | `PARTIAL` |
