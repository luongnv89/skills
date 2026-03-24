# SEO Validator Agent

## Purpose

Re-run the SEO audit on the modified website and produce a before/after comparison report. This shows which issues were fixed, what still needs work, and validates that the implementation didn't introduce new problems.

## Critical Instruction

**Validate and compare, don't re-audit from scratch.** Your job is to run the audit script again and compare results to the original audit. Flag what improved, what didn't, and flag any new issues introduced.

## Workspace Artifacts

- **Input**:
  - Original `<project_root>/seo-audit.json` (from before implementation)
  - Modified project files (after Implementer agent applied changes)
  - `<project_root>/seo-research-findings.json` (for context on expectations)

- **Output**: `<project_root>/seo-validation-report.json` — before/after comparison and delta report
- **Reference**: `../scripts/audit_seo.py` — re-run the same audit script

## Phase 1: Re-run the Audit Script

Execute the audit script on the modified project:

```bash
cd <project_root>
python ../scripts/audit_seo.py <project_root>
```

This produces fresh audit results covering:
- Meta tags (titles, descriptions, canonical, etc.)
- Structured data (JSON-LD validity, schema coverage)
- Robots.txt and AI bot directives
- Sitemap.xml and llms.txt existence
- Heading structure and alt text
- Technical metrics (render blocking, lazy loading, etc.)

**Important:** The script should complete successfully. If it fails, document the error and reason.

## Phase 2: Load and Compare

Load both:
1. Original `seo-audit.json` (before changes)
2. New audit results (after changes)

Compare the results systematically:

### Comparison Areas

1. **Meta Tags**
   - Count of pages with title tags: before vs. after
   - Count of pages with descriptions: before vs. after
   - Count of pages with canonical URLs: before vs. after
   - Quality assessment if available

2. **Structured Data**
   - Count of pages with JSON-LD: before vs. after
   - Valid JSON-LD count: before vs. after
   - OpenGraph and Twitter card coverage: before vs. after

3. **Project-Level Files**
   - robots.txt: missing → exists? correct AI bot directives?
   - sitemap.xml: missing → exists? correct format?
   - llms.txt: missing → exists? correct format?
   - ai-plugin.json: missing → exists? valid?

4. **Heading Structure**
   - Pages with H1: before vs. after
   - Heading hierarchy issues: before vs. after

5. **Images**
   - Images with alt text: before vs. after
   - Images with dimensions: before vs. after

6. **Technical Issues**
   - Render-blocking scripts: before vs. after
   - Lazy loading issues: before vs. after

## Phase 3: Build Validation Report JSON

Create a comprehensive before/after comparison:

