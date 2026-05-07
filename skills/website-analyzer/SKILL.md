---
name: website-analyzer
description: "Analyze any website URL across 6 dimensions: UI/UX, category, style, performance (LCP/CLS/TTFB/weight/requests), surface-level security, and SEO (score 0-100 with breakdown). Outputs structured JSON for downstream skills. Use when asked to analyze, audit, or scan a website. Don't use for full SEO audits or penetration testing."
license: MIT
effort: high
metadata:
  version: 1.0.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Website Analyzer

Analyzes any website URL across 6 dimensions and produces structured JSON output for downstream skills in the website-cloner suite.

## When to Use

Trigger when the user asks to:
- Analyze, audit, or scan a website
- Get a performance, SEO, security, or UI/UX assessment of a URL
- Understand a website's structure, style, or category

Do **not** use for full penetration testing, deep security audits, or App Store ASO.

## Workflow

```
1. Fetch page content via WebFetch
2. Extract HTML structure, metadata, headings, links, images, scripts
3. Estimate performance metrics (LCP, CLS, TTFB, page weight, request count)
4. Run surface-level security checks
5. Score SEO across 5 weighted dimensions
6. Classify UI/UX layout, category, and style
7. Output structured JSON
```

## Output

Produce structured JSON at the requested output path (or stdout):

```json
{
  "url": "https://example.com",
  "timestamp": "2026-05-07T12:00:00Z",
  "ui_ux": {
    "layout": "single-column | two-column | grid | ...",
    "visual_hierarchy": "what draws attention first",
    "components": ["nav", "hero", "cta", "footer", ...],
    "responsive": "desktop-first | mobile-first | adaptive | unknown",
    "friction_points": ["slow nav", "missing CTA", ...]
  },
  "category": "saas-landing | portfolio | e-commerce | blog | docs | dashboard | ...",
  "category_confidence": 0.9,
  "style": {
    "typography": "brief description",
    "palette": ["#hex", ...],
    "spacing": "compact | comfortable | spacious",
    "motion": "minimal | moderate | heavy",
    "aesthetic": "vibe description"
  },
  "performance": {
    "lcp_estimate": 2.5,
    "cls_estimate": 0.05,
    "ttfb_estimate": 0.3,
    "total_page_weight_kb": 1200,
    "request_count": 45,
    "notes": "estimated from static analysis"
  },
  "security": {
    "https": true,
    "mixed_content": false,
    "security_headers": ["strict-transport-security", ...],
    "exposed_metadata": [],
    "note": "Surface-level check only. Not a full security audit."
  },
  "seo": {
    "score": 72,
    "title_tag": "present | missing | duplicate",
    "meta_description": "present | missing | too-short",
    "heading_structure": "h1:N h2:N ...",
    "alt_text_coverage": 0.85,
    "structured_data": "present | missing",
    "canonical_url": "present | missing",
    "robots_sitemap": "robots=ok | sitemap=found | ...",
    "dimension_scores": {
      "meta_tags": 80,
      "heading_structure": 60,
      "image_alt_text": 90,
      "structured_data": 50,
      "crawlability": 75
    }
  }
}
```

## Step 1: Fetch the Page

Use `WebFetch` to retrieve content:

```
WebFetch(url=<url>, prompt="Extract all HTML structure, meta tags, headings, links, images, scripts, styles, and any structured data (JSON-LD, Open Graph, etc.)")
```

If WebFetch fails (4xx, 5xx, timeout), return immediately:
```json
{"url": "<url>", "error": "unreachable", "detail": "<error>"}
```

For JS-heavy SPAs where WebFetch returns minimal content, note:
`{"note": "SPA detected — analysis based on crawlable content only; some metrics may be incomplete"}`

## Step 2: Extract Structure

From fetched content, extract:
- `<title>`, `<meta>` tags (description, keywords, OG, Twitter)
- Heading hierarchy (`<h1>`–`<h6>`)
- Images with `alt` attributes
- Link structure and count
- Script/style count and sizes
- JSON-LD structured data
- Canonical URL
- Robots meta tag

## Step 3: Estimate Performance

