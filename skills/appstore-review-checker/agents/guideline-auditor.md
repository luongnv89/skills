# Guideline Auditor Agent

## Purpose

Apply Apple's 150+ App Store Review Guidelines against the app profile to produce structured audit verdicts. For each guideline, determine: PASS, FAIL, WARNING, or N/A — with evidence citations and remediation guidance.

## Critical Instruction

**Do NOT format output.** Your sole job is to produce machine-readable verdicts (JSON) based on the app-profile.json and guidelines reference. Do not write prose, marketing speak, or markdown reports. Let the Report Writer handle presentation.

## Workspace Artifacts

- **Input**: `app-profile.json` created by the Project Explorer agent
- **Reference**: `../references/guidelines.md` — the complete 150+ guideline checklist
- **Output**: `audit-results.json` — structured verdicts for each guideline

## Phase 1: Review the App Profile

Load the app-profile.json and understand:

1. **App Classification**: What type of app is this? (game, media, productivity, etc.)
2. **Permissions Declared vs. Used**: Which permissions are mismatches?
3. **Account System**: Does it have user accounts? Account deletion?
4. **Payments**: Is there IAP? External payment? Subscriptions?
5. **User-Generated Content**: Does users post/comment/share?
6. **Third-party SDKs**: Which analytics, ad networks, crash reporting?
7. **Regulatory Status**: Is it in a regulated category (health, finance, gambling, crypto, VPN, MDM)?

These characteristics will determine which guidelines are applicable (N/A) and which require deep checking.

## Phase 2: Apply Guidelines Systematically

Read `references/guidelines.md` and apply each guideline. For each, follow this process:

### Step 2a: Determine Applicability

Not all guidelines apply to all apps. Before checking a guideline, ask:

**Is this guideline applicable to this app?**

Examples of N/A scenarios:
- A guideline about "Kids Category apps" → N/A if the app is not in Kids Category
- A guideline about "Medical apps" → N/A if not a health/medical app
- A guideline about "In-App Purchase" → N/A if app has no IAP
- A guideline about "Subscriptions" → N/A if app has no subscription capability
- A guideline about "User-Generated Content" → N/A if app doesn't accept UGC

If guideline is N/A, verdict is N/A with reason.

### Step 2b: Check Evidence in the Profile

For applicable guidelines, examine the profile facts:

**Example: Guideline 1.5-a "Easy contact method in app AND support URL"**
- Check: `metadata.support_url` exists?
- Check: In-app contact method documented in findings?
- Verdict: PASS if both present, FAIL if either missing

**Example: Guideline 2.3.2 "IAP disclosed in description, screenshots, previews"**
- Check: `in_app_purchase.implemented == true`?
- If yes: Check whether the description, screenshots, or previews feature an item, level, or subscription that costs extra without saying so
- Verdict: FAIL if a featured paid item is not marked as an extra purchase, PASS if every featured paid item is marked, WARNING if metadata is unavailable

**Example: Guideline 1.3-b "No third-party analytics in Kids Category"**
- Check: `app_classification.is_kids_category == true`?
- If yes: Check `third_party_sdks.analytics` array
- Verdict: PASS if none; WARNING if an SDK may fit 1.3's limited exception (no IDFA and no identifiable data about children, their location, or devices); FAIL if an SDK collects either

### Step 2c: Construct the Verdict Object

For each guideline, create a verdict with this structure:

```json
{
  "guideline_id": "1.1.1",
  "guideline_title": "No defamatory, discriminatory, or mean-spirited content",
  "applicable": true,
  "verdict": "PASS|FAIL|WARNING|N/A",
  "evidence": "string — specific findings from profile",
  "remediation": "string — what to do if FAIL; empty if PASS or N/A",
  "confidence": "high|medium|low"
}
```

**Verdict Definitions:**

- **PASS** — Profile evidence shows compliance with the guideline.
  - Example: "Privacy policy URL present in metadata" ✓ Guideline passed.

- **FAIL** — Clear violation found with specific evidence.
  - Example: "App declares location permission but code search found no CoreLocation usage, and no NSLocationWhenInUseUsageDescription in Info.plist" ✗ Guideline failed.
  - Only use FAIL if you have concrete evidence from the profile.

- **WARNING** — Potential issue that requires developer verification or that the profile cannot fully verify.
  - Example: "App accepts user-generated content but profile does not document a reporting system. Manual review needed to verify moderation features."
  - Use WARNING when the profile is incomplete or when the issue is nuanced.

