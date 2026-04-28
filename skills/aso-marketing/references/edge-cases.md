# Edge Cases and Platform Notes

## Edge Cases

- **No local metadata files** — App has no `metadata/`, `fastlane/`, or equivalent. Create the canonical directory structure and write optimized files from scratch, then provide upload instructions.
- **Single-platform app** — Skip phases for the irrelevant store. Do not propose a keywords field for Android (it has none).
- **No competitor access** — Skip Phase 1.3; base keyword strategy on app features alone. Flag this gap in the analysis report.
- **Unverifiable keyword volume data** — Proceed with heuristic priority (feature-specific over generic, long-tail over head terms) and note the limitation.
- **Pre-launch app** — No live listing. Skip performance-baseline steps; focus on metadata creation and visual guidance.
- **Metadata policy violation in proposed plan** — Compliance check (Phase 3) catches a prohibited term. Revise the plan silently, replace the violation, re-run compliance, present the corrected plan.
- **Non-English primary locale** — Adapt all metadata templates, character limits, and keyword strategies to the target language.
- **User rejects the plan** — Do not execute. Iterate in Phase 2, then re-run Phase 3 compliance check before presenting the revised plan.

## Platform-Specific Notes

### Apple App Store
- Indexed fields: title, subtitle, keyword field (100 chars)
- Description is NOT indexed but affects conversion
- Screenshot captions are OCR-indexed (since June 2025)
- Custom Product Pages (CPPs) enable audience-specific listings
- Use `asc` CLI tools if available for metadata sync

### Google Play Store
- All text fields are indexed (title, short description, full description)
- No separate keyword field
- Google detects and penalizes keyword stuffing
- Store Listing Experiments enable A/B testing
- Long description supports up to 4,000 chars
- Google considers app quality signals: crash rate, ANR rate, retention

### Both Stores
- App ratings above 4.0 are critical for conversion (90% of featured apps are 4.0+)
- Regular updates signal active maintenance
- Localization should be market-aware, not simple translation
- First 1-3 lines of description must hook the user before "Read More"

## Acceptance Criteria

A run is successful when all are verifiable:

- [ ] **Description ≤40 words with imperative verb** — Frontmatter passes asm eval check.
- [ ] **Analysis report produced** — App Overview, Metadata Status table, Key Findings.
- [ ] **ASO plan covers all required fields** — Title, subtitle/short desc, keywords (iOS), full description, visual recommendations.
- [ ] **Compliance check ran and passed** — Phase 3 report present and PASS before plan shown.
- [ ] **User approval gate respected** — Phase 4 does not begin until explicit approval.
- [ ] **All metadata fields within character limits** — Title ≤30, subtitle ≤30, iOS keywords ≤100, Android short desc ≤80, full desc ≤4000.
- [ ] **No prohibited keywords in any output metadata** — Zero banned terms.
- [ ] **No trademark violations** — No competitor brand names anywhere.
- [ ] **iOS keywords field has no duplicates with title/subtitle**.
- [ ] **Metadata files written** — At least one file or correct directory structure exists.
- [ ] **Summary report produced** — Changes Made, Metadata Comparison, Compliance, Next Steps.

## Step Completion Reports

After each major step, output:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Skill-specific checks per phase

- **Phase: Analyze (Phase 1)** — `Current state analysis`, `Metadata audit complete`, `Competitive landscape identified`, `Baseline documented`
- **Phase: Plan + Compliance (Phases 2-3)** — `Plan completeness`, `Policy compliance`, `Prohibited keyword scan`, `Trademark check`
- **Phase: Execute (Phase 4)** — `Metadata fields updated`, `Character limits respected`, `Keywords correctly formatted`, `Implementation quality`
- **Phase: Review + Verify (Phases 5-6)** — `No policy violations re-introduced`, `Best practices met`, `Cross-field keyword combinations valid`, `Localization market-aware`

## Cross-Skill Integration

Works well combined with:
- **`asc-aso-audit`** — Detailed offline iOS metadata audit
- **`asc-localize-metadata`** — Bulk localization across locales
- **`asc-metadata-sync`** — Sync local metadata with App Store Connect
- **`asc-whats-new-writer`** — Generate engaging release notes
- **`asc-shots-pipeline`** — Automated screenshot capture
- **`seo-ai-optimizer`** — Align ASO and SEO keyword strategies
