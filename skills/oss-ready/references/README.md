<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# OSS Ready

> Transform projects into professional open-source repositories with all standard community files.

## Highlights

- Generate README, CONTRIBUTING, LICENSE, Code of Conduct, and SECURITY files
- Create GitHub issue and PR templates
- Build documentation structure (ARCHITECTURE, DEVELOPMENT, DEPLOYMENT, CHANGELOG)
- Update project metadata (package.json, pyproject.toml, Cargo.toml)

## When to Use

| Say this... | Skill will... |
|---|---|
| "Make this open source" | Add all OSS standard files |
| "Setup OSS standards" | Generate community health files |
| "Add a license" | Create LICENSE and related docs |
| "Create contributing guide" | Write CONTRIBUTING.md and templates |

## How It Works

```mermaid
graph TD
    F["Create Feature Branch"] --> A["Analyze Project"]
    A --> B["Create Core Files"]
    B --> C["Add GitHub Templates"]
    C --> D["Build Documentation"]
    D --> E["Update Metadata"]
    style F fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
```

## Installation

Install via [npx (Vercel)](https://www.npmjs.com/package/skills):

```bash
npx skills add https://github.com/luongnv89/skills --skill oss-ready
```

Or via [agent-skill-manager (asm)](https://www.npmjs.com/package/agent-skill-manager):

```bash
asm install github:luongnv89/skills:skills/oss-ready
```

## Usage

```
/oss-ready
```

## Resources

| Path | Description |
|---|---|
| `assets/` | File templates and boilerplate content |

## Output

- Core files: README.md, CONTRIBUTING.md, LICENSE, CODE_OF_CONDUCT.md, SECURITY.md
- GitHub templates: bug report, feature request, pull request
- Documentation: ARCHITECTURE.md, DEVELOPMENT.md, DEPLOYMENT.md, CHANGELOG.md
- Updated project metadata and .gitignore
