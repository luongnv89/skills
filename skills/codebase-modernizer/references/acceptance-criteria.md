# Acceptance Criteria — the full run checklist

Walk this list before writing `MODERNIZATION_REPORT.md`'s closing summary and again before
declaring the run complete. The run is successful only if **all** of these hold. SKILL.md keeps
the two read-only bars inline because they are the promise this skill exists to make; every other
criterion lives here.

## Outputs

- [ ] `MODERNIZATION_REPORT.md` and `MODERNIZATION_PLAN.md` both exist at the target repo root.
- [ ] The baseline table is complete with a `GREEN | AMBER | RED` verdict and per-row evidence.
- [ ] All 10 dimensions appear in the coverage table with `Audited` or `Not Assessed + reason`.
- [ ] Limitations lists every **Not Assessed** dimension, missing tool, and degraded pass.

## Read-only contract

Both bars below are restated in SKILL.md — they are the contract, not detail.

- [ ] **No tracked file's content changed** relative to the pre-run snapshot. On a clean tree,
      `git diff --stat` is empty. On a stale already-dirty tree, `git status --porcelain` and
      `git diff` match the snapshot taken before the run (declared artifacts set aside). No
      source, manifest, lockfile, hook, workflow, test, or docs file was modified by the audit.
- [ ] Every new file in `git status --short` is either one of the two reports, a **declared
      delegate artifact** (`CODE_REVIEW.md`), or a probe byproduct listed in the report's
      Artifacts section. Anything else is a contract breach.

## Findings

- [ ] Every finding record has a unique `F-<DIM>-<NNN>` ID, a severity, and `path:line` evidence
      (or manifest+version for `DEP`).
- [ ] Every `Critical` and `High` finding is closed by at least one task in the plan.

## Plan

- [ ] The plan starts with the Agent-environment pre-step, then P0–P4, each with ≥ 1 sprint and a
      measurable milestone. Pre is present whether `CLAUDE.md` / `AGENTS.md` already exist
      (update) or not (create). `/agent-config` is named, never invoked.
- [ ] Every task has ≥ 2 testable acceptance criteria, explicit `Dependencies`, an effort
      estimate, and a `Closes:` line. P0–P4 tasks include a baseline-green assertion. Pre is
      exempt when the baseline is RED (install/run notes plus create-or-update of
      `CLAUDE.md` / `AGENTS.md`).
- [ ] The dependency table has no broken task IDs and no cycles; the critical path is stated.
- [ ] Major dependency bumps are one task each, never batched, each naming its migration source.

## Final report — understandable

Correct files are not enough: the user must be able to read the result. Check the final chat report
(`references/output-format.md`) against these four criteria:

- [ ] **Main result is findable.** The first line is `Result:` with `COMPLETE`, `PARTIAL — <reason>`,
      or `BLOCKED — <reason>`, set by the SKILL.md rules. The reader needs no log or file to learn
      the status.
- [ ] **Facts and assumptions are separated.** `Evidence:` names only checks that ran. Every Not
      Assessed row, degraded path, and unexecuted item is under `Uncertainty:`. Inferences and
      assumptions carry a label.
- [ ] **Claims are traceable.** Each material claim points to its evidence: a command, a
      `path:line`, or a finding ID. A passing phase report does not imply the run is complete.
- [ ] **Next decision is clear.** `Decision:` says `No approval needed.` or names the approval, and
      `Next:` names the user's remaining action.

Agent inspection checks that these are present. It cannot confirm that a human understood the
report. If no human reviewer answered, record human understanding as unconfirmed; do not count it
as passed.

If any criterion fails, report it as a `FAIL` row in the Step Completion Report and do not claim
success.
