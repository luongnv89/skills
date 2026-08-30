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

If any criterion fails, report it as a `FAIL` row in the Step Completion Report and do not claim
success.
