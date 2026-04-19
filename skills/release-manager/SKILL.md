---
name: release-manager
description: Automate the full release lifecycle — version bump, changelog, README update, git tag, GitHub release, and PyPI/npm publishing.
effort: max
license: MIT
metadata:
  version: 2.3.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Release Manager

Automate the entire release lifecycle: version bump, changelog, README update, documentation sync, build, git tag, GitHub release, and publishing to PyPI/npm.

## Architecture

This skill uses a **main-agent-as-orchestrator** pattern. The main agent handles user communication, confirmation gates, and lightweight steps. Heavy work (scanning files, generating changelogs, updating docs) is delegated to subagents that run in isolated context — keeping the main conversation clean and enabling parallel execution.

```
Main Agent (orchestrator)
├── Step 1: Pre-flight checks (inline)
├── Step 2: Determine version (inline — needs user input)
│
├── Steps 3-6: Spawn subagents in parallel ──────────────┐
│   ├── version-bumper    — scan & propose version changes │
│   ├── changelog-generator — generate changelog from git  │
│   └── docs-updater      — find & propose doc updates     │
│                                                          │
├── Collect results, present to user for confirmation  ◄───┘
├── Spawn: release-reviewer — independent quality check
│
├── Step 7: Build (inline — needs user confirmation)
├── Step 8: Commit, tag, push (inline — needs user confirmation)
├── Step 9: GitHub Release (inline — needs user confirmation)
└── Step 10: Publish to registries (inline — needs user confirmation)
```

### Graceful degradation
If the Agent tool is not available (e.g., Claude.ai), execute steps 3-6 inline instead of spawning subagents. Follow the same logic described in each agent file, but run it directly in the main conversation. This is less context-efficient but functionally identical.

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Overview

A release typically involves these steps in order. Some are optional depending on the project. Walk through each one, confirming with the user before making changes.

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

---

## Step 1: Pre-flight Checks (inline)

Verify the repo is in a clean state before starting:

```bash
# Check for uncommitted changes
git status --porcelain

# Check current branch (usually main or master)
git rev-parse --abbrev-ref HEAD

# Ensure we're up to date
git fetch origin
git status -sb
```

If there are uncommitted changes, ask the user whether to stash them, commit them first, or abort. Do not silently discard work.

### Check for existing release tools

Before proceeding with manual steps, check if the project already uses a release tool:

```bash
# package.json scripts
grep -E '"(release|version|publish)"' package.json 2>/dev/null

# Config files
ls .releaserc* .changeset/ .versionrc* lerna.json 2>/dev/null
```

If found, tell the user: "This project uses `<tool>`. I'll run its release command instead of manual steps." and defer to that tool.

---

## Step 2: Determine Version (inline)

### Analyze changes since last release

```bash
# Find the latest tag
git tag --sort=-creatordate | head -10

# Show commits since last tag
git log $(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~50")..HEAD --oneline --no-merges

# Count by type for the recommendation
git log $(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~50")..HEAD --oneline --no-merges | grep -cE "^[a-f0-9]+ feat" || true
git log $(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~50")..HEAD --oneline --no-merges | grep -cE "^[a-f0-9]+ fix" || true
git log $(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~50")..HEAD --oneline --no-merges | grep -ciE "^[a-f0-9]+ (BREAKING|!:)" || true
```

### Suggest version bump

Based on conventional commits:
- **MAJOR** — any `BREAKING:` or `!:` commits exist
- **MINOR** — any `feat:` commits (with no breaking changes)
- **PATCH** — only `fix:`, `docs:`, `chore:`, `refactor:`, etc.

Present the suggestion: "Based on N features, M fixes, and K breaking changes since vX.Y.Z, I recommend bumping to **vA.B.C**. Does that look right?"

Always let the user override the version number. When in doubt, lean toward MINOR over PATCH — features are easy to miss in commit messages.

---

## Steps 3-6: Parallel Subagent Execution

Once the user confirms the version number, create a workspace directory and spawn three subagents in the same turn (parallel execution). This is where the orchestrator pattern pays off — all three agents work simultaneously in isolated context while the main conversation stays clean.

### Setup workspace

```bash
WORKSPACE="/tmp/release-workspace-$(date +%s)"
mkdir -p "$WORKSPACE"/{version-bumper,changelog-generator,docs-updater}
```

### Spawn subagents (all in the same turn)

**1. Version Bumper** — Read `agents/version-bumper.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version
- `OUTPUT_DIR`: `$WORKSPACE/version-bumper`

**2. Changelog Generator** — Read `agents/changelog-generator.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version
- `OUTPUT_DIR`: `$WORKSPACE/changelog-generator`

**3. Docs Updater** — Read `agents/docs-updater.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version
- `CHANGELOG_SUMMARY`: brief summary of changes from Step 2 analysis (e.g., "3 features, 2 fixes, 0 breaking changes")
- `OUTPUT_DIR`: `$WORKSPACE/docs-updater`

### Collect and present results

After all three subagents complete, read their output files and present a consolidated summary to the user:

1. **Version changes** — read `$WORKSPACE/version-bumper/version-changes.md` and show which files will be updated
2. **Changelog** — read `$WORKSPACE/changelog-generator/changelog-entry.md` and show the formatted entry
3. **Doc updates** — read `$WORKSPACE/docs-updater/docs-changes.md` and show proposed documentation changes

Present all three together: "Here's the full picture of what this release will change. Review and confirm, or tell me what to adjust."

### Independent review (optional but recommended)

After the user has seen the proposed changes, spawn the release-reviewer subagent for an independent quality check. Read `agents/release-reviewer.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `WORKSPACE_DIR`: `$WORKSPACE`
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version

