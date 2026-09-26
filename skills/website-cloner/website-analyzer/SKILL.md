---
name: website-analyzer
description: "Analyze a website's UI/UX, category, style, performance, surface security, and SEO; emit structured JSON. Use for URL audits or website-cloner input. Don't use for penetration tests, full SEO audits, or App Store ASO."
license: MIT
effort: high
metadata:
  version: 1.5.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Website Analyzer

Analyzes any website URL across 6 dimensions and produces structured JSON output for downstream skills in the website-cloner suite.

## When to Use

Trigger when the user asks to:
- Analyze, audit, or scan a website
- Get a performance, SEO, security, or UI/UX assessment of a URL
- Understand a website's structure, style, or category

Do **not** use for full penetration testing, deep security audits, or App Store ASO.

## Prerequisites

1. Require a valid `http://` or `https://` URL and an output path or stdout destination.
2. Confirm page-fetch access is available; never bypass authentication, paywalls, or bot protections.
3. When an output path is supplied, validate that its directory exists and is writable; skip this check for stdout.
4. If any prerequisite fails, return a descriptive error with the failing input and corrective action.

## Repo Sync Before Edits (mandatory)

When an output path is supplied and it lives inside a git worktree, sync before writing the analysis to avoid clobbering remote work:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash → sync → pop. If `origin` is missing or a conflict occurs: **stop and ask the user.** Skip this section when writing to stdout or to a path outside any git repository.

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
    "lcp_estimate_seconds": 2.5,
    "cls_estimate": 0.05,
    "ttfb_estimate_seconds": 0.3,
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
    "status": "PASS | PARTIAL",
    "availability": "available | partial | unavailable",
    "reason": null,
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
| LCP (`lcp_estimate_seconds`) | Inferred from above-fold content size; seconds, with a 0.5-second minimum for bare HTML |
| CLS (`cls_estimate`) | Estimated from layout shift indicators (missing dimensions, late loaders); unitless |
| TTFB (`ttfb_estimate_seconds`) | Inferred from hosting signals; seconds; static → low, dynamic → moderate |

All metrics are estimates from static analysis. Note this in output.

## Step 4: Security Check (Surface-Level Only)

Check:
- HTTPS usage
- Mixed content (HTTP resources on HTTPS page)
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- Exposed metadata (dev tools, debug endpoints, sensitive data in comments)

Always label as surface-level.

## Step 5: SEO Scoring

Use the rubrics below to make evidence-backed integer sub-scores, or explicit
`null` when a dimension cannot be computed. Then pass exactly the five-key
`seo.dimension_scores` map to the local pure-stdlib
[`scripts/score_seo.py`](scripts/score_seo.py). It validates the schema,
renormalizes weights over known dimensions, and calculates `seo.score` with
Decimal `ROUND_HALF_UP`. Read [references/seo-scoring.md](references/seo-scoring.md)
for the input/output contract and safe CLI invocation. Do not calculate,
round, or override the aggregate score in prose.

| Dimension | Weight | Sub-score rubric (0–100) |
|-----------|--------|--------------------------|
| Meta tags (title + description) | 20% | Start at 0. +50 if `<title>` is present and 10–60 chars. +50 if `<meta name="description">` is present and 50–160 chars. Subtract 25 each for: title outside 10–60, description outside 50–160, duplicate title across siblings (when crawlable). Floor at 0. |
| Heading structure | 15% | 100 if exactly one `<h1>` and at least one `<h2>`. 70 if exactly one `<h1>` but no `<h2>`. 40 if zero or multiple `<h1>`s. Subtract 20 if any heading level is skipped (e.g. h2 → h4). Floor at 0. |
| Image alt text coverage | 15% | `round(100 × non_empty_alt_count / total_img_count)`. If `total_img_count == 0`, report 100 (no images = no alt-text debt). Decorative images using `alt=""` count as "non-empty intent" only when paired with `role="presentation"`; otherwise count as missing. |
| Structured data | 20% | 100 if at least one valid JSON-LD block is present and parses (any schema). 60 if only Open Graph or Twitter Card meta tags are present (no JSON-LD). 30 if only microdata or RDFa. 0 if none. |
| Crawlability (canonical, robots, sitemap) | 30% | Start at 0. +40 if a `<link rel="canonical">` resolves to an absolute URL. +30 if `robots.txt` is fetchable and not `Disallow: /`. +30 if a sitemap is referenced (via `robots.txt` `Sitemap:` directive, `<link rel="sitemap">`, or a fetchable `/sitemap.xml`). Cap at 100. |

When a sub-score cannot be computed (e.g. `robots.txt` unreachable), record
that dimension explicitly as `null` in `dimension_scores`; the helper excludes
it and redistributes its weight proportionally across remaining known
dimensions. Keep `seo.status: "PARTIAL"` and the helper's unavailable fields.
If all five dimensions are `null`, preserve `seo.score: null` and
`availability: "unavailable"`; never substitute `0` or `100`, and never rank
or compare that result as numeric.

## Step 6: UI/UX, Category, Style

- **Layout**: Infer from HTML structure (divs, sections, nav, main, footer)
- **Category**: `saas-landing` | `portfolio` | `e-commerce` | `blog` | `docs` | `dashboard` | `marketing-site` | `web-app` | `other`
- **Style**: Typography, color palette, spacing density, motion indicators, aesthetic vibe

## Edge Cases and Error Handling

| Failure | Behavior |
|---|---|
| Unreachable (4xx/5xx/timeout) | `{"error": "unreachable"}` — stop |
| JS-heavy SPA | Note limitation, proceed with crawlable content |
| Paywall / login | `{"error": "paywall"}` — stop |
| Redirect loop | `{"error": "redirect-loop"}` — stop |
| Empty page | `{"error": "empty"}` — stop |
| Invalid SEO score input | Stop before emitting the final analysis; surface the helper's `error[seo-input]` diagnostic and correct the five-key map. |

## Acceptance Criteria

Verify the expected output before reporting success:

- JSON parses and contains `url`, `timestamp`, `ui_ux`, `category`, `style`, `performance`, `security`, and `seo`.
- `seo.score` is the helper's integer from 0 through 100 when at least one dimension is known, and matches its weighted, null-adjusted calculation.
- All five `seo.dimension_scores` keys are present with integer `0..100` values or explicit `null`; all-null output preserves `seo.score: null`, `seo.status: "PARTIAL"`, and `availability: "unavailable"`.
- Performance estimates use `lcp_estimate_seconds`, unitless `cls_estimate`, `ttfb_estimate_seconds`, and `total_page_weight_kb`, plus an explicit static-analysis limitation.
- Every unavailable measurement is `null` or an error field, never an invented value.
- The output is written to the requested destination; assert the file exists and can be parsed when a path is supplied.

## Step Completion Report

Emit this after analysis:

```text
◆ Analyze Website
··································································
  Input fetched:        √ pass | × fail ([reason])
  Six dimensions:      √ pass | × partial ([missing])
  SEO calculation:     √ pass | × partial ([null dimensions/helper diagnostic])
  Output JSON:         √ pass ([path or stdout])
  Result:              PASS | PARTIAL | FAIL
```

Report `PASS` only when the JSON is valid and all six top-level dimensions are present; use `PARTIAL` for explicitly labeled crawlability gaps.

