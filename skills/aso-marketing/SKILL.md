---
name: aso-marketing
version: 1.1.0
description: Comprehensive App Store Optimization (ASO) marketing skill for mobile applications. Analyzes your app's codebase, store listing, and competitive landscape, then builds and executes a full ASO plan covering keyword strategy, metadata optimization, visual asset guidance, localization, and conversion rate improvement — for both Apple App Store and Google Play. Includes built-in store policy compliance checking that validates all proposed metadata against Apple App Store Review Guidelines (2.3.7, 5.2.1) and Google Play metadata policies — catching prohibited keywords, trademark violations, competitor brand misuse, and listing policy issues before submission to prevent app rejection. Use when asked to "optimize my app store listing", "ASO plan", "improve app visibility", "app store marketing", "increase app downloads", "keyword strategy for my app", "optimize for App Store", "optimize for Google Play", "app marketing plan", "store listing optimization", "improve app conversion rate", "ASO audit and fix", "check listing policy compliance", "avoid app store rejection", or any request about making a mobile app more discoverable and downloadable in app stores. Also trigger when the user mentions app store rankings, keyword research for apps, screenshot optimization, app metadata, store policy compliance, or wants to increase organic installs — even if they don't say "ASO" explicitly.
---

# ASO Marketing — Full-Lifecycle App Store Optimization

A comprehensive, iterative ASO workflow that takes your mobile app from analysis through planning, execution, verification, and reporting — covering both Apple App Store and Google Play Store.

## Repo Sync Before Edits (mandatory)

Before modifying any files in the repository:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash, sync, then pop. If `origin` is missing or conflicts occur: stop and ask the user before continuing.

## Philosophy

ASO is not a one-time task — it's a continuous optimization cycle. The best ASO strategies combine data-driven keyword research with compelling creative assets and ongoing measurement. This skill guides you through the full cycle, but always defers to the user on business priorities and brand voice. The goal is to make the app easier to find and more compelling to download.

## Before You Start

1. Read `references/aso_best_practices.md` for the complete ASO knowledge base covering both stores — **especially the "Store Policy Compliance" section** which details prohibited keywords, trademark rules, and listing policy restrictions for both Apple and Google.
2. Determine which store(s) the user wants to optimize for (App Store, Google Play, or both).
3. Identify whether the user has existing metadata files, a live store listing, or is launching fresh.

## Workflow Overview

The skill follows a 7-phase cycle. Each phase produces visible output for the user. Never skip the policy compliance check or the planning approval gate — the user must approve a policy-compliant plan before execution begins.

```
Phase 1: Analyze → Phase 2: Plan → Phase 3: Policy Compliance Check → [User Approval Gate] → Phase 4: Execute → Phase 5: Review → Phase 6: Verify → Phase 7: Summarize
```

---

## Phase 1: Analyze the Current State

The analysis phase gathers everything needed to build an informed ASO plan. Investigate all available sources.

### 1.1 Codebase & Project Analysis

Understand what the app does by reading the codebase:
- Read README, package.json, build.gradle, Podfile, Info.plist, AndroidManifest.xml, or any project config files
- Identify the app's core features, target audience, and value proposition
- Detect the app's category, supported platforms (iOS/Android/both), and supported languages
- Look for existing metadata directories (`metadata/`, `fastlane/`, `supply/`, or custom paths)

### 1.2 Existing Store Metadata Audit

If metadata files exist locally:
- **App Store (iOS):** Check `metadata/app-info/{locale}.json` and `metadata/version/{version}/{locale}.json` for name, subtitle, keywords, description, whatsNew, promotionalText
- **Google Play (Android):** Check `fastlane/metadata/android/{locale}/` or `supply/metadata/` for title.txt, short_description.txt, full_description.txt, changelogs/
- Audit each field for character limit compliance, keyword utilization, and quality

If the `asc-aso-audit` skill is available, recommend running it first for iOS metadata — it provides detailed offline checks that complement this skill's broader scope.

### 1.3 Competitive Landscape

Ask the user to identify 3-5 direct competitors. For each:
- Note their app name, subtitle/short description, and apparent keyword strategy
- Identify what makes them rank well (keywords in title, strong ratings, etc.)
- Look for gaps — keywords they miss that the user's app could target

