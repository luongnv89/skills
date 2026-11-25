# AI Bot Accessibility Guide

## llms.txt

A Markdown file at `/llms.txt` that some AI tools read to understand a site. Proposed by Jeremy Howard (Answer.AI), adopted by Anthropic, Cloudflare, Stripe, and documentation platforms. It is optional: offer it for those AI tools, and create it only when the user chooses it.

### What llms.txt does not do

Google Search does not use llms.txt: "You don't need to create new machine readable files, AI text files, markup, or Markdown to appear in Google Search (including its generative AI capabilities), as Google Search itself doesn't use them." ([Google Search Central, *Optimizing your website for generative AI features on Google Search*](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide))

The same guide adds that creating one "will neither harm nor help your site's visibility or rankings in Google Search", and that chunking content or rewriting it just for AI systems is not needed. So llms.txt never counts toward crawl accessibility, the audit score or acceptance.

### Format

```markdown
# Site Name

> Brief description with key context.

## Documentation

- [Getting Started](https://example.com/docs/start.md): Quick start guide
- [API Reference](https://example.com/docs/api.md): Complete API docs

## Optional

- [Changelog](https://example.com/docs/changelog.md): Version history
```

### Rules
- H1 heading required (site/project name)
- Optional blockquote for summary
- H2 sections with link lists: `- [Title](URL): Description`
- `## Optional` section for secondary resources (can be skipped by LLMs)
- Serve as `text/plain` or `text/markdown`
- Place at site root: `https://example.com/llms.txt`

### llms-full.txt

Single Markdown file with all documentation content concatenated. Placed at `/llms-full.txt`. Useful for full-context ingestion by AI tools (Claude Code, Cursor, etc.).

## robots.txt AI Bot Directives

### Major AI Crawlers

**Training crawlers** (collect data for model training):
- `GPTBot` (OpenAI)
- `ClaudeBot` (Anthropic)
- `Google-Extended` (Google Gemini training -- does NOT affect Search indexing)
- `CCBot` (Common Crawl)
- `Bytespider` (ByteDance)
- `Meta-ExternalAgent` (Meta/Llama)
- `cohere-training-data-crawler` (Cohere)
- `DeepSeekBot` (DeepSeek)
- `Applebot-Extended` (Apple AI)

**Search/index bots** (build AI search indexes):
- `OAI-SearchBot` (OpenAI)
- `PerplexityBot` (Perplexity)
- `Claude-SearchBot` (Anthropic)
- `DuckAssistBot` (DuckDuckGo)
- `Amazonbot` (Amazon)

**On-demand fetchers** (real-time user requests):
- `ChatGPT-User` (OpenAI)
- `Claude-User` (Anthropic)
- `Perplexity-User` (Perplexity)
- `MistralAI-User` (Mistral)

### Which crawler controls which surface

Each token is independent: blocking one leaves the others as they are.

