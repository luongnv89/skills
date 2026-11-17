# Technical SEO Checklist

## Core Web Vitals (2025-2026)

| Metric | Measures | Good | Needs Work | Poor |
|---|---|---|---|---|
| LCP (Largest Contentful Paint) | Loading speed | <= 2.5s | 2.5-4.0s | > 4.0s |
| INP (Interaction to Next Paint) | Responsiveness | <= 200ms | 200-500ms | > 500ms |
| CLS (Cumulative Layout Shift) | Visual stability | <= 0.1 | 0.1-0.25 | > 0.25 |

INP replaced FID in March 2024. Measured at 75th percentile of all page loads.

## Required Meta Tags

```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>50-60 chars, primary keyword near beginning</title>
<meta name="description" content="140-160 chars, unique per page, focus on user intent">
<link rel="canonical" href="https://example.com/current-page">
```

- Every page needs a unique title (50-60 chars)
- Every page needs a unique meta description (140-160 chars)
- Viewport tag required for mobile-first indexing
- Self-referencing canonical on every page
- `<html lang="en">` attribute required

## Sitemap Requirements

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page</loc>
    <lastmod>2026-02-16</lastmod>
  </url>
</urlset>
```

- Max 50MB uncompressed or 50,000 URLs per file
- Use sitemap index for larger sites
- `<lastmod>` must be accurate (Google verifies)
- `<priority>` and `<changefreq>` are ignored by Google
- Reference in robots.txt: `Sitemap: https://example.com/sitemap.xml`

## Heading Hierarchy

- Exactly one H1 per page
- Strict order: H1 > H2 > H3 (never skip levels)
- H1 max ~80 chars, contains primary keyword naturally
- H1 must be unique across the site

## Image Optimization

```html
<!-- Above-fold / LCP image -->
<img src="hero.webp" alt="Descriptive text" width="800" height="600"
     loading="eager" fetchpriority="high">

<!-- Below-fold image -->
<img src="photo.webp" alt="Descriptive text" width="400" height="300"
     loading="lazy">

<!-- Modern format with fallback -->
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="..." width="800" height="600">
</picture>
```

- Every `<img>` must have `alt` attribute (empty `alt=""` for decorative)
- Alt text: 80-140 chars, no "image of" prefix
- Always include `width` and `height` to prevent CLS
- Use `loading="lazy"` for below-fold, `loading="eager"` for above-fold
- Use `fetchpriority="high"` on LCP image

## Page Speed HTML Patterns

### Resource Hints
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preload" href="/critical.css" as="style">
<link rel="preload" href="/hero.webp" as="image">
<link rel="dns-prefetch" href="https://analytics.example.com">
```

### Script Loading
```html
<!-- Non-critical: defer (executes after parsing, in order) -->
<script src="app.js" defer></script>

<!-- Independent scripts: async -->
<script src="analytics.js" async></script>

<!-- Never: render-blocking scripts in <head> -->
```

### CSS Loading
```html
<!-- Critical CSS inlined -->
<style>/* above-fold CSS */</style>

<!-- Non-critical CSS async loaded -->
<link rel="preload" href="styles.css" as="style"
      onload="this.onload=null;this.rel='stylesheet'">
```

## Internal Linking

- Every page reachable within 3 clicks from homepage
- Descriptive anchor text (not "click here")
- Links must be crawlable `<a href>` (not JS-only)
- No `nofollow` on internal links
- Breadcrumb navigation recommended

## Mobile-First Indexing (100% since July 2024)

- Content parity between mobile and desktop
- Viewport meta tag required
- Minimum tap target: 48x48 pixels
- Minimum font: 16px body text
- Same structured data on mobile
- Same internal links on mobile
- Do not lazy-load primary/above-fold content

## HTTPS

- HTTPS is a ranking signal
- No mixed content (HTTP resources on HTTPS pages)
- All HTTP URLs must redirect to HTTPS
