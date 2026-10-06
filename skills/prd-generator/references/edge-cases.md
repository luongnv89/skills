# Edge Cases

Handle each case below explicitly. The status column is the Final Report status when the run ends on that case (SKILL.md → *Final Report*).

| Case | Required behavior | Status if the run ends here |
|------|-------------------|-----------------------------|
| **Missing `idea.md`** | Stop in Phase 1 step 3 and ask for the path. Never invent a product concept. | `BLOCKED` |
| **Missing `validate.md`** | Ask in Phase 1 step 4 whether to continue with `idea.md` only. Without a yes, stop. With a yes, record the missing validation in §9 and on the `Uncertainty:` line. | `BLOCKED` (no yes) |
| **Verdict is `Skip it`, `REJECT` or `NOT RECOMMENDED`** | Show the verdict in Phase 1 step 5 and ask whether the user still wants a PRD. Never generate silently. With a yes, record the override in §9. | `BLOCKED` (no yes) |
| **Existing `prd.md`** | Copy it to `prd.backup.YYYYMMDD_HHMMSS.md` before any overwrite. Check that the backup exists and is non-empty. If the check fails, stop without writing. | `BLOCKED` (backup failed) |
| **Conflicting requirements** between `idea.md` and `validate.md` (e.g. idea says "free tier", validate flags it infeasible) | Record both positions in §9 Open Questions & Risks and ask the user to resolve them. | `PARTIAL` (unresolved) |
| **No technical context in `idea.md`** | Write `TBD` placeholders in §6 Technical Specifications. Never invent a stack. List each `TBD` on the `Uncertainty:` line. | not a stop |
| **Compliance constraints unclear** | Ask in Phase 3. Never assume GDPR, HIPAA or SOC2 applies. An unanswered question becomes `TBD` in §9. | not a stop |
| **Multiple candidate project folders** in auto-pick mode | List them and ask the user to choose. Never pick silently. | `BLOCKED` (no choice) |
| **`PROJECT_DIR` not in a git repository** | Skip Repo Sync, Phase 6 and Phase 7. Note the skipped phases on the `Uncertainty:` line. | `COMPLETE` if all checks pass |
| **`PROJECT_DIR` in a git repository that is not an ideas repo** | Skip Phase 6 and Phase 7. Note them on the `Uncertainty:` line. | `COMPLETE` if all checks pass |
| **User declines the push** | Keep the local commit. Report the hash as `local only` and omit GitHub links. | `PARTIAL` |
| **Push rejected twice** | After the one fetch-rebase-push retry fails, stop. Never force-push. | `PARTIAL` |
| **Repo Sync conflict or missing `origin`** | Stop before writing and ask the user. | `BLOCKED` |
| **Mermaid syntax invalid** | Before writing, check each block: a `flowchart` or `sequenceDiagram` first line, no tab characters, balanced brackets. If a block fails, replace it with a bulleted text flow and note it on the `Uncertainty:` line. | not a stop |
