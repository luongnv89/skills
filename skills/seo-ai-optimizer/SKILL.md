---
name: seo-ai-optimizer
description: Audit and optimize website codebases for technical SEO, content SEO, and AI bot accessibility. Fixes meta tags, sitemaps, robots.txt, structured data, llms.txt, and GPTBot/ClaudeBot directives across any web framework.
effort: high
license: MIT
metadata:
  version: 1.1.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# SEO & AI Bot Optimizer

Audit and optimize website codebases for search engines and AI systems.

## Repo Sync Before Edits (mandatory)

Before modifying any project files, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Quick Reference

Consult these reference files as needed during the workflow:
- `references/technical-seo.md` — Full SEO checklist and best practices
- `references/framework-configs.md` — Framework-specific configuration (Next.js, Nuxt, Astro, Hugo, etc.)
- `references/ai-bot-guide.md` — AI crawler directives, llms.txt format, JSON-LD templates

## Environment Check

This skill has two modes of operation:

**With Subagent Architecture (Recommended):**
If the Agent tool is available in your environment, the audit runs via a 4-phase subagent workflow for maximum accuracy and depth. See "Subagent Architecture" section below.

**Without Subagent Tool (Fallback):**
If Agent is not available, the skill still runs a complete audit in a single conversation, though without the structured intermediate data format. The end result (SEO audit report) is the same.

## Subagent Architecture

When the Agent tool is available, this skill uses a 4-phase, multi-agent architecture optimized for large websites:

### Phase 1: Auditor Agent
**Purpose:** Run automated SEO audit and manual review checklist

This agent:
- Scans website files for technical SEO issues (meta tags, headings, canonical URLs, structured data)
- Checks project-level files (robots.txt, sitemap.xml, llms.txt, ai-plugin.json)
- Performs manual review of content quality, internal linking, and framework configuration
- Creates seo-audit.json: a complete machine-readable inventory of all SEO issues with severity levels

**Output artifact:** `<project>/seo-audit.json`

### Phase 2: Researcher Agent
**Purpose:** Fetch latest SEO and AI-bot best practices via web search

This agent:
- Performs 4+ targeted web searches covering SEO best practices, meta tags, AI-bot directives, framework-specific guidance
- Synthesizes findings into actionable recommendations
- Compares research against audit findings to identify gaps
- Creates seo-research-findings.json: structured research results and recommendations with citations

**Output artifact:** `<project>/seo-research-findings.json`

### Phase 3: Implementer Agent
**Purpose:** Apply user-approved changes per category (meta tags, robots.txt, llms.txt, structured data, sitemaps)

This agent:
- Receives user-approved list of improvements to apply
- Implements changes categorized by type (meta tags, robots.txt, AI bot directives, JSON-LD, sitemap, etc.)
- Handles framework-specific implementation (Next.js, Nuxt, Astro, Hugo, SvelteKit, static HTML)
- Produces modified source files ready for testing

**Output:** Modified project files with git-ready changes

### Phase 4: Validator Agent
**Purpose:** Re-run audit on modified site, return before/after comparison

This agent:
- Re-runs the audit script on the modified website
- Produces before/after comparison showing what was fixed
- Validates critical files (robots.txt syntax, JSON-LD validity, canonical URLs, image links)
- Creates seo-validation-report.json: detailed delta report with recommendations for remaining work

**Output artifact:** `<project>/seo-validation-report.json`

### Data Flow

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

## Important

- Audit first, present findings, then propose a plan — never modify files without user approval
- Fetch latest best practices via web search during each audit to supplement embedded knowledge
- For large codebases (100+ pages), audit a representative sample and offer to expand

## Workflow

1. **Detect** -- Identify project framework and scan for relevant files
2. **Audit** -- Run automated scan + manual review across 4 categories
3. **Research** -- Web search for latest SEO/AI bot best practices
4. **Report** -- Present findings grouped by severity
5. **Plan** -- Propose prioritized improvements for user approval
6. **Implement** -- Apply approved changes
7. **Validate** -- Re-check modified files

---

## Step 1: Detect Project Type

Run the audit script to detect framework and scan files:

```bash
python scripts/audit_seo.py <project-root>
```

The script automatically:
- Detects the framework (Next.js, Nuxt, Astro, Hugo, SvelteKit, static HTML, etc.)
- Finds all HTML/template files (excluding node_modules, build dirs)
- Samples representative files for large codebases

