# Agent Config

> Create, update, or audit CLAUDE.md and AGENTS.md configuration files following official best practices.

## Highlights

- Generate project-aware CLAUDE.md with code style, workflows, and architecture context
- Create AGENTS.md custom subagent definitions for specialized tasks
- Audit existing configs against official guidelines and suggest improvements
- Support directory-specific instructions at multiple levels (home, project, child)

## When to Use

| Say this... | Skill will... |
|---|---|
| "Create a CLAUDE.md for this project" | Analyze project and generate config |
| "Audit my agent config" | Review existing files against best practices |
| "Update CLAUDE.md" | Improve existing configuration |
| "Setup AGENTS.md" | Create custom subagent definitions |

## How It Works

```mermaid
graph TD
    A["Analyze Project"] --> B{"Create, Update, or Audit?"}
    B -->|Create| C["Draft Config"]
    B -->|Update| D["Improve Existing"]
    B -->|Audit| E["Review & Report"]
    C --> F["Write Config File"]
    D --> F
    E --> F
    style A fill:#4CAF50,color:#fff
    style B fill:#FF9800,color:#fff
    style F fill:#2196F3,color:#fff
```

## Usage

```
/agent-config
```

## Output

Production-ready `CLAUDE.md` or `AGENTS.md` files with clear sections for bash commands, code style, workflows, testing instructions, and architectural decisions.
