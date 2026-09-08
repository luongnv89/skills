# Output Format — /issue-work-loop

Terminal style: `● ✓ ✗ ◆ ⚡ ⚠ ○`, two-space indent, separators, URLs on their own line, and approximately 80 columns where practical. Every report names `mode: ISSUE | PR`.

## Preflight — ISSUE

```text
◆ Preflight (ISSUE #{N})
··································································
  Git / gh / Herdr:  √ pass
  Skills:             √ issue-resolver, issue-pr-review, herdr-agent
  Issue open:         √ #{N} — {title}
  Linked open PRs:    √ 0 | ⚠ 1 → awaiting switch | × {count}
  Criteria:           √ 4/4 met
  Result:             PASS | FAIL
```

Exactly one linked open PR prints the confirmation from `error-messages.md`; accepting restarts the report as PR mode, declining reports ABORTED.

## Preflight — PR

```text
◆ Preflight (PR #{M})
··································································
  Git / gh / Herdr:  √ pass
  Skills:             √ issue-pr-review, herdr-agent
  PR open:            √ #{M} — {title}
  Head:               √ {head_ref} @ {sha_short}
  Source / fork:      √ {owner_repo} | ⚠ unknown; review allowed
  Issue context:      {none | #N | #N,#K}
  Explicit link:      √ matched | ○ not supplied | × mismatch
  Criteria:           √ 6/6 met
  Result:             PASS | FAIL
```

## Plan banners

```text
◆ Issue Work Loop Plan
  Mode:          ISSUE
  Issue:         #{N} — {title}
  Max rounds:    {K}
  Implementer:   {impl_name}
  Reviewer:      {rev_name}
  Merge:         USER only
```

```text
◆ PR Work Loop Plan
  Mode:          PR
  PR:            #{M} — {title}
  {pr_url}
  Head:          {head_ref} @ {sha_short}
  Issue context: {none | #N | #N,#K}
  Max rounds:    {K}
  Reviewer:      {rev_name} (spawn first)
  FIXER:         lazy {fix_name} (FINDINGS + safe push only)
  Merge:         USER only
```

## Per-ROUND — ISSUE

```text
◆ ROUND {r}/{K} (ISSUE)
··································································
  Current head:       √ {sha_short}
  Context reviewer:   √ reuse ({p}%) | ⚡ freshen
  Review:             √ CLEAN | ✗ FINDINGS ({count})
  Context implementer:√ reuse ({p}%) | ⚡ freshen | ○ CLEAN exit
  Fix:                √ pushed {new_sha_short} | ○ skipped | × fail
  Same PR / branch:   √ #{M} / {head_ref}
  Criteria:           √ {n}/{total} met
  Result:             PASS | CONTINUE | FAIL
```

## Per-ROUND — PR

```text
◆ ROUND {r}/{K} (PR)
··································································
  Current head:       √ {sha_short}
  Reviewer SHA:       √ matched | × stale
  Review:             √ CLEAN | ✗ FINDINGS ({count})
  Push safety:        √ pass | ○ not needed | × unavailable/unknown
  FIXER pane:         √ {fix_name} | ○ not spawned | × prohibited
  Isolated worktree:  √ {path} | ○ not needed | × missing
  Fix / new head:     √ {new_sha_short} | ○ CLEAN exit | × stopped
  Same PR / branch:   √ #{M} / {head_ref}
  Criteria:           √ {n}/{total} met
  Result:             PASS | CONTINUE | FAIL
```

A CLEAN-first PR report must show `FIXER pane: ○ not spawned` and `Isolated worktree: ○ not needed`.

## Push-safety handoff — review completed, fixing blocked

```text
◆ PR Work Loop Stopped (push safety)
  Mode:          PR
  PR:            #{M}
  {pr_url}
  Head:          {head_ref} @ {sha}
  Issue context: {none | #N | #N,#K}
  Review:        FINDINGS ({count})
  FIXER:         not spawned
  Push:          not attempted — {reason}

  Remaining FINDINGS:
  1. ...

  Next:          PR owner/collaborator applies fixes on the existing branch,
                 then re-run /issue-work-loop --pr {M}
```

## SWEEP — mode aware

```text
◆ SWEEP (cleanup, {ISSUE|PR})
··································································
  Worker panes:       √ closed {spawned_names} | ○ none | ⚠ partial
  Worktrees removed:  √ {paths} | ○ none | ⚠ partial
  Issue-resolver wt:  √ removed | ○ not applicable (PR mode)
  On default branch:  √ {default_branch}
  Working tree:       √ clean
  Criteria:           √ 5/5 met
  Result:             PASS | PARTIAL | FAIL
```

`spawned_names` is ISSUE implementer+reviewer, or PR reviewer plus optional FIXER. Never claim a FIXER was closed when one was not spawned.

## Final — CLEAN

```text
◆ Work Loop Complete
  Mode:          {ISSUE|PR}
  Issue context: {#N | none | #N,#K}
  PR:            #{M}
  {pr_url}
  Branch:        {head_ref} (remote open; local loop worktree removed)
  Head:          {sha}
  Rounds:        {r}/{K}
  Spawned roles: {IMPLEMENTER, REVIEWER | REVIEWER | REVIEWER, FIXER}
  Freshen:       {role=count, ...}
  Cleanup:       √ | ⚠ partial | ○ skipped
  Verdict:       CLEAN

  Next:          inspect and merge manually if ready
                 {pr_url}
```

## Final — MAX_ROUNDS

```text
◆ Work Loop Stopped
  Mode:          {ISSUE|PR}
  Issue context: {#N | none | #N,#K}
  PR:            #{M}
  {pr_url}
  Head:          {head_ref} @ {sha}
  Rounds:        {K}/{K}
  Spawned roles: {roles}
  Cleanup:       √ | ⚠ partial | ○ skipped
  Verdict:       MAX_ROUNDS

  Remaining FINDINGS:
  1. ...

  Next:          continue fixes on this PR or re-run the same mode;
                 merge remains a human decision
```

## Final — FAILED / ALREADY_RESOLVED / ABORTED

```text
◆ Work Loop Ended
  Mode:          {ISSUE|PR}
  Issue context: {none | #N | #N,#K}
  Verdict:       FAILED | ALREADY_RESOLVED | ABORTED
  Phase:         {phase}
  Reason:        {short}
  PR:            {url or none}
  Head:          {sha or unknown}
  Spawned roles: {roles or none}
  Cleanup:       √ | ⚠ partial | ○ skipped
```

## Demanding completion report

Each phase/ROUND uses:

```text
◆ {Step} ({mode})
··································································
  {GitHub/pane/SHA/worktree check}: √ pass | × fail — {evidence}
  Criteria:                         √ N/M met
  Result:                           PASS | CONTINUE | FAIL | PARTIAL
```

A final CLEAN PASS is invalid unless a fresh GitHub query matches PR number, OPEN state, branch, reviewed SHA, and zero FINDINGS; SWEEP must separately account for every spawned pane and loop-created worktree.
