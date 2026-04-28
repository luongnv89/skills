# Quality Checks: Acceptance Criteria, Step Reports, Static-Audit Limits, Common Red Flags

## Acceptance Criteria

The skill run is considered successful when all of the following are verifiable:

- [ ] **`APPSTORE_AUDIT.md` created** — The report file exists at the project root (or a clearly specified path) after the skill completes.
- [ ] **Overall verdict present** — The report begins with one of: `LIKELY PASS`, `AT RISK`, or `LIKELY REJECT`.
- [ ] **All Top 20 rejection triggers evaluated** — Each trigger from the guidelines reference has a verdict (PASS, FAIL, WARNING, or N/A). No trigger is silently skipped.
- [ ] **Every FAIL includes evidence** — Each Critical Issue entry names a specific file, line number, or config key where the violation was found. No vague "might have issues" language.
- [ ] **Every FAIL includes a concrete fix** — Each fix is actionable: a specific API change, a missing Info.plist key, a required UI element — not just "fix the issue."
- [ ] **Pre-submission checklist present** — The report ends with a numbered checklist of required actions before submitting.
- [ ] **Scope of static analysis declared** — The report includes a section or note listing items that require manual verification (runtime behavior, screenshot accuracy, backend API behavior, etc.).
- [ ] **Phase 4 (Fixer) conditional** — The fixer agent is only offered after the user reviews the report and explicitly approves which FAILs to fix. No code changes are made automatically.
- [ ] **No entitlements modified** — The fixer agent does not touch `.entitlements` files or App Store Connect configuration.

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Understand the App (Phase 1)** — checks: `App understanding`, `Project config read`, `Code patterns identified`, `App category classified`

**Phase: Run the Audit (Phase 2)** — checks: `Guideline coverage`, `Evidence specificity`, `Top 20 triggers checked`, `Entitlements cross-referenced`

**Phase: Generate the Report (Phase 3)** — checks: `Report completeness`, `Verdict accuracy`, `Fix suggestions`, `Pre-submission checklist present`

**Phase: Offer to Fix (Phase 4)** — checks: `Fix scope confirmed`, `Code changes applied`, `Metadata guidance provided`, `No entitlements modified`

## Things You Cannot Check From Code Alone

Be transparent about the limits of a static audit. Flag these as "requires manual verification":

- App crashes or performance issues at runtime
- Actual screenshot accuracy (do they match real app UI?)
- Third-party content licensing agreements
- Backend API behavior and data handling
- App Tracking Transparency dialog appearing at the right time
- Real-device hardware compatibility
- Actual IPv6 network behavior
- Subscription flow user experience
- Content moderation system effectiveness

## Common Patterns to Watch For

### Privacy Red Flags
- `NSCameraUsageDescription` missing but camera framework imported
- `ATTrackingManager` not used but ad SDKs present (Facebook, Google Ads, AdMob)
- `NSUserTrackingUsageDescription` missing with tracking SDKs
- No privacy policy URL in project or metadata
- Account creation exists but no account deletion flow

### IAP Red Flags
- `StoreKit` imported but no restore purchases mechanism
- Subscription without clear terms display before purchase
- Digital goods sold without Apple IAP (external payment links)
- Loot boxes or gacha mechanics without probability disclosure

### Metadata Red Flags
- Keywords containing "free", "best", "#1", "top", "sale"
- Competitor names in keywords or description
- "Android", "Google Play" mentioned anywhere in metadata
- "For Kids" used outside Kids Category
- Screenshots that are just marketing graphics without real app UI
- Description promising features that don't exist in the code

### Design Red Flags
- `UIWebView` usage (deprecated, should be `WKWebView`)
- App is essentially a web wrapper with no native functionality
- Sign in with Apple not implemented alongside third-party login (Facebook, Google, etc.)
- Multiple targets producing nearly identical apps (spam/copycat risk)
