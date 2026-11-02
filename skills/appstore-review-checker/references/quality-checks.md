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
- [ ] **Final Report produced** — The run ends with the four-line Final Report (`references/final-report.md`), and its status follows that file's status table.

Not applicable items: in a metadata-only or no-source audit, the code-level items are not applicable once each skipped code-level guideline is marked `N/A (no source)`. When the user declines every fix, the Phase 4 items are not applicable.

These items check correctness only. Also review the Final Report against the four reader checks in `references/final-report.md` (*Reader checks*).

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
- Paywall copy, prices, and offers served remotely (RevenueCat Paywalls, Superwall, Adapty, a homegrown config endpoint)
- What an OTA update SDK will push after approval

## Common Patterns to Watch For

### Privacy Red Flags
- `NSCameraUsageDescription` missing but camera framework imported
- `ATTrackingManager` not used but ad SDKs present (Facebook, Google Ads, AdMob)
- `NSUserTrackingUsageDescription` missing with tracking SDKs
- No privacy policy URL in project or metadata
- Account creation exists but no account deletion flow
- User data sent to a third-party AI API with no disclosure and opt-in (5.1.2-i-ai)
- Attribution SDKs (MMPs such as AppsFlyer, Adjust, Branch, Singular, Kochava) or ad SDKs sending data with no ATT prompt, or data the privacy policy doesn't name (5.1.2-i, 5.1.1-i-content)
- A pre-permission screen whose button says "Allow", "Enable", or "Grant access" instead of "Continue" or "Next" (5.1.1-iv)
- Purpose strings that don't say which feature uses the data ("This app needs camera access") (5.1.1-ii)

### IAP Red Flags
- `StoreKit` imported but no restore purchases mechanism
- Subscription without clear terms display before purchase
- Digital goods bought through an in-app non-IAP checkout (Stripe, PayPal)
- External purchase links shown outside the US storefront without an entitlement (3.1.1a)
- Loot boxes or gacha mechanics without probability disclosure

### Paywall Red Flags
- Promised results or outcomes ("Get rid of acne in 7 days", "Lose 10 kg") (3.1.2-scam)
- Hardcoded social proof: user counts, star ratings, or testimonials as string literals (3.1.2-scam)
- Countdown timers, "limited time" banners, or discounts produced by `Int.random`, a timer, or a reset on every launch (3.1.2-scam)
- Abandoned-checkout or exit offers (shown on dismissing the paywall) that misstate the price or the deal (3.1.2-scam)
- The billed price smaller or fainter than a per-day or per-week breakdown, or missing (3.1.2-disclosure)
- No Terms of Use (EULA) or Privacy Policy links on the paywall itself (3.1.2-disclosure)

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
- Third-party login (Facebook, Google, etc.) with no equivalent privacy-focused option such as Sign in with Apple (4.8)
- Multiple targets producing nearly identical apps (spam/copycat risk)
- Remote feature flags gating features absent from the review notes (2.5.19)
- Custom rating dialog instead of the system review prompt (5.6.1)
- "Coming soon" labels, disabled teaser buttons, or placeholder screens (2.1-a)
- An OTA update SDK (expo-updates, CodePush, Shorebird, Capgo, Hot Updater) that could change features after approval (2.5.2, 2.5.19)
- Promotional or marketing content in a Live Activity (4.5.3), or marketing pushes with no in-app consent and opt-out (4.5.4)
- Interstitial ads so frequent they interrupt core use, such as after every tap or every few seconds (2.5.18)
- An icon or name resembling a large company's brand (Google, Meta, OpenAI) (4.1-c, 5.2.1)
