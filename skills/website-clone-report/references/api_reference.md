# Analyzer JSON Schema and Translation Guide

This skill consumes the JSON output produced by `website-analyzer` (Phase 1 of the website-cloner suite). Use this reference to map each analyzer field to a plain-language report section.

## Input Shape

The skill expects JSON in this shape (see `skills/website-analyzer/SKILL.md` for the canonical definition):

```json
{
  "url": "https://example.com",
  "timestamp": "2026-05-07T12:00:00Z",
  "ui_ux": {
    "layout": "single-column | two-column | grid | ...",
    "visual_hierarchy": "what draws attention first",
    "components": ["nav", "hero", "cta", "footer"],
    "responsive": "desktop-first | mobile-first | adaptive | unknown",
    "friction_points": ["slow nav", "missing CTA"]
  },
  "category": "saas-landing | portfolio | e-commerce | blog | docs | dashboard",
  "category_confidence": 0.9,
  "style": {
    "typography": "brief description",
    "palette": ["#hex"],
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
    "security_headers": ["strict-transport-security"],
    "exposed_metadata": [],
    "note": "Surface-level check only. Not a full security audit."
  },
  "seo": {
    "score": 72,
    "title_tag": "present | missing | duplicate",
    "meta_description": "present | missing | too-short",
    "heading_structure": "h1:N h2:N",
    "alt_text_coverage": 0.85,
    "structured_data": "present | missing",
    "canonical_url": "present | missing",
    "robots_sitemap": "robots=ok | sitemap=found",
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

Error variant (skill should report and stop, not produce a report):

```json
{"url": "<url>", "error": "unreachable", "detail": "<error>"}
```

## Field-to-Section Mapping

| Analyzer field | Report section | Translation rule |
|---|---|---|
| `ui_ux.layout` | How It Looks and Works | Spell out the layout name — "single-column" → "a single column down the page". |
| `ui_ux.visual_hierarchy` | How It Looks and Works | Restate as "what catches the eye first". Avoid the term "visual hierarchy". |
| `ui_ux.friction_points` | How It Looks and Works | Convert each to a concrete observation: "slow nav" → "the navigation is slow to respond". |
| `ui_ux.responsive` | How It Looks and Works | "mobile-first" → "designed for phones first; works well on small screens". |
| `category` + `category_confidence` | What Kind of Site This Is | Use confidence to soften: < 0.6 → "appears to be"; ≥ 0.9 → state plainly. |
| `style.typography` | Design and Style | Replace font-family jargon with feel: "modern sans-serif fonts that feel clean". |
| `style.palette` | Design and Style | Translate hex to color families: "cool blues and grays with orange accents". |
| `style.spacing` | Design and Style | "compact" → "densely packed"; "spacious" → "lots of breathing room". |
| `style.motion` | Design and Style | "heavy" → "lots of animation"; "minimal" → "very little movement". |
| `performance.lcp_estimate` | Performance | "How fast content appears". Benchmarks: < 2.5s good, 2.5–4s fair, > 4s slow. |
| `performance.cls_estimate` | Performance | "How stable the page feels while loading". < 0.1 stable, ≥ 0.25 jumpy. |
| `performance.total_page_weight_kb` | Performance | "How much data the page uses". Compare to images: "≈ N average photos worth". |
| `performance.request_count` | Performance | "Number of pieces the page needs to load". |
| `security.https` / `mixed_content` | Security Overview | HTTPS + no mixed content → "encrypted from end to end". |
| `security.security_headers` | Security Overview | Translate to "the site sends a few security signals to browsers" — never list header names. |
| `security.note` | Security Overview | Always include the "not a full security audit" caveat. |
| `seo.score` | Search Engine Visibility | Bucket: ≥ 90 excellent, 70–89 good, 50–69 fair, < 50 poor. |
| `seo.dimension_scores.*` | Search Engine Visibility | Translate each: low `image_alt_text` → "Images are missing alternative text, which helps search and accessibility". |
| `seo.title_tag` / `meta_description` | Search Engine Visibility | "missing" → "no title/description for search engines to read". |
| `seo.heading_structure` | Search Engine Visibility | If h1 ≠ 1 → "the heading structure could be improved". |

## Null Handling

Any analyzer field may be `null` when the metric couldn't be computed. Translation rule: omit the corresponding line from the report rather than writing "unknown" or "N/A". Note in the *Summary and Next Steps* section that some metrics were unavailable, if the omission affects the conclusions.

## Output Path

The orchestrator (`website-cloner`) invokes this skill with `--output "$PROJECT_DIR/report.md"`. Honor that path. If invoked standalone without `--output`, default to `report.md` in the current working directory and print the absolute path on save.

## Cross-References

- `skills/website-analyzer/SKILL.md` — upstream producer; canonical schema definition.
- `skills/website-cloner/SKILL.md` — orchestrator; defines `$PROJECT_DIR` and the approval-gate contract.
- `skills/website-improvement-prd/SKILL.md` — downstream consumer of the approved report.
