# AI/search AX checklist

AX here is AI/search accessibility and discoverability, not the OS accessibility API.
These checks improve inspectability; they do not guarantee rankings or model citations.
Read `native-app.md` for a native surface. Optional formats are opportunities, not failures.

## Robots / sitemap (`robots-sitemap`)

Inspect real robots.txt status/body, supported user-agent/path rules, sitemap references,
and representative sitemap entries (valid canonical, public, indexable URLs; truthful
lastmod when present). Inspect response X-Robots-Tag, HTML robots/noindex, canonical and
redirects where accessible. A robots disallow controls fetching, not guaranteed deindexing;
noindex must be crawlable to be read. Robots is not authentication/security. A sitemap is
a discovery hint and not mandatory on every site. Preserve deliberate private/noindex
areas and report inconsistent intent, not simply “allow all”.
[Google guidance](https://developers.google.com/search/docs/crawling-indexing/robots/intro).

## Structured data (`structured-data`)

Inspect JSON-LD/microdata, valid syntax, appropriate schema types, stable identifiers,
canonical URLs and agreement with visible/public content. Do not invent reviews, prices,
authors or product capabilities. Separate Schema.org validity from eligibility for a
specific engine's rich result. Use official validators when available and permission
allows public URLs; do not send private pages to external validation services.
[Schema.org](https://schema.org/) and [Google structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
Validation: parser/schema checks plus matching visible content; eligibility ≠ appearance.

## Markdown pages (`markdown-pages`)

Inspect provided/documented .md routes, content negotiation or Markdown exports if present;
do not probe every path or assume an HTML URL must have a .md twin. Check readable headings,
meaningful links, stable URLs, parity/freshness, canonical attribution and public-only
content. Preserve auth/noindex and avoid duplicating large stale content. Absence is an
optional opportunity unless product requirements explicitly mandate it. Validation: a
named public export is accurate, readable, link-resolvable and not leaking private data.

## llms.txt (`llms-txt`)

Fetch only where applicable/allowed. Verify format, short description, curated links,
public accuracy, URL validity and maintenance owner. [llms.txt](https://llmstxt.org/) is a
**proposal**, not a universally adopted standard or robots replacement. Presence is not
proof a provider reads it; absence is not a ranking defect. llms-full.txt is optional and
can introduce duplication/privacy risks. Validation: parse/read links and compare to public
canonical content; make no claim of provider adoption without specific current evidence.

## Crawler access (`crawler-access`)

Distinguish search, training and user-triggered fetchers using current provider docs, e.g.
[OpenAI bots](https://platform.openai.com/docs/bots) and [Google crawlers](https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers).
Document crawler-specific policy intention first. Check deployment headers, accessible
initial HTML, hydration-only content, CDN/WAF/auth restrictions, redirects and relevant
logs where supplied. A normal browser 200 does not prove real bot access; configured
allow-rules do not prove verified crawlers are reaching content. A spoofed user-agent test
cannot authenticate a bot and is not a bypass strategy. Don't broaden training permission
as a prerequisite for search visibility. Validation: owner-approved policy checks and
verified crawler logs/engine inspection, or label deployed access not-tested.

## Copy / share / open-in-AI actions (`ai-actions`)

Inspect discoverable copy/export, canonical share/deep links, native share sheets and
opt-in open-in-AI handoffs where task-relevant. Check keyboard/accessibility, copied
content correctness, source attribution, encoded URLs, feedback/error state, clipboard
permissions, popup blocking and useful fallback. Missing AI buttons are optional UX
opportunities, not universal requirements. Do not execute third-party AI handoffs with
private data. Avoid undocumented prompt URLs and brittle vendor links; verify supported
integration docs before recommending a concrete deep link. Do not add auto-send behavior
or tracking without informed consent. Validation: staged/local test of only public or
consented content with clear preview, minimal disclosure, valid links and fallback copy.
