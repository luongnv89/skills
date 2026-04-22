<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# README to Landing Page

> Transform any README.md into a concise, visual, developer-friendly landing page — diagrams over paragraphs, tables over lists, code over prose.

## Highlights

- Mermaid diagrams for architecture and workflows — visuals first, text second
- Anti-slop rules — bans filler phrases, rhetorical questions, empty adjectives
- No emoji — clean, professional output
- PAS, AIDA, or StoryBrand frameworks adapted for developer audiences
- All original technical content preserved in collapsible `<details>` sections

## When to Use

| Say this... | Skill will... |
|---|---|
| "Turn my README into a landing page" | Rewrite with visual-first landing page structure |
| "Make my README sell the project" | Apply copywriting framework with mermaid diagrams |
| "Make my GitHub page more persuasive" | Optimize for developer conversion |

## How It Works

```mermaid
graph LR
    A["Read project"] --> B["Identify audience"]
    B --> C["Rewrite"]
    C --> D["Anti-slop check"]
    D --> E["Present"]
    style A fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
```

## Output Structure

```mermaid
graph TD
    H["Hero: badges + value prop + CTA"] --> W["How It Works: mermaid diagram"]
    W --> F["Features: table or short bullets"]
    F --> Q["Quick Start: 3-5 commands"]
    Q --> U["Usage: code examples"]
    U --> S["Social Proof — only if real data"]
    S --> C["Final CTA"]
    C --> D["Technical Details — collapsed"]
    style H fill:#4CAF50,color:#fff
    style D fill:#2196F3,color:#fff
```

## Installation

```bash
npx skills add https://github.com/luongnv89/skills --skill readme-to-landing-page
```

## Usage

```
/readme-to-landing-page
```

## Output

- Rewritten `README.md` — visual-first, scannable, mermaid-driven, zero slop
- `README.backup.md` — exact copy of original
- Original technical content in collapsible `<details>` blocks