If the script reports "No HTML/template files found," inform the user: this skill is designed for web frontends with HTML output.

For framework-specific configuration guidance, consult `references/framework-configs.md`.

## Step 2: Audit

The audit script checks **per-file issues** and **project-level issues**.

### Per-File Checks (automated)
- **Technical SEO:** title tag, meta description, viewport, charset, canonical, lang attribute
- **Content SEO:** H1 presence/count, heading hierarchy, image alt text, image dimensions
- **Structured Data:** JSON-LD presence/validity, OpenGraph tags, Twitter Cards
- **Performance:** render-blocking scripts, lazy-loading on LCP candidates

### Project-Level Checks (automated)
- robots.txt existence and AI bot directives
- sitemap.xml existence (or sitemap generation package)
- llms.txt existence
- ai-plugin.json existence

### Manual Review (after script)

After running the script, manually review these items that require human judgment:

1. **Title/description quality** -- Are they compelling and keyword-relevant? (not just present)
2. **Structured data accuracy** -- Does JSON-LD match visible page content?
3. **Internal linking** -- Are pages reachable within 3 clicks? Descriptive anchors?
4. **Content depth** -- Sufficient E-E-A-T signals? Author bios? Source citations?
5. **Framework-specific config** -- Are SEO packages properly configured?

Consult `references/technical-seo.md` for the full checklist.

## Step 3: Research Latest Best Practices

Use web search to check for updates:

```
Search: "SEO best practices [current year]"
Search: "AI bot robots.txt directives [current year]"
Search: "llms.txt specification latest"
Search: "Google algorithm update [current month/year]"
```

Compare findings with embedded knowledge in `references/` and note any new recommendations.

## Step 4: Report

Present the audit report to the user in this format:

```markdown
## SEO & AI Bot Audit Report

**Project:** [project name]
**Framework:** [detected framework]
**Files audited:** [N] / [total]
**Date:** [date]

### Critical Issues (must fix)
1. [File:line] Issue description
2. ...

### Warnings (should fix)
1. [File:line] Issue description
2. ...

### Info (nice to have)
1. Issue description
2. ...

### Project-Level Findings
- robots.txt: [status]
- sitemap.xml: [status]
- llms.txt: [status]
- Structured data: [status]
- AI bot directives: [status]

### Latest Best Practices (from web search)
- [Any new recommendations not covered by existing fixes]
```

## Step 5: Plan

Present a prioritized improvement plan:

```markdown
## Improvement Plan

### Priority 1: Critical Fixes
- [ ] [Fix description] -- [file(s) affected]
- [ ] ...

### Priority 2: Warnings
- [ ] [Fix description] -- [file(s) affected]
- [ ] ...

### Priority 3: Enhancements
- [ ] [Fix description] -- [file(s) affected]
- [ ] ...

### New Files to Create
- [ ] robots.txt with AI bot directives
- [ ] sitemap.xml (or install generation package)
- [ ] llms.txt
- [ ] JSON-LD structured data
```

Ask the user: "Which improvements should I implement? You can approve all, select specific items, or modify the plan."

Do NOT proceed without explicit approval.

## Step 6: Implement

Apply approved changes. For each category:

### Technical SEO Fixes
- Add/fix meta tags, title, description, viewport, charset, canonical, lang
- For framework-specific implementation, consult `references/framework-configs.md`

### robots.txt with AI Bot Directives
- Consult `references/ai-bot-guide.md` for the full list of AI crawlers
- Ask user preference: allow all AI bots, allow search only, or block all
- Include sitemap reference: `Sitemap: https://example.com/sitemap.xml`

### llms.txt Generation
- Create based on site structure and content
- Follow format in `references/ai-bot-guide.md`
- Include H1 with site name, blockquote summary, H2 sections with key page links

### Structured Data (JSON-LD)
- Add Organization schema on homepage
- Add Article/BlogPosting on content pages
- Add Product on e-commerce pages
- Add BreadcrumbList for navigation
- Consult `references/ai-bot-guide.md` for templates

### OpenGraph & Twitter Cards
- Add og:title, og:type, og:image, og:url, og:description
- Add twitter:card, twitter:title, twitter:description, twitter:image

### sitemap.xml
- Generate or install appropriate package for the framework
- See `references/framework-configs.md` for framework-specific packages

## Step 7: Validate

After implementing changes:

