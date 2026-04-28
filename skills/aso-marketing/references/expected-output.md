# Expected Output Examples

A complete run produces three artifacts.

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
| Title      | iOS      | FocusFlow: Work Timer            | 22     | 30    | 73%     | No primary keyword in title  |
| Keywords   | iOS      | timer,focus,work,productivity    | 34     | 100   | 34%     | 66 chars unused              |
| Short Desc | Android  | A simple timer for focused work. | 36     | 80    | 45%     | Weak value prop, low density |
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
pomodoro,deep,work,concentration,study,block,distraction,habit,goal,flow,task
```

(97/100 chars, all prohibited terms cleared, no title/subtitle duplicates)

## 3. ASO Marketing Summary Report (Phase 7)

```
## ASO Marketing Summary Report

### Changes Made
| # | Area         | Change                          | Before                        | After                          | Expected Impact              |
|---|--------------|---------------------------------|-------------------------------|--------------------------------|------------------------------|
| 1 | iOS Title    | Added primary keyword           | FocusFlow: Work Timer         | FocusFlow: Focus & Work Timer  | +rankings for "focus timer"  |
| 2 | iOS Keywords | Expanded from 34 to 97 chars    | timer,focus,work,productivity | pomodoro,deep,work,...         | 3x more indexable queries    |
| 3 | Android Desc | Rewrote opening hook + keywords | A simple timer for focused... | Block distractions. Build...   | Higher conversion rate       |

### Store Policy Compliance
- Prohibited keyword check: PASS — no banned terms in any metadata field
- Trademark check: PASS — no competitor or third-party trademarks used
- Overall compliance: PASS for App Store + Google Play
```
