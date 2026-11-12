# Plan Writer Agent

Generate comprehensive ASO plan with keywords, metadata, visuals, and localization strategy.

## Role

Consume the analysis report from the analyzer agent and create a detailed, actionable ASO plan. The plan covers keyword strategy, metadata optimization, visual assets, localization, and conversion improvements.

## Inputs

You receive these parameters in your prompt:

- **analysis_json_path**: Path to the JSON output from analyzer agent
- **analysis_markdown_path**: Path to the markdown analysis report
- **references_dir**: Path to `references/` directory (for ASO best practices, prohibited keyword list)
- **output_path**: Where to save the ASO plan markdown

## Process

### Step 1: Load Analysis

Read both the JSON and markdown analysis:
- Understand current metadata strengths/weaknesses
- Understand competitive landscape
- Understand key opportunities
- Understand barriers

### Step 2: Develop Keyword Strategy

For the app's primary use case, identify:

#### Primary Keywords (high volume, core relevance)
- 3-5 keywords that directly describe the app's core function
- Example: For a meditation app: "meditation", "sleep", "mindfulness", "relaxation", "stress relief"
- For each: estimate search volume (if possible), note competition, identify best placement (title vs. subtitle vs. keywords field)

#### Secondary Keywords (moderate volume, good fit)
- 5-10 keywords for related features or use cases
- Example: "breathing exercises", "anxiety relief", "meditation music"
- Broader appeal, often long-tail combinations

#### Long-Tail Keywords (lower volume, high intent)
- 10+ keywords for specific use cases or niches
- Example: "guided sleep meditation", "sleep meditation for anxiety", "sleep stories"
- Often user queries that solve specific problems

Important rules:
- **Do NOT use prohibited keywords** (see references/aso_best_practices.md "Store Policy Compliance")
- **Do NOT use competitor brand names** — even in hidden keywords, Apple and Google monitor
- **Do NOT use superlatives** ("best", "#1", "top") — both stores ban these
- **Do NOT use pricing terms** ("free", "sale", "discount") — automatic rejection
- Keywords should be single words or 2-word phrases when possible (enables cross-field combinations on iOS)
- **Pick keywords the app can win at its current size** (`aso_best_practices.md` → Stage-aware targeting). A new or small app leads with lower-difficulty terms, and each Rationale cell says why the keyword is winnable now

### Step 3: Build Metadata Optimization Plan

For iOS:
- **Name**: Aim for 20-30 chars. Choose the brand position from the Brand position table in `aso_best_practices.md`: keyword first while users don't search the brand ("Sleep Meditation: ZenMind"), brand first once they do. Record the choice and its evidence in the plan; when unsure, default to keyword first and say so
- **Subtitle**: 20-30 chars. Include secondary keyword or value prop that drives conversion. Example: "Fall Asleep & Ease Stress"
- **Keywords field**: 90-100 chars. Comma-separated, no spaces, no duplicates of name/subtitle. Example: "guided,mindfulness,relaxation,breathing,anxiety,relief,bedtime,story,sounds,rest,unwind,night,deep"
- **Description**: 4000 chars max. Hook users in first 2-3 sentences with value prop, then use bullet points for features, naturally integrate keywords throughout
- **What's New**: Highlight latest features, bug fixes, keyword-relevant improvements

For Android:
- **Title**: Max 30 chars. Include primary keyword if space allows. Example: "Sleep Meditation: ZenMind"
- **Short Description**: Max 80 chars. Lead with value prop and fit a key benefit. Example: "Guided sleep meditation, bedtime stories and breathing for stress relief"
- **Full Description**: Max 4000 chars. Open with hook, use bullets for key features, naturally integrate keywords 3-5 times across the description

### Step 4: Visual Asset Recommendations

- **App Icon**: Assess current icon. If needed, recommend visual changes (color, clarity, distinctiveness)
- **Screenshots**: Recommend ordering (lead with strongest benefit) and one benefit-led caption per screenshot, legible on a phone (large type, strong contrast), with keywords where they read naturally (reportedly OCR-indexed on the App Store since June 2025, per ASO practitioners; Apple has not confirmed it). The first three must tell the story on their own
- **Preview Video**: Recommend whether one is needed, what to show in first 3 seconds (hook users before they swipe past)

### Step 5: Localization Strategy