1. Re-run the audit script on modified files:
   ```bash
   python scripts/audit_seo.py <project-root>
   ```

2. Verify critical issues are resolved
3. Report remaining warnings to user

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Phase-specific checks

**Step 1 — Detection**
```
◆ Detection (step 1 of 7 — project scan)
··································································
  Framework identified:     √ pass (Next.js | Nuxt | Astro | ...)
  File structure mapped:    √ pass (N HTML/template files found)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 2 — Audit**
```
◆ Audit (step 2 of 7 — SEO analysis)
··································································
  Meta tags checked:        √ pass (N files scanned)
  Structured data validated: √ pass (JSON-LD present/valid)
  AI bot access verified:   √ pass (robots.txt + llms.txt checked)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 3 — Research**
```
◆ Research (step 3 of 7 — best practices lookup)
··································································
  Web searches completed:   √ pass (N queries executed)
  Latest practices fetched: √ pass (current year updates noted)
  Gaps identified:          √ pass | × fail — [missing coverage areas]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 4 — Report**
```
◆ Report (step 4 of 7 — findings presentation)
··································································
  Issues categorized:       √ pass (critical/warning/info grouped)
  Project-level findings:   √ pass (robots.txt, sitemap, llms.txt, JSON-LD)
  Report presented:         √ pass
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 5 — Plan**
```
◆ Plan (step 5 of 7 — improvement planning)
··································································
  Priorities ranked:        √ pass (critical → warnings → enhancements)
  New files identified:     √ pass (N files to create)
  User approval received:   √ pass | × fail — [awaiting approval]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 6 — Implementation**
```
◆ Implementation (step 6 of 7 — applying fixes)
··································································
  Fixes applied:            √ pass (N issues resolved)
  Sitemaps updated:         √ pass
  Schema.org added:         √ pass (Organization + Article JSON-LD)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 7 — Validation**
```
◆ Validation (step 7 of 7 — post-fix verification)
··································································
  SEO score improved:       √ pass (critical issues: N → 0)
  No regressions:           √ pass
  AI crawl accessible:      √ pass (llms.txt + GPTBot/ClaudeBot allowed)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

## Error Handling

### No HTML Files Found
**Cause:** API-only backend or non-web project.
**Solution:** Inform user this skill is for web frontends. Exit gracefully.

### Framework Config Not Found
**Cause:** Framework detected but config file missing or non-standard location.
**Solution:** Warn and skip framework-specific optimizations. Proceed with generic HTML analysis.

### Web Search Fails
**Cause:** Network issues or rate limiting.
**Solution:** Fall back to embedded best practices in `references/`. Note that latest guidelines could not be fetched.

### Large Codebase
**Cause:** 100+ HTML/template files.
**Solution:** The audit script samples 50 representative files by default. Offer to increase with `--max-files N`.

## Expected Output

After a full run on a Next.js project, the audit report looks like:

```markdown
## SEO & AI Bot Audit Report

**Project:** my-saas-app
**Framework:** Next.js 14
**Files audited:** 24 / 24
**Date:** 2026-04-19

### Critical Issues (must fix)
1. [pages/about.tsx:1] Missing <title> tag
2. [pages/blog/[slug].tsx:14] Duplicate H1 — 2 H1 tags found

### Warnings (should fix)
1. [public/robots.txt] GPTBot not listed — AI crawlers get no explicit directive

### Project-Level Findings
- robots.txt: present, missing AI bot directives
- sitemap.xml: absent — install next-sitemap
- llms.txt: absent — AI-friendly summary missing
- Structured data: partial (homepage only)
- AI bot directives: not configured
```

And after implementation, validation shows: `critical issues: 2 → 0`, `llms.txt created`, `sitemap.xml generated`.

## Edge Cases

- **No HTML files found**: Project is API-only or a non-web backend — skill exits gracefully with a message explaining it targets web frontends.
- **Framework not detected**: Generic HTML analysis proceeds; framework-specific config steps are skipped with a warning.
- **Web search fails**: Falls back to embedded best practices in `references/`; output notes that latest guidelines could not be fetched.
- **robots.txt already exists with custom rules**: Merges AI bot directives without overwriting existing Allow/Disallow entries; shows diff before writing.
- **Conflicting canonical URLs**: Flags each conflict individually; does not auto-fix without user approval since canonical choice affects link equity.
- **Large codebase (100+ pages)**: Audits a representative 50-file sample; offers `--max-files N` flag to expand scope.

