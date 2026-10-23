# Plan, approval gate, kit index, step reports and final report

The main agent reads this file in Steps 4, 5c and 8, and on the Resume branch.

## launch-plan.md (Step 4)

Write the file in this shape. Replace each `<…>`, and keep the headings: writers and Resume
read them.

```
# Launch plan: <product name>
Status: awaiting-approval | approved <YYYY-MM-DD> | kit-complete <YYYY-MM-DD> | stopped
Generated: <YYYY-MM-DD> · L-day: <YYYY-MM-DD> (<user-set | assumed>) · Budget: <$N | $0, free paths only> · sync: <done | skipped (reason)>
Opted-in actions: <the second-yes actions the user picked, or "none">

## Product Profile
<the explorer's Profile table, unchanged>

## Launch blockers
<the explorer's Blockers table, unchanged>

## Assets found
<the explorer's Assets table, unchanged>

## Fix before launch
<each failed blocker: what to fix, why, and the platforms it unblocks; or "None">

## Plan
| Tier | Platform | Why (score: fit/reach/cost/timing = total) | Path and cost | Go-live (platform time and UTC) | Mode |
<one row per shortlisted platform, ordered by tier, then by go-live. reddit lists its chosen subreddits.>

## Skipped
| Platform | Reason |
<one row per skipped platform: a failed gate, a low score, or over cap>

## Timeline
| Date | Action | Platform |
<every dated action from today to L+30, built with platform-index.md §5>

## Budget
Free path total: $0. Paid options proposed: <each option, its price and what it buys>. Total if all are accepted: $<N>.

## Materials Step 5 will write
<the file list: README.md, copy-bank.md, assets.md, and platforms/<id>.md for each platform>

## Actions that need a second yes
<only what applies: "gh repo edit (metadata)" when the repo is public on GitHub; "/logo-designer: no square logo found"; "/landing-page-generator: no landing page"; "/seo-ai-optimizer: og tags missing"; or "None">

## Assumptions and unknowns
<each assumption, inferred value, and unknown profile field that affected a decision>

## Live check
| Platform | Result | Checked URL | Changes from catalog |
```

## Approval gate (Step 4, in chat)

Print a summary of no more than 40 lines, in this order:

1. The product in one line.
2. The blockers to fix.
3. The plan table: tier, platform, path and go-live.
4. The number of skipped platforms, by reason.
5. The budget.
6. The path of the plan file.
7. The four lines below:

```
Result: PLAN READY — awaiting approval
Evidence: <profile sources read; live check: N same, N changed, N unreachable, with dates>
Uncertainty: <unknown or inferred profile fields that affect the plan; unverified platform facts>
Decision: approve, change or stop the plan<; and pick which second-yes actions to run>
```

Then ask with AskUserQuestion. The answer must be explicit; silence is not approval.

1. **"What should I do with the launch plan?"**
   - Approve: write the launch kit now.
   - Change the plan: add or remove platforms, or change the date or budget.
   - Stop here: keep `launch-plan.md` only.
2. **Only when "Actions that need a second yes" lists something:** "Which of these actions
   should run after the kit is written?" Use multiSelect and list each action. Unchecked
   means not run.

Record the answers in `Status:` and `Opted-in actions:`. An action that is not opted in
never runs. An opted-in action still asks for its own confirmation in Step 7.

Without AskUserQuestion, ask the same questions in plain text, then end the turn.

## Resume table

The Resume branch reads the plan's `Status:` line and acts on it.

| Status              | Action                                                                                                                                                                                         |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `awaiting-approval` | If the request approves the plan, record the approval and go to Step 5. If it changes the plan (date, budget, platforms), take the Change path. Otherwise print the gate summary and ask again. |
| `approved …`        | A change request takes the Change path, then asks for approval again. Otherwise: if `Generated:` is more than 14 days old, re-run Step 3 and show the changes first; then run Step 5.            |
| `kit-complete …`    | Ask what to update. Re-run only the steps it touches, and confirm before replacing any file.                                                                                                   |
| `stopped`           | Treat it as a new run (Full or Named). Ask before replacing the plan.                                                                                                                          |

## README.md (Step 5c)

```
# Launch kit: <product name>
Plan approved <date> · L-day <date> · <N> platforms · Budget $<N>

## Next 3 actions
1. <the earliest-dated unchecked action, with its date>
2. …
3. …

## Checklist
- [ ] <date> · <action> · [<platform>](platforms/<id>.md)
<every timeline row, in date order>

## Founder inputs needed
<every open question the writers returned, with its file>

## Files
| File | What it holds |
```

## Step Completion Reports

After each step, print this block. Write each check as `√` (pass), `×` (fail) or `—`
(note), and tie it to a count, a file or a command.

```
◆ <Step name> (step N of 8)
··································································
  <check>:            √ <evidence>
  <check>:            × <reason>
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

| Step              | Checks                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| 1 Product Profile | profile rows filled (N/30), sources per row, blockers checked (N/8), assets listed               |
| 2 Fit table       | rows gated (N of 53), scores with all 4 components, tiers within caps, every skip has a reason    |
| 3 Live check      | shortlisted platforms checked (N/M), changes found, fetch failures labeled                       |
| 4 Plan and gate   | sync recorded, launch-plan.md written, approval asked, answers recorded                          |
| 5 Launch kit      | copy-bank written, platform files (N/M), README and assets written                               |
| 6 Kit check       | check_kit.py exit 0, reviewer blocking issues (0), review fresh or self-review (labeled)         |
| 7 Actions         | each opted-in action: run and verified, declined, failed, or none opted in                       |
| 8 Final report    | Result line first; Evidence, Uncertainty and Decision present                                    |

## Final report (Step 8)

Print this block last, after the Step 8 Step Completion Report. The Result line comes
first.

```
Result: COMPLETE | PLAN READY — stopped | PARTIAL — <reason> | BLOCKED — <reason>
Evidence: <what was verified: profile sources, live-check results with dates, check_kit.py output, gh repo view output>
Uncertainty: <unverified platform facts (catalog date), unknown profile fields, Reddit rules to re-read, Korean copy to review, self-review instead of a fresh reviewer; or "none known within these checks">
Decision: <the approval needed, or "No approval needed."> Next for you: <the earliest dated action in README.md>
```

**Status rule:**

- COMPLETE: Steps 5 and 6 passed, and every opted-in action ran. Set `Status: kit-complete <date>`.
- PLAN READY — stopped: the user chose Stop at the gate.
- PARTIAL: the kit was written, but a check still failed after its fix rounds, or an
  opted-in action failed.
- BLOCKED: no readable landing page and no codebase; a sync problem the user must resolve;
  or several products and no answer about which one.