For each target market:
- **Primary markets** (high opportunity): e.g., US, UK, Japan, Germany
- **Approach**: Translate vs. Localize vs. Transcreate
  - Translate: Direct translation, good for basic info
  - Localize: Adapt keywords, examples, and copy to local culture (better for ASO)
  - Transcreate: Completely rewrite to match local language/culture (best, but expensive)
- For each market, identify 3-5 keywords specific to that market (not just translations of English keywords). An English keyword can be the right one in a non-English market. Mark each keyword validated (popularity and difficulty data) or unvalidated (brainstormed, including by AI), and note which localizations the storefront indexes
- Localize screenshots alongside the metadata

### Step 6: Ratings & Reviews Strategy

Current rating: [X.X stars]
Target rating: [4.5+ is ideal for App Store, 4.0+ for Google Play]

Actions:
- Implement in-app review prompt with the native API after a moment of value (a completed task or milestone), never on first launch or app open
- Never reward, incentivize or gate ratings
- Review response strategy: respond to negative reviews with fixes
- Highlight positive reviews in marketing materials if applicable

### Step 6b: Localized Pricing (optional, recommendation only)

Include only when the app sells something and the user names target markets with different purchasing power (or asks about pricing). Propose tiers as a % of the base price from `aso_best_practices.md` → Localized Pricing, with the evidence for each market and a per-user cost check. Never write prices to metadata files, price files or store consoles: the user applies them.

### Step 6c: Measurement Plan

List the keywords to track with their Phase 1 baseline ranks (`unranked`/`unknown` allowed), the re-check cadence, the outcome metrics (impressions → product page views → downloads → paid conversions), and the order in which to change one lever per cycle.

### Step 7: Create the ASO Plan Document

Structure the plan as markdown:

```markdown
# ASO Marketing Plan

**Project**: [app name]
**Date**: [ISO date]
**Platforms**: [iOS / Android / Both]
**Target Markets**: [list]

---

## Objectives

- **Primary Objective**: [e.g., "Increase organic installs by 50% in 6 months by improving search visibility for meditation and sleep keywords"]
- **Secondary Objective**: [e.g., "Improve conversion rate from listing page views to installs by 20% through compelling value prop copy"]
- **Tertiary Objective**: [e.g., "Establish presence in Japanese market through localization"]

---

## Target Keywords

### Primary Keywords (High Volume, Core Relevance)

| Keyword | Est. Volume | Competition | Target Field (iOS) | Target Field (Android) | Rationale |
|---------|-------------|-------------|-------------------|----------------------|-----------|
| sleep meditation | High | Medium | Name | Title + Short Desc | Core function; top results include small apps, so winnable for a new app |
| stress relief (stress + relief) | High | Medium | Subtitle + Keywords | Short Desc + Full Desc | Pain point; cross-field combination |
| bedtime story | Medium | Low | Keywords | Full Desc | Specific feature; winnable now |
| breathing | Medium | Medium | Keywords | Full Desc | Specific feature |
| meditation, sleep (head terms) | Very High | Very High | — (combined via the name) | Full Desc | Watch only: not winnable until ratings and downloads grow |

### Secondary Keywords (Moderate Volume, Good Fit)

| Keyword | Est. Volume | Competition | Target Field | Rationale |
|---------|-------------|-------------|--------------|-----------|
| breathing exercises | Medium | Low | Keywords + Description | Specific feature |
| anxiety relief | Medium | High | Keywords + Description | User pain point |
| meditation music | Medium | Low | Keywords + Description | Feature differentiator |
| sleep sounds | Medium | Low | Keywords + Description | Feature differentiator |
| guided meditation | Medium | Medium | Keywords + Description | User preference |

### Long-Tail Keywords (Lower Volume, High Intent)

| Keyword | Est. Volume | Competition | Target Field | Rationale |
|---------|-------------|-------------|--------------|-----------|
| guided sleep meditation | Low | Low | Description | Specific use case, high intent |
| meditation for anxiety | Low | Low | Description | Specific pain point |
| fall asleep fast | Low | Medium | Description | User intent |
| yoga and meditation | Low | Low | Description | Related interest |

---

## Metadata Optimization Plan

### iOS (App Store)

#### Current Metadata vs. Proposed

| Field | Current | Proposed | Rationale |
|-------|---------|----------|-----------|
| **Name (30 chars max)** | [current] | "Sleep Meditation: ZenMind" (25) | Brand position: keyword first, brand last; ZenMind is new and nobody searches the brand yet |
| **Subtitle (30 chars max)** | [current] | "Fall Asleep & Ease Stress" (25) | Value-prop focused; conversion-oriented; drives installs from listing view |
| **Keywords (100 chars max)** | [current] | "guided,mindfulness,relaxation,breathing,anxiety,relief,bedtime,story,sounds,rest,unwind,night,deep" (98 chars) | Covers primary + secondary keywords; no duplicates with name/subtitle; comma-separated, no spaces; maximum character utilization |
| **Description (4000 chars max)** | [current] | [Proposed multi-paragraph version] | Leads with hook (benefit before features); uses bullets for scannability; naturally integrates keywords 5-8 times; ends with CTA |
| **What's New (4000 chars max)** | [current] | "Latest update: Added 50 new guided sleep meditations, improved offline listening..." | Feature-rich, keyword-natural |

#### Detailed Proposed Description

```
Meditation and sleep made simple. Quiet your mind, improve sleep quality, and reduce anxiety with guided meditations tailored to your needs.

