# Framework-Specific SEO Configuration

## Next.js

### Metadata API (App Router)
```tsx
// app/layout.tsx
export const metadata = {
  title: { default: 'Site Name', template: '%s | Site Name' },
  description: 'Site description',
  openGraph: {
    title: 'Site Name',
    description: 'Site description',
    url: 'https://example.com',
    siteName: 'Site Name',
    images: [{ url: '/og.jpg', width: 1200, height: 630 }],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Site Name',
    description: 'Site description',
    images: ['/og.jpg'],
  },
  robots: { index: true, follow: true },
  alternates: { canonical: 'https://example.com' },
};
```

### next-sitemap
```js
// next-sitemap.config.js
module.exports = {
  siteUrl: 'https://example.com',
  generateRobotsTxt: true,
  robotsTxtOptions: {
    additionalSitemaps: ['https://example.com/server-sitemap.xml'],
  },
};
```

### Key files
- `public/robots.txt` or generated via next-sitemap
- `app/sitemap.ts` for dynamic sitemap
- `app/robots.ts` for dynamic robots.txt
- `public/llms.txt` for AI bot accessibility

## Nuxt

### SEO Configuration
```ts
// nuxt.config.ts
export default defineNuxtConfig({
  app: {
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      title: 'Site Name',
      meta: [
        { name: 'description', content: 'Site description' },
        { property: 'og:title', content: 'Site Name' },
        { property: 'og:description', content: 'Site description' },
        { property: 'og:image', content: '/og.jpg' },
      ],
    },
  },
  modules: ['nuxt-simple-sitemap', '@nuxtjs/robots'],
  sitemap: { siteUrl: 'https://example.com' },
});
```

### Per-page SEO
```vue
<script setup>
useSeoMeta({
  title: 'Page Title',
  ogTitle: 'Page Title',
  description: 'Page description',
  ogDescription: 'Page description',
  ogImage: '/page-og.jpg',
})
</script>
```

## Astro

### Head component
```astro
---
// src/components/SEOHead.astro
const { title, description, image, canonical } = Astro.props;
---
<title>{title}</title>
<meta name="description" content={description} />
<link rel="canonical" href={canonical || Astro.url.href} />
<meta property="og:title" content={title} />
<meta property="og:description" content={description} />
<meta property="og:image" content={image} />
<meta property="og:url" content={canonical || Astro.url.href} />
<meta name="twitter:card" content="summary_large_image" />
```

### Sitemap
```js
// astro.config.mjs
import sitemap from '@astrojs/sitemap';
export default defineConfig({
  site: 'https://example.com',
  integrations: [sitemap()],
});
```

### Static files
Place `robots.txt`, `llms.txt` in `public/` directory.

## Hugo

### Config
```toml
# hugo.toml
baseURL = "https://example.com"
title = "Site Name"

[params]
  description = "Site description"
  images = ["/images/og-default.jpg"]

[outputs]
  home = ["HTML", "RSS", "sitemap"]
```

### Head template
```html
<!-- layouts/partials/head.html -->
<title>{{ .Title }} | {{ .Site.Title }}</title>
<meta name="description" content="{{ .Description | default .Site.Params.description }}">
<link rel="canonical" href="{{ .Permalink }}">
{{ template "_internal/opengraph.html" . }}
{{ template "_internal/twitter_cards.html" . }}
{{ template "_internal/schema.html" . }}
```

### Static files
Place `robots.txt`, `llms.txt`, `sitemap.xml` in `static/` directory.

## SvelteKit

### Per-page SEO
```svelte
<svelte:head>
  <title>{title}</title>
  <meta name="description" content={description} />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <link rel="canonical" href={url} />
</svelte:head>
```

### Static files
Place in `static/` directory.

## Vue (Vite)

### vue-meta or @unhead/vue
```ts
useHead({
  title: 'Page Title',
  meta: [
    { name: 'description', content: 'Description' },
    { property: 'og:title', content: 'Page Title' },
  ],
  link: [{ rel: 'canonical', href: 'https://example.com/page' }],
});
```

## Static HTML

All tags go directly in `<head>`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title | Site Name</title>
  <meta name="description" content="Page description">
  <link rel="canonical" href="https://example.com/page">
  <meta property="og:title" content="Page Title">
  <meta property="og:description" content="Page description">
  <meta property="og:image" content="https://example.com/og.jpg">
  <meta property="og:url" content="https://example.com/page">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Page Title">
  <meta name="twitter:description" content="Page description">
  <meta name="twitter:image" content="https://example.com/og.jpg">
  <script type="application/ld+json">
  { "@context": "https://schema.org", "@type": "WebPage", ... }
  </script>
</head>
```

Place `robots.txt`, `sitemap.xml`, `llms.txt` in root directory.

## Common Packages

| Framework | Sitemap | Robots | SEO Meta |
|---|---|---|---|
| Next.js | next-sitemap | next-sitemap | Metadata API |
| Nuxt | nuxt-simple-sitemap | @nuxtjs/robots | useSeoMeta() |
| Astro | @astrojs/sitemap | manual | manual / astro-seo |
| Gatsby | gatsby-plugin-sitemap | gatsby-plugin-robots-txt | react-helmet / Gatsby Head |
| Hugo | Built-in | Built-in template | Built-in templates |
| SvelteKit | Manual / svelte-sitemap | Manual | svelte:head |
