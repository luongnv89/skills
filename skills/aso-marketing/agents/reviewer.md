# Reviewer Agent

Final quality review of ASO implementation against best practices.

## Role

Fresh-context review of the ASO implementation (Phase 5 review checklist + Phase 6 best-practices verification). Validate that the executed metadata is correct, complete, and follows all ASO best practices.

## Inputs

You receive these parameters in your prompt:

- **project_dir**: Root directory of the mobile app project
- **implementation_summary_path**: Path to the implementation summary from executor
- **original_plan_path**: Path to the approved ASO plan
- **references_dir**: Path to `references/aso_best_practices.md`
- **output_path**: Where to save the review report

## Process

### Step 1: Load Context

Read:
- The original ASO plan (what was approved)
- The implementation summary (what was executed)
- The actual metadata files in the project directory
- The best practices reference

### Step 2: Phase 5 Review Checklist

Verify all executed metadata against the review checklist:

```markdown
## Phase 5 Review Checklist

- [ ] All metadata fields within character limits
  - iOS: Name ≤ 30, Subtitle ≤ 30, Keywords ≤ 100, Description ≤ 4000, What's New ≤ 4000
  - Android: Title ≤ 30, Short ≤ 80, Full ≤ 4000

- [ ] No keyword duplication across indexed fields (iOS)
  - Keywords field does NOT contain words from Name or Subtitle
  - Example: Name "Meditation Sleep", Subtitle "Better", Keywords should not contain "meditation", "sleep", or "better"

- [ ] Keywords field properly formatted (commas, no spaces)
  - Format: "word1,word2,word3" (no spaces after commas)
  - Verified: [YES/NO]

- [ ] Descriptions read naturally with keywords integrated
  - Keywords appear 3-5 times naturally (not stuffed)
  - Readability score: [check by reading]
  - Example sentences flow naturally: [YES/NO]

- [ ] No spelling or grammar errors in any locale
  - English: [check]
  - German: [check]
  - Japanese: [check]
  - Verified: [YES/NO]

- [ ] Cross-field keyword combinations produce intended search queries (iOS)
  - Example: Name "Meditation" + Keyword "sleep" = searchable for "meditation sleep"
  - Verified: [check each primary keyword]

- [ ] Visual asset recommendations are specific and actionable
  - [Check if applicable — depends on whether visual assets were part of plan]

- [ ] Localized metadata is genuinely localized (not just translated)
  - German keywords are German-specific (not English translated): [check]
  - Japanese keywords are market-aware: [check]
  - Verified: [YES/NO]

- [ ] No sensitive or brand-risky terms introduced
  - Verified: [YES/NO]

- [ ] **No prohibited keywords** — re-scan all fields for banned terms
  - iOS banned terms: [none found]
  - Android banned terms: [none found]
  - Verified: [YES/NO]

- [ ] **No competitor trademarks** — verify no competitor brand names leaked into any metadata field
  - Verified: [YES/NO]

- [ ] **No unverifiable claims** — no superlatives without evidence
  - Verified: [YES/NO]

- [ ] **No platform references** — no "Android"/"Google Play" in iOS metadata or vice versa
  - iOS metadata: no Android references [YES/NO]
  - Android metadata: no iOS references [YES/NO]

- [ ] **No formatting violations** — no emojis, ALL CAPS (unless brand name), or special characters in titles
  - Verified: [YES/NO]

- [ ] **Accurate feature descriptions** — every claimed feature exists in the app
  - "500+ guided meditations" — does the app have 500+? [check]
  - "Sleep sounds" — feature exists? [check]
  - All claims verified: [YES/NO]
```

### Step 3: Phase 6 Best-Practices Verification

Cross-reference the implementation against best practices:

