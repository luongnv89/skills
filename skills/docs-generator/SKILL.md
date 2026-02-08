---
name: docs-generator
version: 1.1.0
description: Restructure project documentation for clarity and accessibility. Use when users ask to "organize docs", "generate documentation", "improve doc structure", "restructure README", or need to reorganize scattered documentation into a coherent structure. Analyzes project type and creates appropriate documentation hierarchy.
---

## Workflow

### 0. Create Feature Branch

Before making any changes:
1. Check the current branch - if already on a feature branch for this task, skip
2. Check the repo for branch naming conventions (e.g., `feat/`, `feature/`, etc.)
3. Create and switch to a new branch following the repo's convention, or fallback to: `feat/docs-generator`

### 1. Analyze Project

Identify:
- **Project type**: Library, API, web app, CLI, microservices
- **Architecture**: Monorepo, multi-package, single module
- **User personas**: End users, developers, operators

### 2. Restructure Documentation

**Root README.md** - Streamline as entry point:
- Project overview and purpose
- Quickstart (install + first use)
- Modules/components summary with links
- License and contacts

**Component READMEs** - Add per module/package/service:
- Purpose and responsibilities
- Setup instructions
- Testing commands

**Centralize in `docs/`** - Organize by category (select applicable):
```
docs/
├── architecture.md      # System design, diagrams
├── api-reference.md     # Endpoints, authentication
├── database.md          # Schema, migrations
├── deployment.md        # Production setup
├── development.md       # Local setup, contribution
├── troubleshooting.md   # Common issues
└── user-guide.md        # End-user documentation
```

### 3. Create Diagrams

Use Mermaid for all visual documentation:
- Architecture diagrams
- Data flow diagrams
- Database schemas

### Guidelines

- Keep docs concise and scannable
- Adapt structure to project type (not all categories apply)
- Maintain cross-references between related docs
- Remove redundant or outdated content
