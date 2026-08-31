# Acceptance Criteria (full)

The unabridged run-success contract. SKILL.md carries a condensed form and points here.


The run is successful only if **all** hold:

- [ ] Preflight passed every applicable check before the first mutation, and resolved exactly one
      input. Degraded checks are named in the final report.
- [ ] On a fresh conversation, the user confirmed the drafted task list verbatim before anything
      was created, and that draft is recorded under `## Source`. On `--epic <n>` resume, the
      existing fenced `## Source` **is** that confirm — do not re-ask.
- [ ] Every task in scope has exactly one issue, and every issue traces to a task id.
- [ ] Every child issue carries `Part of #<epic>` and a label set with at least `phase:` and a type
      label; every child with dependencies also carries `Depends on #N`.
- [ ] Every child issue is registered as a **native sub-issue** of the epic — verified against
      `gh api repos/{owner}/{repo}/issues/<epic>/sub_issues`, not assumed from `--parent`.
- [ ] The epic exists, carries the `epic` label, and its body holds exactly one source marker for
      this input and one plan map between the sentinels — verified by re-reading, not by exit code.
- [ ] The map groups every child by phase, in order, and asserts **no issue status**: no checkbox,
      progress bar, percentage, milestone verdict, or "next actionable". Re-rendering it after
      issues close reproduces identical bytes.
- [ ] Milestones from the input appear in the map with their measurable exit conditions.
- [ ] No source file was modified — including on the conversation path, which **never materializes a
      plan file**. `git status --porcelain` matches the pre-run snapshot (the mandatory sync aside).
- [ ] Re-running Create mode on the same input creates zero duplicate issues and zero new epics —
      automatically on the file path, and via the reuse prompt or `--epic <n>` on the conversation
      path.
- [ ] Every dropped label, failed creation, and unmapped task is named in the final report.

If any criterion fails, report it as a `FAIL` row and do not claim success.