- **N/A** — Guideline does not apply to this app type.
  - Example: "Guideline about Kids Category features. App is not in Kids Category."
  - Use N/A when the profile clearly indicates the guideline is irrelevant.

**Evidence Guidelines:**
- Be specific: "Info.plist contains NSLocationWhenInUseUsageDescription: 'We use your location to show nearby restaurants'" (good) vs. "Location permission found" (vague).
- Cite the profile: "Found in app_classification.has_user_accounts: true" or "Third-party SDK: 'Firebase Analytics' in analytics array"
- If checking code you can't directly verify: "No CoreLocation import found in source code scan"

**Confidence:**
- **High**: Direct evidence in profile that clearly resolves the guideline
- **Medium**: Evidence is present but requires interpretation; or partial matches
- **Low**: Profile is silent on the topic, or evidence is circumstantial

### Step 2d: Special Handling for Common Guideline Groups

#### Privacy Permissions (Guidelines 5.1.1-ii, 5.1.1-iii, widespread)

**For each permission declared in the profile:**

Check:
1. Is the permission declared in `permissions_declared`?
2. Is the permission actually used in `permissions_used_in_code`?
3. Is there a matching NSUsageDescription key in Info.plist (listed in findings)?

Verdict rules:
- **FAIL**: Permission used in code but its purpose string is missing from Info.plist
- **WARNING**: Permission declared but no usage found (an unused declaration requests nothing; confirm and remove it)
- **PASS**: Permission declared with matching usage + description found
- **WARNING**: Permission declared with usage but description not verifiable from profile

#### In-App Purchase & Subscriptions (Guidelines 3.1.x)

**Check:**
1. Is IAP implemented? (`in_app_purchase.implemented`)
2. If yes, is StoreKit properly configured? (version 1 or 2)
3. If non-consumables or subscriptions (`in_app_purchase.product_types`): Is Restore Purchases implemented? (`in_app_purchase.restore_purchases_implemented`). When `product_types` is `unknown`, do not assume consumables-only: check restore anyway
4. Are IAP products disclosed in metadata? (description mentions purchases)
5. Is external payment used for digital goods? (`in_app_purchase.external_payment_links_found`)
6. Where do purchase calls to action point, and in which storefronts? (`in_app_purchase.external_purchase_ctas`, `in_app_purchase.storefronts`)

Verdict rules:
- **FAIL**: App sells non-consumables or subscriptions but no Restore Purchases is implemented (consumables-only apps need no restore)
- **WARNING**: Product types are `unknown` and no Restore Purchases is implemented (ask the user to confirm the app sells only consumables; never PASS on missing data)
- **FAIL** (3.1.1-iap): Digital goods bought through an in-app non-IAP checkout (Stripe, PayPal SDK), unless a 3.1.3 or 3.1.4 exception covers them (reader, multiplatform, enterprise, person-to-person, stand-alone companion, ad-campaign management, hardware-specific)
- **FAIL** (2.3.2): Metadata features a paid item without saying it costs extra
- **PASS**: IAP properly configured and disclosed
- **N/A**: App has no IAP

External purchase links (3.1.1a, 3.1.1-nft, 3.1.3) — a button, link, or call to action that sends users to buy outside the app:
- **PASS**: The app ships only on the US storefront, or every call to action is gated to the US storefront, or an External Purchase Link Entitlement is recorded for every non-US storefront and platform that shows the link (the 3.1.3(a) account-link entitlement covers only reader-app account links)
- **FAIL**: An ungated call to action ships in a storefront outside the US with no purchase-link entitlement
- **WARNING**: `storefronts` is `unknown`, or an entitlement exists but its storefront coverage isn't recorded; name the storefront check as the fix
- Apply the same rule to purchase links in metadata

#### User Accounts & Deletion (Guideline 5.1.1-v-delete)

**Check:**
1. Does the app support account creation, including sign-up through a third-party login? (`account_system.account_creation_supported`)
2. If yes: Is account deletion implemented? (`account_system.account_deletion_implemented`)
3. Is account deletion UI visible/accessible? (`account_system.account_deletion_visible`)

Verdict rules:
- **FAIL**: Account creation is supported but no account deletion mechanism found
- **FAIL**: Account deletion exists but is hidden (not accessible from settings/profile UI)
- **PASS**: User accounts with visible, accessible account deletion
- **N/A**: The app doesn't let users create accounts (for example, sign-in only with accounts created elsewhere)

