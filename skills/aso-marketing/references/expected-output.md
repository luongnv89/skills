# Expected Output Examples

A complete run produces three artifacts, followed by the Final Report.

## 1. ASO Analysis Report (Phase 1)

```
## ASO Analysis Report

### App Overview
- App Name: FocusFlow – Deep Work Timer
- Platforms: iOS, Android
- Category: Productivity
- Core Value Proposition: Distraction-free Pomodoro-style focus sessions with team accountability
- Target Audience: Knowledge workers, students, remote teams

### Current Metadata Status
| Field      | Platform | Current Value                    | Length | Limit | Usage % | Issues                       |
|------------|----------|----------------------------------|--------|-------|---------|------------------------------|
| Title      | iOS      | FocusFlow: Work Timer            | 21     | 30    | 70%     | No primary keyword in title  |
| Keywords   | iOS      | timer,focus,work,productivity    | 29     | 100   | 29%     | 71 chars unused              |
| Short Desc | Android  | A simple timer for focused work. | 32     | 80    | 40%     | Weak value prop, low density |
```

## 2. ASO Plan + Compliance Report + Updated Metadata Files (Phases 2-4)

Example `metadata/app-info/en-US.json` after execution:

```json
{
  "name": "FocusFlow: Focus & Work Timer",
  "subtitle": "Deep Work Sessions & Tracking"
}
```

Example iOS keywords field (Phase 4):

```
pomodoro,concentration,study,productivity,distraction,blocker,habit,goal,task,routine,break,planner
```

(99/100 chars, all prohibited terms cleared, no word repeated from the title or subtitle)

## 3. ASO Marketing Summary Report (Phase 7)

```
## ASO Marketing Summary Report

### Changes Made
| # | Area         | Change                          | Before                        | After                          | Expected Impact              |
|---|--------------|---------------------------------|-------------------------------|--------------------------------|------------------------------|
| 1 | iOS Title    | Added primary keyword           | FocusFlow: Work Timer         | FocusFlow: Focus & Work Timer  | +rankings for "focus timer"  |
| 2 | iOS Keywords | Expanded from 29 to 99 chars    | timer,focus,work,productivity | pomodoro,concentration,...     | 3x more indexable queries    |
| 3 | Android Desc | Rewrote opening hook + keywords | A simple timer for focused... | Block distractions. Build...   | Higher conversion rate       |

### Store Policy Compliance
- Prohibited keyword check: PASS — no banned terms in any metadata field
- Trademark check: PASS — no competitor or third-party trademarks used
- Overall compliance: PASS for App Store + Google Play
```

## 4. Final Report (closing response)

After the Summary Report, every run ends with the four-line Final Report. Status rules and `PARTIAL` / `BLOCKED` examples: `references/final-report.md`.

```text
Result: COMPLETE. Optimized the iOS and Android listings for FocusFlow; wrote 4 metadata files; Phase 3 compliance PASS.
Evidence: Phase 1 baseline iOS keywords 29/100; after Phase 4 iOS title 29/30, keywords 99/100; Phase 5 re-scan found 0 prohibited terms and 0 competitor names.
Uncertainty: Search volumes are heuristic estimates; ranking and conversion effects are untested until the listing is live.
Decision: No approval needed. Upload the metadata to both stores, then re-check rankings in 1-2 weeks.
```