**Trademark warning:** Competitive analysis is for strategic insight only. Never carry competitor brand names into the proposed metadata (title, subtitle, keywords, descriptions). Using competitor trademarks in metadata violates Apple guideline 2.3.7/5.2.1 and Google Play policy, and can result in app rejection, de-indexing, or account termination.

### 1.4 Current Performance Baseline

If available, gather:
- Current keyword rankings (from ASO tools, App Store Connect analytics, or Google Play Console)
- Download/install numbers and trends
- Ratings and review sentiment
- Conversion rate (impressions → installs)

### 1.5 Produce the Analysis Report

Output a structured analysis covering:

```markdown
## ASO Analysis Report

### App Overview
- **App Name:** [name]
- **Platforms:** [iOS / Android / Both]
- **Category:** [category]
- **Core Value Proposition:** [1-2 sentences]
- **Target Audience:** [demographics/use cases]

### Current Metadata Status
| Field | Platform | Current Value | Length | Limit | Usage % | Issues |
|-------|----------|---------------|--------|-------|---------|--------|

### Competitive Landscape
| Competitor | Platform | Keywords in Title | Rating | Apparent Strategy |
|-----------|----------|-------------------|--------|-------------------|

### Key Findings
1. [Finding 1 — most impactful]
2. [Finding 2]
3. ...

### Opportunities
1. [Opportunity 1 — highest potential impact]
2. [Opportunity 2]
3. ...
```

---

## Phase 2: Propose the ASO Plan

Build a prioritized, actionable plan based on the analysis. The plan must cover all relevant optimization areas and be specific enough that the user can evaluate each recommendation.

### Plan Structure

```markdown
## ASO Marketing Plan

### Objectives
- Primary: [e.g., "Increase organic installs by improving search visibility for [category] keywords"]
- Secondary: [e.g., "Improve conversion rate from listing page views to installs"]

### Target Keywords
#### Primary Keywords (high volume, core relevance)
| Keyword/Phrase | Est. Volume | Competition | Target Field | Rationale |
|---------------|-------------|-------------|--------------|-----------|

#### Secondary Keywords (moderate volume, good fit)
| Keyword/Phrase | Est. Volume | Competition | Target Field | Rationale |
|---------------|-------------|-------------|--------------|-----------|

#### Long-Tail Keywords (lower volume, high intent)
| Keyword/Phrase | Est. Volume | Competition | Target Field | Rationale |
|---------------|-------------|-------------|--------------|-----------|

### Metadata Optimization Plan

#### App Name / Title
- Current: "[current]"
- Proposed: "[proposed]"
- Rationale: [why this change improves discoverability]

#### Subtitle (iOS) / Short Description (Android)
- Current: "[current]"
- Proposed: "[proposed]"
- Rationale: [keyword + conversion reasoning]

#### Keywords Field (iOS only)
- Current: "[current]"
- Proposed: "[proposed]"
- Characters used: [X/100]
- Cross-field combinations enabled: [list key search queries this enables]

#### Description / Full Description
- Key changes: [what to add/remove/restructure]
- Keyword integration points: [where keywords appear naturally]
- Conversion optimization: [how the description drives installs]

#### What's New / Release Notes
- Strategy: [how to leverage release notes for engagement]

### Visual Asset Recommendations
- **App Icon:** [assessment and suggestions]
- **Screenshots:** [ordering, messaging, keyword captions]
- **Preview Video:** [if applicable — recommendation]

### Localization Strategy
- Priority markets: [ranked by opportunity]
- Localization approach per market: [translate vs. localize vs. transcreate]

### Ratings & Reviews Strategy
- Current rating: [X.X]
- Target rating: [X.X]
- Actions: [in-app review prompt timing, response strategy]

### Timeline & Priorities
| Priority | Action | Impact | Effort | Timeline |
|----------|--------|--------|--------|----------|
| P0 | [highest impact, do first] | High | Low | Week 1 |
| P1 | ... | ... | ... | ... |
| P2 | ... | ... | ... | ... |
```

### Iteration Gate

Present the plan to the user and explicitly ask for approval — but only after the policy compliance check (Phase 3) has validated all proposed metadata.

---

## Phase 3: Policy Compliance Check

Before presenting the plan for approval, validate **every piece of proposed metadata** against Apple App Store and Google Play Store policies. This phase prevents rejected submissions and protects the developer account.

