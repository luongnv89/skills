# Final Report

The single closing output of every product-planner run, stops included. The status rules and the
required lines are in `SKILL.md` (*Final Report*); this file holds the template, two filled examples
and the fill rules.

## Template

```text
◆ Product Planner — Final Report
··································································
Result:      <COMPLETE|PARTIAL|BLOCKED> — stages <start>–<end> (brand check: <ran|skipped|not requested>)
             Verdict: <Build it|Maybe|Skip it|not read> (<ratings>); override: <none|"user's words">
             <for PARTIAL/BLOCKED: stopped at <stage> because <reason>>
Evidence:    PROJECT_DIR: <absolute path>

  | Artifact    | Status   | Path                | Member result | Link · commit           |
  |-------------|----------|---------------------|---------------|-------------------------|
  | idea.md     | <status> | <absolute path>     | <result>      | <link> · <hash>         |
  | validate.md | <status> | <absolute path>     | <result>      | <link> · <hash>         |
  | prd.md      | <status> | <absolute path>     | <result>      | <link> · <hash>         |
  | brand check | inline   | (no file)           | —             | RISK: … · RECOMMEND: …  |
  | tad.md      | <status> | <absolute path>     | <result>      | <link> · <hash>         |
  | tasks.md    | <status> | <absolute path>     | <result>      | <link> · <hash>         |

             Preflight: <lease|installed>, <members checked>; release: <done|not needed|failed>
             Sync: <done|skipped (reason)>
Uncertainty: <member>: <item>; stale: <files>; skipped: <checks>  — or: none within the checks run
Decision:    <the pending question> — or: No approval needed.
Next step:   <one action>
```

## Fill rules

- `Result:` comes first, and its first word is the status.
- Status values: `generated`, `reused`, `regenerated`, `skipped` (outside the range or opted out),
  `not reached` (the chain stopped earlier), `not written` (the member ran but wrote no file),
  `inline` (brand check only).
- `Member result` is the first word of that member's `Result:` line. Write `—` for an artifact no
  member ran for in this run (`reused`, `skipped`, `not reached`).
- Copy each link and hash from that member's `Evidence:` line. Never build a link yourself. When the
  member wrote `local only`, write `<hash> (local only)` with no link. A `reused` row reads `—`.
- `idea.md` and `validate.md` share idea-validator's commit hash.
- Put an artifact on a `generated` or `regenerated` row only when `test -s` passed on its file and its
  member report was read.
- Under `Uncertainty:`, label every item with its source member, or `product-planner` for this
  skill's own skipped checks (sync skipped, brand check skipped, release failed). Keep stale flags
  here: a regenerated `prd.md` makes an existing `tad.md` and `tasks.md` possibly stale.
- `Decision:` names the question the chain stopped on (verdict override, continue after a member's
  `PARTIAL`, sync conflict), or says `No approval needed.`

## Example: PARTIAL, push declined at stage 3

```text
◆ Product Planner — Final Report
··································································
Result:      PARTIAL — stages 3–4 (brand check: not requested)
             Verdict: Build it (Creativity 7, Feasibility 8, Market 6, Execution 8); override: none
             stopped after tad-generator because its push was declined and the user chose to stop
Evidence:    PROJECT_DIR: /Users/ana/ideas/2026_10_06_habit_nudge

  | Artifact    | Status      | Path                                  | Member result | Link · commit       |
  |-------------|-------------|---------------------------------------|---------------|---------------------|
  | idea.md     | reused      | /Users/ana/ideas/2026_10_06_habit_nudge/idea.md     | — | — |
  | validate.md | reused      | /Users/ana/ideas/2026_10_06_habit_nudge/validate.md | — | — |
  | prd.md      | reused      | /Users/ana/ideas/2026_10_06_habit_nudge/prd.md      | — | — |
  | tad.md      | generated   | /Users/ana/ideas/2026_10_06_habit_nudge/tad.md      | PARTIAL | d4e5f6a (local only) |
  | tasks.md    | not reached | —                                     | —             | —                   |

             Preflight: lease, tad-generator + tasks-generator; release: done
             Sync: done
Uncertainty: tad-generator: hosting budget answered TBD
Decision:    No approval needed.
Next step:   push the tad.md commit, then re-run /product-planner on this folder to resume at tasks-generator
```

## Example: BLOCKED at stage 4

```text
◆ Product Planner — Final Report
··································································
Result:      BLOCKED — stages 1–4 (brand check: skipped)
             Verdict: Maybe (Creativity 6, Feasibility 7, Market 5, Execution 6); override: none
             stopped at tasks-generator because it reported BLOCKED: python3 is not installed
Evidence:    PROJECT_DIR: /Users/ana/ideas/2026_10_06_bread_swap

  | Artifact    | Status      | Path                                     | Member result | Link · commit |
  |-------------|-------------|------------------------------------------|---------------|---------------|
  | idea.md     | generated   | /Users/ana/ideas/2026_10_06_bread_swap/idea.md     | COMPLETE | https://github.com/ana/ideas/blob/planning/2026_10_06_bread_swap/idea.md · a1b2c3d |
  | validate.md | generated   | /Users/ana/ideas/2026_10_06_bread_swap/validate.md | COMPLETE | https://github.com/ana/ideas/blob/planning/2026_10_06_bread_swap/validate.md · a1b2c3d |
  | prd.md      | generated   | /Users/ana/ideas/2026_10_06_bread_swap/prd.md      | COMPLETE | https://github.com/ana/ideas/blob/planning/2026_10_06_bread_swap/prd.md · b2c3d4e |
  | brand check | skipped     | (no file)                                | —             | brand-name-checker not installed |
  | tad.md      | generated   | /Users/ana/ideas/2026_10_06_bread_swap/tad.md      | COMPLETE | https://github.com/ana/ideas/blob/planning/2026_10_06_bread_swap/tad.md · c3d4e5f |
  | tasks.md    | not written | —                                        | BLOCKED       | —             |

             Preflight: installed, four chain members; release: not needed
             Sync: done
Uncertainty: idea-validator: market size rests on one source; product-planner: brand check skipped
             (brand-name-checker missing)
Decision:    No approval needed.
Next step:   install python3, then re-run /product-planner on this folder to resume at tasks-generator
```

The ideas repo was on the `planning` branch, so each member built its links with `blob/planning/`;
the report copies them unchanged.

## Reader checks

Before sending the report, check that a reader can answer each question from it alone:

1. What is the status, and where did the chain stop?
2. Which files exist now, and which member produced each one in this run?
3. Which statements are member-reported unknowns or skipped checks rather than verified results?
4. Is any approval pending, and what is the one next action?