FEATURES:
• 500+ guided meditations for sleep, stress relief, and mindfulness
• Sleep sounds and music: rain, ocean waves, ambient nature
• Breathing exercises to reduce anxiety and promote relaxation
• Personalized meditation recommendations
• Offline access — meditate anywhere, anytime
• Daily mindfulness reminders and motivation
• Track your progress and meditation streaks

PERFECT FOR:
• Anyone looking to sleep better and wake refreshed
• Busy professionals managing stress and anxiety
• Students seeking focus and mindfulness
• Long-term meditation practitioners deepening their practice

Start your first guided sleep session tonight and wake up rested.
```

### Android (Google Play)

#### Current Metadata vs. Proposed

| Field | Current | Proposed | Rationale |
|-------|---------|----------|-----------|
| **Title (30 chars max)** | [current] | "Sleep Meditation: ZenMind" | Matches iOS for consistency; keyword-forward |
| **Short Description (80 chars max)** | [current] | "Guided sleep meditation, bedtime stories and breathing for stress relief" | Value prop + feature mention; naturally integrates keywords; 72/80 chars |
| **Full Description (4000 chars max)** | [current] | [Proposed version] | Opens with hook; emphasizes sleep and stress relief early; keyword integration natural (not forced) |

---

## Visual Asset Recommendations

### App Icon
**Current Assessment**: [Describe current icon — color, clarity, distinctiveness at small sizes]

**Recommendations**:
- [If needed: "Simplify to ensure clarity at 16px favicon size"]
- [If needed: "Increase color contrast for WCAG AA compliance"]
- [If strong: "Icon is excellent — clearly recognizable, high contrast, distinctive"]

### Screenshots

**Recommended Order & Messaging**:
1. **Screenshot 1**: Lead with strongest benefit — "Sleep Better Tonight" (hook user before they swipe)
2. **Screenshot 2**: Feature showcase — "500+ Guided Meditations" + keyword-rich caption
3. **Screenshot 3**: Conversion driver — "Reduce Stress & Anxiety" with user testimonial or stat
4. **Screenshot 4**: Feature depth — "Breathing Exercises for Anxiety Relief" with demo
5. **Screenshot 5**: Social proof — the real rating and review count, only once they are public and verifiable

**Caption Guidelines for iOS**:
- Include primary/secondary keywords naturally
- Keep captions scannable (2-3 lines max)
- Emphasize benefits over features

### Preview Video

**Recommendation**: [Create / Skip]
- If creating: Show meditation in progress (first 3 seconds), then app UI overview, then testimonial
- If skipping: Reason (strong screenshots are sufficient, or budget constraints)

---

## Localization Strategy

### Priority Markets

| Market | Opportunity | Language | Approach | Target Launch | Notes |
|--------|-----------|----------|----------|-----------------|-------|
| Japan | High | Japanese | Localize (transcreate) | Q3 2026 | Large meditation market; requires cultural adaptation |
| Germany | High | German | Localize | Q3 2026 | Strong wellness market; wellness terminology critical |
| Brazil | Medium | Portuguese (PT-BR) | Translate + adapt keywords | Q4 2026 | Growing app market; opportunity market |
| France | Medium | French | Translate + adapt keywords | Q4 2026 | Smaller market but high engagement possible |

### Per-Market Keywords

**Japan**:
- Primary: 瞑想 (meditation), 睡眠 (sleep), マインドフルネス (mindfulness)
- Secondary: ストレス軽減, 不安緩和, リラックス

**Germany**:
- Primary: Meditation, Schlaf, Achtsamkeit (mindfulness)
- Secondary: Stressabbau, Entspannung, Schlafqualität

**Brazil**:
- Primary: Meditação, Sono, Mindfulness
- Secondary: Alívio de stress, Ansiedade, Relaxamento

---

## Ratings & Reviews Strategy

**Current Rating**: [X.X stars] across [Y] reviews

**Target Rating**: 4.5+ (excellent for featured placement)

**Actions**:
1. **In-app Review Prompt**: Native prompt after the user completes their first meditation (a moment of value; never on first launch, never rewarded)
   - Timing: After user presses "Complete"
   - Messaging: "Enjoying your meditation? Rate us!" (positive, not forced)
   - Frequency: Once per month max (don't annoy users)

2. **Review Response Strategy**:
   - Respond to negative reviews within 48 hours
   - Address specific complaints (crash reports, feature requests)
   - Highlight fixes in release notes

3. **Social Proof**:
   - Quote top reviews in App Store screenshots (if allowed)
   - Mention user count and rating in descriptions

---

## Localized Pricing (recommendation only — omit if the app sells nothing)

| Tier | Markets | Proposed price (% of base) | Evidence |
|------|---------|----------------------------|----------|
| 1 | US, UK, Germany | 100% | High purchasing power; local competitors price near the base |
| 2 | Brazil | 60% | Lower purchasing power; local competitors priced lower |

- Per-user cost check: [a lower tier stays profitable, or keep the base price there and say why; unknown → mark the section "unvalidated: confirm costs before applying"]
- Applied by the user in App Store Connect / Google Play Console — this skill does not change prices

---

## Measurement Plan

| Keyword | Store | Baseline Rank (Phase 1) | Cadence |
|---------|-------|-------------------------|---------|
| sleep meditation | iOS | unranked | weekly, 6-8 weeks |

- Outcome metrics: impressions → product page views → downloads → paid conversions
- Change order: cycle 1 ships the indexed metadata set (title, subtitle, keywords) for the locales the approved plan covers; then one lever per cycle: screenshots, new localizations, pricing

---

## Timeline & Priorities

| Priority | Action | Impact | Effort | Timeline |
|----------|--------|--------|--------|----------|
| **P0** | Update iOS name + subtitle + keywords (ships with the next app version submission) | Very High | Low | Week 1 |
| **P0** | Update Android title + short description (takes 30 min in Google Play Console) | Very High | Low | Week 1 |
| **P1** | Refresh app icon for better small-size clarity | High | Medium | Week 2-3 |
| **P1** | Create localization keywords for Japan, Germany | High | Medium | Week 2-4 |
| **P2** | Record preview video highlighting meditation experience | Medium | High | Week 3-4 |
| **P2** | Implement in-app review prompt (developer time required) | Medium | Medium | Week 2-3 |

---

## Expected Impact Summary

**Conservative Estimate** (first 3 months):
- +30% visibility for primary keywords (meditation, sleep)
- +15% conversion rate improvement (from better value prop copy)
- +10% installs overall

**Optimistic Estimate** (with localization + visuals):
- +50% visibility for primary keywords
- +25% conversion rate improvement
- +30% installs overall

**Long-term** (6+ months with ongoing optimization):
- Establish as top-3 app in meditation category
- Strong presence in Japan, Germany secondary markets
- Consistent 4.5+ rating

---

## Next Steps

This plan is ready for **Phase 3: Policy Compliance Check**.

All proposed metadata will be validated against Apple App Store and Google Play Store policies before final approval.
```

## Output Format

Markdown file at the specified output path, ready for the compliance-checker agent to validate.

## Tips

- Keyword research should be as specific as possible. If you can't estimate search volume, use relative terms (high/medium/low) and note the limitation.
- Android description is much longer (4000 chars) — use it to rank for long-tail keywords that don't fit iOS keywords field.
- Localization should be market-aware, not just translation. Different markets have different search behavior and user preferences.
- Visual asset recommendations should be specific (what caption text to use, what to emphasize) — the implementer will need to execute on these.
