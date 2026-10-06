# Edge Cases — oss-ready

Check these before Step 0 of SKILL.md. If one matches the repo, handle it as written. Do not fail silently.

| Case | How to detect | Handling | Status effect |
|------|---------------|----------|---------------|
| Not a git repository | `git rev-parse --git-dir` fails | Stop. Ask the user to run `git init` or to point at the repository root | `BLOCKED` |
| No `origin` remote | `git remote get-url origin` fails | Ask the user. Continue only with explicit approval, list `Repo Sync skipped (no origin)` under `Uncertainty:`, and leave the `repository` metadata field out | `BLOCKED` without approval |
| Detached HEAD | `git symbolic-ref --quiet HEAD` fails | Stop before stashing or syncing. Never force changes onto an unstable branch | `BLOCKED` |
| Dirty working tree | `git status --porcelain` prints a line | Use the stash-first flow in `repo-sync.md`. If stashing, syncing or restoring fails, stop and give the printed recovery commands. Never discard changes | `BLOCKED` on failure |
| Existing LICENSE with a non-MIT identifier | First line of `LICENSE` | Never overwrite. Log the detected license and skip the LICENSE step. Its check becomes "file unchanged" | None |
| Monorepo with multiple `package.json` files | More than one manifest | Update only the root metadata file unless the user names a sub-package | None |
| No detectable language (empty repo or only docs) | No manifest and no source files | Pause and ask the user which template stack to assume | `BLOCKED` with no answer |
| Existing `CODE_OF_CONDUCT.md` or `SECURITY.md` | Step 1 file list | Diff against the template. Append only a missing section; never replace user content | None |
| Private or internal project | `gh repo view --json visibility` returns `PRIVATE` or `INTERNAL`, or the user says so | Confirm with the user before adding `SECURITY.md` or the community templates. A declined file is `not applicable` | None |
| `gh` unavailable | `gh repo view` fails | Record `visibility unknown` under `Uncertainty:` and continue | None |
| No security or conduct contact given | The user does not answer the Step 1 question | Leave the placeholder. Never invent an address | `PARTIAL` |
| Pre-existing `.github/` workflows or templates | `ls .github` | Preserve them; copy only the missing files | None |
| Existing root `CHANGELOG.md` | Step 1 file list | Keep it; do not create `docs/CHANGELOG.md` (`not applicable`) | None |
| Non-English README | README prose | Keep the language. Do not translate; add only structurally missing sections, in the same language | None |
| The user stops the run | The user says stop | Print the final report | `BLOCKED` before Step 2 writes a file, otherwise `PARTIAL` |
