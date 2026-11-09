# Phases 1-2: Analysis and Planning

## Phase 1: Analyze the Current State

The analysis phase gathers everything needed to build an informed ASO plan.

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

If the `asc-aso-audit` skill is available, recommend running it first for iOS metadata.

### 1.3 Competitive Landscape

Ask the user to identify 3-5 direct competitors. For each:
- Note their app name, subtitle/short description, and apparent keyword strategy
- Identify what makes them rank well
- Look for gaps — keywords they miss

**Trademark warning:** Competitive analysis is for strategic insight only. Never carry competitor brand names into proposed metadata.

### 1.4 Current Performance Baseline

If available, gather:
- Current rank for each candidate keyword. Record `unranked` or `unknown` where there is no data; Phase 7 measures against this baseline
- Download/install numbers and trends (and paid conversions, if the app sells anything)
- Ratings and review sentiment
- Conversion rate (impressions → installs)

### 1.5 Analysis Report Template

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

### Keyword Rank Baseline
| Keyword | Store | Current Rank (or unranked / unknown) | Source and date |
|---------|-------|--------------------------------------|-----------------|

### Key Findings
1. [Finding 1 — most impactful. If product signals are weak (rating below 4.0, or recent reviews repeatedly reporting a broken core function), say so: ASO will not fix it]

### Opportunities
1. [Opportunity 1 — highest potential impact]
```

---

## Phase 2: Propose the ASO Plan

Build a prioritized, actionable plan based on the analysis.

### Plan Template

```markdown
## ASO Marketing Plan

### Objectives
- Primary: [e.g., "Increase organic installs"]
- Secondary: [e.g., "Improve conversion rate"]

### Target Keywords
Pick keywords the app can win at its current size (`aso_best_practices.md` → Stage-aware targeting). The Rationale column says why each one is winnable now.

#### Primary Keywords (high volume, core relevance)
| Keyword/Phrase | Est. Volume | Competition | Target Field | Rationale |

#### Secondary Keywords (moderate volume, good fit)
| Keyword/Phrase | Est. Volume | Competition | Target Field | Rationale |

#### Long-Tail Keywords (lower volume, high intent)
| Keyword/Phrase | Est. Volume | Competition | Target Field | Rationale |

### Metadata Optimization Plan

#### App Name / Title
- Current: "[current]"
- Proposed: "[proposed]"
- Brand position: [keyword first / brand first — brand status known or unknown, and the evidence]
- Rationale: [why this change improves discoverability]

#### Subtitle (iOS) / Short Description (Android)
- Current: "[current]"
- Proposed: "[proposed]"
- Rationale: [keyword + conversion reasoning]

#### Keywords Field (iOS only)
- Current: "[current]"
- Proposed: "[proposed]"
- Characters used: [X/100]
- Cross-field combinations enabled: [list key search queries]

#### Description / Full Description
- Key changes: [what to add/remove/restructure]
- Keyword integration points
- Conversion optimization

#### What's New / Release Notes
- Strategy

### Visual Asset Recommendations
- **App Icon:** [assessment and suggestions]
- **Screenshots:** [ordering; one benefit-led caption per screenshot, legible on a phone; what the first three say on their own]
- **Preview Video:** [if applicable]

### Localization Strategy
- Priority markets: [ranked by opportunity]
- Per market: researched local keywords (not translations), marked validated or unvalidated; localized screenshots; which localizations the storefront indexes

### Ratings & Reviews Strategy
- Current rating, target rating, actions
- Prompt moment: [the value moment that triggers the native review prompt; never on first launch, never rewarded]

### Localized Pricing (optional — recommendation only)
Include only when the app sells something and the user names target markets with different purchasing power, or asks about pricing (`aso_best_practices.md` → Localized Pricing). The skill never changes prices or writes them to any file.
| Tier | Markets | Proposed price (% of base) | Evidence (purchasing power, local competitors) |
- Per-user cost check: [does a lower tier stay profitable? If not, keep the base price there and say why. Unknown → "unvalidated: confirm costs before applying"]

### Measurement Plan
- Keywords to track: [primary and secondary, with the Phase 1 baseline rank]
- Cadence: [e.g., weekly for a measurement window of at least 6 weeks]
- Outcome metrics: impressions → product page views → downloads → paid conversions
- Change order: [cycle 1 = the indexed metadata set (title, subtitle, keywords); then one lever per cycle: screenshots, localizations, pricing]

### Timeline & Priorities
| Priority | Action | Impact | Effort | Timeline |
| P0 | [highest impact, do first] | High | Low | Week 1 |
```

### Iteration Gate

Present the plan to the user and ask for approval — but only after the policy compliance check (Phase 3) has validated all proposed metadata.