### 3.1 Prohibited Keyword Scan

Check all proposed metadata fields (title, subtitle, keywords, short description, full description) for prohibited terms:

**Apple App Store — Banned in title, subtitle, and keywords:**
- Pricing terms: "free", "sale", "discount", "limited time"
- Superlative claims: "best", "#1", "top-rated", "must-have", "top app", "#1 in the world"
- Reserved terms: "For Kids", "For Children" (unless Kids Category), "Editor's Choice"
- Platform references: "Android", "Google Play", "Play Store"
- Call-to-action phrases: "download now", "install now", "try now"

**Google Play — Banned in title, short description, developer name, and icon:**
- Performance claims: "top", "best", "#1", "number one", "popular"
- Pricing terms: "free", "no ads", "ad free"
- Promotional terms: "new", "hot", "first", "bonus", "discount", "sale", "million downloads"
- Ranking claims: "App of the Year", "Best Google Play App of [year]"
- Call-to-action: "download now", "install now", "play now", "try now", "update now"

### 3.2 Trademark and Competitor Check

Scan all proposed metadata for:
- **Competitor brand names** — Any mention of competitor app names (e.g., "WhatsApp", "Instagram", "Nike Training Club") must be removed from title, subtitle, keywords, and descriptions
- **Trademarked terms** — Any trademarked term the user doesn't own or have a license for must be flagged
- **Celebrity names** — Unless explicitly authorized
- **Apple/Google trademarks** — Cannot suggest endorsement (e.g., "Featured by Apple", "Google's Choice")

If competitor analysis was done in Phase 1, verify that competitor names referenced in the analysis are **not** carried into the proposed metadata. Competitor analysis is for strategic insight only — never embed competitor names in metadata.

### 3.3 Formatting Compliance

- [ ] No emojis or special characters in title/subtitle (both stores)
- [ ] No ALL CAPS in title/subtitle unless it's the registered brand name
- [ ] No repeated special characters
- [ ] Title within character limits (30 chars both stores)
- [ ] No unattributed user testimonials or fake reviews in metadata
- [ ] No graphic elements in icon suggesting store rankings (Google Play)

### 3.4 Content Accuracy Check

- [ ] No unverifiable claims ("fastest", "most popular", "award-winning" without evidence)
- [ ] Description accurately reflects app features — no features the app doesn't have
- [ ] Screenshots show the actual app in use (not just marketing art)
- [ ] In-app purchases and subscriptions clearly disclosed
- [ ] No misleading descriptions of app functionality

### 3.5 Produce the Compliance Report

Output a compliance report alongside the plan:

```markdown
## Store Policy Compliance Report

### Prohibited Keyword Check
| Proposed Term | Field | Store | Status | Issue | Fix |
|--------------|-------|-------|--------|-------|-----|
| [term] | [field] | [iOS/Android] | PASS/FAIL | [issue if any] | [replacement if needed] |

### Trademark Check
| Term | Field | Risk Level | Action |
|------|-------|-----------|--------|
| [term] | [field] | None/Low/High | [keep/remove/replace] |

### Formatting Check
- [x] or [ ] for each formatting rule

### Content Accuracy Check
- [x] or [ ] for each accuracy rule

### Overall Status: PASS / NEEDS REVISION
[If NEEDS REVISION, list all required changes before the plan can be approved]
```

If any violations are found, **revise the plan to fix all issues before presenting to the user**. The user should only see a compliant plan.

### Present for Approval

After the compliance check passes, present both the ASO plan and the compliance report to the user:

> "Here's the ASO plan based on my analysis. All proposed metadata has been validated against Apple App Store and Google Play Store listing policies — no prohibited keywords, trademark violations, or policy issues found.
>
> Please review each section. Let me know:
> 1. Which recommendations you approve
> 2. Which you'd like to modify
> 3. Any you want to skip
> 4. Any additional ideas to include
>
> I'll revise the plan based on your feedback before executing anything."

**Do not proceed to Phase 4 until the user explicitly approves the plan.** Iterate on the plan as many times as needed. Each revision should clearly show what changed and why — and each revision must pass the compliance check again.

---

## Phase 4: Execute the Plan

Once the user approves, implement the changes systematically. Work through the priority list in order.

### 4.1 Metadata Updates

For each approved metadata change:

