# Step Completion Reports

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

## Skill-specific checks per step

The five steps match `SKILL.md` → *Instructions*.

**Step 1: Check Prerequisites** — checks: `Input captured` (the input type from the Input Handling table), `Preflight` (`browse_mode` recorded, or `— not needed` when no live URL is loaded)

**Step 2: Process Input** — checks: `Evidence captured` (screenshots, widths, interactions, or files read), `Script output` (`process_screenshots.py` exit result, or `— not run`)

**Step 3: Evaluate** — checks: `Lens evaluation` (N of M applicable lenses scored; name each one not assessed), `Issue prioritization` (counts per severity; Thinking Cost matches them)

**Step 4: Generate Report** — checks: `Format compliance` (the `**Result:**` line, Evidence and Limits, and Next Decision are present), `Report clarity` (the four reader checks in `report-format.md`), `Report written` (`<output-dir>/usability-review.md`, or `— printed only`)

**Step 5: Redesign (if requested)** — checks: `Confirmation` (the user confirmed the dry-run diff, or `× not confirmed` with nothing written), `Redesign fidelity` (N of M confirmed fixes written), `Sync` (the Repo Sync record)

`PASS` means every check passed. `PARTIAL` means the step finished with a check failed or not assessed. `FAIL` means the step could not finish; the run then ends with the `BLOCKED` block or the `BLOCKED` Redesign summary.