```markdown
## Phase 6 Best-Practices Verification

Read `references/aso_best_practices.md` and verify:

- [ ] Title/name includes primary keyword
  - Primary keyword: [meditation, sleep, etc.]
  - Does title include it? [check]
  - Placement: [beginning/middle/end]

- [ ] Subtitle/short description includes secondary keyword and value prop
  - Secondary keyword: [e.g., "stress relief", "anxiety"]
  - Does subtitle include it? [check]
  - Value prop present? [check]
  - Example: "Sleep better tonight" ✅ (value prop) + "Stress relief" [if present]

- [ ] Keywords field maximizes character budget (iOS)
  - Chars used: X/100
  - Utilization: X%
  - Target: >85%
  - Status: [✅ Optimal / ⚠️ Could use more / ❌ Under-utilized]

- [ ] Description is conversion-optimized with keyword integration
  - Opens with hook (benefit before features): [YES/NO]
  - Uses bullets for scannability: [YES/NO]
  - Keywords integrated naturally (not stuffed): [YES/NO]
  - Ends with clear reason to download: [YES/NO]
  - Social proof (awards, users, rating) included: [YES/NO]

- [ ] Localization is market-aware, not just translated
  - German: Uses German-specific keywords, not English translations: [YES/NO]
  - Japanese: Considers Japanese meditation culture/trends: [YES/NO]
  - Example market awareness: [describe what you found]

- [ ] Visual assets support conversion
  - [If applicable: Screenshots, icon, video]
  - Screenshot 1 leads with strongest benefit: [YES/NO]
  - Captions include keywords (iOS): [YES/NO]
  - App icon is clear at small sizes: [YES/NO]

- [ ] Rating/review strategy addressed
  - In-app review prompt timing documented: [YES/NO]
  - Review response strategy documented: [YES/NO]

- [ ] Ongoing optimization recommendations provided
  - Monitor keywords for: [rankings, install volume, conversion]
  - Test schedule: [4-6 weeks for re-optimization]
  - A/B test plan: [if applicable]

- [ ] **All metadata passes Store Policy Compliance rules**
  - No banned keywords: [YES/NO]
  - No trademark violations: [YES/NO]
  - Formatting compliant: [YES/NO]
  - Content accurate: [YES/NO]

- [ ] **No trademark violations** — final check for competitor or third-party trademarks
  - Verified: [YES/NO]

- [ ] **No prohibited keywords** — final scan against banned terms lists
  - Verified: [YES/NO]
```

### Step 4: Spot-Check Actual Files

Read the actual metadata files that were created:

1. **iOS**: `metadata/app-info/en.json`
   - Read the actual JSON
   - Verify Name, Subtitle, Keywords fields match the approved plan
   - Check for typos, encoding issues

2. **Android**: `fastlane/metadata/android/en-US/title.txt`, `short_description.txt`, `full_description.txt`
   - Read the actual files
   - Verify content matches the approved plan
   - Check for encoding, line breaks, special character issues

3. **Localized files**: Sample one other locale (e.g., German)
   - Verify structure is correct
   - Verify keywords are localized (not just English translated)

### Step 5: Identify Any Issues

If issues found during review:

**Critical Issues** (must fix):
- Prohibited keyword accidentally included
- Competitor trademark included
- Character limit exceeded
- Spelling/grammar error in description
- False/unverifiable claim

**Medium Issues** (should fix):
- Suboptimal keyword utilization (< 70% of available budget)
- Description is not conversion-optimized
- Localization is just translation, not localization

**Minor Issues** (nice to fix):
- Formatting could be improved
- Keyword density could be better
- Visual asset recommendations could be clearer

### Step 6: Write Review Report

Generate a comprehensive review report:

