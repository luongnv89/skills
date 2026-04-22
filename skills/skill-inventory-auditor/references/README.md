<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Skill Inventory Auditor

> Find and remove duplicate skills across installed skill directories.

## Highlights

- Scans global (`~/.claude/skills/`, `~/.agents/skills/`) and project-local (`.claude/skills/`) directories
- Detects duplicate skills using name matching and description similarity analysis
- Distinguishes symlink shared installations from true duplicates
- Interactive cleanup workflow with confirmation before removals

## When to Use

| Say this... | Skill will... |
|---|---|
| "Check for duplicate skills" | Find and list duplicate/overlapping skills |
| "Deduplicate skills" | Find duplicates and help remove them |
| "Clean up skills" | Interactive removal of duplicate skills |
| "Audit my skills" | Scan all scopes for duplicates |

## How It Works

```mermaid
graph TD
    A["Scan Directories"] --> B{"Duplicates Found?"}
    B -->|Yes| C["Report Duplicate Groups"]
    B -->|No| D["Done - No duplicates"]
    C --> E["User Picks Which to Remove"]
    E --> F["Execute Removals"]
    F --> G["Verify Clean"]
    style A fill:#4CAF50,color:#fff
    style C fill:#FF9800,color:#fff
    style G fill:#4CAF50,color:#fff
```

## Installation

Install via [npx (Vercel)](https://www.npmjs.com/package/skills):

```bash
npx skills add https://github.com/luongnv89/skills --skill skill-inventory-auditor
```

Or via [agent-skill-manager (asm)](https://www.npmjs.com/package/agent-skill-manager):

```bash
asm install github:luongnv89/skills:skills/skill-inventory-auditor
```

## Usage

```
/skill-inventory-auditor
```

## Resources

| Path | Description |
|---|---|
| `scripts/scan_inventory.py` | Python scanner — extracts metadata and detects duplicates via name + description similarity |

## Output

- Duplicate groups with similarity scores and keep/remove recommendations
- Symlink shared installation summary (these are NOT flagged as duplicates)
- Cleanup actions with confirmation and verification
