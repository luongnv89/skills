# Example Output

A complete run produces `APPSTORE_AUDIT.md` in the project root. Example snippet:

```markdown
# App Store Review Audit Report

**App:** NutriTrack – Meal Planner
**Date:** 2026-04-19
**Platform:** iOS 16+
**App Type:** Health & Fitness — uses HealthKit, has user accounts, offers subscriptions

## Verdict: AT RISK

**Summary:** Two critical issues will likely cause rejection: missing account deletion flow (Guideline 5.1.1) and UIWebView usage (Guideline 4.2). Fix these before submitting.

- Total checks: 47
- Pass: 38 | Fail: 2 | Warning: 5 | N/A: 2

---

## Critical Issues (FAIL)

### 5.1.1 — Account Deletion
**Verdict:** FAIL
**Evidence:** `AccountViewController.swift` has a "Delete Account" button (line 142) that calls `deleteAccountAPI()` but no confirmation screen or in-app deletion flow was found. The API call is stubbed and returns a 501 Not Implemented response in `NetworkClient.swift:87`.
**Why it matters:** Apple requires apps with account creation to provide an in-app account deletion option that fully removes user data.
**Fix:** Implement a two-step deletion flow (confirm dialog → API call → sign out → clear local data). See Human Interface Guidelines: Deleting an account.

### 4.2 — Minimum Functionality (UIWebView)
**Verdict:** FAIL
**Evidence:** `LegacyBrowserViewController.swift:14` imports `UIKit` and declares `var webView: UIWebView`. UIWebView is deprecated since iOS 12 and forbidden in new submissions.
**Fix:** Replace with `WKWebView` from `WebKit`. Import `WebKit` and update the property type and any delegate methods.

---

## Warnings

### 3.1.2 — Accurate Metadata
**Verdict:** WARNING
**Evidence:** App Store description claims "Real-time nutritionist AI chat" but no chat UI or AI integration was found in source code.
**Recommendation:** Either implement the feature before submitting or remove the claim from the description to avoid a 2.1 rejection for "spam/misleading".
```
