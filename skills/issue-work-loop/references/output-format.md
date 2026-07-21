# Output Format — /issue-work-loop

Terminal style follows shared conventions: symbols `● ✓ ✗ ◆ ⚡ ⚠ ○`, two-space indent, `┄` separators, URLs on their own line, ≤80 chars where practical.

## Preflight report

```
◆ Preflight (issue #{N})
··································································
  Git / gh:           √ pass
  Herdr server:       √ pass
  Skills:             √ pass (issue-resolver, issue-pr-review, herdr-agent-comms)
  Issue open:         √ pass — {title}
  Criteria:           √ 4/4 met
  Result:             PASS
```

## Plan banner (before spawn)

```
◆ Issue Work Loop Plan
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  Issue:         #{N} — {title}
  Max rounds:    {K}
  Agent CLI:     {agent_cli}
  Implementer:   {impl_name}
  Reviewer:      {rev_name}
  Merge:         USER (never auto)

  ⟶ Starting...
```

## Per-ROUND report

```
◆ ROUND {r}/{K}
··································································
  Context impl:       √ reuse ({p}%) | ⚡ freshen | ○ n/a
  Context rev:        √ reuse ({p}%) | ⚡ freshen
  Review:             √ CLEAN | ✗ FINDINGS ({count})
  Fix:                √ pushed {sha_short} | ○ skipped | × fail
  Criteria:           √ … 
  Result:             PASS | CONTINUE | FAIL
```

## SWEEP report

```
◆ SWEEP (cleanup)
··································································
  Worker panes:       √ closed impl-{N}, rev-{N}
  Worktrees removed:  √ {path} | ○ none
  On default branch:  √ {default_branch}
  Working tree:       √ clean
  Criteria:           √ 4/4 met
  Result:             PASS | PARTIAL | FAIL
```

## Final summary — CLEAN

```
◆ Issue Work Loop Complete
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  Issue:         #{N} — {title}
  PR:            #{M}
  {pr_url}
  Branch:        {branch} (remote only — local workspace cleaned)
  Head:          {sha}
  Rounds:        {r}/{K}
  Freshen:       impl={ni}, rev={nr}
  Cleanup:       √ panes closed, worktrees removed, on {default_branch}
  Verdict:       CLEAN

  Next:          open the PR and merge when ready (human only)
                 gh pr merge {M}
```

## Final summary — MAX_ROUNDS

```
◆ Issue Work Loop Stopped
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  Issue:         #{N}
  PR:            #{M}
  {pr_url}
  Rounds:        {K}/{K}
  Cleanup:       √ workspace cleaned (PR left open)
  Verdict:       MAX_ROUNDS

  Remaining FINDINGS:
  1. ...
  2. ...

  Next:          fix on GitHub / re-run /issue-work-loop {N},
                 or merge with known gaps (human decision)
```

## Final summary — FAILED / ALREADY_RESOLVED

```
◆ Issue Work Loop Ended
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  Issue:         #{N}
  Verdict:       FAILED | ALREADY_RESOLVED
  Phase:         {phase}
  Reason:        {short}
  PR:            {url or none}
  Cleanup:       √ | ⚠ partial | ○ skipped
```

## Compact success line (after full report)

```
  ✓ Issue #{N} ready for human merge (workspace clean)
    https://github.com/owner/repo/pull/{M}
```
