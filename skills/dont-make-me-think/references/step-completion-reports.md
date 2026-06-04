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

## Skill-specific checks per phase

**Phase: Input Processing** — checks: `Input captured`, `Type identified`

**Phase: Usability Evaluation** — checks: `Lens evaluation`, `Issue prioritization`

**Phase: Report Generation** — checks: `Report clarity`, `Format compliance`

**Phase: Redesign (if requested)** — checks: `Redesign fidelity`, `Report clarity`, `Issue prioritization`
