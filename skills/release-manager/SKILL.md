---
name: release-manager
version: 2.2.0
description: Complete release automation — version bumping, changelog generation, README updates, documentation sync, builds, git tags, GitHub releases, and publishing to PyPI/npm. Use this skill whenever the user says "prepare a release", "bump the version", "cut a release", "do a release", "create a new version", "release v1.2.0", "tag a release", "publish a release", "publish to npm", "publish to pypi", "update the changelog", "generate release notes", or anything related to shipping a new version. Also trigger when the user asks "what changed since last release" or "what's ready to release". Even if they only mention one part (like "update changelog" or "bump version"), use this skill because releases have interdependent steps that should be done together.
---

# Release Manager

Automate the entire release lifecycle: version bump, changelog, README update, documentation sync, build, git tag, GitHub release, and publishing to PyPI/npm.

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
6. **Update documentation** — sync all project docs with the release changes
7. **Build** — run the project's build step if one exists
8. **Commit, tag, push** — create the release commit and tag
9. **GitHub Release** — publish on GitHub with release notes
10. **Publish to registries** — publish to PyPI and/or npm

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

### CHANGELOG.md

If the project has a `CHANGELOG.md`, prepend the new entry at the top (below any header). If it does not exist, create `CHANGELOG.md` with a `# Changelog` header and add the new entry below it. Do NOT create or update a `RELEASE_NOTES.md` file.

Keep previous entries intact — only add the new version at the top.

### README.md

Look for version-related content in the README and update it:

- Version badge: `![Version](https://img.shields.io/badge/version-X.Y.Z-blue)`
- Version numbers in a packages/skills table
- "Latest Release" or "What's New" section
- Any hardcoded version strings that refer to the project's own version

Show the user the proposed changes before applying.

---

## Step 6: Update Documentation

Update all project documentation to reflect the new version and changes. This happens before the release commit so that documentation is included in the tagged release.

### Discover documentation files

```bash
# Find all documentation files in the project
find . -maxdepth 4 \( -name "*.md" -o -name "*.rst" -o -name "*.txt" \) \
  ! -path "./.git/*" ! -path "*/node_modules/*" ! -path "*/venv/*" \
  ! -name "CHANGELOG.md" ! -name "LICENSE*" | head -50

# Check for a dedicated docs directory
ls -d docs/ doc/ documentation/ wiki/ site/ 2>/dev/null

# Check for documentation site generators
ls mkdocs.yml .readthedocs.yml docusaurus.config.js docs/.vitepress/ conf.py 2>/dev/null
```

### Identify docs that reference the version or changed features

```bash
# Find docs referencing the old version
grep -rl "<old-version>" docs/ *.md 2>/dev/null

# Find docs referencing APIs, features, or modules that changed in this release
# Use the list of changed files/features from the changelog
grep -rl "<changed-feature-or-module>" docs/ *.md 2>/dev/null
```

### Update documentation content

For each relevant documentation file:

1. **Version references** — update any hardcoded version strings (installation instructions, compatibility matrices, migration guides)
2. **API documentation** — if public APIs changed, update usage examples, parameter descriptions, and return values
3. **Installation / getting-started guides** — update install commands (`pip install pkg==X.Y.Z`, `npm install pkg@X.Y.Z`)
4. **Migration / upgrade guides** — if there are breaking changes, add or update a migration guide section with clear before/after examples
5. **Feature documentation** — add docs for new features, update docs for changed features, remove docs for deprecated/removed features
6. **Configuration references** — update any new config options, environment variables, or CLI flags introduced in the release
7. **Screenshots / diagrams** — flag any that may be outdated due to UI or architectural changes

### Confirm with the user

Show the user a summary of all documentation changes before applying:

"I found N documentation files that need updates:
- `docs/install.md` — version string in install command
- `docs/api.md` — new parameter added to `createWidget()`
- `README.md` — already updated in Step 5

Should I apply these changes?"

### Rebuild documentation site (if applicable)

```bash
# MkDocs
[ -f mkdocs.yml ] && mkdocs build

# Sphinx
[ -f conf.py ] && make html

# Docusaurus
[ -f docusaurus.config.js ] && npm run build

# VitePress
[ -d docs/.vitepress ] && npm run docs:build
```