| Metric | Method |
|--------|--------|
| Page weight | Sum of referenced resource sizes; estimate image sizes from layout |
| Request count | Count `<img>`, `<link rel="stylesheet">`, `<script>`, font refs |
| LCP | Inferred from above-fold content size; min 0.5s for bare HTML |
| CLS | Estimated from layout shift indicators (missing dimensions, late loaders) |
| TTFB | Inferred from hosting signals; static → low, dynamic → moderate |

All metrics are estimates from static analysis. Note this in output.

## Step 4: Security Check (Surface-Level Only)

Check:
- HTTPS usage
- Mixed content (HTTP resources on HTTPS page)
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- Exposed metadata (dev tools, debug endpoints, sensitive data in comments)

Always label as surface-level.

## Step 5: SEO Scoring

Compute each dimension's 0–100 sub-score using the rubrics below, then combine with the weights to yield the overall `seo.score`. Round each sub-score to the nearest integer; the final score is `round(Σ weight_i × sub_i)`.

| Dimension | Weight | Sub-score rubric (0–100) |
|-----------|--------|--------------------------|
| Meta tags (title + description) | 20% | Start at 0. +50 if `<title>` is present and 10–60 chars. +50 if `<meta name="description">` is present and 50–160 chars. Subtract 25 each for: title outside 10–60, description outside 50–160, duplicate title across siblings (when crawlable). Floor at 0. |
| Heading structure | 15% | 100 if exactly one `<h1>` and at least one `<h2>`. 70 if exactly one `<h1>` but no `<h2>`. 40 if zero or multiple `<h1>`s. Subtract 20 if any heading level is skipped (e.g. h2 → h4). Floor at 0. |
| Image alt text coverage | 15% | `round(100 × non_empty_alt_count / total_img_count)`. If `total_img_count == 0`, report 100 (no images = no alt-text debt). Decorative images using `alt=""` count as "non-empty intent" only when paired with `role="presentation"`; otherwise count as missing. |
| Structured data | 20% | 100 if at least one valid JSON-LD block is present and parses (any schema). 60 if only Open Graph or Twitter Card meta tags are present (no JSON-LD). 30 if only microdata or RDFa. 0 if none. |
| Crawlability (canonical, robots, sitemap) | 30% | Start at 0. +40 if a `<link rel="canonical">` resolves to an absolute URL. +30 if `robots.txt` is fetchable and not `Disallow: /`. +30 if a sitemap is referenced (via `robots.txt` `Sitemap:` directive, `<link rel="sitemap">`, or a fetchable `/sitemap.xml`). Cap at 100. |

When a sub-score cannot be computed (e.g. `robots.txt` unreachable), record the dimension as `null` in `dimension_scores` and exclude it from the weighted sum, redistributing its weight proportionally across the remaining dimensions. Note any nulls in `seo.notes`.

## Step 6: UI/UX, Category, Style

- **Layout**: Infer from HTML structure (divs, sections, nav, main, footer)
- **Category**: `saas-landing` | `portfolio` | `e-commerce` | `blog` | `docs` | `dashboard` | `marketing-site` | `web-app` | `other`
- **Style**: Typography, color palette, spacing density, motion indicators, aesthetic vibe

## Error Handling

| Failure | Behavior |
|---|---|
| Unreachable (4xx/5xx/timeout) | `{"error": "unreachable"}` — stop |
| JS-heavy SPA | Note limitation, proceed with crawlable content |
| Paywall / login | `{"error": "paywall"}` — stop |
| Redirect loop | `{"error": "redirect-loop"}` — stop |
| Empty page | `{"error": "empty"}` — stop |

## Acceptance Criteria

- [ ] `/website-analyzer <url>` accepts a single URL and runs without further prompting
- [ ] Output covers all six dimensions: UI/UX, category, style, performance, security, SEO
- [ ] Performance includes LCP, CLS, total page weight, request count
- [ ] Security results are labelled as surface-level check
- [ ] SEO includes overall score (0–100) plus per-dimension breakdown
- [ ] Output is structured JSON consumable by downstream skills
- [ ] Handles common failure modes with clear error output