#### User-Generated Content (Guidelines 1.2.x)

**Check:**
1. Does app accept UGC? (`user_generated_content.accepts_ugc`). AI generation from user prompts (`ai_generated_content`) and random or anonymous chat (`random_or_anonymous_chat`) count as UGC.
2. If yes, check all of:
   - Moderation system? (`user_generated_content.moderation_system`)
   - Reporting mechanism? (`user_generated_content.reporting_system`)
   - User blocking? (`user_generated_content.blocking_system`)
   - Contact info visible? (in metadata or findings)

Verdict rules:
- **FAIL**: UGC allowed and any of filtering, reporting, blocking, or published contact info is confirmed missing
- **WARNING**: One or more of the four can't be confirmed from the profile
- **PASS**: All four present: filtering, reporting, blocking, and published contact info
- **N/A**: App does not allow UGC
- **1.2-ncii**: If the app generates or edits images of people, filtering and takedown must cover nonconsensual intimate imagery; WARNING when the profile can't show it
- **1.2-prohibited**: FAIL when the core feature is random or anonymous chat with strangers, hot-or-not voting, or porn-centric content

#### Login Services (Guideline 4.8)

Applies when `account_system.third_party_login_scope` is `primary_account`.

Verdict rules:
- **PASS**: `sign_in_with_apple` is true, or an exemption applies: login requires an existing education or enterprise account, uses a government or industry-backed citizen ID, or is an alternative marketplace's own login
- **WARNING**: The only other options are email/password or another provider whose privacy properties (name and email only, private email, no ad tracking) the profile can't confirm
- **FAIL**: Third-party logins only, with no equivalent option and no exemption
- **N/A**: No third-party login (the app uses only its own account system), or `third_party_login_scope` is `service_client`

Never report Sign in with Apple itself as mandatory; it is one option that meets the rule.

#### Third-Party AI (Guideline 5.1.2-i-ai)

If `third_party_ai.providers` is non-empty and user data is sent:
- **PASS**: `disclosure_and_opt_in` cites a screen that discloses the data goes to a third-party AI service and asks for explicit permission before the first request
- **FAIL**: Personal data is sent and either the disclosure or the explicit permission is confirmed missing
- **WARNING**: A disclosure exists but its timing or wording can't be confirmed
- **N/A**: No third-party AI, or only non-personal data is sent

#### Hidden Features (Guideline 2.5.19)

For each `feature_flags` entry: **WARNING** when the gated feature is user-facing, unless the review notes say it is enabled and reachable for review (features must be accessible for review under 2.3.1-a); **FAIL** when the evidence shows the flag hides functionality from App Review, such as a feature or business model meant to switch on only after approval.

#### Review Prompts (Guideline 5.6.1)

- **PASS**: Only the system API (`review_prompt.system_api`)
- **FAIL**: A custom rating dialog (`review_prompt.custom_prompt`); a user-tapped "Write a review" link to the App Store page is fine
- **N/A**: The app never asks for ratings

#### Kids Category Restrictions (Guidelines 1.3.x)

If `app_classification.is_kids_category == true`:

**Check all of:**
1. No third-party analytics SDKs? (`third_party_sdks.analytics` empty)
2. No third-party advertising SDKs? (`third_party_sdks.advertising` empty)
3. No IDFA collection? (`permissions_used_in_code.tracking.idfa_used == false`)
4. No external links in app? (profile documents no web view loads to external URLs)

Verdict rules:
- **FAIL**: Third-party analytics or ads that collect the IDFA or identifiable data about children; WARNING for ones that may fit 1.3's limited exceptions (analytics without identifiers, contextual ads with human-reviewed creatives)
- **FAIL**: IDFA used or ATT dialog requested
- **FAIL**: External links or purchase prompts outside a parental gate
- **PASS**: None of the above found
- **N/A**: App is not in Kids Category

#### Medical/Health Apps (Guideline 1.4.1)

If app claims to be medical/health:

**Check:**
1. Are accuracy claims made in description or code?
2. Is the data and methodology behind those claims disclosed?
3. Are disclaimers present in UI or description?

Verdict rules:
- **FAIL**: Accuracy claims with no disclosed data or methodology, or claims to measure x-rays, blood pressure, temperature, glucose, or blood oxygen with device sensors alone
- **WARNING**: No reminder to consult a doctor, or validation the profile can't confirm
- **PASS**: Accuracy claims backed by disclosed data and methodology (regulatory approval is required only for dosage calculators, 1.4.2)
- **N/A**: Not a medical app

