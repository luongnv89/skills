# Audit Workflow Detail

## Phase 1: Understand the App

Before checking guidelines, build a mental model of the app. Read these files (in parallel where possible) to understand what kind of app this is:

**Project configuration:**
- `*.xcodeproj/project.pbxproj` or `*.xcworkspace` — target platforms, capabilities, frameworks
- `Info.plist` (or `*-Info.plist`) — permissions, background modes, URL schemes
- `*.entitlements` — capabilities like HealthKit, HomeKit, Apple Pay, Push
- `Podfile`, `Package.swift`, `Cartfile` — third-party dependencies
- `AppStoreConnect` metadata or `fastlane/metadata` — if present, read app description, keywords, screenshots

**Code patterns to look for:**
- Privacy-sensitive APIs: location, contacts, photos, camera, microphone, health, tracking
- Payment/purchase code: StoreKit, IAP, subscription handling
- Authentication: login flows, Sign in with Apple, social logins
- User-generated content: posting, commenting, messaging features
- Push notifications: registration, handling, marketing use
- Web views: WKWebView vs deprecated UIWebView
- Background modes: audio, location, fetch, processing
- Network: IPv4 hardcoding, API calls, data transmission
- Third-party SDKs: analytics, ads, crash reporting (especially in Kids apps)

**Metadata (if available):**
- App Store description, keywords, title, subtitle
- Screenshots and preview videos
- Privacy policy URL
- Age rating configuration

Classify the app into relevant categories to determine which guidelines apply:
- General app / Game / Kids Category
- Uses IAP / Subscriptions / External payments
- Has user accounts / UGC / Social features
- Medical / Health / Finance / Gambling / Cannabis (regulated)
- Uses extensions / widgets / keyboard / Safari extension
- Has AR / streaming / mini-apps / chatbot features

## Phase 2: Run the Audit

Read `references/guidelines.md` for the complete checklist of 150+ guidelines organized by section.

For each guideline, determine one of:
- **PASS** — Evidence the app complies
- **FAIL** — Clear violation found with specific evidence
- **WARNING** — Potential issue that needs developer verification
- **N/A** — Guideline doesn't apply to this app type

Important principles:
- Start with the "Top 20 Rejection Triggers" at the bottom of the guidelines reference — these cause the most rejections and should be checked first
- Be specific about evidence. Don't say "might have privacy issues" — say "Found `CLLocationManager` usage in `LocationService.swift:42` but no `NSLocationWhenInUseUsageDescription` in Info.plist"
- Check what you can verify from code and config. For things you can't verify (like "does the app crash?"), note them as requiring manual verification
- Cross-reference entitlements with actual usage — requested capabilities that aren't used raise flags, and used capabilities without entitlements will crash

## Phase 3: Generate the Report

Structure the output as a clear, actionable report.

### Report Format

```
# App Store Review Audit Report

**App:** [name from project]
**Date:** [today]
**Platform:** [iOS / macOS / tvOS / visionOS]
**App Type:** [classification from Phase 1]

## Verdict: [LIKELY PASS / AT RISK / LIKELY REJECT]

**Summary:** [1-2 sentence overall assessment]

- Total checks: [N]
- Pass: [N] | Fail: [N] | Warning: [N] | N/A: [N]

---

## Critical Issues (FAIL)

Issues that will almost certainly cause rejection. Fix these before submitting.

### [Guideline ID] — [Short title]
**Verdict:** FAIL
**Evidence:** [Specific file, line, config, or metadata where the violation was found]
**Why it matters:** [Brief explanation of why Apple cares about this]
**Fix:** [Concrete steps to resolve the issue]

---

## Warnings

Issues that might cause rejection or that need manual verification.

### [Guideline ID] — [Short title]
**Verdict:** WARNING
**Evidence:** [What was found or what couldn't be verified]
**Recommendation:** [What to check or fix]

---

## Passed Checks

[Collapsible or summarized list of passed guidelines, grouped by section]

## N/A Guidelines

[Brief list of guidelines that don't apply and why]

---

## Pre-Submission Checklist

Based on this audit, here's what to do before submitting:

1. [ ] [Fix item 1]
2. [ ] [Fix item 2]
...
```

### Verdict Criteria

- **LIKELY PASS** — Zero FAILs, few warnings, and those warnings are minor or likely OK
- **AT RISK** — Zero FAILs but multiple warnings that could go either way, OR 1-2 minor FAILs that are easy fixes
- **LIKELY REJECT** — Any FAIL on a Top 20 rejection trigger, or 3+ FAILs on any guidelines

## Phase 4: Offer to Fix

After presenting the report, offer to help fix the identified issues. For code-level fixes (missing privacy descriptions, IAP restore button, account deletion flow), you can often implement them directly. For metadata issues, provide the exact text or configuration changes needed.
