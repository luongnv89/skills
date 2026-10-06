---
name: release-manager
description: "Manage software releases end-to-end: bump version, generate changelog, tag, push, GitHub release, publish to PyPI/npm. Use when asked to ship, cut a release, or tag a version. Don't use for routine commits or marketplace publishing."
license: MIT
effort: max
metadata:
  version: 2.7.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Release Manager

Automate the entire release lifecycle: version bump, changelog, README update, documentation sync, build, git tag, GitHub release, and publishing to PyPI/npm.

## Architecture (summary)

The main agent orchestrates; Steps 3-6 run as parallel subagents to keep context clean (diagram and spawn details: `references/orchestration.md`). Without the Agent tool, run the same logic inline.

## Overview

Run these steps in order, confirming with the user before changes. **Step 1 can short-circuit the rest:** if the project ships a release tool (`.changeset`, `.releaserc`, semantic-release, `lerna.json`), defer to it.

1. **Pre-flight checks** — clean working tree, synced with remote
2. **Determine version** — analyze changes, suggest semver bump
3. **Bump version numbers** — *(subagent)* scan and propose version changes
4. **Generate changelog / release notes** — *(subagent)* from git history and PRs
5. **Update README** — *(subagent, combined with docs)* version badges, changelog entries
6. **Update documentation** — *(subagent)* sync all project docs
6b. **Update landing page** — *(subagent, parallel with 3-6)* refresh version, install CTA, and "What's New" when a landing page exists; otherwise a no-op
7. **Build** — run the project's build step if one exists
8. **Commit, tag, push** — create the release commit and tag
9. **GitHub Release** — publish on GitHub with release notes
10. **Publish to registries** — publish to PyPI and/or npm

## Prerequisites

- Clean working tree (or user-approved stash)
- Local branch synced with `origin` (Repo Sync below)
- For publishing: PyPI/npm credentials configured; for GitHub release: `gh` CLI authenticated

## Repo Sync Before Edits (mandatory)

Before creating, updating, or deleting files, sync the current branch with the remote. If the working tree is not clean, run `git stash push -u -m "pre-sync"` first and `git stash pop` after:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

---

## Step 1: Pre-flight Checks (inline)

Verify the repo is in a clean state:

```bash
git status --porcelain
git rev-parse --abbrev-ref HEAD
git fetch origin
git status -sb
```

1. If `git status --porcelain` prints anything, ask the user whether to stash, commit, or abort. Never silently discard work.
2. If `git status -sb` shows the branch behind or diverged from `origin`, run the Repo Sync above before Step 2.

### Check for existing release tools

```bash
ls -d .releaserc* .changeset .versionrc* lerna.json release.config.* 2>/dev/null
grep -E '"(release|semantic-release|release-it|@changesets/cli|standard-version)"[[:space:]]*:' package.json 2>/dev/null
```

The `grep` matches a `scripts.release` entry or a release-tool dependency, never the `"version"` field.

- If either command prints a match, tell the user: "This project uses `<tool>`. I'll run its release command instead of manual steps." Ask for confirmation, then defer to that tool and skip Steps 2-10.
- If neither prints a match, or the user declines, continue to Step 2.

---

## Step 2: Determine Version (inline)

Analyze changes since the last tag:

```bash
git tag --sort=-creatordate | head -10
last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"
if [ -n "$last_tag" ]; then git log "$last_tag"..HEAD --oneline --no-merges; else git log --oneline --no-merges -n 100; fi
```

Recommend a bump using conventional commits:
- **MAJOR** — any `BREAKING:` or `!:` commits
- **MINOR** — any `feat:` (no breaking)
- **PATCH** — only `fix:`, `docs:`, `chore:`, `refactor:`, etc.

Present: "Based on N features, M fixes, K breaking changes since vX.Y.Z, I recommend **vA.B.C**. Confirm or override?" When in doubt, lean MINOR over PATCH. Do not start Step 3 until the user confirms a version.

---

## Steps 3-6: Parallel Subagent Execution

Once the user confirms the version, spawn `version-bumper`, `changelog-generator`, `docs-updater`, and `landing-page-updater` in the same turn. `landing-page-updater` leaves raw version strings to `version-bumper`, so those two never edit the same line. Then optionally spawn `release-reviewer`, which also flags cross-agent collisions. Apply changes only after the user confirms the consolidated summary. Workspace setup, spawn parameters, and apply order: `references/orchestration.md`.

---

## Step 7: Build (inline)

Detect the build command:

```bash
[ -f package.json ] && grep -q '"build"' package.json && echo "npm run build"
[ -f Makefile ] && grep -q '^build:' Makefile && echo "make build"
[ -f Cargo.toml ] && echo "cargo build --release"
[ -f pyproject.toml ] && echo "python -m build"
```

Ask the user before running. If the build fails, stop and help debug — never continue with a broken build. If no build step exists, skip and tell the user.

