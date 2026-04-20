---
name: oss-ready
description: "Transform projects into professional open-source repositories with standard components. Use when users ask to make this open source, add open source files, setup OSS standards, create contributing guide, add license, or want to prepare a project for public release with README, CONTRIBUTING, LICENSE, and GitHub templates. Don't use for documentation structure overhauls, landing-page generation, or releasing/publishing to registries."
effort: low
license: MIT
metadata:
  version: 1.1.2
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# OSS Ready

Transform a project into a professional open-source repository with standard community files and GitHub templates.

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

## Workflow

### 0. Create Feature Branch

Before making any changes:
1. Check the current branch - if already on a feature branch for this task, skip
2. Check the repo for branch naming conventions (e.g., `feat/`, `feature/`, etc.)
3. Create and switch to a new branch following the repo's convention, or fallback to: `feat/oss-ready`

### 1. Analyze Project

Identify:
- Primary language(s) and tech stack
- Project purpose and functionality
- Existing documentation to preserve
- Package manager (npm, pip, cargo, etc.)

### 2. Create/Update Core Files

**README.md** - Enhance with:
- Project overview and motivation
- Key features list
- Quick start (< 5 min setup)
- Prerequisites and installation
- Usage examples with code
- Project structure
- Technology stack
- Contributing link
- License badge

**CONTRIBUTING.md** - Include:
- How to contribute overview
- Development setup
- Branching strategy (feature branches from main)
- Commit conventions (Conventional Commits)
- PR process and review expectations
- Coding standards
- Testing requirements

**LICENSE** - Default to MIT unless specified. Copy from `assets/LICENSE-MIT`.

**CODE_OF_CONDUCT.md** - Use Contributor Covenant. Copy from `assets/CODE_OF_CONDUCT.md`.

**SECURITY.md** - Vulnerability reporting process. Copy from `assets/SECURITY.md`.

### 3. Create GitHub Templates

Copy from `assets/.github/`:
- `ISSUE_TEMPLATE/bug_report.md`
- `ISSUE_TEMPLATE/feature_request.md`
- `PULL_REQUEST_TEMPLATE.md`

### 4. Create Documentation Structure

```
docs/
├── ARCHITECTURE.md    # System design, components
├── DEVELOPMENT.md     # Dev setup, debugging
├── DEPLOYMENT.md      # Production deployment
└── CHANGELOG.md       # Version history
```

### 5. Update Project Metadata

Update package file based on tech stack:
- **Node.js**: `package.json` - name, description, keywords, repository, license
- **Python**: `pyproject.toml` or `setup.py`
- **Rust**: `Cargo.toml`
- **Go**: `go.mod` + README badges

### 6. Ensure .gitignore

Verify comprehensive patterns for the tech stack.

### 7. Present Checklist

After completion, show:
- [x] Files created/updated
- [ ] Items needing manual review
- Recommendations for next steps

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

### Analysis (step 1 of 4)

```
◆ Analysis (step 1 of 4 — project profiling)
··································································
  Language detected:       √ pass — TypeScript (primary)
  Project type identified: √ pass — CLI tool
  Existing docs found:     √ pass — README.md (partial), no LICENSE
  [Criteria]:              √ 3/3 met
  ____________________________
  Result:                  PASS
```

### Core Files (step 2 of 4)

```
◆ Core Files (step 2 of 4 — community standards)
··································································
  README created:          √ pass — enhanced with badges, examples
  LICENSE added:           √ pass — MIT from assets/LICENSE-MIT
  CONTRIBUTING written:    √ pass — branching strategy included
  CODE_OF_CONDUCT added:   × fail — assets/CODE_OF_CONDUCT.md missing
  [Criteria]:              √ 3/4 met
  ____________________________
  Result:                  PARTIAL
```

### GitHub Setup (step 3 of 4)

```
◆ GitHub Setup (step 3 of 4 — issue and PR templates)
··································································
  Issue templates created: √ pass — bug_report.md, feature_request.md
  PR template created:     √ pass — PULL_REQUEST_TEMPLATE.md
  [Criteria]:              √ 2/2 met
  ____________________________
  Result:                  PASS
```

### Documentation (step 4 of 4)

```
◆ Documentation (step 4 of 4 — docs structure)
··································································
  ARCHITECTURE written:    √ pass — system components documented
  CHANGELOG created:       √ pass — version history initialized
  Metadata updated:        √ pass — package.json keywords, license, repo
  [Criteria]:              √ 3/3 met
  ____________________________
  Result:                  PASS
```

## Guidelines

- Preserve existing content - enhance, don't replace
- Use professional, welcoming tone
- Adapt to project's actual tech stack
- Include working examples from the actual codebase

## Assets

Templates in `assets/`:
- `LICENSE-MIT` - MIT license template
- `CODE_OF_CONDUCT.md` - Contributor Covenant
- `SECURITY.md` - Security policy template
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
