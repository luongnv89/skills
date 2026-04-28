---
name: release-manager
description: "Manage software releases end-to-end: bump version, generate changelog, tag, push, GitHub release, publish to PyPI/npm. Use when user asks to ship, cut a release, tag a version, or list changes since last tag. Skip routine commits and marketplace publishing."
license: MIT
effort: max
metadata:
  version: 2.4.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Release Manager

Automate the entire release lifecycle: version bump, changelog, README update, documentation sync, build, git tag, GitHub release, and publishing to PyPI/npm.

## Architecture (summary)

Main agent orchestrates; heavy steps (scan files, generate changelog, update docs) run as parallel subagents to keep context clean. See `references/orchestration.md` for the full architecture diagram, repo-sync rules, and subagent spawn details. If the Agent tool is unavailable, run the same logic inline.

## Overview

A release typically involves these steps in order. Walk through each, confirming with the user before changes.

1. **Pre-flight checks** — clean working tree, synced with remote
2. **Determine version** — analyze changes, suggest semver bump
3. **Bump version numbers** — *(subagent)* scan and propose version changes
4. **Generate changelog / release notes** — *(subagent)* from git history and PRs
5. **Update README** — *(subagent, combined with docs)* version badges, changelog entries
6. **Update documentation** — *(subagent)* sync all project docs
7. **Build** — run the project's build step if one exists
8. **Commit, tag, push** — create the release commit and tag
9. **GitHub Release** — publish on GitHub with release notes
10. **Publish to registries** — publish to PyPI and/or npm

## Prerequisites

- Clean working tree (or user-approved stash)
- Local branch synced with `origin` (see `references/orchestration.md` for sync commands)
- For publishing: PyPI/npm credentials configured; for GitHub release: `gh` CLI authenticated

---

## Step 1: Pre-flight Checks (inline)

Verify the repo is in a clean state:

```bash
git status --porcelain
git rev-parse --abbrev-ref HEAD
git fetch origin
git status -sb
```

If there are uncommitted changes, ask the user whether to stash, commit, or abort. Never silently discard work.

### Check for existing release tools

```bash
grep -E '"(release|version|publish)"' package.json 2>/dev/null
ls .releaserc* .changeset/ .versionrc* lerna.json 2>/dev/null
```

If found, tell the user: "This project uses `<tool>`. I'll run its release command instead of manual steps." and defer to that tool.

---

## Step 2: Determine Version (inline)

Analyze changes since the last tag:

```bash
git tag --sort=-creatordate | head -10
git log $(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~50")..HEAD --oneline --no-merges
```

Recommend a bump using conventional commits:
- **MAJOR** — any `BREAKING:` or `!:` commits
- **MINOR** — any `feat:` (no breaking)
- **PATCH** — only `fix:`, `docs:`, `chore:`, `refactor:`, etc.

Present: "Based on N features, M fixes, K breaking changes since vX.Y.Z, I recommend **vA.B.C**. Confirm or override?" When in doubt, lean MINOR over PATCH.

---

## Steps 3-6: Parallel Subagent Execution

Once the user confirms the version, spawn the three subagents (`version-bumper`, `changelog-generator`, `docs-updater`) in the same turn for parallel execution. After they finish, optionally spawn `release-reviewer` for a quality check. See `references/orchestration.md` for the full workspace setup, agent spawn parameters, result collection, and apply-changes workflow.

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

Confirm before pushing — this is a visible action:

```bash
git push origin <branch>
git push origin vX.Y.Z
```

---

## Step 9: GitHub Release (inline)

If `gh` CLI is available and the repo is on GitHub:

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file CHANGELOG.md \
  --latest
```

Append artifact paths (`.tar.gz`, `.zip`, binaries, `.skill` files) at the end of the command if any exist. Share the release URL with the user.

---

## Step 10: Publish to Package Registries (inline)

If the project publishes to PyPI and/or npm, read `references/publishing.md` for the full workflow (pre-requisites, build, verify, upload, post-publish verification).

---

## Expected Output

A successful release ends with the agent printing this expected output:

```
Release v2.4.0 complete.

Version bumped: pyproject.toml, package.json (1.3.1 → 2.4.0)
Changelog: CHANGELOG.md updated (8 commits: 3 features, 4 fixes, 1 breaking change)
Git tag: v2.4.0 (annotated) pushed to origin
GitHub release: https://github.com/owner/repo/releases/tag/v2.4.0
Published: PyPI — https://pypi.org/project/mypackage/2.4.0/

Post-release reminders:
- [ ] Announce on Discord
- [ ] Monitor for install issues (pip install mypackage==2.4.0)
```

## Edge Cases

- **No conventional commits** — version bump cannot be auto-suggested. Show the raw commit list and ask the user to confirm the semver bump explicitly.
- **No remote configured** — `git remote` returns nothing. Skip push and GitHub release; offer a local tag only.
- **Already published version** — target version exists on PyPI/npm (detected via `pip index versions` or `npm view`). Abort the publish step and ask whether to bump again or skip publishing.
- **Build artifacts missing** — for projects requiring built artifacts, refuse to publish until `Step 7` succeeds.

## Acceptance Criteria

- [ ] Version string is bumped consistently in all detected files (e.g., `pyproject.toml`, `package.json`, `__version__`)
- [ ] `CHANGELOG.md` has a new entry for the release version
- [ ] Annotated git tag created and pushed to origin
- [ ] GitHub release created with notes when `gh` is available
- [ ] User is asked to confirm before each destructive or visible action (push, publish, GitHub release)
- [ ] Post-release checklist is presented after completion

## Step Completion Reports

After each major step, output a status report. The full template and per-step variants live in `references/step-reports.md`. Quick form:

```
◆ [Step Name] (step N of M — context)
··································································
  Check 1:    √ pass
  Check 2:    × fail — reason
  Criteria:   √ N/M met
  ____________________________
  Result:     PASS | FAIL | PARTIAL
```

## Post-Release Checklist

Remind the user about common follow-ups:

- [ ] Announce the release (blog, social, Discord, Slack)
- [ ] Bump to next dev version (e.g., `X.Y.Z-dev`) if the project uses that convention
- [ ] Close the GitHub milestone if one exists
- [ ] Monitor for issues
- [ ] Verify packages install (`pip install pkg==X.Y.Z`, `npm install pkg@X.Y.Z`)

## Tips

- Always confirm destructive or visible actions (push, release creation)
- For monorepos, handle each package's version independently
- Respect the existing CHANGELOG format — only add the new entry, don't reformat
- If a release goes wrong mid-way, help the user roll back: delete the tag locally and remotely, revert the commit

## Reference files

- `references/orchestration.md` — Architecture, repo-sync rules, parallel subagent workflow
- `references/step-reports.md` — Full step-completion report templates
- `references/publishing.md` — PyPI / npm publishing workflow
- `agents/version-bumper.md` — Subagent prompt for version string changes
- `agents/changelog-generator.md` — Subagent prompt for changelog generation
- `agents/docs-updater.md` — Subagent prompt for documentation updates
- `agents/release-reviewer.md` — Subagent prompt for independent quality review
