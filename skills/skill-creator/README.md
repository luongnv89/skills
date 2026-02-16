# Skill Creator

> Interactive, guided skill creation following Anthropic's best practices with a 4-phase workflow.

## Highlights

- Discovery phase to understand purpose, requirements, and edge cases
- Approval gate before building to confirm understanding
- Generate YAML frontmatter, SKILL.md, README.md, and supporting resources
- Include test suite with trigger and functional test cases

## When to Use

| Say this... | Skill will... |
|---|---|
| "Create a new skill" | Start guided skill creation |
| "Build a skill for X" | Design and build from requirements |
| "Update an existing skill" | Modify with diff-style summary |
| "Help me make a skill" | Walk through the 4-phase process |

## How It Works

```mermaid
graph TD
    A["Discovery Phase"] --> B["Present Understanding"]
    B --> C{"User Approves?"}
    C -->|Yes| D["Build Skill"]
    C -->|No| A
    D --> E["Test & Deliver"]
    style A fill:#4CAF50,color:#fff
    style C fill:#FF9800,color:#fff
    style E fill:#2196F3,color:#fff
```

## Usage

```
/skill-creator
```

## Resources

| Path | Description |
|---|---|
| `references/` | Skill structure guidelines and best practices |
| `scripts/` | Validation and packaging scripts |

## Output

- Complete skill folder with SKILL.md (YAML frontmatter + instructions) and README.md (human-readable docs)
- Supporting resources in `scripts/`, `references/`, `assets/` as needed
- Packaged `.skill` file for distribution
- Test suite with trigger and functional tests

## Acknowledgement

Customized from Anthropic's official [skill-creator](https://github.com/anthropics/claude-code/tree/main/plugins/skill-creator) skill. Added README.md generation step and adapted for this skill collection.
