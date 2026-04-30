# Workflow Detail & Templates

This reference provides detailed checklists, markdown templates, and granular implementation instructions for the SEO & AI Bot Optimizer workflow.

## Step 2: Audit — Manual Review Checklist

After running the automated audit script, manually review these items:

1. **Title/description quality** -- Are they compelling and keyword-relevant? (not just present)
2. **Structured data accuracy** -- Does JSON-LD match visible page content?
3. **Internal linking** -- Are pages reachable within 3 clicks? Descriptive anchors?
4. **Content depth** -- Sufficient E-E-A-T signals? Author bios? Source citations?
5. **Framework-specific config** -- Are SEO packages properly configured?
6. **Mobile readiness** -- Viewport configured? Touch targets adequate? No horizontal scrolling?

Consult `references/technical-seo.md` for the full checklist.

## Step 5: Plan — Improvement Plan Template

Use this template when presenting the prioritized improvement plan to the user:

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

## Step 6: Implementation Details

### Safety First: Diff & Confirm Protocol

**CRITICAL:** For every file modification, you MUST follow this safety protocol:
1. **Generate Diff:** Create a clear diff of the changes.
2. **Show Preview:** Present the diff or a detailed summary of changes to the user.
3. **Request Confirmation:** Ask for explicit approval for the specific file(s) before writing (e.g., "Apply these changes to `robots.txt`? [Y/n]").
4. **Backup (Optional but recommended):** Offer to create a `.bak` copy for high-risk files like `robots.txt`.

### Technical SEO Fixes
- Add/fix meta tags, title, description, viewport, charset, canonical, lang.
- For framework-specific implementation, consult `references/framework-configs.md`.

### robots.txt with AI Bot Directives
- Consult `references/ai-bot-guide.md` for the full list of AI crawlers.
- Ask user preference: allow all AI bots, allow search only, or block all.
- Include sitemap reference: `Sitemap: https://example.com/sitemap.xml`.
- **Merge logic:** Do NOT overwrite existing `Allow`/`Disallow` rules. Append new directives to the end or merge intelligently.

### llms.txt Generation
- Create based on site structure and content.
- Follow format in `references/ai-bot-guide.md`.
- Include H1 with site name, blockquote summary, H2 sections with key page links.

### Structured Data (JSON-LD)
- Add Organization schema on homepage.
- Add Article/BlogPosting on content pages.
- Add Product on e-commerce pages.
- Add BreadcrumbList for navigation.
- Consult `references/ai-bot-guide.md` for templates.

### OpenGraph & Twitter Cards
- Add `og:title`, `og:type`, `og:image`, `og:url`, `og:description`.
- Add `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`.

### sitemap.xml
- Generate or install appropriate package for the framework.
- See `references/framework-configs.md` for framework-specific packages.

## Auxiliary Information

### Error Handling
- **No HTML Files Found:** Inform user this skill is for web frontends. Exit gracefully.
- **Framework Config Not Found:** Warn and skip framework-specific optimizations. Proceed with generic HTML analysis.
- **Web Search Fails:** Fall back to embedded best practices in `references/`. Note that latest guidelines could not be fetched.
- **Large Codebase:** The audit script samples 50 representative files by default. Offer to increase with `--max-files N`.

### Expected Output

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

After implementation, validation shows: `critical issues: 2 → 0`, `llms.txt created`, `sitemap.xml generated`.

### Acceptance Criteria
- [ ] Audit report identifies the framework detected or explicitly states "generic HTML".
- [ ] Findings are grouped by severity (Critical / Major / Minor) and each cites the affected file path.
- [ ] User explicitly approved the improvement plan before any file was modified.
- [ ] Safety Protocol (Diff & Confirm) was followed for all file modifications.
- [ ] Post-implementation validation re-runs the audit script and shows the critical-issue count drop to 0.
- [ ] `llms.txt`, `robots.txt`, and `sitemap.xml` are present (or explicitly justified).

### Edge Cases
- **robots.txt already exists with custom rules:** Merges AI bot directives without overwriting existing entries; shows diff before writing.
- **Conflicting canonical URLs:** Flags each conflict individually; does not auto-fix without user approval.
- **Large codebase (100+ pages):** Audits a representative 50-file sample; offers `--max-files N` flag to expand scope.