---

## Step 8: Commit, Tag, Push (inline)

Stage changed files (version bumps, changelog, README, docs) and commit:

```bash
git add <specific files that were changed>
git commit -m "chore(release): vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

Ask: "Push `<branch>` and tag `vX.Y.Z` to origin?" If the user declines, stop and report `PARTIAL — tag vX.Y.Z created locally, not pushed`. If the user confirms, push and verify:

```bash
git push origin <branch>
git push origin vX.Y.Z
git ls-remote --tags origin "refs/tags/vX.Y.Z"
```

If `git ls-remote` prints nothing, report the tag as not pushed and do not start Step 9.

---

## Step 9: GitHub Release (inline)

If `gh auth status` fails or the remote is not on GitHub, skip this step and give the user the command below.

Ask: "Create GitHub release vX.Y.Z with the generated notes?" If the user declines, list it under `Decision` in the final report. If the user confirms, run:

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file "$WORKSPACE/changelog-generator/release-notes.md" \
  --latest
```

For a pre-release version (one containing `-`, such as `2.0.0-rc.1`), replace `--latest` with `--prerelease`. Append artifact paths (`.tar.gz`, `.zip`, binaries, `.skill` files) at the end of the command if any exist. Share the release URL with the user.

---

## Step 10: Publish to Package Registries (inline)

If the project publishes to PyPI and/or npm, read `references/publishing.md` for the full workflow (pre-requisites, build, verify, upload, post-publish verification).

---

## Expected Output

Every run, including one that stops early, ends with the final report: `Result:` with `COMPLETE`, `PARTIAL — <reason>`, or `BLOCKED — <reason>`, then `Evidence:` (checks that ran), `Uncertainty:` (not verified), and `Decision:` (pending user action, or "No approval needed"). Status rules and a `PARTIAL` example: `references/final-report.md`.

```
Result: COMPLETE — v2.4.0 released

Evidence:
- Version bumped: pyproject.toml, package.json (1.3.1 → 2.4.0)
- Git tag: v2.4.0 (annotated) pushed to origin (confirmed by git ls-remote)
- GitHub release: https://github.com/owner/repo/releases/tag/v2.4.0
- Published: PyPI — https://pypi.org/project/mypackage/2.4.0/ (PyPI JSON API returned the version)

Uncertainty:
- A clean install was not tested (pip install mypackage==2.4.0)

Decision: No approval needed.
```

## Edge Cases

- **No conventional commits** — show the raw commit list and ask the user to choose the semver bump.
- **No previous tag** — `git describe --tags` fails. Treat this as the first release: show the recent commits, propose the version from the project's version file, and ask the user to confirm it.
- **No remote configured** — `git remote` returns nothing. Skip push and GitHub release; offer a local tag only, and report `PARTIAL — no remote`.
- **Already published version** — target version exists on PyPI/npm (detected via `pip index versions` or `npm view`). Abort the publish step and ask whether to bump again or skip publishing.
- **Build artifacts missing** — for projects requiring built artifacts, refuse to publish until `Step 7` succeeds.

## Acceptance Criteria

- [ ] Version string is bumped consistently in all detected files (e.g., `pyproject.toml`, `package.json`, `__version__`)
- [ ] `CHANGELOG.md` has a new entry for the release version
- [ ] Annotated git tag created and pushed to origin
- [ ] GitHub release created with notes when `gh` is available
- [ ] User is asked to confirm before each destructive or visible action (push, publish, GitHub release)
- [ ] Post-release checklist is presented after completion
- [ ] The final report passes the reader checks in `references/final-report.md`: result findable first, facts separated from assumptions, claims traceable to evidence, next decision named. Without reviewer feedback, human understanding stays unconfirmed

## Step Completion Reports

After each major step, output a status report (`√` pass, `×` fail, a `Criteria` line, and `Result: PASS | FAIL | PARTIAL`). The template and per-step variants live in `references/step-reports.md`.

## Post-Release Checklist

Present the checklist in `references/final-report.md` after the final report.

## Tips

- For monorepos, handle each package's version independently
- Respect the existing CHANGELOG format — only add the new entry, don't reformat
- If a release goes wrong mid-way, help the user roll back (delete the tag locally and remotely, revert the commit). Ask before each rollback command: both change shared history. A version already published to PyPI or npm cannot be reused; the fix is a new version

## Reference files

- `references/orchestration.md` — Architecture, repo-sync rules, parallel subagent workflow
- `references/step-reports.md` — Full step-completion report templates
- `references/publishing.md` — PyPI / npm publishing workflow
- `references/final-report.md` — Final report status rules, examples, reader checks, post-release checklist
- `agents/` — Subagent prompts: `version-bumper`, `changelog-generator`, `docs-updater`, `landing-page-updater` (skips if no landing page), `release-reviewer`