**App Store (iOS) — if canonical metadata exists:**
- Update `metadata/app-info/{locale}.json` for name, subtitle
- Update `metadata/version/{version}/{locale}.json` for keywords, description, whatsNew, promotionalText
- Validate character limits after each edit
- Cross-check keywords field: no duplicates with title/subtitle, no spaces after commas, single words preferred

**Google Play (Android) — if fastlane/supply metadata exists:**
- Update `title.txt` (max 30 chars)
- Update `short_description.txt` (max 80 chars)
- Update `full_description.txt` (max 4,000 chars) — integrate keywords naturally, avoid stuffing
- Update changelogs if applicable

**If no local metadata structure exists:**
- Create the appropriate directory structure
- Write the optimized metadata files
- Provide instructions for how to upload/sync with the store

### 4.2 Keyword Implementation

Follow these rules when writing keywords:

**Store Policy Compliance (MUST CHECK FIRST):**
- **Never use prohibited terms** — check every keyword against the banned words lists in `references/aso_best_practices.md` → "Store Policy Compliance" section
- **Never use competitor brand names or trademarks** — even in the hidden iOS keywords field, Apple monitors and de-indexes trademarked terms
- **Never use unverifiable superlatives** — "best", "#1", "top-rated" are banned on both stores
- **Never use pricing/promotional language** — "free", "sale", "discount" trigger rejection
- If unsure whether a term is trademarked, err on the side of caution and use a generic alternative

**Apple App Store:**
- Keywords field: comma-separated, no spaces after commas
- Never duplicate words from title or subtitle in keywords
- Prefer single words over phrases (enables cross-field combinations)
- Aim for 90%+ character utilization (90+ of 100 chars)
- Consider cross-field search queries: word in subtitle + word in keywords = matched search
- Do not include competitor app names in the keywords field — Apple actively monitors and can silently de-index or reject

**Google Play:**
- Keywords go naturally into title, short description, and full description
- No separate keyword field — Google indexes all text fields
- Repeat important keywords 3-5 times across fields (not stuffing, natural usage)
- Long description should cover related concepts and use cases
- Google's algorithm detects keyword stuffing — prioritize readability
- Do not embed competitor brand names anywhere in metadata — trademark owners can file complaints leading to app removal

### 4.3 Description Optimization

Optimize descriptions for both search and conversion:

- **First 1-3 lines are critical** — this is what users see before "Read More"
- Lead with the strongest value proposition and a clear call-to-action
- Use bullet points or short paragraphs for scannability
- Naturally integrate target keywords without forcing them
- Include social proof (awards, press mentions, user count) if available
- End with a clear reason to download now

### 4.4 Localization Execution

For each target locale:
- Research locale-specific keywords (not just translations of English keywords)
- Adapt the messaging to local culture and usage patterns
- Verify character limits in the target language (some languages are more verbose)
- If the `asc-localize-metadata` skill is available, recommend it for bulk translation workflows

### 4.5 Visual Asset Guidance

Provide specific, actionable guidance:

- **Screenshots:** Recommend ordering (lead with the strongest feature), caption text with keywords (OCR-indexed on App Store since June 2025), and visual hierarchy
- **App Icon:** Assess current icon for clarity at small sizes, color contrast, and category conventions
- **Preview Video:** Recommend whether one is needed and what to show in the first 3 seconds

---

## Phase 5: Review the Implementation

After execution, review all changes for quality and correctness.

### Review Checklist

- [ ] All metadata fields within character limits
- [ ] No keyword duplication across indexed fields (iOS)
- [ ] Keywords field properly formatted (commas, no spaces)
- [ ] Descriptions read naturally with keywords integrated
- [ ] No spelling or grammar errors in any locale
- [ ] Cross-field keyword combinations produce intended search queries
- [ ] Visual asset recommendations are specific and actionable
- [ ] Localized metadata is genuinely localized (not just translated)
- [ ] No sensitive or brand-risky terms introduced
- [ ] **No prohibited keywords** — re-scan all fields for banned terms (see Phase 3)
- [ ] **No competitor trademarks** — verify no competitor brand names leaked into any metadata field
- [ ] **No unverifiable claims** — no superlatives without evidence ("fastest", "best", "#1")
- [ ] **No platform references** — no "Android"/"Google Play" in iOS metadata or vice versa
- [ ] **No formatting violations** — no emojis, ALL CAPS (unless brand name), or special characters in titles
- [ ] **Accurate feature descriptions** — every claimed feature exists in the app