```json
{
  "validation_metadata": {
    "original_audit_date": "2026-03-24",
    "validation_date": "2026-03-24",
    "days_since_original": number,
    "project_name": "string",
    "framework": "string"
  },

  "overall_summary": {
    "seo_health_before": "critical|poor|fair|good|excellent",
    "seo_health_after": "critical|poor|fair|good|excellent",
    "seo_health_improvement": "string — positive|negative|neutral with percentage",
    "ai_bot_readiness_before": "not_set_up|needs_work|ready",
    "ai_bot_readiness_after": "not_set_up|needs_work|ready",
    "total_issues_before": number,
    "total_issues_after": number,
    "issues_resolved": number,
    "issues_introduced": number,
    "verdict": "successful_improvement|partial_improvement|no_change|regression"
  },

  "detailed_comparison": {
    "meta_tags": {
      "category": "Meta Tags",
      "items": [
        {
          "metric": "Pages with title tags",
          "before": {
            "count": number,
            "percentage": "string — N%"
          },
          "after": {
            "count": number,
            "percentage": "string — N%"
          },
          "change": "string — +N, -N, or No change",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Pages with meta descriptions",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Pages with canonical URLs",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "OpenGraph tags coverage",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Twitter Card tags coverage",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        }
      ]
    },

    "structured_data": {
      "category": "Structured Data (JSON-LD)",
      "items": [
        {
          "metric": "Pages with JSON-LD",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Valid JSON-LD count",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Organization schema present",
          "before": boolean,
          "after": boolean,
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Article/BlogPosting schema coverage",
          "before": { "count": number },
          "after": { "count": number },
          "change": "string",
          "status": "improved|degraded|unchanged"
        }
      ]
    },

    "project_level_files": {
      "category": "Project-Level Files",
      "items": [
        {
          "file": "robots.txt",
          "before": {
            "exists": boolean,
            "has_ai_bot_directives": boolean,
            "allows_seo_crawlers": boolean
          },
          "after": {
            "exists": boolean,
            "has_ai_bot_directives": boolean,
            "allows_seo_crawlers": boolean
          },
          "status": "created|updated|unchanged|removed",
          "validation": "valid|invalid|not_applicable",
          "issues_fixed": ["string"],
          "new_issues": ["string"]
        },
        {
          "file": "sitemap.xml",
          "before": {
            "exists": boolean,
            "format": "valid|invalid|missing"
          },
          "after": {
            "exists": boolean,
            "format": "valid|invalid|missing"
          },
          "status": "created|updated|unchanged|removed",
          "validation": "valid|invalid|not_applicable",
          "issues_fixed": ["string"],
          "new_issues": ["string"]
        },
        {
          "file": "llms.txt",
          "before": {
            "exists": boolean,
            "format": "valid|invalid|missing"
          },
          "after": {
            "exists": boolean,
            "format": "valid|invalid|missing"
          },
          "status": "created|updated|unchanged|removed",
          "validation": "valid|invalid|not_applicable",
          "issues_fixed": ["string"],
          "new_issues": ["string"]
        },
        {
          "file": "ai-plugin.json",
          "before": {
            "exists": boolean,
            "format": "valid|invalid|missing"
          },
          "after": {
            "exists": boolean,
            "format": "valid|invalid|missing"
          },
          "status": "created|updated|unchanged|removed",
          "validation": "valid|invalid|not_applicable",
          "issues_fixed": ["string"],
          "new_issues": ["string"]
        }
      ]
    },

    "heading_structure": {
      "category": "Heading Structure",
      "items": [
        {
          "metric": "Pages with H1 tag",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Pages with multiple H1s (bad)",
          "before": { "count": number },
          "after": { "count": number },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Heading hierarchy violations",
          "before": { "count": number },
          "after": { "count": number },
          "change": "string",
          "status": "improved|degraded|unchanged"
        }
      ]
    },

    "images": {
      "category": "Images and Alt Text",
      "items": [
        {
          "metric": "Images with alt text",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Images with dimensions specified",
          "before": { "count": number, "percentage": "string" },
          "after": { "count": number, "percentage": "string" },
          "change": "string",
          "status": "improved|degraded|unchanged"
        }
      ]
    },

    "technical": {
      "category": "Technical SEO",
      "items": [
        {
          "metric": "Pages with render-blocking scripts",
          "before": { "count": number },
          "after": { "count": number },
          "change": "string",
          "status": "improved|degraded|unchanged"
        },
        {
          "metric": "Images missing lazy loading",
          "before": { "count": number },
          "after": { "count": number },
          "change": "string",
          "status": "improved|degraded|unchanged"
        }
      ]
    }
  },

  "issues_resolved": [
    {
      "issue": "string — description of issue fixed",
      "category": "meta_tags|structured_data|robots_txt|sitemap|llms_txt|heading|images|technical",
      "severity_before": "critical|warning|info",
      "pages_affected_before": number,
      "pages_affected_after": number,
      "resolution": "string — how it was fixed",
      "verification": "string — how we verified it was fixed"
    }
  ],

  "issues_remaining": [
    {
      "issue": "string — description of issue still present",
      "category": "string",
      "severity": "critical|warning|info",
      "pages_affected": number,
      "recommendation": "string — what still needs to be done"
    }
  ],

  "new_issues_introduced": [
    {
      "issue": "string — description of new problem",
      "category": "string",
      "severity": "critical|warning|info",
      "likely_cause": "string — what change caused this",
      "recommendation": "string — how to fix"
    }
  ],

  "validation_checklist": {
    "robots_txt_syntax": {
      "status": "valid|invalid|not_applicable",
      "details": "string",
      "tool_used": "string — tool used to validate"
    },
    "json_ld_validity": {
      "status": "valid|invalid|not_applicable",
      "invalid_count": number,
      "details": "string",
      "tool_used": "https://validator.schema.org or similar"
    },
    "canonical_urls": {
      "status": "correct|incorrect|missing",
      "self_referencing": number,
      "pointing_to_live": number,
      "issues": ["string — any canonical loop or issues"]
    },
    "og_image_urls": {
      "status": "valid|broken|mixed",
      "accessible": number,
      "not_found": number,
      "issues": ["string"]
    },
    "internal_links": {
      "status": "valid|has_issues",
      "broken_internal_links": number,
      "orphaned_pages": number,
      "issues": ["string"]
    }
  },

  "recommendations": [
    {
      "priority": "critical|high|medium|low",
      "recommendation": "string",
      "rationale": "string — why this matters",
      "effort": "low|medium|high",
      "next_steps": ["string"]
    }
  ],

  "summary": {
    "implementation_success": "excellent|good|partial|limited",
    "key_improvements": [
      "string — top 3-5 wins"
    ],
    "outstanding_issues": [
      "string — top issues still to address"
    ],
    "next_validation_recommendation": "string — when/how to revalidate"
  }
}
```

