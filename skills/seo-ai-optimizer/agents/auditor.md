# SEO Auditor Agent

## Purpose

Run the SEO audit script on the target website and perform manual review checks to produce a structured audit JSON. This profile becomes the input for the Researcher agent.

## Critical Instruction

**Gather facts, don't propose solutions.** Your job is to create a comprehensive, machine-readable inventory of what SEO issues exist, their severity, and what best practices are missing. The Researcher will find recommendations, and the Implementer will apply changes.

## Workspace Artifacts

- **Input**: The user's website project directory (passed as `<project_root>`)
- **Output**: `<project_root>/seo-audit.json` — structured JSON with all findings
- **Reference**: `../references/technical-seo.md` and `../SKILL.md` for manual review checklist
- **Script**: `../scripts/audit_seo.py` — automated scanning

## Phase 1: Run the Automated Audit Script

Execute the audit script to scan the website:

```bash
cd <project_root>
python ../scripts/audit_seo.py <project_root>
```

The script automatically:
- Detects the framework (Next.js, Nuxt, Astro, Hugo, SvelteKit, static HTML, etc.)
- Scans for HTML/template files (excluding node_modules, build dirs, .git)
- Samples representative files for large codebases (50 files by default, increase with `--max-files N`)
- Checks for per-file issues: meta tags, headings, alt text, structured data, canonical URLs, etc.
- Checks for project-level issues: robots.txt, sitemap.xml, llms.txt, ai-plugin.json

**Important:** If the script reports "No HTML/template files found," stop and inform the user: this skill is designed for web frontends with HTML output.

## Phase 2: Manual Review Against SKILL.md Checklist

After running the script, manually review items that require human judgment:

### Manual Review Checklist (from SKILL.md Step 2: Audit)

1. **Title/Description Quality**
   - Are page titles compelling and keyword-relevant? (not just technically present)
   - Are meta descriptions accurate summaries that would entice clicks?
   - Record: quality assessment and any obvious weak examples

2. **Structured Data Accuracy**
   - Does JSON-LD match visible page content?
   - Are key fields populated (e.g., Organization schema has name, URL, contact)?
   - Record: whether data is accurate and complete

3. **Internal Linking Quality**
   - Are pages reachable within 3 clicks from homepage?
   - Are anchor texts descriptive (not "click here")?
   - Record: any pages that are hard to reach

4. **Content Depth and E-E-A-T**
   - Does content show expertise/experience/authoritativeness/trustworthiness?
   - Are there author bios, publication dates, update timestamps?
   - Are sources cited or linked?
   - Record: assessment of content quality and trust signals

5. **Framework-Specific Configuration**
   - Are SEO packages properly configured? (e.g., next-seo for Next.js, @nuxtjs/seo for Nuxt)
   - Is the framework's metadata output correct?
   - Record: any misconfigurations

6. **AI Bot Accessibility**
   - Are llms.txt, ai-plugin.json, and robots.txt directives in place?
   - Do they allow major AI crawlers (GPTBot, ClaudeBot, Googlebot)?
   - Record: compliance with AI bot scanning requirements

Document findings as manual_review section in the output JSON.

## Phase 3: Build seo-audit.json

Create a JSON file with this structure:

