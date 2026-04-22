# Contributing to Agent Skills

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-new-skill`)
3. Make your changes
4. Commit using conventional commits (`git commit -m "feat: add new skill"`)
5. Push to your branch (`git push origin feature/my-new-skill`)
6. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/skills.git
cd skills

# Create a new skill
python3 skills/skill-creator/scripts/init_skill.py my-skill --path skills/

# Edit the skill
# ... make changes to skills/my-skill/SKILL.md

# Package and validate
python3 skills/skill-creator/scripts/package_skill.py skills/my-skill
```

## Skill Structure

Each skill must follow this structure:

```
skill-name/
├── SKILL.md              # Required: Skill definition
├── references/           # Required: contains README.md; may hold additional docs
│   └── README.md         # Required: human-readable catalog docs (AI-skip notice at top)
├── scripts/              # Optional: Executable scripts
└── assets/               # Optional: Templates and resources
```

`references/README.md` must start with the AI-skip HTML comment so agents don't accidentally load it into context — the runtime loads `SKILL.md` as the canonical skill definition.

### SKILL.md Requirements

```yaml
---
name: skill-name
version: 1.0.0
description: Clear description of what the skill does and when to use it
---

# Skill content...
```

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature or skill
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
- `feat: add code-review skill`
- `fix: correct trigger phrases in smart-commit`
- `docs: update installation instructions`

## Versioning

Skills use [semantic versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

- **PATCH** (e.g., `1.0.0` → `1.0.1`): Bug fixes, typo corrections
- **MINOR** (e.g., `1.0.0` → `1.1.0`): New features, added capabilities
- **MAJOR** (e.g., `1.0.0` → `2.0.0`): Breaking changes to skill behavior

Always update the `version` field in SKILL.md frontmatter when modifying a skill.

## Pull Request Process

1. Ensure your skill passes validation (`package_skill.py`)
2. Update README.md if adding a new skill
3. Fill out the PR template completely
4. Wait for review and address any feedback

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Questions?

Open an issue for any questions about contributing.
