# Error Messages — /issue-work-loop

Rich format: `✗ what failed`, then `To fix:`, optional docs line.

## Authentication & Setup

### Not a git repository
```
✗ Not a git repository

  To fix:  cd into the project repo, or git init && git remote add origin <url>
```

### GitHub CLI not found
```
✗ GitHub CLI not found

  To fix:  brew install gh
  Docs:    https://cli.github.com
```

### Not authenticated
```
✗ Not authenticated with GitHub

  To fix:  gh auth login
  Docs:    https://cli.github.com/manual/gh_auth_login
```

### No GitHub remote
```
✗ No GitHub remote configured

  To fix:  git remote add origin <url>
```

### Herdr missing
```
✗ herdr not found on PATH

  To fix:  curl -fsSL https://herdr.dev/install.sh | sh
           (or: brew install herdr)
```

### Herdr server not running
```
✗ Herdr server is not running

  To fix:  open a real terminal and run: herdr
           (do not launch bare herdr from a non-TTY agent shell)

  Check:   herdr status
```

## Skills & Bundles

### Missing required skill
```
✗ Missing required skill(s): {names}

  To fix:  install issue-resolver, issue-pr-review, and herdr-agent-comms
           from the same distribution as this skill, then restart the session

  This skill needs all three to spawn workers and run resolve/review.
```

### Missing bundled dependency
```
✗ Missing bundled dependency: {missing_file}

  To fix:  reinstall issue-work-loop from the skills catalog
           (or restore references/ under the skill directory)

  Then restart the agent session and re-run /issue-work-loop.
```

## Issue & PR

### Issue number required
```
✗ Issue number required

  To fix:  /issue-work-loop <N>
  Example: /issue-work-loop 42
```

### Issue not found
```
✗ Issue #{N} not found

  To fix:  gh issue list --state open
           then re-run with a valid number
```

### Issue already closed
```
✗ Issue #{N} is already closed

  State:   {state}
  To fix:  reopen it if work remains: gh issue reopen {N}
           or pick a different open issue
```

### Implementer produced no PR
```
✗ Implementer finished without an open PR for issue #{N}

  Reason:  {failure_reason or "no PR detected"}
  To fix:  read the implementer pane, fix blockers, re-run
           /issue-work-loop {N}
```

### Ambiguous PR match
```
✗ Multiple open PRs reference issue #{N} — will not pick silently

  Candidates:
  - #{a}  {url_a}
  - #{b}  {url_b}

  To fix:  close extras, or tell the orchestrator which PR number to use
```

### Open PR already exists (single)
```
⚠ Issue #{N} already has open PR #{M}
  {pr_url}

  Choose one:
  (a) review-only + fix loop on PR #{M} (skip resolve)
  (b) abort

  The skill will not re-run /issue-resolver unless you close the PR first.
```

### Reviewer verdict missing
```
✗ Reviewer did not return VERDICT: CLEAN or VERDICT: FINDINGS

  To fix:  skill re-prompts once automatically; if it still fails,
           FRESHEN the reviewer or inspect pane rev-{N}
```

## Loop limits

### Max rounds exhausted
```
⚠ Max rounds reached ({K}/{K}) with remaining FINDINGS

  PR:      #{M}
  {pr_url}

  Remaining FINDINGS are listed in the final summary.
  Merge is still a human decision — the skill will not merge.
```

### Worker blocked
```
⚠ Worker {role} is blocked (trust/auth dialog)

  Pane:    {pane_id}
  Polling: every 30s for up to 15m (or until you say resume/abort)
  To fix:  focus the pane in Herdr, answer the dialog, then say:
           resume   — continue the loop
           abort    — stop the skill
```

### Stash pop failed
```
✗ Stash pop failed after repo sync

  To fix:  git stash list && git stash show -p stash@{0}
           resolve conflicts, then re-run /issue-work-loop
```
