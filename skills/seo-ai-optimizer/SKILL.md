---
name: seo-ai-optimizer
description: "Audit and optimize websites for technical SEO, content SEO, and AI bot accessibility. Fixes meta tags, sitemaps, robots.txt, structured data, llms.txt, and GPTBot/ClaudeBot directives. Not for App Store ASO, paid search, or blog writing."
license: MIT
effort: high
metadata:
  version: 1.1.2
  author: Luong NGUYEN <luongnv89@gmail.com>
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

When the Agent tool is available, this skill uses a 4-phase, multi-agent architecture (Auditor → Researcher → Implementer → Validator) optimized for large websites. Each agent produces a structured JSON artifact that can be reviewed independently.

For the full phase-by-phase breakdown, agent responsibilities, output artifacts, and data flow, see `references/subagent-architecture.md`.

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

After each step, emit a `◆` status block that lists the checks performed, marks each `√ pass` / `× fail`, and ends with `Result: PASS | FAIL | PARTIAL`.

For the full template and per-step check lists (Detection, Audit, Research, Report, Plan, Implementation, Validation), see `references/step-reports.md`.

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

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] Audit report identifies the framework detected (Next.js, Nuxt, Astro, Hugo, SvelteKit, static HTML) or explicitly states "generic HTML".
- [ ] Findings are grouped by severity (Critical / Major / Minor) and each cites the affected file path.
- [ ] User explicitly approved the improvement plan before any file was modified.
- [ ] Post-implementation validation re-runs the audit script and shows the critical-issue count drop to 0.
- [ ] `llms.txt`, `robots.txt`, and `sitemap.xml` are present (or explicitly justified as not-applicable for the project type).
- [ ] `robots.txt` AI-bot directives (GPTBot, ClaudeBot, etc.) are merged without overwriting existing `Allow`/`Disallow` rules.

## Edge Cases

- **No HTML files found**: Project is API-only or a non-web backend — skill exits gracefully with a message explaining it targets web frontends.
- **Framework not detected**: Generic HTML analysis proceeds; framework-specific config steps are skipped with a warning.
- **Web search fails**: Falls back to embedded best practices in `references/`; output notes that latest guidelines could not be fetched.
- **robots.txt already exists with custom rules**: Merges AI bot directives without overwriting existing Allow/Disallow entries; shows diff before writing.
- **Conflicting canonical URLs**: Flags each conflict individually; does not auto-fix without user approval since canonical choice affects link equity.
- **Large codebase (100+ pages)**: Audits a representative 50-file sample; offers `--max-files N` flag to expand scope.