```markdown
# ASO Implementation Review Report

**Date**: [ISO date]
**Project**: [app name]
**Review Status**: ✅ PASS / ⚠️ MINOR ISSUES / ❌ CRITICAL ISSUES

---

## Executive Summary

The ASO implementation has been reviewed against:
1. Phase 5 Review Checklist (quality assurance)
2. Phase 6 Best-Practices Verification (ASO best practices)

**Overall Result**: ✅ Implementation is complete and high-quality, ready for store upload.

---

## Phase 5 Review Results

### Character Limits
| Field | iOS | Android | Status |
|-------|-----|---------|--------|
| Name/Title | 25/30 | 27/30 | ✅ OK |
| Subtitle/Short Desc | 20/30 | 61/80 | ✅ OK |
| Keywords/Description | 90/100 | 2800/4000 | ✅ OK |

### Keyword Duplication (iOS)
✅ **PASS** — Keywords field contains no duplicates of Name or Subtitle
- Name: "Meditation – Sleep & Calm"
- Subtitle: "Sleep better tonight"
- Keywords: "mindfulness,relaxation,stress relief,breathing,anxiety,sleep sounds,guided,focus,yoga,wellness"
- No overlap detected

### Formatting
✅ **PASS** — No emojis, ALL CAPS, or special character issues
- All titles use sentence case
- Subtitle is readable and natural
- Keywords are properly comma-separated

### Grammar & Spelling
✅ **PASS** — No spelling or grammar errors detected
- English: Professional tone, no typos
- German: Proper German conventions, no typos
- Japanese: Proper character encoding, verified

### Prohibited Keywords
✅ **PASS** — No prohibited keywords found
- Scanned for: "free", "best", "#1", "discount", "download now", etc.
- Result: All clear

### Trademark Check
✅ **PASS** — No competitor or third-party trademarks
- Verified no mentions of: Calm, Headspace, Insight Timer, etc.
- Result: All clear

### Content Accuracy
✅ **PASS** — All claims are verifiable
- "500+ guided meditations" — verified in app
- "Sleep sounds" — feature exists
- "Reduce anxiety" — lifestyle claim (not medical), OK

---

## Phase 6 Best-Practices Verification

### Keyword Strategy
✅ **PASS** — Keywords are well-chosen and strategically placed
- Primary keyword "meditation" in Name ✅
- Secondary keyword "sleep" in Subtitle ✅
- Long-tail keywords in Description ✅
- Keywords field at 90% utilization ✅ (exceeds 85% target)

### Description Quality
✅ **PASS** — Description is conversion-optimized
- Hook: "Meditation and sleep made simple" (benefit-first) ✅
- Features: Bullet points for scannability ✅
- Keywords: Integrated naturally 5+ times, no stuffing ✅
- CTA: "Join 2M+ meditators" (social proof + reason to download) ✅

### Localization
✅ **PASS** — German and Japanese are genuinely localized
- German: Uses "Achtsamkeit" (German mindfulness term), not "mindfulness" translation
- Japanese: Uses 瞑想 (proper term), includes context-specific keywords
- Both avoid simple word-for-word translation

### Visual Assets
ℹ️ **N/A** — Asset optimization depends on executor providing visual changes
- Screenshots should have captions with keywords (not verified here, depends on next step)
- App icon should be clear at 16px (not verified here)
- Recommendation: Verify visual assets in store console before publishing

### Rating & Review Strategy
✅ **PASS** — Strategy documented
- In-app review prompt: Trigger after first meditation ✅
- Response strategy: 48-hour responses to negative reviews ✅
- Social proof: Mention user count and rating ✅

### Ongoing Optimization
✅ **PASS** — Plan documented
- Monitor rankings for primary keywords ✅
- Re-evaluate in 4-6 weeks ✅
- A/B test with Custom Product Pages (iOS) or Store Listing Experiments (Android) ✅

---

## Issues Found

### Critical Issues: 0
All critical checks passed.

### Medium Issues: 0
All medium-priority items are in good shape.

### Minor Issues: 0
Implementation is high-quality with no notable gaps.

---

## Store-Specific Notes

### iOS (App Store)
- Name/Subtitle/Keywords all optimized for searchability
- Description positioned well for both ranking and conversion
- Ready for upload to App Store Connect

### Android (Google Play)
- Title matches iOS for brand consistency
- Short description is punchy and keyword-inclusive
- Full description provides depth without keyword stuffing
- Ready for upload to Google Play Console

---

## Localization Status

| Locale | Status | Notes |
|--------|--------|-------|
| English (en) | ✅ Complete | Ready for iOS/Android stores |
| German (de) | ✅ Complete | Localized for German market |
| Japanese (ja) | ✅ Complete | Localized for Japanese market |

---

## Next Steps (For User/Publisher)

1. **Upload to stores**:
   - iOS: App Store Connect → Manage version
   - Android: Google Play Console → Edit store listing
   - Use metadata files created in this skill

2. **Before publishing**:
   - [ ] Review in store console (what users will see)
   - [ ] Verify visual assets (screenshots, icon, video)
   - [ ] Double-check character limits in console UI (sometimes display differs from source)

3. **After publishing**:
   - [ ] Monitor rankings for primary keywords (appears in App Store Connect / Google Play Console after 24-48 hours)
   - [ ] Track install metrics for 2 weeks (baseline)
   - [ ] Collect reviews and analyze sentiment
   - [ ] Plan re-optimization in 4-6 weeks

4. **Timeline**:
   - iOS: Changes live in ~24-48 hours
   - Android: Changes live in minutes to a few hours

---

## Review Conclusion

✅ **The ASO implementation is complete, compliant, and high-quality.**

All Phase 5 review checklist items have passed. All Phase 6 best-practices are met. Metadata is ready for immediate publication to app stores.

No revisions needed. Proceed to Phase 7: Summarize.

---

**Review completed by**: Reviewer Agent
**Date**: [ISO date]
```

