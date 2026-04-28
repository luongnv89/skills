# Edge Cases, Step Reports, and Error Handling

## Edge Cases

| Scenario | Handling |
|---|---|
| Merge conflict detected | Stop; show conflicting files; tell user to resolve conflicts then re-run |
| Protected branch (main/master) | Warn with a banner; recommend creating a branch and using a PR instead |
| Empty commit (nothing staged) | Detect with `git status`; report "nothing to commit" and exit cleanly |
| No remote configured | Report "no remote origin"; suggest `git remote add origin <url>` |
| Push rejected (non-fast-forward) | Run `git pull --rebase && git push`; if rebase fails, stop and report |
| Pre-commit hook fails | Surface hook output; do not retry; ask user to fix the hook issue |
| Binary or large file (>10 MB) | Block and suggest Git LFS; do not stage the file |

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

- **Analyze Changes** — checks: `Modified files listed`, `Change statistics available`, `Recent commit style identified`
- **Safety Checks** — checks: `Safety scan`, `Secret detection`, `Large file check`, `Branch warning (main/master)`
- **Commit** — checks: `Staging complete`, `Commit message conventional`, `No merge conflicts`
- **Push** — checks: `Push success`, `Remote branch exists`, `Final log verified`

## Error Handling

- **git add fails**: Check permissions, locked files, verify repo initialized
- **git commit fails**: Fix pre-commit hooks, check git config (user.name/email)
- **git push fails**:
  - Non-fast-forward: `git pull --rebase && git push`
  - No remote branch: `git push -u origin [branch]`
  - Protected branch: Use PR workflow instead

## Alternatives

If user wants control, suggest:
1. **Selective staging**: Review/stage specific files
2. **Interactive staging**: `git add -p` for patch selection
3. **PR workflow**: Create branch → push → PR (use `/pr` command)
