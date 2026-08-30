<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# SEO & AI Bot Optimizer

> Audit and optimize website codebases for search engines and AI discovery systems.

## Highlights

- Detect project framework (Next.js, Nuxt, Astro, Hugo, SvelteKit, etc.)
- Run automated scans across 4 categories with severity-based reporting
- Research latest SEO and AI bot best practices via web search
- Handle large codebases by sampling representative files
- Hand off to `/website-agent-readiness` for a live-site agent-readiness score

## When to Use

| Say this... | Skill will... |
|---|---|
| "Optimize for SEO" | Run full audit and apply fixes |
| "Audit SEO" | Scan for issues without modifying |
| "Add structured data" | Implement schema.org markup |
| "Optimize for AI bots" | Add llms.txt and AI-friendly metadata |
| "Check the live site too" | Hand off to `/website-agent-readiness` (Step 8) |

## How It Works

```mermaid
graph TD
    A["Detect Framework"] --> B["Audit Files"]
    B --> C["Research Best Practices"]
    C --> D["Report Findings"]
    D --> E["Plan Improvements"]
    E --> F["Implement Changes"]
    F --> G["Validate Results"]
    G --> H["Agent-Readiness Handoff<br/>(/website-agent-readiness)"]
    style A fill:#4CAF50,color:#fff
    style G fill:#2196F3,color:#fff
    style H fill:#9C27B0,color:#fff
```

## Installation

Install via [npx (Vercel)](https://www.npmjs.com/package/skills):

```bash
npx skills add https://github.com/luongnv89/skills --skill seo-ai-optimizer
```

Or via [agent-skill-manager (asm)](https://www.npmjs.com/package/agent-skill-manager):

```bash
asm install github:luongnv89/skills:skills/seo-ai-optimizer
```

## Usage

```
/seo-ai-optimizer
```

## Resources

| Path | Description |
|---|---|
| `agents/auditor.md` | Scan codebase and generate comprehensive SEO & AI bot audit report |
| `agents/researcher.md` | Identify framework-specific best practices and improvement opportunities |
| `agents/implementer.md` | Apply SEO fixes (meta tags, robots.txt, llms.txt, structured data, sitemaps) |
| `agents/validator.md` | Validate fixes and confirm improvements in generated report |
| `references/` | Framework-specific configs and SEO checklists |
| `scripts/` | Automated scanning and validation scripts |

## Requires

Step 8 invokes [`website-agent-readiness`](../../website-agent-readiness/). Install it with `asm install github:luongnv89/skills:skills/website-agent-readiness`; without it, Steps 1-7 still run and Step 8 is skipped.

## Output

- SEO & AI Bot Audit Report with Critical/Warning/Info findings
- Prioritized improvement plan with implementation checklist
- Applied fixes: meta tags, robots.txt, llms.txt, structured data, sitemaps
- Validation results confirming improvements
- Live-site agent-readiness score and `agent-ready-plan.md` (Step 8), or a stated reason it was skipped