### Self-Audit

Run through the Phase 1 analysis checks again on the updated metadata to verify improvements:
- Field utilization percentages improved
- Keyword coverage expanded
- No new issues introduced

---

## Phase 6: Verify Against Best Practices

Cross-reference the implementation against the best practices in `references/aso_best_practices.md`:

- [ ] Title/name includes primary keyword
- [ ] Subtitle/short description includes secondary keyword and value prop
- [ ] Keywords field maximizes character budget (iOS)
- [ ] Description is conversion-optimized with keyword integration
- [ ] Localization is market-aware, not just translated
- [ ] Visual assets support conversion
- [ ] Rating/review strategy addressed
- [ ] Ongoing optimization recommendations provided
- [ ] **All metadata passes Store Policy Compliance rules** (see "Store Policy Compliance" section in best practices)
- [ ] **No trademark violations** — final check that no competitor or third-party trademarks appear in any metadata
- [ ] **No prohibited keywords** — final scan against the prohibited terms lists for both stores

If any best practice or policy rule is violated, fix it before moving to the summary.

---

## Phase 7: Summarize

Produce a final summary report for the user:

```markdown
## ASO Marketing Summary Report

### Changes Made
| # | Area | Change | Before | After | Expected Impact |
|---|------|--------|--------|-------|-----------------|

### Metadata Comparison
| Field | Platform | Before | After | Improvement |
|-------|----------|--------|-------|-------------|

### Keyword Strategy Summary
- **Total unique keywords targeted:** [X]
- **Primary keywords:** [list]
- **Cross-field combinations enabled:** [list key search queries]
- **Keyword field utilization:** [X/100 chars (Y%)]

### Store Policy Compliance
- **Prohibited keyword check:** PASS — no banned terms in any metadata field
- **Trademark check:** PASS — no competitor or third-party trademarks used
- **Formatting check:** PASS — no emojis, ALL CAPS, or special characters in titles
- **Content accuracy check:** PASS — all features described exist in the app
- **Overall compliance:** PASS for [App Store / Google Play / Both]

### Expected Outcomes
- [Outcome 1: e.g., "Improved visibility for [keyword] searches"]
- [Outcome 2: e.g., "Higher conversion rate from improved first-impression copy"]

### Next Steps
1. **Upload metadata** to the store(s) — [specific instructions]
2. **Monitor rankings** for target keywords after 1-2 weeks
3. **A/B test** screenshots and descriptions (use Custom Product Pages on iOS or Store Listing Experiments on Google Play)
4. **Re-run this skill** in 4-6 weeks to iterate based on performance data

### Files Modified
- [list all files created or modified with paths]
```

---

## Platform-Specific Notes

### Apple App Store
- Indexed fields: title, subtitle, keyword field (100 chars)
- Description is NOT indexed but affects conversion
- Screenshot captions are OCR-indexed (since June 2025)
- Custom Product Pages (CPPs) enable audience-specific listings
- Use `asc` CLI tools if available for metadata sync

### Google Play Store
- All text fields are indexed (title, short description, full description)
- No separate keyword field — keywords must be woven into text naturally
- Google detects and penalizes keyword stuffing
- Store Listing Experiments enable A/B testing
- Long description supports up to 4,000 chars — use them wisely
- Google considers app quality signals: crash rate, ANR rate, retention

### Both Stores
- App ratings above 4.0 are critical for conversion (90% of featured apps are 4.0+)
- Regular updates signal to algorithms that the app is actively maintained
- Localization should be market-aware, not simple translation
- First 1-3 lines of description must hook the user before "Read More"

---

## Cross-Skill Integration

This skill works well in combination with:
- **`asc-aso-audit`** — Detailed offline audit of iOS metadata (run before this skill for a deep keyword audit)
- **`asc-localize-metadata`** — Bulk localization of App Store metadata across all locales
- **`asc-metadata-sync`** — Sync local metadata files with App Store Connect
- **`asc-whats-new-writer`** — Generate engaging release notes with keyword reinforcement
- **`asc-shots-pipeline`** — Automated screenshot capture with keyword-optimized captions
- **`seo-ai-optimizer`** — If the app has a web presence, align ASO and SEO keyword strategies
