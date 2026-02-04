# Agent Skills

A collection of skills for AI coding agents. Works with Claude Code, Codex, OpenCode, and other AI agents that support skill-based workflows.

## Available Skills

### Development Workflow

| Skill | Description |
|-------|-------------|
| **smart-commit** | Create intelligent git commits with conventional commits format (feat, fix, docs, etc.) |
| **auto-push** | Safely commit and push changes with comprehensive verification and security checks |
| **code-optimizer** | Analyze code for performance issues, memory leaks, and optimization opportunities |

### Product Development

| Skill | Description |
|-------|-------------|
| **idea-validator** | Critically evaluate app ideas, startup concepts, and product proposals |
| **name-checker** | Check product/brand names for trademark, domain, and social media conflicts |
| **prd-generator** | Generate comprehensive Product Requirements Documents from validated ideas |
| **tasks-generator** | Generate development tasks from PRD with sprint-based planning |
| **system-design** | Generate Technical Architecture Documents from PRD files |

### Skill Development

| Skill | Description |
|-------|-------------|
| **skill-creator** | Guide for creating effective agent skills |

## Installation

### Claude Code

```bash
claude /install-skill dist/skill-name.skill
```

### Other Agents

Copy the skill markdown file to your agent's skills directory, or reference it directly in your agent's configuration.

## Usage

Once installed, skills are automatically triggered based on your requests:

- "commit" or "commit my changes" → **smart-commit**
- "optimize this code" or "find performance issues" → **code-optimizer**
- "evaluate my idea" or "is this a good idea" → **idea-validator**
- "create a PRD" → **prd-generator**
- "design the architecture" → **system-design**

## Structure

```
.
├── dist/                # Packaged skill files (distributable)
│   └── *.skill
└── .claude/skills/      # Skills source
    └── skill-name/
        ├── SKILL.md     # Skill definition and instructions
        ├── scripts/     # Optional executable scripts
        ├── references/  # Optional reference documentation
        └── assets/      # Optional templates and resources
```

## Creating New Skills

Use the **skill-creator** skill to create new skills, or follow this structure:

```markdown
---
name: my-skill
description: What the skill does and when to use it
---

# Skill Name

Instructions for the AI agent...
```

## License

MIT