If the docs site has a separate deployment step (e.g., `mkdocs gh-deploy`, Netlify, Vercel), inform the user but do not trigger deployment without explicit confirmation.

---

## Step 7: Build (if applicable)

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

## Step 8: Commit, Tag, Push

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

## Step 9: GitHub Release

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

## Step 10: Publish to Package Registries

Publish the new release to PyPI and/or npm based on what the project uses.

### Detect which registries apply

```bash
# Python package (PyPI)
[ -f pyproject.toml ] || [ -f setup.py ] || [ -f setup.cfg ] && echo "PYPI"

# Node.js package (npm)
[ -f package.json ] && grep -q '"name"' package.json && echo "NPM"
```

### Publish to PyPI

If the project is a Python package:

#### Pre-requisites check

```bash
# Ensure build tools are available
pip install --upgrade build twine 2>/dev/null || pip3 install --upgrade build twine

# Check for PyPI credentials
# Token in environment variable
echo "${TWINE_PASSWORD:+PyPI token is set}"

# Or check for .pypirc
[ -f ~/.pypirc ] && echo ".pypirc found"
```

#### Build the distribution

If the build step (Step 7) already produced distribution files in `dist/`, reuse them. Otherwise, build now:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build
```

#### Verify the package

```bash
# Check the built packages
twine check dist/*

# Show what will be uploaded
ls -la dist/
```

#### Upload to PyPI

Ask the user before publishing — this is an irreversible action:

"Ready to publish the following to PyPI:
- `dist/package-X.Y.Z.tar.gz`
- `dist/package-X.Y.Z-py3-none-any.whl`

Proceed? (Note: once published, this version cannot be overwritten on PyPI)"

```bash
# Upload to PyPI (production)
twine upload dist/*

# Or upload to Test PyPI first (if user wants to verify)
# twine upload --repository testpypi dist/*
```

After successful upload, share the PyPI URL: `https://pypi.org/project/<package-name>/X.Y.Z/`

### Publish to npm

If the project is a Node.js package:

#### Pre-requisites check

```bash
# Check if logged in to npm
npm whoami

# Check package.json for publish config
grep -A5 '"publishConfig"' package.json 2>/dev/null

# Check if package is scoped and has access setting
grep '"name"' package.json
```

#### Verify the package

```bash
# Dry run to see what will be published
npm pack --dry-run

# Check for .npmignore or "files" field in package.json
[ -f .npmignore ] && echo ".npmignore found"
grep '"files"' package.json 2>/dev/null && echo "files field found"
```

#### Publish to npm

Ask the user before publishing — this is a visible, hard-to-reverse action:

"Ready to publish `<package-name>@X.Y.Z` to npm. Proceed?"

```bash
# Publish to npm
npm publish

# For scoped packages that should be public
# npm publish --access public

# Or publish with a specific tag (e.g., beta, next)
# npm publish --tag <tag>
```

After successful publish, share the npm URL: `https://www.npmjs.com/package/<package-name>/v/X.Y.Z`

### Handle publish failures

If publishing fails:

- **Authentication error** — guide the user to set up credentials:
  - PyPI: `twine upload` requires a PyPI API token (set via `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<token>`, or configure `~/.pypirc`)
  - npm: run `npm login` or set `NPM_TOKEN` environment variable
- **Version conflict** — the version already exists on the registry. The user must bump the version and re-release.
- **Package name conflict** — the package name is taken. Suggest using a scoped name or choosing a different name.
- **Build error** — re-run the build step (Step 7) and fix any issues before retrying.

### Post-publish verification

```bash
# Verify PyPI publication (check the PyPI JSON API)
curl -sf "https://pypi.org/pypi/<package-name>/X.Y.Z/json" | head -1 && echo "PyPI: OK"

# Verify npm publication
npm view <package-name>@X.Y.Z version 2>/dev/null && echo "npm: OK"
```

---

## Post-Release Checklist

After the release is complete, remind the user about common post-release tasks:

- [ ] Announce the release (blog, social media, Discord, Slack)
- [ ] Bump version to next development version (e.g., `X.Y.Z-dev`) if the project uses that convention
- [ ] Close the GitHub milestone if one exists
- [ ] Monitor for issues related to the new release
- [ ] Verify published packages are installable (`pip install pkg==X.Y.Z`, `npm install pkg@X.Y.Z`)

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
