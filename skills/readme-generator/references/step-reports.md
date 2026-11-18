# Step Completion Reports

After each workflow step, print a status block in this format:

```
◆ [Step name] (step N of 5 — [context])
··································································
  [Check]:                 √ pass (note)
  [Check]:                 × fail — [reason]
  ____________________________
  Result:                  PASS | FAIL | PARTIAL
```

Use `√` for a pass, `×` for a fail, and `—` for brief context. List only checks that ran. `PARTIAL` means the step produced its output but at least one check failed.

## Checks per step

| Step | Checks |
|---|---|
| 0 Sync | `Sync` (pulled, or `sync: skipped (<reason>)`) |
| 1 Gather facts | `Mode picked` (Create, Rewrite, or Landing only), `Install source` (`path:line`, or from source), `Common task source` (`path:line`, or the user's answer), `Output source` (`path:line`, or none) |
| 2 Back up | `Backup written` (file name), or `—` skipped in Create mode |
| 3 Write | `Landing section written`, `Detail sections written` (count), `Original sections placed` (N of N; Create: `—`) |
| 4 Self-review | One line per Step 4 check, then `Checks: N/8 passed` (`N/7` in Create mode) |
| 5 Present | `Summary given`, `Placeholders listed` (count) |

## Example

```
◆ Gather facts (step 1 of 5 — Rewrite mode)
··································································
  Mode picked:             √ pass (Rewrite: README.md has install and usage)
  Install source:          √ pass (README.md:9)
  Common task source:      √ pass (README.md:17, first usage example)
  Output source:           — none (no sample output in README, docs, or tests)
  ____________________________
  Result:                  PASS
```
