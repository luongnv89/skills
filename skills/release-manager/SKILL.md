---
name: release-manager
version: 2.0.0
description: >
  Complete release automation — version bumping, changelog generation, README updates, builds, git tags,
  and GitHub releases. Use this skill whenever the user says "prepare a release", "bump the version",
  "cut a release", "do a release", "create a new version", "release v1.2.0", "tag a release",
  "publish a release", "update the changelog", "generate release notes", or anything related to
  shipping a new version. Also trigger when the user asks "what changed since last release" or
  "what's ready to release". Even if they only mention one part (like "update changelog" or "bump version"),
  use this skill because releases have interdependent steps that should be done together.
---

# Release Manager

Automate the entire release lifecycle: version bump, changelog, README update, build, git tag, and GitHub release.

## Repo Sync Before Edits (mandatory)

Before making any changes, sync with the remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash, sync, then pop. If `origin` is missing or conflicts occur, stop and ask the user before continuing.

## Overview

A release typically involves these steps in order. Some are optional depending on the project. Walk through each one, confirming with the user before making changes.

1. **Pre-flight checks** — clean working tree, synced with remote
2. **Determine version** — analyze changes, suggest semver bump
3. **Bump version numbers** — update all files that contain the version
4. **Generate changelog / release notes** — from git history and PRs
5. **Update README** — insert changelog entry or update version badges
6. **Build** — run the project's build step if one exists
7. **Commit, tag, push** — create the release commit and tag
8. **GitHub Release** — publish on GitHub with release notes

---

## Step 1: Pre-flight Checks

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

---

## Step 2: Determine Version

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

Always let the user override the version number.

---

## Step 3: Bump Version Numbers

Search the project for all files that contain the current version string and update them. Common locations:

| File | Pattern |
|------|---------|
| `package.json` | `"version": "X.Y.Z"` |
| `pyproject.toml` | `version = "X.Y.Z"` |
| `setup.py` / `setup.cfg` | `version='X.Y.Z'` or `version = X.Y.Z` |
| `Cargo.toml` | `version = "X.Y.Z"` |
| `build.gradle` / `build.gradle.kts` | `version = 'X.Y.Z'` |
| `pom.xml` | `<version>X.Y.Z</version>` |
| `*.md` frontmatter | `version: X.Y.Z` |
| `VERSION` file | Plain version string |
| `__version__` in Python | `__version__ = "X.Y.Z"` |
| `Info.plist` | `<string>X.Y.Z</string>` under CFBundleShortVersionString |

### Strategy

1. Find the previous version tag (strip the `v` prefix if present)
2. Search for that version string across the project
3. Show the user which files will be updated and the exact changes
4. Apply changes only after user confirmation

Be careful not to change version strings that refer to dependency versions or unrelated software. Only update the project's own version.

---

## Step 4: Generate Changelog / Release Notes

### Gather changes

Run in parallel:

```bash
# Commits since last tag
git log <old-tag>..HEAD --pretty=format:"%h %s (%an)" --no-merges

# Merge commits (PRs)
git log <old-tag>..HEAD --merges --pretty=format:"%h %s"
```

If this is a GitHub repo with `gh` available:

```bash
# Merged PRs since last release
gh pr list --state merged --base main --json number,title,labels,author --limit 100

# Closed issues
gh issue list --state closed --json number,title,labels --limit 50
```

### Categorize

Group changes by type based on commit prefixes and PR labels:

| Category | Commit Prefixes | PR Labels |
|----------|-----------------|-----------|
| **Breaking Changes** | `BREAKING:`, `!:` | `breaking-change` |
| **Features** | `feat:`, `feature:` | `enhancement`, `feature` |
| **Bug Fixes** | `fix:`, `bugfix:` | `bug`, `fix` |
| **Performance** | `perf:` | `performance` |
| **Documentation** | `docs:` | `documentation` |
| **Dependencies** | `deps:`, `chore(deps):` | `dependencies` |
| **Other** | `chore:`, `refactor:`, `style:`, `test:`, `ci:` | — |

### Format

Generate the release notes entry:

```markdown
## vX.Y.Z — YYYY-MM-DD

### Breaking Changes
- Description of breaking change (#PR) @author

### Features
- Add new feature X (#123) @author

### Bug Fixes
- Fix issue with Z (#125) @author

### Performance
- Improve loading speed by 50% (#126) @author

### Documentation
- Update README with new examples (#127) @author

### Dependencies
- Bump package-name from 1.0 to 2.0 (#128)

### Other Changes
- Refactor internal APIs (#129) @author

### New Contributors
- @username made their first contribution in #123

**Full Changelog**: https://github.com/OWNER/REPO/compare/vOLD...vNEW
```

Omit empty sections. Link PR numbers. Credit authors. Highlight breaking changes first with upgrade instructions if applicable.

---

## Step 5: Update Project Files

### CHANGELOG.md or RELEASE_NOTES.md

If the project has a `CHANGELOG.md`, prepend the new entry at the top (below any header). If it has `RELEASE_NOTES.md`, do the same. If neither exists, create `RELEASE_NOTES.md`.

Keep previous entries intact — only add the new version at the top.

### README.md

Look for version-related content in the README and update it:

- Version badge: `![Version](https://img.shields.io/badge/version-X.Y.Z-blue)`
- Version numbers in a packages/skills table
- "Latest Release" or "What's New" section
- Any hardcoded version strings that refer to the project's own version

Show the user the proposed changes before applying.

---

## Step 6: Build (if applicable)

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

## Step 7: Commit, Tag, Push

### Create the release commit

Stage all changed files (version bumps, changelog, README updates):

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

## Step 8: GitHub Release

If `gh` CLI is available and this is a GitHub repo, offer to create a GitHub release:

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

If there are build artifacts to attach (`.tar.gz`, `.zip`, binaries, `.skill` files, etc.):

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file RELEASE_NOTES.md \
  --latest \
  path/to/artifact1 path/to/artifact2
```

After creating the release, share the release URL with the user.

---

## Post-Release Checklist

After the release is complete, remind the user about common post-release tasks:

- [ ] Announce the release (blog, social media, Discord, Slack)
- [ ] Update documentation site if separate from repo
- [ ] Bump version to next development version (e.g., `X.Y.Z-dev`) if the project uses that convention
- [ ] Close the GitHub milestone if one exists
- [ ] Monitor for issues related to the new release

---

## Existing Release Tools

If the project already uses a release tool (e.g., `semantic-release`, `changesets`, `release-it`, `standard-version`, `lerna`), detect it and defer to that tool rather than running manual steps. Check for:

```bash
# package.json scripts
grep -E '"(release|version|publish)"' package.json 2>/dev/null

# Config files
ls .releaserc* .changeset/ .versionrc* lerna.json 2>/dev/null
```

If found, tell the user: "This project uses `<tool>`. I'll run its release command instead of manual steps."

## Tips

- Always confirm destructive or visible actions (push, release creation) with the user
- For monorepos with multiple packages, handle each package's version independently
- Respect existing CHANGELOG format — don't reformat the entire file, just add the new entry
- When in doubt about the version bump, lean toward MINOR over PATCH — features are easy to miss in commit messages
- If a release goes wrong mid-way, help the user roll back: delete the tag locally and remotely, revert the commit
