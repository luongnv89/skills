# Edge Cases

Handle each case below explicitly. The status column is the Final Report status when the run ends on that case (SKILL.md → *Final Report*).

| Case | Required behavior | Status if the run ends here |
|------|-------------------|-----------------------------|
| **Missing `prd.md`** | Stop in Phase 1 step 3. Never invent requirements. The `Next step:` line suggests running `prd-generator` first. | `BLOCKED` |
| **PRD under 200 words** | Warn in Phase 1 step 4 and ask for the user flows and non-functional requirements. If the user says to proceed anyway, mark each missing value `TBD`. | `BLOCKED` (no answer) |
| **Conflicting stack hints in the PRD** | Show both hints in Phase 3 and ask the user to choose. Never pick one silently. An unanswered conflict becomes `TBD` in §3 and a risk in §10. | not a stop |
| **Existing `tad.md`** | Enter `modify` mode. Copy it to `tad.md.bak.YYYYMMDD_HHMMSS` before any change. If the backup is missing or empty, stop without writing. | `BLOCKED` (backup failed) |
| **WebSearch or WebFetch unavailable** | Run the rounds without web access. List the unverified versions on the `Uncertainty:` line. | not a stop |
| **A research round returns nothing twice** | Continue with the other rounds. Name the missing round on the `Uncertainty:` line. | `PARTIAL` |
| **`PROJECT_DIR` not in a git repository** | Skip Repo Sync, Phase 6 and Phase 7. Note the skipped phases on the `Uncertainty:` line. | `COMPLETE` if all checks pass |
| **Git repository that is not an ideas repo** | Skip Phase 6. Never create `scripts/update_readme_ideas_index.py`. Phase 7 still commits. | not a stop |
| **No git remote `origin`** | Skip the Repo Sync pull and the Phase 7 push. Commit locally. The `Next step:` line tells the user how to add the remote (`git remote add origin <url>`). | `PARTIAL` |
| **User declines the push** | Keep the local commit. Report the hash as `local only` and omit GitHub links. | `PARTIAL` |
| **Push rejected twice** | After the one fetch-rebase-push retry fails, stop. Never force-push. | `PARTIAL` |
| **Repo Sync conflict** | Stop before writing and ask the user. | `BLOCKED` |
| **Mermaid syntax invalid** | Check each block (`references/verification-steps.md`, check 2). Regenerate once. If it still fails, replace it with a bulleted text flow and note it on the `Uncertainty:` line. | not a stop while one valid block remains; `PARTIAL` when none does |