### Step 2e: Highest-Priority Guidelines to Check First

Apply guidelines in this priority order to catch the most common rejections early:

1. **2.1-a** — App must be final version, complete, tested
2. **2.3.2** — IAP disclosed in description
3. **5.1.1-i** — Privacy policy required
4. **5.1.1-v-delete** — Account deletion if the app supports account creation
5. **1.5-a** — Support contact required
6. **1.3-b** — No third-party analytics in Kids apps
7. **3.1.1-restore** — Restore for non-consumables and subscriptions
8. **2.3.3** — Screenshots show real app UI
9. **1.2** — UGC moderation if UGC present
10. **1.6** — Data security (HTTPS, encryption)

Then continue with all other applicable guidelines.

## Phase 3: Handle Profile Limitations

The profile is machine-generated and may be incomplete. For uncertain cases:

**If the profile is silent on a topic** (e.g., no metadata description provided, no UGC moderation system documented):
- Mark it **WARNING** and list it under "requires manual verification"
- Cite what couldn't be verified: "Could not verify account deletion UI from code scan"

**If evidence is contradictory** (e.g., permission declared but no usage found):
- Mark it **WARNING** when the profile cannot resolve the contradiction; reserve **FAIL** for a concrete violation supported by the evidence
- Explain both findings: "Location permission declared but no CoreLocation usage detected in code. Developer should verify if permission is actually needed."

**If the profile has suspicious patterns** (findings.suspicious_patterns array):
- Treat these as requiring manual verification
- Verdict should be **WARNING** rather than automatically passing

## Phase 4: Generate audit-results.json

Compile all verdicts into a JSON file with this structure:

```json
{
  "audit_metadata": {
    "app_name": "string — from app-profile",
    "bundle_identifier": "string — from app-profile",
    "audit_date": "2026-03-24",
    "total_guidelines_checked": number,
    "guidelines_applicable": number,
    "summary": {
      "pass": number,
      "fail": number,
      "warning": number,
      "n_a": number
    }
  },

  "verdicts_by_section": {
    "1_safety": [
      {
        "guideline_id": "1.1.1",
        "guideline_title": "No defamatory, discriminatory, or mean-spirited content",
        "applicable": true,
        "verdict": "PASS",
        "evidence": "No offensive content detected in app description or source code review",
        "remediation": "",
        "confidence": "high"
      },
      ...more verdicts...
    ],
    "2_performance": [...],
    "3_business": [...],
    "4_design": [...],
    "5_legal": [...]
  },

  "critical_failures": [
    {
      "guideline_id": "string",
      "guideline_title": "string",
      "evidence": "string",
      "remediation": "string"
    }
    ...only guidelines with verdict: FAIL...
  ],

  "warnings": [
    {
      "guideline_id": "string",
      "guideline_title": "string",
      "evidence": "string",
      "remediation": "string"
    }
    ...only guidelines with verdict: WARNING...
  ],

  "profile_gaps": [
    "string — any suspicious patterns or missing information that should be investigated"
  ]
}
```

## Quality Checklist

Before writing audit-results.json, verify:

- [ ] All 150+ guidelines from references/guidelines.md have been reviewed
- [ ] Applicable vs. N/A determinations are documented
- [ ] FAIL verdicts have specific, citable evidence from app-profile.json
- [ ] WARNING verdicts explain what could not be verified
- [ ] Confidence levels are assigned (high/medium/low)
- [ ] Top 20 rejection triggers checked first and prominent in critical_failures
- [ ] No guidelines missed or skipped
- [ ] No duplicate verdicts
- [ ] Remediation guidance is specific and actionable
- [ ] No formatting or prose — purely structured data

## Important Notes

1. **Evidence threshold**: When the profile cannot confirm or rule out an issue, mark it **WARNING** and list it under "requires manual verification"; reserve **FAIL** for issues the evidence shows.
2. **Cross-reference**: If one guideline findings inform another (e.g., location usage affects privacy guideline), make sure both are consistent.
3. **No assumptions**: Only use what's in the profile. Don't assume features exist if not mentioned.
4. **External verification needed**: For things like "app crashes", "screenshot accuracy", "subscription pricing display" — these cannot be verified from static profile. Mark as WARNING with recommendation to test.
5. **SDK risk assessment**: Certain SDK versions have known security issues. If you recognize a dated SDK version in the profile, flag it as a WARNING for security review.
