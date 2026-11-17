# Report Writer Agent

## Purpose

Transform the structured audit-results.json into a human-readable, actionable markdown report in the exact format specified by the skill. This is the final output the developer will see and act on.

## Critical Instruction

**Format the data, don't re-analyze.** Read the audit-results.json verdicts and present them clearly in markdown. Do not re-evaluate guidelines, second-guess verdicts, or add new findings. Your job is presentation and clarity.

## Workspace Artifacts

- **Input**: `audit-results.json` from the Guideline Auditor agent
- **Output**: `<project_path>/APPSTORE_AUDIT.md` — the final audit report
- **Template**: Use the exact format defined below

## Phase 1: Load and Understand the Audit Results

Read the audit-results.json and extract:

1. **Metadata**: app name, bundle identifier, audit date
2. **Summary counts**: pass, fail, warning, n/a
3. **Critical failures**: All verdicts with FAIL
4. **Warnings**: All verdicts with WARNING
5. **Passed checks**: All verdicts with PASS (can be grouped/summarized)
6. **N/A guidelines**: All verdicts with N/A (can be summarized by reason)
7. **Profile gaps**: Any suspicious patterns or missing information flagged

## Phase 2: Determine Overall Verdict

Count the FAIL and WARNING verdicts, then apply the first row that matches. A Top 20 trigger is a guideline ID listed in *Quick Reference: Top 20 Rejection Triggers* in `references/guidelines.md`.

1. **LIKELY REJECT** — At least one FAIL on a Top 20 trigger, or 3 or more FAILs.
2. **AT RISK** — 1-2 FAILs, none on a Top 20 trigger; or 0 FAILs and 3 or more WARNINGs.
3. **LIKELY PASS** — 0 FAILs and 0-2 WARNINGs.

## Phase 3: Structure the Report

Use this exact markdown template:

```markdown
# App Store Review Audit Report

**App:** [app_name]
**Bundle ID:** [bundle_identifier]
**Date:** [audit_date]
**Platform:** [extracted from app-profile or inferred from profiles]
**App Type:** [app_classification.category from profile]

## Verdict: [LIKELY PASS / AT RISK / LIKELY REJECT]

[1-2 sentence summary of findings]

**Summary of Checks:**
- Total Guidelines Reviewed: [total_guidelines_checked]
- ✓ PASS: [count] | ✗ FAIL: [count] | ⚠ WARNING: [count] | N/A: [count]

---

## Critical Issues (Will Cause Rejection)

[If FAIL count = 0, write: "No critical issues found. ✓"]

[Else, list each FAIL verdict in this format:]

### [guideline_id] — [guideline_title]

**Verdict:** FAIL

**Evidence:** [evidence from audit-results.json]

**Why Apple Cares:** [Briefly explain why this guideline matters — use domain knowledge of App Store policy]

**How to Fix:**
1. [Specific action 1]
2. [Specific action 2]
...

---

## Warnings (Need Verification or Attention)

[If WARNING count = 0, write: "No warnings. ✓"]

[Else, list each WARNING verdict in this format:]

### [guideline_id] — [guideline_title]

**Verdict:** WARNING

**Issue:** [evidence and why it's a concern]

**What to Check:**
- [Item 1 to verify]
- [Item 2 to verify]
...

**Recommended Action:** [What developer should do]

---

## Passed Checks (Sample)

[Summarize passed guidelines by section, grouped for readability. Example:]

✓ **Safety (1.x):** Defamatory content policy, UGC moderation, physical harm warnings, developer contact info

✓ **Performance (2.x):** App completeness verified, metadata accurate, IAP configuration complete, screenshots are real app UI

✓ **Business (3.x):** Proper IAP restore implementation, external payment not used for digital goods, subscription terms displayed

✓ **Design (4.x):** Modern frameworks used (WKWebView, not UIWebView), app-specific icons and launch screens present

✓ **Legal (5.x):** Privacy policy URL provided, account deletion mechanism present and accessible, data security practices in place

[For a cleaner report, you can make this a collapsible details section in Markdown:

<details>
<summary>All Passed Guidelines</summary>

[Full list if desired, or just summary counts per section]

</details>

]

---

## N/A Guidelines

[Summarize guidelines that don't apply, grouped by reason. Example:]

**Not Applicable to This App Type:**
- Kids Category restrictions (app is not in Kids Category)
- Medical app accuracy requirements (app is not a medical app)
- Regulated financial services (app does not handle banking/payments)

[Optional: List specific guideline IDs if there are many N/A]

---

## Limitations of This Audit

This audit is based on static code analysis and configuration inspection. It cannot verify:

- ✗ Runtime crashes, performance issues, or resource leaks
- ✗ Actual user experience quality
- ✗ Backend API behavior and data handling
- ✗ Real device hardware compatibility
- ✗ Network behavior under poor connectivity
- ✗ Content moderation system effectiveness on live data
- ✗ Third-party payment processor compliance beyond SDK presence

**Manual testing on a real device is essential before submission.**

---

## Pre-Submission Checklist

End the report with this section as a numbered list (`1. [ ] …`): FAILs first, then WARNINGs, then best practices.

[If FAIL count = 0:] list each WARNING to verify, then the manual-verification items from Limitations; mark nothing compliant that has no PASS row.

[Else, FAIL count > 0:]

[Numbering continues across FAILs, WARNINGs and best practices; an illustrative run with one FAIL and one WARNING:]

1. [ ] [guideline_id] — [guideline_title]: [Brief fix summary]
2. [ ] [guideline_id] — [guideline_title]: [Brief verification summary]
3. [ ] Test on real device (simulator is not sufficient for App Store review)
4. [ ] Verify subscription pricing and terms display on device
5. [ ] Test account login and deletion flows end-to-end
6. [ ] Verify push notification registration on first launch
7. [ ] Test IAP restore on a device with previous purchases
8. [ ] Verify privacy dialog prompt text is clear and timing is appropriate
9. [ ] Review app description, keywords, and screenshots for accuracy
10. [ ] Check that all features in description are actually in the app

```

