# Step Completion Reports

After each step, print a compact status block. Use `√` for pass, `×` for fail, and `—` to add brief context. The `Criteria` line counts the checks met, and the `Result` line gives the step's verdict.

```text
◆ Inventory (step 1 of 8 — comment inventory)
··································································
  Scope listed:          √ 42 files (9 generated, 3 vendored left out)
  Tokenizer used:        √ Python tokenize + ast for 42/42 files
  Units recorded:        √ 214 comments, 11 machine-read
  Audit file written:    √ $TMPDIR/comment-audit-shop-3f2a9c1/audit.md
  ____________________________
  Criteria:      4/4 met
  Result:        PASS
```

Adapt the check names to what the step actually checked.

## Checks per step

| Step | Checks |
|---|---|
| 0 Prepare | `Git repository`, `Repo synced` (or skipped, with the reason), `Scope listed`, `Base recorded`, `Baseline checks run`, `Branch ready` (Full mode) |
| 1 Inventory | `Scope listed`, `Tokenizer used` (or scanner, as an approximation), `Units recorded`, `Machine-read listed`, `Audit file written` |
| 2 Sort | `Every unit has a kind or is unsure`, `Stale entries cite evidence`, `Decisions grouped`, `Hacks grouped` |
| 3 Estimate | `Own lines summed`, `Inline and machine-read counted apart`, `Share of scope computed` |
| 4 Gate A | `Plan shown`, `Approval received` (or skipped), `ADRs written`, `ADR commit made` |
| 5 Gate B | `Duplicates searched`, `Plan shown`, `Approval received` (or skipped), `Issues filed or drafted` |
| 6 Gate C | `Plan shown`, `Approval received` (or skipped), `Deletion check clean`, `Baseline checks still pass`, `Tests passed not lower`, `Deletion commit made` |
| 7 Gate D | `Plan shown`, `Approval received` (or skipped), `Baseline written`, `Probe: passes on tree`, `Probe: fails on added comment`, `Probe: lowers on deletion`, `Ratchet commit made` |
| 8 Report | `Estimate and lines shed reported apart`, `Unchanged items listed`, `Final Report printed` |

A skipped gate reports `Approval received: — skipped by the user` and `Result: PASS`. A gate that stops with no user to answer reports `Result: PARTIAL`.
