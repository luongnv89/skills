# Phases 4-7: Execute, Review, Verify, Summarize

## Phase 4: Execute the Plan

Once the user approves, implement the changes systematically. Work through the priority list in order.

### 4.1 Metadata Updates

**App Store (iOS):**
- Update `metadata/app-info/{locale}.json` for name, subtitle
- Update `metadata/version/{version}/{locale}.json` for keywords, description, whatsNew, promotionalText
- Validate character limits after each edit
- Cross-check keywords field: no duplicates with title/subtitle, no spaces after commas, single words preferred

**Google Play (Android):**
- Update `title.txt` (max 30 chars)
- Update `short_description.txt` (max 80 chars)
- Update `full_description.txt` (max 4,000 chars)
- Update changelogs if applicable

**Backup-first rule:** Before overwriting any existing metadata file, create a `.bak` copy in the same directory or confirm the user has the file in version control. Do not overwrite or delete files without confirmation.

### 4.2 Keyword Implementation

**Store Policy Compliance (MUST CHECK FIRST):**
- Never use prohibited terms (see `phase-3-compliance.md`)
- Never use competitor brand names or trademarks
- Never use unverifiable superlatives
- Never use pricing/promotional language

**Apple App Store keyword field:**
- Comma-separated, no spaces after commas
- Never duplicate words from title or subtitle
- Prefer single words over phrases
- Aim for 90%+ character utilization
- Consider cross-field combinations

**Google Play keywords:**
- Keywords go naturally into title, short description, and full description
- Repeat important keywords 3-5 times across fields (natural usage)
- Long description should cover related concepts and use cases
- Prioritize readability — Google detects stuffing

### 4.3 Description Optimization

- First 1-3 lines are critical (visible before "Read More")
- Lead with strongest value proposition and clear CTA
- Use bullet points or short paragraphs for scannability
- Naturally integrate target keywords
- Include social proof if available

### 4.4 Localization Execution

- Research locale-specific keywords (not just translations)
- Adapt messaging to local culture and usage patterns
- Verify character limits in target language

### 4.5 Visual Asset Guidance

- **Screenshots:** Recommend ordering, caption text with keywords (OCR-indexed on App Store since June 2025)
- **App Icon:** Assess clarity at small sizes, color contrast
- **Preview Video:** First 3 seconds matter most

---

## Phase 5: Review

### Review Checklist

- [ ] All metadata fields within character limits
- [ ] No keyword duplication across indexed fields (iOS)
- [ ] Keywords field properly formatted
- [ ] Descriptions read naturally
- [ ] No spelling/grammar errors in any locale
- [ ] Cross-field keyword combinations produce intended search queries
- [ ] Visual asset recommendations are specific and actionable
- [ ] Localized metadata is genuinely localized
- [ ] No prohibited keywords (re-scan all fields)
- [ ] No competitor trademarks
- [ ] No unverifiable claims
- [ ] No platform references
- [ ] No formatting violations
- [ ] Accurate feature descriptions

### Self-Audit

Re-run Phase 1 analysis checks on updated metadata to verify improvements.

---

## Phase 6: Verify Against Best Practices

Cross-reference against `references/aso_best_practices.md`:

- [ ] Title/name includes primary keyword
- [ ] Subtitle/short description includes secondary keyword + value prop
- [ ] Keywords field maximizes character budget (iOS)
- [ ] Description is conversion-optimized
- [ ] Localization is market-aware
- [ ] Visual assets support conversion
- [ ] Rating/review strategy addressed
- [ ] All metadata passes Store Policy Compliance rules
- [ ] No trademark violations
- [ ] No prohibited keywords

---

## Phase 7: Summarize

### Summary Report Template

```markdown
## ASO Marketing Summary Report

### Changes Made
| # | Area | Change | Before | After | Expected Impact |

### Metadata Comparison
| Field | Platform | Before | After | Improvement |

### Keyword Strategy Summary
- Total unique keywords targeted
- Primary keywords
- Cross-field combinations enabled
- Keyword field utilization

### Store Policy Compliance
- Prohibited keyword check: PASS
- Trademark check: PASS
- Formatting check: PASS
- Content accuracy check: PASS
- Overall compliance: PASS for [App Store / Google Play / Both]

### Expected Outcomes
- [Outcome 1, 2, ...]

### Next Steps
1. Upload metadata to the store(s)
2. Monitor rankings for target keywords after 1-2 weeks
3. A/B test screenshots and descriptions
4. Re-run this skill in 4-6 weeks

### Files Modified
- [list all files created or modified with paths]
```