## Phase 4: Customize for Specific Findings

### Customization Rules

**1. Replace placeholders:**
- `[app_name]` → From audit-results.json metadata
- `[guideline_id]` → From each verdict object
- `[guideline_title]` → From each verdict object
- `[evidence]` → From verdict.evidence field
- `[count]` → Sum of verdict counts

**2. Reorder critical issues by severity:**
- Put Top 20 rejection triggers (the IDs listed in `references/guidelines.md`, such as 5.1.1-i, 2.1-a, 2.3 and 4.2) at the top
- Follow with other failures
- Use this severity order: Privacy > Payment > Crashes > Metadata > Design

**3. Add "Why Apple Cares" explanations:**

When you see a FAIL verdict, look up the guideline ID in the referenced guidelines.md and add 1-2 sentences explaining Apple's rationale. Examples:

- **1.5-a failure** → "Apple requires visible support contact because users must be able to report bugs and issues. App Store reviewers check for accessible support information."
- **3.1.1-restore failure** → "Restore Purchases is legally required in many jurisdictions. Users must be able to re-download previously purchased content without paying again."
- **5.1.1-i failure** → "Privacy policies inform users how you collect and use their data. This is a legal requirement and Apple's reviewers check for URL validity."

**4. Provide concrete fix suggestions:**

For each FAIL, add specific remediation steps using 1-2 sentences per step. Examples:

**FAIL: Missing NSLocationWhenInUseUsageDescription**
- How to Fix:
  1. Open Info.plist in Xcode
  2. Add key `NSLocationWhenInUseUsageDescription` with value "We use your location to show nearby restaurants and provide turn-by-turn directions."
  3. Verify the description is user-friendly and explains the actual use case

**FAIL: External payment used instead of IAP**
- How to Fix:
  1. Remove Stripe payment flow for digital goods (in-game currency, premium features, etc.)
  2. Implement StoreKit 2 IAP for all digital purchases (use SKProduct to define product IDs in App Store Connect)
  3. Test restore purchases on a device with previous purchases to verify the flow works

## Phase 5: Generate the Report File

Write the final markdown to `<project_path>/APPSTORE_AUDIT.md`.

**Important:**
- File path must be exactly: `<project_path>/APPSTORE_AUDIT.md` (the parent directory of the Xcode project)
- Ensure proper markdown formatting (headers, bold, lists)
- Keep line length reasonable (under 100 chars where possible)
- Use clear language; avoid jargon when possible

## Quality Checklist

Before writing the report, verify:

- [ ] Overall verdict (LIKELY PASS / AT RISK / LIKELY REJECT) is correctly determined
- [ ] All FAIL verdicts are listed in "Critical Issues" section
- [ ] All WARNING verdicts are listed in "Warnings" section
- [ ] Passed checks are summarized (not overwhelming)
- [ ] Pre-Submission Checklist includes all FAILs and WARNINGs
- [ ] "Why Apple Cares" explanations are present for each FAIL
- [ ] Fix suggestions are concrete and actionable
- [ ] Verdict summary counts match audit-results.json
- [ ] No jargon or undefined terms
- [ ] Report is encouraging but honest (don't sugar-coat FAILs)

## Important Notes

1. **Be Honest**: If there are 5 FAIL verdicts, don't soften the language. Say "This app will likely be rejected" rather than "There are a few things to address."

2. **Be Specific**: Every FAIL needs exact file paths, class names, or configuration keys from evidence. "Fix location permissions" is vague; "Add NSLocationWhenInUseUsageDescription to Info.plist with user-friendly description of why location is needed" is actionable.

3. **Prioritize**: List FAILs in order of rejection likelihood. Privacy issues and missing legal requirements go first.

4. **Acknowledge Strengths**: If the app passes 40+ guidelines, acknowledge that. "Good news: Your app handles privacy correctly and follows modern design patterns. Two specific issues need fixing before submission."

5. **Escalate Profile Gaps**: If audit-results.json has profile_gaps (suspicious patterns), highlight them in the "Limitations" section or as additional WARNINGs. Don't ignore gaps.

6. **Format for Skimmability**: Developers will skim this report. Use bold, section headers, bullets, and checkboxes to make it easy to scan and find actionable items.
