# ASO Best Practices Reference (2025-2026)

Comprehensive reference for App Store Optimization techniques across Apple App Store and Google Play Store. This document covers keyword strategy, metadata optimization, conversion optimization, localization, pricing, and ongoing measurement.

Sections marked *(practitioner)* draw on Darius Pop's X Article "The Ultimate Guide to ASO" (x.com/tyd3n_/status/2117694233301725635, November 3, 2026). They are one indie developer's advice, not Apple or Google rules: present them as starting points, never as guarantees.

## Table of Contents

1. [Keyword Strategy](#keyword-strategy)
2. [Metadata Optimization — Apple App Store](#metadata-optimization--apple-app-store)
3. [Metadata Optimization — Google Play Store](#metadata-optimization--google-play-store)
4. [Conversion Rate Optimization](#conversion-rate-optimization)
5. [Visual Asset Optimization](#visual-asset-optimization)
6. [Localization Best Practices](#localization-best-practices)
7. [Ratings & Reviews Strategy](#ratings--reviews-strategy)
8. [Algorithm & Ranking Factors](#algorithm--ranking-factors)
9. [A/B Testing](#ab-testing)
10. [Localized Pricing](#localized-pricing-practitioner)
11. [Measurement and Iteration](#measurement-and-iteration-practitioner)
12. [Store Policy Compliance](#store-policy-compliance)
13. [Common Mistakes](#common-mistakes)
14. [Character Limits Quick Reference](#character-limits-quick-reference)

---

## Keyword Strategy

### Research Approach

1. **Start with your app's core features** — list 10-15 words that describe what your app does
2. **Expand with synonyms and related terms** — users search in diverse ways
3. **Include competitor brand-adjacent terms** — keywords their users search for
4. **Mix keyword tiers:**
   - **Head terms** (1-2 words, high volume, high competition): e.g., "fitness", "meditation"
   - **Mid-tail** (2-3 words, moderate volume): e.g., "home workout", "sleep sounds"
   - **Long-tail** (3+ words, lower volume, high intent): e.g., "7 minute workout timer", "rain sounds for sleep"

### Keyword Prioritization Framework

Score each keyword on three dimensions:
- **Relevance** (1-5): How well does this keyword describe your app?
- **Volume** (1-5): How many people search for this term? (Use ASO tools for data)
- **Difficulty** (1-5): How many strong apps compete for this term?

**Priority = Relevance × Volume / Difficulty**

Target keywords where you score high relevance and volume with manageable difficulty. Avoid high-difficulty keywords unless your app has strong signals (ratings, downloads) to compete.

**Stage-aware targeting *(practitioner)*.** Work in this order: relevance (real search intent for what the app does) → popularity (someone searches it) → difficulty (who already ranks) → opportunity (demand the app can realistically win). A new or small app targets keywords it can win now. It moves to competitive head terms as its ratings and downloads grow. Ranking #1 for a term nobody searches is worth nothing, and a top-volume term owned by apps with millions of downloads is out of reach from day one. Record in the plan why each primary keyword is winnable at the app's current size. Treat a keyword as **winnable** when the median rating count of the current top-10 results is within about 10× of the app's own, or when an ASO tool's difficulty score is in its low or medium band; otherwise mark it watch-only.

### Long-Tail Keyword Strategy (2025-2026 Focus)

Long-tail keywords have become more valuable because:
- Less competition means faster ranking improvements
- Higher intent means better conversion rates
- Mid-2025 App Store algorithm update now shows results for multiple user intents per search query
- Google Play's semantic understanding matches long-tail queries to relevant apps

**How to find long-tail keywords:**
- App store autocomplete suggestions
- Competitor review mining (what words do users use?)
- Related searches shown in store results
- Question-based queries ("how to" + your category)

### Cross-Field Combination Strategy (iOS)

Apple's search combines words across title, subtitle, and keywords. This means:
- "workout" in title + "home" in keywords = matches "home workout" search
- "meditation" in subtitle + "guided" in keywords = matches "guided meditation" search

**Maximize combinations by:**
- Placing different high-value words in each indexed field
- Avoiding word repetition across fields (wastes character budget)
- Testing which combinations produce the best ranking results
- Keeping an exact phrase together only when that phrase is itself the target query. Combination does not make every pairing rank.

---

## Metadata Optimization — Apple App Store

### App Name (30 chars)
- Include your primary keyword alongside the brand name
- The name carries the strongest indexation weight
- Keep it readable — don't sacrifice clarity for keyword cramming

**Brand position *(practitioner)*.** Choose the order by whether people already search for the brand:

| Brand status | Order | Example |
|---|---|---|
| Unknown: new app, or no evidence users search the brand name | Keyword first | `Habit Tracker: MyApp` |
| Known: users already search the brand (as they do for Duolingo) | Brand first | `MyApp: Habit Tracker` |

Treat the brand as **known** only with evidence: the brand name appears in the store's search autocomplete, App Analytics shows brand-name searches, or the user says people search for it. Otherwise it is unknown. Keyword-first does not guarantee a better rank. It tells someone scrolling search results what the app does before they know the name. When the brand status is unclear, default to keyword-first and state the assumption in the plan.

### Subtitle (30 chars)
- Include your secondary keyword and a benefit
- Complements the title — don't repeat the same words
- Aim for 65%+ character utilization (20+ chars)
- Think of it as a search-optimized tagline

### Keywords Field (100 chars)
- Comma-separated, NO spaces after commas
- Never duplicate words from title or subtitle
- Prefer single words over phrases (enables more cross-field combinations)
- Avoid plurals if singular exists (Apple handles stemming)
- Don't include your app name (already indexed)
- Aim for 90%+ character utilization (90+ chars)
- Prioritize by keyword score (relevance × volume / difficulty)

### Description (4,000 chars)
- NOT indexed for search on Apple, but critical for conversion. Don't stuff it with keywords: it is written for people deciding whether to download. Google Play differs (see below)
- Description keyword coverage matters for conversion rate — users who see their search terms reflected are more likely to download
- Structure: Hook → Features → Social Proof → Call to Action
- First 3 lines visible before "Read More" — make them count
- Use line breaks and formatting for scannability

### Promotional Text (170 chars)
- NOT indexed for search
- Updated without app review — use for seasonal messaging, sales, events
- Appears above the description
- Great for time-sensitive promotions

### What's New (4,000 chars)
- Shown to existing users and on the app page
- Keep it engaging and specific about improvements
- Echoing keywords naturally can reinforce relevance perception

---

## Metadata Optimization — Google Play Store

### App Title (30 chars)
- Most heavily weighted field for ranking
- Include primary keyword naturally
- Google's algorithm understands semantic relationships

### Short Description (80 chars)
- Visible on the store page before expanding
- Include secondary keyword and value proposition
- Indexed by Google — every word matters

### Full Description (4,000 chars)
- Fully indexed by Google — unlike Apple's description
- Natural keyword integration throughout (3-5 mentions of key terms)
- Cover related concepts, use cases, and synonyms
- Google's NLP detects keyword stuffing — write for humans first
- Structure with clear sections for features, benefits, and use cases
- First 1-3 lines are the "above the fold" — front-load value

### Developer Name
- Indexed by Google Play — if your developer name contains relevant keywords, it helps

### What's New / Changelogs
- Keep changelogs user-friendly and specific
- Mention new features that align with target keywords

---

## Conversion Rate Optimization

### The Conversion Funnel
```
Search Results → App Page View → Install → First Launch → Retention
```

Each stage matters for ASO because stores reward apps that convert well and retain users.

### First Impression Elements (in order of impact)
1. **App Icon** — The single most viewed element; must communicate purpose at 60x60px
2. **App Name** — Clarity + keyword = discoverability + understanding
3. **Rating & Review Count** — Social proof drives trust (90% of featured apps are 4.0+)
4. **First Screenshot** — Often visible in search results; must hook immediately
5. **Subtitle / Short Description** — Value prop in a few words

### Conversion Rate Benchmarks
- Average App Store CVR: 25-35% (varies by category)
- Average Google Play CVR: 20-30%
- Apps that improved from 3.6 to 4.2 rating saw ~60% higher conversion
- Custom Product Pages (iOS) boost CVR by avg. 5.9%, up to 8.6% for generic campaigns

---

## Visual Asset Optimization

### App Icon
- Must be recognizable at 16x16px and look good at 1024x1024px
- Use bold, simple shapes — avoid photographic detail or text
- Color contrast should stand out against both light and dark backgrounds
- Research category conventions (e.g., game icons tend to be more detailed)

### Screenshots
- **Order matters:** Lead with the single most compelling feature
- **First 2-3 screenshots:** Visible in search results — they must tell the story
- **Captions:** State a benefit first and use keywords where they read naturally. ASO practitioners report that App Store caption text has been indexed by text recognition since June 2025; Apple has not confirmed it
- **Show real app UI** — not just marketing graphics
- **Highlight value propositions** — each screenshot should answer "why should I download?"
- **Optimal count:** 8-10 screenshots covering core features, edge cases, and social proof

**Screenshot captions *(practitioner)*:**
- **Benefits, not feature labels.** "See How Much Money You've Saved" beats "Advanced Analytics Dashboard": it gives the viewer a reason to care.
- **Legible on a phone.** Large type and strong contrast. Light gray text on white fails.
- **One message per screenshot.** The first screenshot only has to earn the next look, not explain everything.
- **The first three carry the search result.** Depending on the layout, search results show up to three screenshots, so those three must tell the story on their own.

### Preview Video
- First 3 seconds are auto-played in search results — lead with the best moment
- Show the app in action, not a cinematic trailer
- Keep under 30 seconds for maximum engagement
- Include captions/text for silent auto-play

---

## Localization Best Practices

### Market Prioritization
Rank markets by: (1) market size for your category, (2) competition level, (3) localization effort required.

### Localization vs. Translation
- **Translation:** Converting text to another language (minimum viable)
- **Localization:** Adapting content to cultural context, local search behavior, and market norms (recommended)
- **Transcreation:** Recreating the message entirely for the local market (premium, for top markets)

### Keyword Localization Rules
- Never just translate your English keywords 1:1 — research what local users actually search for
- Keyword popularity varies dramatically across markets (a keyword with 70 popularity in the US may have 5 in France)
- Local competitors differ — run competitor analysis per market
- Consider character encoding: some languages need more characters for the same meaning

**Market keyword research *(practitioner)*:**
1. Research the terms people actually use in that market. The literal translation of "budget tracker" may not be what people in Germany, Italy or France search for. Users in a non-English market sometimes search an English keyword, which can be an opening.
2. Compare their popularity and difficulty, and choose the ones that fit the app.
3. Adapt the title, subtitle and keywords per locale, and localize the screenshots too.
4. Treat AI-brainstormed local keywords as hypotheses. Mark them unvalidated until popularity and difficulty data, from an ASO tool or the store's autocomplete, back them up.
5. Check which localizations each target storefront indexes, from Apple's current App Store Connect Help list of localizations per storefront; if you can't check it, mark the mapping unverified. Apple indexes localizations per storefront, not one independent keyword field per country. Plan the keyword budget per localization, not per country.
6. Confirm the app is available in each target storefront before planning for it.

### Key Markets by App Store Revenue (2025-2026)
1. United States (en-US)
2. China (zh-Hans)
3. Japan (ja)
4. United Kingdom (en-GB)
5. South Korea (ko)
6. Germany (de-DE)
7. France (fr-FR)
8. Brazil (pt-BR)
9. Canada (en-CA, fr-CA)
10. Australia (en-AU)

### Non-Latin Script Considerations
- **Arabic:** ال-prefix normalization, right-to-left layout, hamza variants in search
- **Chinese:** No word-separating spaces; tokenize by `、` or `，`
- **Japanese:** Mix of kanji, hiragana, katakana affects search matching
- **Korean:** Hangul decomposition may affect search indexing
- **Cyrillic:** Include Latin transliterations for users who search in Latin script

---

## Ratings & Reviews Strategy

### Why Ratings Matter for ASO
- Apps rated 4.0+ are 3x more likely to be featured
- Rating directly impacts conversion rate
- Review text is indexed by Google Play (not Apple)

### In-App Review Prompt Strategy
- **When to prompt:** After a moment of value, such as a completed task, a reached milestone or an achievement
- **When NOT to prompt:** On first launch, after errors or crashes, or during onboarding
- **Never reward or incentivize a rating,** and never manipulate reviews. Both stores' policies forbid it. Trust comes from genuine ratings: users choose a 4.8-star app with hundreds of reviews over a 3.2-star app with almost none *(practitioner)*
- **Frequency:** Max once per 30 days; respect "don't ask again"
- **Use native API:** `AppStore.requestReview(in:)` / SwiftUI `requestReview` (iOS; older code uses `SKStoreReviewController`) / `ReviewManager` (Android). iOS shows the system prompt at most 3 times per 365 days, whatever the app requests

### Review Response Strategy
- Respond to negative reviews within 24 hours
- Address the issue specifically, not with templates
- Updated reviews (after fixes) improve aggregate rating
- Thank positive reviewers — it encourages more reviews

---

## Algorithm & Ranking Factors

### Apple App Store (2025-2026)
1. **Keyword relevance** — metadata match to search query
2. **Download velocity** — recent install rate relative to category
3. **Conversion rate** — impression-to-install ratio
4. **Rating & review quality** — aggregate score and recent trends
5. **Update frequency** — regularly updated apps rank better
6. **Engagement & retention** — post-install usage signals

**Mid-2025 Algorithm Change:** Search results now reflect multiple user intents for a single query. The first 10-15 results may include apps targeting different interpretations of the search term. This means niche apps can rank alongside broader competitors.

### Google Play Store (2025-2026)
1. **Keyword relevance** — all text fields indexed, semantic matching
2. **Install velocity** — first 48 hours post-update are critical
3. **App quality signals** — crash rate (ANR), stability, performance
4. **User engagement** — retention, session length, uninstall rate
5. **Rating & review volume** — both score and recency matter
6. **Update frequency** — Google favors actively maintained apps
7. **Backlinks and web presence** — deep linking and SEO overlap

**2026 Trend:** Google is moving toward theme-based keyword understanding and video-rich listings. AI-driven discovery blurs the line between ASO and SEO.

---

## A/B Testing

### Apple App Store
- **Custom Product Pages (CPPs):** Up to 35 custom pages with unique screenshots, previews, and promotional text
- **Product Page Optimization (PPO):** A/B test default page elements (icon, screenshots, preview)
- CPPs average +5.9% CVR improvement; generic campaigns see +8.6%

### Google Play Store
- **Store Listing Experiments:** Test up to 5 variants of any listing element
- Test icon, screenshots, descriptions, short description
- Run for minimum 7 days with statistical significance before deciding

### What to Test (Priority Order)
1. Screenshots (ordering and design)
2. App icon
3. Short description / subtitle
4. Description first paragraph
5. Preview video vs. no video

---

## Localized Pricing *(practitioner)*

Pricing is a conversion lever, not a metadata field. The skill **recommends** a pricing test in the plan and never changes prices: the developer sets them in App Store Connect or the Play Console.

Store currency conversion and tax adjustments are not purchasing-power pricing. A user in a lower-income market who would pay half the base price is worth more than one who pays nothing. Starting points to test, not rules:

| Market tier | Starting price |
|---|---|
| Tier 1 | 100% of the base price |
| Tier 2 | 55–70% of the base price |
| Tier 3 | 30–40% of the base price |

- Assign tiers from research (purchasing power, local competitors' prices, subscription behaviour), never at random.
- Check per-user costs first. When variable costs such as AI inference or infrastructure make a lower tier unprofitable, recommend keeping the base price there and say why. When the costs are unknown, ask the user; without an answer, mark the section "unvalidated: confirm costs before applying".
- On the App Store, lowering a subscription's price in a storefront also applies to existing subscribers there; include that revenue effect, and tell the user to confirm it in Apple's current pricing documentation.
- Only include this section when the app sells something (a subscription, an in-app purchase or a paid download) and the user names target markets with different purchasing power, or asks about pricing.

---

## Measurement and Iteration *(practitioner)*

ASO compounds over weeks. Nobody wakes up to a million downloads the day after a title change.

- **Baseline before changes.** Record the current rank for each target keyword in Phase 1 (`unranked` or `unknown` when there is no data). When every baseline is `unknown`, the Final Report's Decision asks the user to record ranks in each target storefront before uploading the new metadata.
- **Track the trend.** Re-check the same keywords on a fixed cadence (for example weekly). A move from #47 to #28 to #16 is a signal. It doesn't prove the metadata caused it: seasonality, updates and competitors also move ranks.
- **Measure outcomes, not just ranks.** Track impressions → product page views → downloads → paid conversions. Better ranks with flat downloads mean the listing is not converting.
- **One lever per cycle**, so a change can be attributed. A cycle is one store submission: cycle 1 ships the indexed metadata set (title, subtitle, keywords, per locale); later cycles change one lever each (screenshots, then localizations, then pricing). On iOS the name, subtitle and keywords change only with a new app version submission; promotional text changes without one.
- **Measurement window:** at least 6 weeks per cycle. A re-run inside the window reviews the data and keeps the metadata unless the user asks for a change.
- **When ranks stall:** the keywords may be too competitive, the search intent may be wrong, or there may be better, unexplored terms. Revisit the keyword tables before rewriting copy.
- **ASO cannot save a product nobody wants.** When Phase 1 finds weak product signals (a rating below 4.0, or recent reviews repeatedly reporting a broken core function), say so in the Analysis Report instead of promising ASO gains.

---

## Store Policy Compliance

Both Apple and Google enforce strict metadata policies. Violating these policies can result in app rejection, removal from the store, or developer account termination. **Always validate metadata against these rules before submission.**

### Apple App Store — Prohibited Metadata (Guidelines 2.3.7, 2.3.8, 5.2.1)

#### Banned Words and Phrases in Title, Subtitle, and Keywords
- **"free"** — pricing terms are not allowed in visible metadata
- **"best"**, **"#1"**, **"top-rated"**, **"must-have"** — unverifiable superlative claims
- **"#1 in the world"**, **"top app"** — ranking claims cannot be verified
- **"limited time"**, **"sale"**, **"discount"** — promotional/pricing language
- **"For Kids"**, **"For Children"** — reserved exclusively for the Kids Category
- **"Editor's Choice"** — reserved; only Apple applies this badge automatically

#### Trademark and Competitor Restrictions
- **Competitor brand names** — cannot appear in title, subtitle, keywords, or description (e.g., using "WhatsApp" in a messaging app's keywords)
- **Trademarked terms** you don't own or license — Apple explicitly prohibits this under guideline 2.3.7
- **Celebrity names** — unless you have explicit authorization
- **Apple trademarks** — cannot suggest Apple endorsement or source relationship (guideline 5.2.4)
- **Consequences:** Apple may silently de-index offending keywords, reject the update, remove the app, or terminate the developer account. Trademark owners can file disputes via Apple's App Store dispute form

#### Content Restrictions
- **Other platform names** — "Android", "Google Play", "Play Store" prohibited in iOS metadata (guideline 2.3.10)
- **Emojis and special characters** — not allowed in app name, subtitle, or keywords
- **ALL CAPS** — not permitted unless it's the actual brand name
- **Unverifiable claims** — "fastest", "most popular", "award-winning" without evidence
- **Misleading descriptions** — describing features the app doesn't have
- **Placeholder/generic text** — unfinished or default metadata
- **Repetition** — repeating the app name in subtitle or keywords wastes budget and may be flagged

#### Metadata Accuracy Requirements (Guideline 2.3)
- Screenshots must show the app in actual use — no title art, splash screens, or login pages only
- Preview videos must use actual app screen captures
- Description must accurately reflect app functionality
- In-app purchases and subscriptions must be clearly disclosed
- Age rating must be honest and accurate

### Google Play Store — Prohibited Metadata

#### Banned Words and Phrases in Title, Short Description, Developer Name, and Icon
- **"top"**, **"best"**, **"#1"**, **"number one"** — store performance claims
- **"free"**, **"no ads"**, **"ad free"** — pricing/promotional terms
- **"new"**, **"hot"**, **"first"**, **"bonus"** — promotional language
- **"discount"**, **"sale"**, **"million downloads"** — promotional claims
- **"App of the Year"**, **"Best Google Play App of 20XX"**, **"Popular"** — ranking claims
- **"download now"**, **"install now"**, **"play now"**, **"try now"**, **"update now"** — call-to-action phrases

#### Trademark and Competitor Restrictions
- **Competitor brand names** — cannot be used in title, short description, or full description to mislead users
- **Trademarked terms** — trademark owners can file complaints, leading to enforcement
- **Misleading developer names** — developer name cannot impersonate another entity
- **Consequences:** Google may remove the app listing, suspend the developer account, or restrict future submissions. Trademark complaints trigger review and potential enforcement

#### Formatting and Content Restrictions
- **Emojis and emoticons** — prohibited in title, icon, and developer name
- **Repeated special characters** — not allowed
- **ALL CAPS** — prohibited unless part of the official brand name
- **Unattributed user testimonials** — cannot include fake or unattributed reviews in metadata
- **Graphic elements suggesting rankings** — no trophy emojis, medal icons, or badges implying store ranking
- **Keyword stuffing** — Google's algorithm detects and penalizes repetitive or unrelated keywords; this includes excessive repetition in the full description
- **Misleading information** — descriptions of features the app doesn't provide

#### Description-Specific Rules
- Avoid excessive length, irrelevant detail, or improper formatting
- Maintain natural readability — Google's NLP detects unnatural keyword cramming
- Do not list keywords as comma-separated blocks in the description
- Do not repeat keywords more than 5 times across all fields

### Both Stores — Universal Rules

| Rule | Apple | Google | Consequence |
|------|-------|--------|-------------|
| No competitor trademarks | Yes (2.3.7, 5.2.1) | Yes | Rejection/removal |
| No pricing terms ("free") | Yes | Yes | Rejection |
| No ranking claims ("#1", "best") | Yes | Yes | Rejection |
| No platform references | Yes (2.3.10) | Yes | Rejection |
| No keyword stuffing | Yes | Yes (algorithmic penalty) | Rejection/demotion |
| No misleading screenshots | Yes (2.3.3) | Yes | Rejection |
| No emojis in title | Yes | Yes | Rejection |
| No ALL CAPS (unless brand) | Yes | Yes | Rejection |
| No unverifiable claims | Yes | Yes | Rejection |
| Accurate feature descriptions | Yes (2.3.1) | Yes | Rejection |
| Disclose IAP/subscriptions | Yes (2.3.2) | Yes | Rejection |

---

## Common Mistakes

1. **Keyword stuffing** — Cramming keywords unnaturally hurts readability and can trigger penalties (Google Play) or rejection (both stores)
2. **Using competitor trademarks** — Including competitor brand names in metadata violates both Apple (2.3.7, 5.2.1) and Google Play policies and can lead to app removal or legal action
3. **Prohibited words in title** — Using "free", "best", "#1", "top" in titles causes immediate rejection on both stores
4. **Duplicating words across indexed fields (iOS)** — Wastes character budget; Apple indexes title + subtitle + keywords together
5. **Translating instead of localizing** — Direct translation misses local search behavior
6. **Ignoring the "above the fold"** — Users see only the first 1-3 lines before "Read More"
7. **Set and forget** — ASO requires ongoing iteration as competition and algorithms change
8. **Optimizing for search only** — High visibility with low conversion wastes potential
9. **Neglecting ratings** — A 3.5-star app converts dramatically worse than a 4.2-star app
10. **Spaces after commas in iOS keywords** — Each space wastes a character of your 100-char budget
11. **Not using all screenshot slots** — Empty slots are missed conversion opportunities
12. **Same metadata across all locales** — Signals lazy localization to both algorithms and users
13. **Unverifiable superlative claims** — "Fastest", "most popular", "award-winning" without evidence triggers rejection
14. **Emojis and special characters in titles** — Both stores now prohibit these in titles and subtitles
15. **Brand-first title for an unknown app** — Searchers can't tell what the app does from a name they've never seen *(practitioner)*
16. **Chasing the highest-volume keywords from day one** — A new app can't outrank apps with millions of downloads; pick winnable terms first *(practitioner)*
17. **Feature-label screenshot captions** — "Advanced Analytics Dashboard" gives no reason to download; state the benefit *(practitioner)*
18. **Prompting for a review on first launch, or rewarding ratings** — Annoying at best, a policy violation at worst *(practitioner)*
19. **Judging ASO by rank alone, or after one day** — Track ranks over weeks and measure downloads and paid conversions *(practitioner)*

---

## Character Limits Quick Reference

### Apple App Store

| Field | Limit | Indexed? | Priority |
|-------|-------|----------|----------|
| App Name | 30 | Yes | Critical |
| Subtitle | 30 | Yes | Critical |
| Keywords | 100 | Yes | Critical |
| Description | 4,000 | No | High (conversion) |
| Promotional Text | 170 | No | Medium |
| What's New | 4,000 | No | Low |

### Google Play Store

| Field | Limit | Indexed? | Priority |
|-------|-------|----------|----------|
| App Title | 30 | Yes | Critical |
| Short Description | 80 | Yes | Critical |
| Full Description | 4,000 | Yes | Critical |
| What's New | 500 | No | Low |