| robots.txt token | What a block affects (quoted from the operator's page) |
|---|---|
| `Googlebot` | Google Search: rules for it "affect Google Search (including Discover and all Google Search features)" ([Google crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)). AI Overviews and AI Mode show only pages that are "indexed and eligible to be shown in Google Search with a snippet" ([Google AI guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)). |
| `Google-Extended` | Training of Google's foundation models and grounding in Google products "aside from Search". It "doesn't impact a site's inclusion in Google Search nor is it used as a ranking signal"; grounding in AI Overviews and AI Mode is managed with the Search generative AI control in Search Console ([Google-Extended](https://developers.google.com/crawling/docs/google-extended)). |
| `GPTBot` | OpenAI model training: disallowing it "indicates a site's content should not be used in training generative AI foundation models" ([OpenAI crawlers](https://developers.openai.com/api/docs/bots)). |
| `OAI-SearchBot` | ChatGPT search: opted-out sites "will not be shown in ChatGPT search answers, though can still appear as navigational links" ([OpenAI crawlers](https://developers.openai.com/api/docs/bots)). |
| `ClaudeBot` | Anthropic model training: a block "signals that the site's future materials should be excluded from our AI model training datasets" ([Anthropic crawlers](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)). |
| `Claude-SearchBot` | Claude search: a block "may reduce your site's visibility and accuracy in user search results" ([Anthropic crawlers](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)). |
| `PerplexityBot` | Perplexity search results; it "is not used to crawl content for AI foundation models" ([Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)). |

Blocking Google-Extended does not remove a site from Google Search or AI Overviews. Blocking Googlebot stops Google crawling the site for Search, AI Overviews included.

### Option A: Allow AI Search, Block Training

```
# Block AI training crawlers
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: Bytespider
Disallow: /

User-agent: Meta-ExternalAgent
Disallow: /

# Allow AI search bots (appear in AI search results)
User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: DuckAssistBot
Allow: /

# Allow on-demand fetching (real-time user queries)
User-agent: ChatGPT-User
Allow: /

User-agent: Claude-User
Allow: /
```

### Option B: Allow Everything

```
# Allow all AI bots for maximum visibility
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-User
Allow: /
```

Neither option is the default. Show both with the table above and let the user choose, or write their own rules, before implementing.

## ai-plugin.json (Deprecated but Referenced)

OpenAI deprecated ChatGPT Plugins in April 2024 (replaced by Custom GPTs). Include only if user specifically requests it or the site has a public API.

Location: `/.well-known/ai-plugin.json`

```json
{
  "schema_version": "v1",
  "name_for_human": "Your Service",
  "name_for_model": "yourService",
  "description_for_human": "Short description (max 120 chars)",
  "description_for_model": "Detailed description for AI (max 8000 chars)",
  "auth": { "type": "none" },
  "api": {
    "type": "openapi",
    "url": "https://example.com/openapi.yaml"
  },
  "logo_url": "https://example.com/logo.png",
  "contact_email": "support@example.com",
  "legal_info_url": "https://example.com/legal"
}
```

## Structured Data for AI

### JSON-LD (Google's recommended format)

Every page should have at minimum:

**Organization (site-wide, on homepage):**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Your Company",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": ["https://github.com/your-org", "https://www.crunchbase.com/organization/your-org", "https://www.linkedin.com/company/your-org"]
}
</script>
```

List in `sameAs` only profiles the founder or company really owns and keeps up (for example GitHub, Crunchbase, LinkedIn). Never create profiles or directory listings only to get a link: Google's spam policies define link spam as "creating links to or from a site primarily for the purpose of manipulating search rankings" ([Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies)).

**Article/BlogPosting (content pages):**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "author": { "@type": "Person", "name": "Author Name" },
  "publisher": {
    "@type": "Organization",
    "name": "Publisher",
    "logo": { "@type": "ImageObject", "url": "https://example.com/logo.png" }
  },
  "datePublished": "2026-01-15",
  "dateModified": "2026-02-10",
  "image": "https://example.com/hero.jpg",
  "description": "Article description"
}
</script>
```

**Product (e-commerce):**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "image": "https://example.com/product.jpg",
  "description": "Product description",
  "brand": { "@type": "Brand", "name": "BrandName" },
  "offers": {
    "@type": "Offer",
    "price": "49.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
}
</script>
```

### Priority Schema Types
1. Organization (every site)
2. WebSite + SearchAction (every site)
3. Article/BlogPosting (content sites)
4. Product + Offer (e-commerce)
5. LocalBusiness (local businesses)
6. BreadcrumbList (all sites with navigation)
7. FAQPage (FAQ pages -- limited to gov/health sites for rich results)
8. Event, Recipe, Video (niche content)

### OpenGraph Tags (Required)

```html
<meta property="og:title" content="Page Title">
<meta property="og:type" content="website">
<meta property="og:image" content="https://example.com/share.jpg">
<meta property="og:url" content="https://example.com/page">
<meta property="og:description" content="Page description">
<meta property="og:site_name" content="Site Name">
```

Image: 1200x630px recommended.

### Twitter Cards

```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Page Title">
<meta name="twitter:description" content="Description">
<meta name="twitter:image" content="https://example.com/twitter.jpg">
<meta name="twitter:image:alt" content="Image description">
```

## Emerging Standards (2025-2026)

- **IETF AI Preferences (aipref):** Proposed `Content-Usage` field in robots.txt with labels: `search`, `train-ai`, `train-genai`, `bots`. Still in draft.
- **Really Simple Licensing (RSL 1.0):** Machine-readable licensing for AI content use. Finalized spec but no major AI company adoption.
- **`noai` meta tag:** `<meta name="robots" content="noai">` -- DeviantArt proposal, not standardized, widely ignored.
