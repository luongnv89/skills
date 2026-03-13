# Release Manager

> Complete release automation — version bumps, changelog, README updates, documentation sync, builds, git tags, GitHub releases, and publishing to PyPI/npm.

## Highlights

- Analyze commits to suggest the right semver bump (major/minor/patch)
- Bump version numbers across all project files automatically
- Generate categorized changelog from git history and GitHub PRs
- Update README with new version info and changelog entries
- Run project build step if one exists
- Create git tags, push, and publish GitHub Releases with artifacts
- Sync all project documentation with the release changes
- Publish to PyPI and/or npm registries
- Detect and defer to existing release tools (semantic-release, changesets, etc.)

## When to Use

| Say this... | Skill will... |
|---|---|
| "Prepare a release" | Run the full release workflow end-to-end |
| "Bump the version" | Analyze changes, suggest version, update all files |
| "Generate release notes" | Create categorized changelog from git history |
| "Cut a release for v2.0" | Execute all release steps for the specified version |
| "What changed since last release?" | Summarize commits and PRs since last tag |
| "Tag and publish a release" | Commit, tag, push, and create GitHub Release |
| "Publish to PyPI" | Build and upload Python package to PyPI |
| "Publish to npm" | Pack and publish Node.js package to npm |
| "Update all docs for the release" | Sync documentation with release changes |

## How It Works

```mermaid
graph TD
    A["Pre-flight Checks"] --> B["Determine Version"]
    B --> C["Bump Version Numbers"]
    C --> D["Generate Changelog"]
    D --> E["Update README"]
    E --> F["Update Documentation"]
    F --> G["Build (if needed)"]
    G --> H["Commit, Tag, Push"]
    H --> I["GitHub Release"]
    I --> J["Publish to PyPI/npm"]
    style A fill:#4CAF50,color:#fff
    style J fill:#2196F3,color:#fff
```

## Usage

```
/release-manager
```

## Output

- Updated version numbers across all project files
- `CHANGELOG.md` with categorized changes
- Updated `README.md` with version info
- Git commit tagged with the new version
- GitHub Release with release notes and optional build artifacts
- Synced project documentation (API docs, guides, migration notes)
- Published package on PyPI and/or npm (if applicable)
- Post-release checklist for follow-up tasks