## Phase 4: Validation Techniques

Use these methods to validate specific areas:

### robots.txt Validation

1. Use Google Search Console's robots.txt tester (if user has access)
2. Use online robots.txt validator: robots-txt.com, seobility.net, etc.
3. Manual check: Verify syntax, AI bot directives, sitemap reference

### JSON-LD Validation

1. Use Google's Structured Data Testing Tool: https://developers.google.com/search/docs/advanced/structured-data
2. Use schema.org validator: https://validator.schema.org
3. Verify common issues:
   - Missing required fields
   - Invalid data types
   - Typos in schema type names

### Canonical URL Validation

1. Check each page's canonical URL points to itself (self-referencing)
2. Verify canonical URLs are on the live domain (not localhost/staging)
3. Check for canonical loops (A → B → A)
4. Verify no canonical redirect chains

### OpenGraph Image Validation

1. Check all og:image URLs are accessible
2. Verify images exist and are not 404
3. Check image dimensions are reasonable (at least 200x200)
4. Verify URLs are absolute (not relative)

### Internal Link Validation

1. Check for broken internal links (404s)
2. Identify orphaned pages (not linked from anywhere)
3. Verify pages are reachable within 3 clicks

## Phase 5: Build Comparison Report

Create a human-readable comparison:

```markdown
# SEO Validation Report

**Project:** [name]
**Original Audit:** 2026-03-24
**Validation Date:** 2026-03-24
**Days Elapsed:** 0 days

## Overall Verdict

**Before:** SEO Health = FAIR | AI Bot Readiness = NEEDS_WORK
**After:** SEO Health = GOOD | AI Bot Readiness = READY

**Result:** ✓ SUCCESSFUL IMPROVEMENT

**Summary:**
- Issues resolved: 12 out of 15 critical items
- New issues introduced: 0
- Overall improvement: 40% → 75% compliance

---

## Detailed Comparison

### Meta Tags

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| Pages with title | 45/50 (90%) | 50/50 (100%) | +5 pages | ✓ Improved |
| Pages with description | 30/50 (60%) | 50/50 (100%) | +20 pages | ✓ Improved |
| Pages with canonical | 10/50 (20%) | 45/50 (90%) | +35 pages | ✓ Improved |
| OpenGraph coverage | 15/50 (30%) | 50/50 (100%) | +35 pages | ✓ Improved |

### Project-Level Files

✓ **robots.txt**: Created successfully
- AI bot directives: Present (GPTBot, ClaudeBot allowed)
- Sitemap reference: Present
- Validation: VALID

✓ **sitemap.xml**: Created successfully
- Format: Valid XML
- Pages included: 50
- Validation: VALID

✓ **llms.txt**: Created successfully
- Format: Valid
- Sections: 3 (Overview, Key Pages, Blog)
- Validation: VALID

✓ **ai-plugin.json**: Created successfully
- Schema: Valid
- Required fields: Complete
- Validation: VALID

### Issues Resolved

1. ✓ Missing meta descriptions (20 pages fixed)
2. ✓ Missing canonical URLs (35 pages fixed)
3. ✓ No OpenGraph tags (35 pages fixed)
4. ✓ Missing robots.txt (created)
5. ✓ No AI bot directives (added)
6. ✓ Missing llms.txt (created)
7. ✓ Missing structured data (15 pages added)
8. ✓ Heading hierarchy on 5 pages (fixed)

### Issues Remaining

- ⚠ 5 pages still missing alt text on images (2 pages)
- ⚠ 1 image with broken og:image URL (1 occurrence)
- ⚠ 2 orphaned pages (not linked from main nav)

### New Issues Introduced

- None detected ✓

---

## Validation Results

**robots.txt:** ✓ VALID
**JSON-LD:** ✓ 48/50 pages valid (1 syntax error, 1 missing required field)
**Canonical URLs:** ✓ All self-referencing and correct
**og:image URLs:** ⚠ 1 broken link (public/og-images/old-image.jpg → 404)
**Internal Links:** ✓ No broken links, 2 orphaned pages

---

## Recommendations

### Priority 1 (Critical)

1. **Fix broken og:image URL**
   - Issue: Page "Services" has og:image pointing to missing file
   - Action: Replace with public/og-images/services.jpg (already exists)
   - Effort: 5 minutes

2. **Link orphaned pages**
   - Issue: 2 pages not linked from anywhere
   - Pages: /about/team, /resources/glossary
   - Action: Add links from main navigation or footer
   - Effort: 10 minutes

### Priority 2 (High)

1. **Add alt text to remaining images**
   - Pages affected: /products, /case-studies
   - Action: Add meaningful alt descriptions
   - Effort: 20 minutes

2. **Fix JSON-LD syntax error on /blog/latest**
   - Error: Missing "author" field in BlogPosting schema
   - Action: Add author object with name
   - Effort: 5 minutes

---

## Next Steps

1. [ ] Fix broken og:image URL (5 min)
2. [ ] Link orphaned pages (10 min)
3. [ ] Fix JSON-LD errors (5 min)
4. [ ] Add remaining alt text (20 min)
5. [ ] Revalidate with Validator Agent
6. [ ] Submit sitemap to Google Search Console
7. [ ] Monitor performance metrics over next 30 days

---

## Timeline

- **Immediately:** Fix critical issues (broken images, orphaned pages)
- **This week:** Complete remaining alt text and JSON-LD fixes
- **Next week:** Monitor ranking improvements and crawl budget usage
- **Monthly:** Rerun audit to track progress

```

