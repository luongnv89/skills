<p align="center">
  <img src="assets/logo/logo-full.svg" alt="Agent Skills" width="320">
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

# Agent Skills

A collection of skills for AI coding agents. Works with Claude Code, Cursor, Windsurf, Codex, OpenCode, and other AI agents that support skill-based workflows.

## Installation

```bash
npx skills add luongnv89/skills
```

To install a specific skill:

```bash
npx skills add luongnv89/skills/auto-push
npx skills add luongnv89/skills/code-optimizer
```

## Available Skills

### Development Workflow

| Skill | Description |
|-------|-------------|
| **auto-push** | Stage, commit, and push changes with security checks |
| **test-coverage** | Expand unit test coverage targeting untested branches |
| **code-optimizer** | Analyze code for performance issues and optimizations |

### Product Development

| Skill | Description |
|-------|-------------|
| **idea-validator** | Critically evaluate app ideas and startup concepts |
| **name-checker** | Check product names for trademark and domain conflicts |
| **prd-generator** | Generate Product Requirements Documents |
| **tasks-generator** | Generate sprint tasks from PRD |
| **system-design** | Generate Technical Architecture Documents |

### Content & Documentation

| Skill | Description |
|-------|-------------|
| **blog-draft** | Draft blog posts with research and iteration |
| **docs-refactor** | Restructure project documentation |
| **oss-ready** | Setup open-source project standards |
| **agent-config** | Create or update CLAUDE.md and AGENTS.md files |

### Design & Branding

| Skill | Description |
|-------|-------------|
| **logo-designer** | Design professional logos with automatic project context detection |

## Usage

Skills trigger automatically based on your requests:

| What you say | Skill triggered |
|--------------|-----------------|
| "push my changes" | auto-push |
| "optimize this code" | code-optimizer |
| "evaluate my idea" | idea-validator |
| "create a PRD" | prd-generator |
| "make this open source" | oss-ready |
| "improve test coverage" | test-coverage |
| "update CLAUDE.md" | agent-config |
| "design a logo" | logo-designer |

## Project Structure

```
.
├── skills/              # Skill source files
│   └── skill-name/
│       ├── SKILL.md     # Skill definition
│       ├── scripts/     # Optional scripts
│       ├── references/  # Optional docs
│       └── assets/      # Optional templates
├── .agents/             # Agent configuration
└── .claude/             # Claude-specific skills
```

## Creating New Skills

Use the **skill-creator** skill or create manually:

```markdown
---
name: my-skill
description: What it does and when to use it
---

# Instructions for the AI agent...
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

[MIT](LICENSE)
