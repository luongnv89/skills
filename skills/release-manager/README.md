# Release Manager

> Complete release automation — version bumps, changelog, README updates, builds, git tags, and GitHub releases.

## Highlights

- Analyze commits to suggest the right semver bump (major/minor/patch)
- Bump version numbers across all project files automatically
- Generate categorized changelog from git history and GitHub PRs
- Update README with new version info and changelog entries
- Run project build step if one exists
- Create git tags, push, and publish GitHub Releases with artifacts
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

## How It Works

```mermaid
graph TD
    A["Pre-flight Checks"] --> B["Determine Version"]
    B --> C["Bump Version Numbers"]
    C --> D["Generate Changelog"]
    D --> E["Update README"]
    E --> F["Build (if needed)"]
    F --> G["Commit, Tag, Push"]
    G --> H["GitHub Release"]
    style A fill:#4CAF50,color:#fff
    style H fill:#2196F3,color:#fff
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
- Post-release checklist for follow-up tasks