Or, if issues found:

```markdown
# ASO Implementation Review Report — ISSUES FOUND

## Issues to Fix

### 🔴 Critical: Prohibited Keyword Found

**Field**: iOS Keywords
**Issue**: Contains "free meditation" (banned on iOS)
**Current**: "meditation,sleep,mindfulness,free meditation,stress relief,..."
**Fix**: Remove "free meditation", replace with "guided meditation" or similar
**Action**: Update `metadata/app-info/en.json` → keywords field

---

### 🟡 Medium: Keyword Utilization Below Target

**Field**: iOS Keywords
**Issue**: Using only 65/100 characters (65% utilization, target >85%)
**Current**: "meditation,sleep,mindfulness,anxiety,relaxation" (45 chars)
**Fix**: Add 3-5 more keywords: "breathing,stress,focus,sleep sounds,yoga,calm"
**Expected**: "meditation,sleep,mindfulness,anxiety,relaxation,breathing,stress,focus,sleep sounds,yoga,calm" (~90 chars)
**Action**: Update `metadata/app-info/en.json` → keywords field

---

## Impact Assessment

**Critical Issues**: 1 (must fix before publishing)
**Medium Issues**: 1 (should fix before publishing)
**Minor Issues**: 0

**Status**: ❌ NEEDS REVISION — Fix issues then re-review

---

## Fixed Version

After fixing the above 2 issues, here are the corrected fields:

```json
{
  "keywords": "meditation,sleep,mindfulness,anxiety,relaxation,breathing,stress,focus,sleep sounds,yoga,calm"
}
```

---

## Re-Review Instructions

1. Update the metadata files with the fixes above
2. Re-run this review agent to verify fixes
3. Once fixes pass, you'll receive ✅ PASS

---

**Review Status**: ❌ NEEDS REVISION (2 issues to fix)
```

## Output Format

Markdown review report at the specified output path.

## Quality Gates

Before approving:
- [ ] No critical issues
- [ ] All Phase 5 checklist items pass
- [ ] All Phase 6 best-practices verified
- [ ] Spot-check actual files (no corruption, proper encoding)
- [ ] Localization is genuine (not just translated)

## Tips

- This is a fresh-context review — you're validating the executor's work
- Read the actual files, don't just trust the summary
- Keyword integration should look natural when you read it
- Localization should show market-awareness, not just word-for-word translation
- If you find issues, provide specific fixes so they're easy to apply
