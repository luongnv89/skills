# Final Report

The closing chat response of every aso-marketing run, stops included. It follows the five
Step Completion Reports and sits after the Phase 7 Summary Report; it never replaces that
report. `SKILL.md` (*Final Report*) holds the status summary; this file holds the status
table, the `COMPLETE`, `PARTIAL` and `BLOCKED` examples, the fill rules, and the reader checks.

## Format

The report is a compact text block of four lines. The Summary Report already carries the
per-field before/after table, so do not repeat it here. If the user asks for a different
format, keep the four items (`Result`, `Evidence`, `Uncertainty`, `Decision`) and present them
in that format.

## Status

Apply the first row that matches:

| Status | When |
|--------|------|
| `BLOCKED` | No Analysis Report was produced: the Environment Check failed (the project is not a mobile app, or neither source code nor metadata can be read), or the user ended the run before Phase 1 finished. |
| `PARTIAL` | The Analysis Report exists and at least one applicable Acceptance Criteria item in `references/edge-cases.md` is unchecked: the user rejected the plan or ended the run at the User Approval Gate; the user approved only part of the plan; Repo Sync stopped (missing `origin`, failed pull, conflict) or a metadata file could not be backed up, so Phase 4 wrote nothing or only some files; or Phase 5 or Phase 6 found a violation that is still present. |
| `COMPLETE` | Every applicable Acceptance Criteria item in `references/edge-cases.md` is checked. |

A plan awaiting approval at the User Approval Gate does not end the run. If the user ends the
run there, the status is `PARTIAL`, because the Analysis Report exists. A plan-only request
("give me the plan, don't change any files") is `COMPLETE` once the compliant plan is
presented and the user declines execution; name the declined plan in `Decision:`, and treat
the Phase 4-7 criteria as not applicable.

## COMPLETE example

```text
Result: COMPLETE. Optimized the iOS and Android listings for FocusFlow; wrote 4 metadata files; Phase 3 compliance PASS.
Evidence: Phase 1 baseline iOS keywords 29/100; after Phase 4 iOS title 29/30, keywords 99/100, Android short description 74/80; Phase 5 re-scan found 0 prohibited terms and 0 competitor names; .bak copies made for 2 overwritten files.
Uncertainty: Search volumes are heuristic estimates (no keyword tool was available); ranking and conversion effects are untested until the listing is live.
Decision: No approval needed. Upload the metadata to App Store Connect and Google Play Console, then re-check rankings in 1-2 weeks.
```

## PARTIAL example

```text
Result: PARTIAL. Plan for ZenMind passed Phase 3 compliance; the user approved items 1-3 of 6; Phase 4 wrote 2 of 5 planned files.
Evidence: Phase 3 report PASS (0 prohibited terms, 0 trademarks); fastlane/metadata/android/en-US/title.txt and short_description.txt written; plan items 4-6 (full description, localization, screenshots) not approved.
Uncertainty: The iOS keyword field was not written, so its cross-field duplicate check is untested; the de-DE localization is not reviewed by a native speaker.
Decision: Approve plan items 4-6, or confirm they stay out of scope.
```

## BLOCKED example

```text
Result: BLOCKED. No Analysis Report: /work/landing-site is a web project, not a mobile app.
Evidence: Environment Check found no Info.plist, build.gradle, fastlane/ or metadata/ directory; no file was written.
Uncertainty: Whether a separate mobile repository exists is unknown.
Decision: Run the skill from the app's repository, or use seo-ai-optimizer for the website.
```

## Fill rules

- `Result:` comes first. The first word after `Result:` is the status. Name the app, the
  store or stores, the number of metadata files written, and the Phase 3 compliance result, or
  say `No Analysis Report`.
- `Evidence:` names each check that ran and its observed result: before and after character
  counts for each indexed field, the Phase 3 and Phase 5 prohibited-keyword and trademark scan
  counts, and the backups made. Cite only checks that ran.
- `Uncertainty:` lists each check that could not run (no competitor access, no keyword volume
  data, no live listing) and each assumption made. Label assumptions as assumptions. A clean
  compliance scan proves the metadata text only; it does not prove store approval, ranking,
  or conversion.
- `Decision:` names the one approval the user must give, or says `No approval needed.` Name a
  remaining user action (upload the metadata, start a Store Listing Experiment) on the same
  line after `No approval needed.`

## Step completion reports

The five Step Completion Reports (`references/edge-cases.md`) use `PASS`, `PARTIAL` and
`FAIL`. A `FAIL` in the Phase 1 report becomes a Final Report `BLOCKED`. A `FAIL` or
`PARTIAL` in any later report becomes a Final Report `PARTIAL`.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in
`references/edge-cases.md` (*Acceptance Criteria*):

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status, the app and store, and what was written (or `No Analysis Report`) without re-reading the conversation. |
| Facts and assumptions are separated | Verified claims name a check that ran (character counts, compliance scan counts, files written); heuristic keyword volumes and untested effects are on the `Uncertainty:` line. |
| Claims are traceable | Each field change cites its before and after count; `COMPLETE` appears only when every applicable Acceptance Criteria item is checked. |
| Next decision is clear | The `Decision:` line names the pending approval or says `No approval needed.` and names any remaining user action. |

A heading's presence alone does not pass a check. Ask a human reviewer the same four
questions. If no reviewer answers, record human understanding as unconfirmed; agent
inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from
these checks.
