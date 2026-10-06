# Final Report — examples and fill rules

Read this when writing the Final Report (SKILL.md → *Final Report*). SKILL.md owns the status rules and the required lines; this file shows filled examples and how to fill each line.

## Example (COMPLETE, create mode)

```
Result: COMPLETE. create mode, /Users/me/ideas/2026_10_06_habit_tracker_for_nurses/tad.md (11/11 sections).
        Next.js 15 on Vercel, Node 20 LTS API, PostgreSQL 16, Redis 7 cache; 5 modules behind typed interfaces.
Evidence: verification 6/6 passed (check 7 n/a, no prior tad.md): 11 numbered sections, 2 mermaid blocks, 0 bare "latest",
          7 risks / 7 Mitigation: lines, 4 cost rows, OAuth2 + OWASP ASVS cited in §7.
          Costs (§11.3): ~$45/mo MVP, ~$220/mo growth, year 1 ~$1,900. Backup: no prior tad.md. Commit a1b2c3d.
  tad.md:    https://github.com/me/ideas/blob/main/2026_10_06_habit_tracker_for_nurses/tad.md
  README.md: https://github.com/me/ideas/blob/main/README.md (TAD status ✅)
Uncertainty: SSO provider is TBD (Phase 3 unanswered, listed in §10). Growth cost assumes 5K MAU from PRD §1
             (assumption: 2 app instances). Research ran with web access; all 5 rounds returned.
Decision: No approval needed.
Next step: Review §10 Risks with the team, then run tasks-generator.
```

## Example (PARTIAL, push declined)

```
Result: PARTIAL. modify mode, /Users/me/ideas/2026_10_06_habit_tracker_for_nurses/tad.md. §6 Infrastructure updated.
        Stopped in Phase 7: user declined the push.
Evidence: verification 7/7 passed. Backup: tad.md.bak.20261006_141502 (21 KB). Revision history row added to §11.4.
          Commit 4b7d0aa (local only).
Uncertainty: The remote does not have this commit; the GitHub links are omitted until it is pushed.
Decision: No approval needed.
Next step: Run `git push origin main` in /Users/me/ideas when ready.
```

## Example (BLOCKED, missing PRD)

```
Result: BLOCKED. No tad.md written. Stopped in Phase 1 step 3: /Users/me/ideas/2026_10_06_ai_meal_planner/prd.md does not exist.
Evidence: idea.md and validate.md found in /Users/me/ideas/2026_10_06_ai_meal_planner/. No files changed.
Uncertainty: none within the checks run.
Decision: No approval needed.
Next step: Run prd-generator on this folder, then re-run tad-generator.
```

## Fill rules

| Line | Fill rule |
|------|-----------|
| `Result:` | Status first, then the run mode and the absolute `tad.md` path. Then the main stack, hosting and module decisions, each as written in `tad.md` §3-§4. For `PARTIAL` or `BLOCKED`, name the phase and step where the run stopped and the `references/edge-cases.md` row or status rule that stopped it. A `BLOCKED` run writes `No tad.md written`. |
| `Evidence:` | Each check from `references/verification-steps.md` that ran, with its observed count. The cost estimates by phase from §11.3, or `TBD`. The backup file name and size, or `no prior tad.md`. The commit hash, marked `local only` when not pushed. One GitHub link per pushed file, built from the current branch. Omit a link or hash that does not exist and say why. |
| `Uncertainty:` | Every `TBD` or `Unknown` value and its section. Every Phase 3 decision left unanswered. Every number derived from an assumption, labeled as an assumption. Every research round that failed, ran inline, or ran without web access. Every skipped phase (for example, Phase 6 outside an ideas repo). Write `none within the checks run` only when the list is empty. |
| `Decision:` | `No approval needed.` when nothing waits on the user. Otherwise the exact question the run is waiting on (a thin PRD, a stack conflict, a Repo Sync conflict, a push confirmation). |
| `Next step:` | One action for the user, tied to the stop reason or to the TAD's weakest section. |

Match each claim to the scope of its evidence. A passing section count supports "11 sections present", not "the architecture is sound". A successful `git commit` supports "committed", not "pushed". A version named in `tad.md` is verified only when a research round's `references` back it; otherwise list it on the `Uncertainty:` line.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in SKILL.md → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status, the run mode and the `tad.md` path, without opening `tad.md`. |
| Facts and assumptions are separated | Verified claims name the check, research round or input file behind them; assumptions, inferences and `TBD` values are labeled on the `Uncertainty:` line. |
| Claims are traceable | Each material claim points to a verification count, a research round, a backup file, a commit hash, a link, or a `tad.md` section that supports its scope. |
| Next decision is clear | The `Decision:` line names the pending question or says `No approval needed.`, and the `Next step:` line names the user's action. |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from these checks.