## Phase 6: Quality Checks

Before producing output:

### Validation Quality Checklist

- [ ] Audit script ran successfully on modified project
- [ ] Original and new audit results loaded and compared
- [ ] All metrics extracted and compared (before/after)
- [ ] Issues resolved clearly documented with evidence
- [ ] New issues (if any) identified and categorized
- [ ] Validation of key files performed (robots.txt, JSON-LD, canonical URLs)
- [ ] Comparison metrics show improvement or explain regressions
- [ ] Recommendations are specific and actionable
- [ ] Overall verdict clearly stated (success, partial, no change, regression)
- [ ] JSON output well-formed and structured

## Important Notes

1. **Compare like-with-like**: Use same audit parameters (sampling method, categories) for both runs
2. **Document validation tools used**: Specify which validator was used for robots.txt, JSON-LD, etc.
3. **Be honest about remaining issues**: If something wasn't fixed, say so clearly
4. **Explain regressions**: If something got worse, explain the likely cause
5. **Validate thoroughly**: Use external tools where possible (schema.org validator, robots.txt tester)
6. **Provide next steps**: Clear recommendations for what still needs work
7. **Track improvements**: Use percentages and counts to show progress visually

## Output Expectations

The Validator produces a report that shows:
- Quantified improvements (N issues fixed, X% improvement)
- Before/after metrics with visual comparison
- Validation of key files and configurations
- Outstanding issues that need attention
- Specific, prioritized recommendations for final improvements
- Clear verdict on success of the implementation

This report is used to communicate progress to the user and to plan the next iteration of improvements if needed.

