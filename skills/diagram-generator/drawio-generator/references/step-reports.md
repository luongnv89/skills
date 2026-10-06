# Step Completion Reports

Read this when printing a phase report (SKILL.md → *Step Completion Reports*). After each phase, print:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Per-phase checks:
- **Understand** — `Requirements gathered`, `Scope confirmed`
- **Propose** — `Plan presented`, `User confirmed` (or `Defaults stated` for a fully specified request)
- **Generate** — `XML generated`, `Output path chosen`, `Requirements covered`
- **Validate** — `Fix cycles N/3`, `Quality checks N/9`, `File written`

The Validate report precedes the Final Report (`final-report.md`); it does not replace it.
