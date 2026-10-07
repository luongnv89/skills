# Final Report

The closing chat response of every appstore-review-checker run, stops included. It follows the
last Step Completion Report and summarizes the run; it never replaces `APPSTORE_AUDIT.md`.
`SKILL.md` (*Final Report*) holds the status summary and the `COMPLETE` example; this file holds
the status table, the `PARTIAL` and `BLOCKED` examples, the fill rules, and the reader checks.

## Format

The Final Report is a compact text block of four lines: `Result`, `Evidence`, `Uncertainty`,
`Decision`. `APPSTORE_AUDIT.md` already carries every per-guideline verdict, so do not repeat
the findings here. If the user asks for a different format, keep the four items and present
them in that format.

The run status and the audit verdict are two different values:

- The **run status** (`COMPLETE`, `PARTIAL`, `BLOCKED`) says whether the skill finished its work.
- The **audit verdict** (`LIKELY PASS`, `AT RISK`, `LIKELY REJECT`) says how the app is likely to
  fare in review.

A `COMPLETE` run can report a `LIKELY REJECT` verdict.

## Status

Apply the first row that matches:

| Status | When |
|--------|------|
| `BLOCKED` | No `APPSTORE_AUDIT.md` (or `APPSTORE_AUDIT_v2.md`) was written. Causes: no project access and no metadata; the project files could not be located and the user gave no path; the user declined both overwriting the existing report and writing `APPSTORE_AUDIT_v2.md`; Repo Sync stopped (missing `origin` or a rebase conflict); or the user ended the run before Phase 3. |
| `PARTIAL` | The report exists and at least one applicable Acceptance Criteria item in `references/quality-checks.md` is unchecked. Examples: a Top 20 trigger has no verdict; a FAIL has no file, line or config citation; an approved Phase 4 fix could not be applied. |
| `COMPLETE` | Every applicable Acceptance Criteria item in `references/quality-checks.md` is checked. |

An offer to fix that is still waiting for an answer does not change the status. Name it in
`Decision:`.

## PARTIAL example

```text
Result: PARTIAL. Audited PhotoVault (iOS 17+); wrote APPSTORE_AUDIT.md; audit verdict LIKELY REJECT (2 FAIL, 4 WARNING); applied 1 of 2 approved fixes.
Evidence: 52 guidelines checked, each Top 20 trigger has a verdict; fix for 5.1.1-ii added NSPhotoLibraryUsageDescription to Info.plist; fix for 3.1.1-restore not applied because no StoreKit purchase code was found to extend.
Uncertainty: The restore-purchases flow lives in a closed-source SDK (assumption based on the Podfile); runtime behavior is untested.
Decision: Confirm where purchases are handled, or approve adding a Restore Purchases button that calls AppStore.sync().
```

## BLOCKED example

```text
Result: BLOCKED. No APPSTORE_AUDIT.md: no Xcode project or App Store metadata was found at /work/app.
Evidence: Searched for *.xcodeproj, *.xcworkspace, Info.plist and Package.swift; 0 matches; no file was written.
Uncertainty: Whether the app lives in another directory or repository is unknown.
Decision: Give the path to the Xcode project, or paste the App Store Connect metadata for a metadata-only audit.
```

## Fill rules

- `Result:` comes first. The first word after `Result:` is the run status. Name the app and
  platform, the report file written (or `No APPSTORE_AUDIT.md`), the audit verdict with FAIL
  and WARNING counts, and the number of fixes applied when Phase 4 ran.
- `Evidence:` names each check that ran and its observed result: the files read, the number of
  guidelines checked, the Top 20 coverage, and the file and line cited for each FAIL. Cite only
  checks that ran.
- `Uncertainty:` lists the static-analysis limits that apply (`references/quality-checks.md`,
  *Things You Cannot Check From Code Alone*) and each assumption made. Label assumptions as
  assumptions. A `LIKELY PASS` verdict is a prediction from static evidence; it does not prove
  Apple will approve the app.
- `Decision:` names the one approval the user must give (for example, the FAIL IDs to fix), or
  says `No approval needed.` Name a remaining user action (fix the metadata in App Store
  Connect, submit the build) on the same line after `No approval needed.`

## Step Completion Reports

The Step Completion Reports (`references/quality-checks.md`) use `PASS`, `PARTIAL` and `FAIL`.
A `FAIL` in a report before Phase 3 becomes a Final Report `BLOCKED`. A `FAIL` or `PARTIAL` in
the Phase 3 or Phase 4 report becomes a Final Report `PARTIAL`.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in
`references/quality-checks.md` (*Acceptance Criteria*):

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the run status, the app, the report file (or `No APPSTORE_AUDIT.md`) and the audit verdict, without re-reading the conversation. |
| Facts and assumptions are separated | `Evidence:` names checks that ran; `Uncertainty:` labels assumptions and lists the static-analysis limits that apply. |
| Claims are traceable | Each FAIL count and fix claim points to a file, line or config key; a written report is not described as an approved app. |
| Next decision is clear | `Decision:` names the pending approval (such as the FAIL IDs to fix) or says `No approval needed.` and names the remaining user action. |

An agent's inspection cannot confirm that a human understood the report. If no human reviewer
answers these checks, record human understanding as unconfirmed.