If the reviewer returns `NEEDS_FIX`, present the issues to the user and address them before proceeding. If `PASS`, continue.

### Apply changes

Only after user confirmation, apply all changes:
1. Update version strings in all files identified by the version-bumper
2. Prepend the changelog entry to `CHANGELOG.md` (create the file with a `# Changelog` header if it doesn't exist). Do NOT create or update a `RELEASE_NOTES.md` file
3. Apply documentation updates identified by the docs-updater

---

## Step 7: Build (inline)

Check if the project has a build step:

```bash
# Check for build configuration
[ -f package.json ] && grep -q '"build"' package.json && echo "npm run build"
[ -f Makefile ] && grep -q '^build:' Makefile && echo "make build"
[ -f Cargo.toml ] && echo "cargo build --release"
[ -f pyproject.toml ] && echo "python -m build"
[ -f build.gradle ] && echo "./gradlew build"
[ -f pom.xml ] && echo "mvn package"
```

If a build step exists:
1. Ask the user: "This project has a build step (`<command>`). Should I run it?"
2. Run the build
3. If it fails, stop and help debug — do not continue with a broken build

If no build step is detected, skip this step and tell the user.

---

## Step 8: Commit, Tag, Push (inline)

### Create the release commit

Stage all changed files (version bumps, changelog, README, documentation updates):

```bash
git add <specific files that were changed>
git commit -m "chore(release): vX.Y.Z"
```

### Create annotated tag

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

### Push

Ask the user before pushing — this is a visible action:

"Ready to push the release commit and tag to origin on `<branch>`. Proceed?"

```bash
git push origin <branch>
git push origin vX.Y.Z
```

---

## Step 9: GitHub Release (inline)

If `gh` CLI is available and this is a GitHub repo, offer to create a GitHub release:

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file CHANGELOG.md \
  --latest
```

If there are build artifacts to attach (`.tar.gz`, `.zip`, binaries, `.skill` files, etc.):

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file CHANGELOG.md \
  --latest \
  path/to/artifact1 path/to/artifact2
```

After creating the release, share the release URL with the user.

---

## Step 10: Publish to Package Registries (inline)

If the project publishes to PyPI and/or npm, read `references/publishing.md` for the full publishing workflow including pre-requisites, build, verify, upload, and post-publish verification steps.

---

## Expected Output

After the release completes, a summary is presented:

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

- **No conventional commits**: If commit messages do not follow the `feat:` / `fix:` / `BREAKING:` convention, the version bump suggestion cannot be automated. Present the raw commit list to the user and ask them to confirm the semver bump explicitly.
- **No remote configured**: If `git remote` returns nothing, skip the push and GitHub release steps. Warn the user and offer to create a local tag only.
- **Already published version**: If the target version already exists on PyPI or npm (detected via `pip index versions` or `npm view`), abort the publish step and ask whether to bump to a new patch version or skip publishing.

## Acceptance Criteria

- [ ] Version string is bumped consistently in all detected files (e.g., `pyproject.toml`, `package.json`, `__version__`)
- [ ] `CHANGELOG.md` is updated with a new entry for the release version
- [ ] An annotated git tag is created and pushed to origin
- [ ] A GitHub release is created with release notes when `gh` CLI is available
- [ ] The user is asked to confirm before each destructive or visible action (push, publish, GitHub release)
- [ ] Post-release checklist is presented to the user after completion

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Phase-specific checks

**Step 1 — Pre-flight**
```
◆ Pre-flight (step 1 of 10 — repo state)
··································································
  Branch clean:             √ pass
  Tests pass:               √ pass
  Dependencies resolved:    √ pass (synced with remote)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Steps 2-3 — Version Bump**
```
◆ Version Bump (step 3 of 10 — version consistency)
··································································
  Files updated:            √ pass (N files changed)
  Version consistent:       √ pass (all files match vX.Y.Z)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 4 — Changelog**
```
◆ Changelog (step 4 of 10 — release notes)
··································································
  Changes extracted:        √ pass (N commits categorized)
  Notes formatted:          √ pass (conventional commit format)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Steps 7-10 — Build & Publish**
```
◆ Build & Publish (step 7-10 of 10 — release delivery)
··································································
  Build success:            √ pass
  Tag created:              √ pass (vX.Y.Z annotated tag)
  Package published:        √ pass (PyPI | npm | skipped)
  GitHub release created:   √ pass (URL: ...)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

## Post-Release Checklist

After the release is complete, remind the user about common post-release tasks:

- [ ] Announce the release (blog, social media, Discord, Slack)
- [ ] Bump version to next development version (e.g., `X.Y.Z-dev`) if the project uses that convention
- [ ] Close the GitHub milestone if one exists
- [ ] Monitor for issues related to the new release
- [ ] Verify published packages are installable (`pip install pkg==X.Y.Z`, `npm install pkg@X.Y.Z`)

---

## Tips

- Always confirm destructive or visible actions (push, release creation) with the user
- For monorepos with multiple packages, handle each package's version independently
- Respect existing CHANGELOG format — don't reformat the entire file, just add the new entry
- If a release goes wrong mid-way, help the user roll back: delete the tag locally and remotely, revert the commit

## Reference files

- `agents/version-bumper.md` — Subagent prompt for scanning and proposing version string changes
- `agents/changelog-generator.md` — Subagent prompt for generating categorized changelog from git history
- `agents/docs-updater.md` — Subagent prompt for discovering and proposing documentation updates
- `agents/release-reviewer.md` — Subagent prompt for independent quality review of all release changes
- `references/publishing.md` — Full publishing workflow for PyPI and npm
