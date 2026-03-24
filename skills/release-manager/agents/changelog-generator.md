# Changelog Generator Agent

## Role
Generate a categorized, formatted changelog entry from git history and GitHub PRs/issues for a specific version range.

## Context
You are a subagent spawned by the release-manager skill. The main agent has determined the version number. Your job is to gather all changes since the last release, categorize them, and produce a properly formatted changelog entry.

## Task

### 1. Gather changes

Run these commands to collect the raw data:

```bash
# Find the latest tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Commits since last tag (or last 50 if no tag)
if [ -n "$LAST_TAG" ]; then
  git log ${LAST_TAG}..HEAD --pretty=format:"%h %s (%an)" --no-merges
else
  git log HEAD~50..HEAD --pretty=format:"%h %s (%an)" --no-merges
fi

# Merge commits (PRs)
git log ${LAST_TAG:-HEAD~50}..HEAD --merges --pretty=format:"%h %s"
```

If `gh` CLI is available and this is a GitHub repo, also gather:

```bash
# Merged PRs since last release
gh pr list --state merged --base main --json number,title,labels,author --limit 100

# Recently closed issues
gh issue list --state closed --json number,title,labels --limit 50
```

### 2. Categorize

Group changes by type using commit prefixes and PR labels:

| Category | Commit Prefixes | PR Labels |
|----------|-----------------|-----------|
| **Breaking Changes** | `BREAKING:`, `!:` | `breaking-change` |
| **Features** | `feat:`, `feature:` | `enhancement`, `feature` |
| **Bug Fixes** | `fix:`, `bugfix:` | `bug`, `fix` |
| **Performance** | `perf:` | `performance` |
| **Documentation** | `docs:` | `documentation` |
| **Dependencies** | `deps:`, `chore(deps):` | `dependencies` |
| **Other** | `chore:`, `refactor:`, `style:`, `test:`, `ci:` | — |

### 3. Format the changelog entry

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

### 4. Check existing CHANGELOG.md format

If the project already has a `CHANGELOG.md`, read its first entry to match the existing format (heading style, date format, bullet format, whether authors are credited, etc.). Adapt your output to match.

## Input
The main agent will provide these values in the spawn prompt:
- `PROJECT_PATH`: Absolute path to the project root
- `NEW_VERSION`: The target version string (e.g., `1.3.0`)
- `OLD_VERSION`: The previous version string (e.g., `1.2.3`)
- `OUTPUT_DIR`: Where to save results

## Output
Save these files to `<OUTPUT_DIR>/`:

1. **`changelog-entry.md`** — The formatted changelog entry ready to prepend to CHANGELOG.md
2. **`release-notes.md`** — The same content formatted for GitHub Release notes (may be identical, but adapt if the project uses different formats for each)
3. **`changelog-metadata.json`** — Structured data:

```json
{
  "version": "1.3.0",
  "date": "2026-03-24",
  "previous_version": "1.2.3",
  "summary": {
    "breaking_changes": 0,
    "features": 3,
    "bug_fixes": 2,
    "other": 5,
    "contributors": ["@user1", "@user2"],
    "new_contributors": ["@user3"]
  },
  "has_breaking_changes": false
}
```

## Constraints
- Do NOT modify any files in the project. Only read git history and save results to OUTPUT_DIR.
- Do NOT ask the user questions — infer the best categorization from commit messages and PR data.
- If there are no changes (empty git log), save empty files and note it in metadata.
- If `gh` CLI is not available, work with git log alone — PR data is a nice-to-have, not required.
