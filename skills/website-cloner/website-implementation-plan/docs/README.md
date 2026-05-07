<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Website Implementation Plan

> Turns approved prd.md into a phased implementation plan with landing page first, asset collection vs creation, individual tasks. Writes tasks.md after user approval.

## Highlights

- Phased plan: landing page first (usable early), then deeper pages, then optimization
- Each task has scope, outputs, and acceptance criteria
- Asset tracking: distinguishes collect-from-original vs. create-new
- Approval gate: persists tasks.md only after explicit user approval

## When to Use

| Say this... | Skill will... |
|---|---|
| "plan the implementation from the PRD" | Create phased tasks.md |
| "break down the improvement proposal into tasks" | Produce sequenced implementation plan |

## Usage

```
/website-implementation-plan <prd.md>
```

## Output

`tasks.md` — phased implementation plan ready for the builder skill.