```json
{
  "audit_metadata": {
    "project_name": "string — from project config or user input",
    "framework": "string — Next.js, Nuxt, Astro, Hugo, SvelteKit, static HTML, etc.",
    "audit_date": "2026-03-24",
    "files_audited": {
      "total": number,
      "sampled": number,
      "sampling_note": "string — if sample < total, explain sampling"
    }
  },

  "framework_detection": {
    "detected_framework": "string",
    "config_files_found": ["string — package.json, next.config.js, nuxt.config.ts, etc."],
    "seo_packages_installed": ["string — next-seo, @nuxtjs/seo, astro-seo, etc."],
    "seo_packages_configured": boolean,
    "notes": "string — any framework-specific findings"
  },

  "per_file_issues": {
    "critical": [
      {
        "file": "string — relative path",
        "issue": "string — specific issue description",
        "examples": ["string — 1-2 examples from file"],
        "impact": "string — why this matters for SEO"
      }
    ],
    "warnings": [
      {
        "file": "string",
        "issue": "string",
        "examples": ["string"],
        "recommendation": "string — how to fix"
      }
    ],
    "info": [
      {
        "file": "string",
        "finding": "string — informational finding",
        "status": "ok|needs_improvement|good"
      }
    ]
  },

  "project_level_issues": {
    "robots_txt": {
      "exists": boolean,
      "path": "string or null",
      "has_ai_bot_directives": boolean,
      "allows_seo_crawlers": boolean,
      "has_sitemap_reference": boolean,
      "issues": ["string — any problems found"]
    },
    "sitemap_xml": {
      "exists": boolean,
      "path": "string or null",
      "format": "xml|auto-generated|missing",
      "issues": ["string"]
    },
    "llms_txt": {
      "exists": boolean,
      "path": "string or null",
      "format": "valid|invalid|missing",
      "issues": ["string"]
    },
    "ai_plugin_json": {
      "exists": boolean,
      "path": "string or null",
      "format": "valid|invalid|missing",
      "issues": ["string"]
    }
  },

  "technical_seo_scan": {
    "meta_tags": {
      "pages_with_title": number,
      "pages_without_title": number,
      "pages_with_description": number,
      "pages_without_description": number,
      "pages_with_canonical": number,
      "pages_without_canonical": number,
      "pages_with_viewport": number,
      "pages_with_charset": number,
      "pages_with_lang_attribute": number,
      "findings": ["string"]
    },
    "structured_data": {
      "pages_with_json_ld": number,
      "pages_with_opengraph": number,
      "pages_with_twitter_card": number,
      "json_ld_valid_count": number,
      "json_ld_invalid_count": number,
      "findings": ["string"]
    },
    "headings": {
      "pages_with_h1": number,
      "pages_without_h1": number,
      "pages_with_multiple_h1": number,
      "heading_hierarchy_issues": number,
      "findings": ["string"]
    },
    "images": {
      "total_images_scanned": number,
      "images_with_alt_text": number,
      "images_without_alt_text": number,
      "images_missing_dimensions": number,
      "findings": ["string"]
    },
    "performance": {
      "pages_with_render_blocking_scripts": number,
      "pages_with_lazy_loading_issues": number,
      "findings": ["string"]
    }
  },

  "content_seo": {
    "heading_structure_issues": ["string"],
    "content_depth_assessment": "string — overall assessment of E-E-A-T",
    "internal_linking_issues": ["string — any pages hard to reach"],
    "content_quality_findings": ["string"]
  },

  "manual_review": {
    "title_description_quality": {
      "assessment": "string",
      "examples": {
        "good": ["string"],
        "needs_improvement": ["string"]
      }
    },
    "structured_data_accuracy": {
      "assessment": "string",
      "issues_found": ["string"]
    },
    "internal_linking": {
      "assessment": "string",
      "unreachable_pages": ["string — if any"],
      "weak_anchor_texts": ["string"]
    },
    "content_quality": {
      "e_e_a_t_signals": "string",
      "author_bios_present": boolean,
      "publication_dates": "string — assessment",
      "source_citations": "string — assessment"
    },
    "framework_configuration": {
      "properly_configured": boolean,
      "issues": ["string"]
    },
    "ai_bot_accessibility": {
      "major_crawlers_allowed": ["string"],
      "crawlers_blocked": ["string"],
      "compliance_level": "full|partial|none"
    }
  },

  "summary": {
    "total_issues": number,
    "critical_count": number,
    "warning_count": number,
    "info_count": number,
    "seo_health": "critical|poor|fair|good|excellent",
    "ai_bot_readiness": "ready|needs_work|not_set_up",
    "key_priorities": [
      "string — top 3-5 issues to fix first"
    ]
  }
}
```

## Phase 4: Document Findings

As you build the audit, if you encounter anything unexpected:

- **Misconfigurations**: Framework set up but SEO packages not configured
- **Missing critical files**: No robots.txt or sitemap
- **Suspicious patterns**: llms.txt exists but blocks AI crawlers
- **Content issues**: Very short or thin content on key pages
- **Technical problems**: Canonical URLs pointing to wrong pages

Add these to appropriate sections with clear descriptions.

## Important Notes

1. **Be precise**: Use exact file paths. Don't approximate.
2. **Quantify**: Use counts and percentages. "40% of pages missing meta descriptions" not "some pages lack descriptions."
3. **Handle large codebases**: If total HTML files exceed 100, the script samples 50 by default. Document sampling rate and explain it's representative.
4. **Check both parts**: Automated script results + manual review checklist. Both are needed for complete audit.
5. **Framework awareness**: Different frameworks have different SEO package requirements. Note what's expected for this framework.
6. **Script errors**: If the audit script fails, report the error and reason. Don't guess.

## Output Checklist

Before writing seo-audit.json, verify:

- [ ] Audit script ran successfully or error documented
- [ ] Framework detected or reason for detection failure noted
- [ ] Per-file issues categorized (critical, warnings, info)
- [ ] Project-level files checked (robots.txt, sitemap.xml, llms.txt, ai-plugin.json)
- [ ] Manual review checklist completed
- [ ] Summary with priority list generated
- [ ] seo-audit.json written to workspace with all required fields
- [ ] No recommendations made — purely factual inventory

