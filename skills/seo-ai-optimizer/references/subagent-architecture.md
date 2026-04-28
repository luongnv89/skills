# Subagent Architecture

When the Agent tool is available, this skill uses a 4-phase, multi-agent architecture optimized for large websites.

## Phase 1: Auditor Agent
**Purpose:** Run automated SEO audit and manual review checklist

This agent:
- Scans website files for technical SEO issues (meta tags, headings, canonical URLs, structured data)
- Checks project-level files (robots.txt, sitemap.xml, llms.txt, ai-plugin.json)
- Performs manual review of content quality, internal linking, and framework configuration
- Creates seo-audit.json: a complete machine-readable inventory of all SEO issues with severity levels

**Output artifact:** `<project>/seo-audit.json`

## Phase 2: Researcher Agent
**Purpose:** Fetch latest SEO and AI-bot best practices via web search

This agent:
- Performs 4+ targeted web searches covering SEO best practices, meta tags, AI-bot directives, framework-specific guidance
- Synthesizes findings into actionable recommendations
- Compares research against audit findings to identify gaps
- Creates seo-research-findings.json: structured research results and recommendations with citations

**Output artifact:** `<project>/seo-research-findings.json`

## Phase 3: Implementer Agent
**Purpose:** Apply user-approved changes per category (meta tags, robots.txt, llms.txt, structured data, sitemaps)

This agent:
- Receives user-approved list of improvements to apply
- Implements changes categorized by type (meta tags, robots.txt, AI bot directives, JSON-LD, sitemap, etc.)
- Handles framework-specific implementation (Next.js, Nuxt, Astro, Hugo, SvelteKit, static HTML)
- Produces modified source files ready for testing

**Output:** Modified project files with git-ready changes

## Phase 4: Validator Agent
**Purpose:** Re-run audit on modified site, return before/after comparison

This agent:
- Re-runs the audit script on the modified website
- Produces before/after comparison showing what was fixed
- Validates critical files (robots.txt syntax, JSON-LD validity, canonical URLs, image links)
- Creates seo-validation-report.json: detailed delta report with recommendations for remaining work

**Output artifact:** `<project>/seo-validation-report.json`

## Data Flow

```
Website Project
    ↓
[Auditor] → seo-audit.json
    ↓
[Researcher] → seo-research-findings.json
    ↓
(User reviews & approves improvements)
    ↓
[Implementer] → Modified source files
    ↓
[Validator] → seo-validation-report.json
    ↓
(User reviews improvements & validates results)
```

Each agent is self-contained, with clear responsibilities and structured outputs that can be reviewed independently.
