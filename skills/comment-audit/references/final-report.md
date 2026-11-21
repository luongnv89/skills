# Final Report

The four-line block that ends every run, stops included. It follows the Step 8 summary and never replaces it. `SKILL.md` → *Final Report* holds a `COMPLETE` example.

## Status

| Status | When |
|---|---|
| `COMPLETE` | Every group the user approved was applied and passed its checks. A Read-only run, and a run where the user approved nothing, are `COMPLETE` too; the `Result:` says which. `COMPLETE (no comments)` when the scope held none |
| `PARTIAL` | The run stopped at a gate with no user to answer; an approved group failed a check (the deletion check, a baseline check, a ratchet probe) and was rolled back or left incomplete; the deletion is unverified because no check could run; or issues are still drafts, so their Excuse comments stayed |
| `BLOCKED` | Nothing was read or changed: not a git repository, the repo sync stopped, or the request is out of scope |

A gate that waits for the user's answer in a live conversation does not end the run.

## Fill rules

- `Result:` the status, the scope, the counts per kind (and unsure), and what changed: comments deleted, ADRs written, issues filed or drafted, ratchet added.
- `Evidence:` each check that ran, with its result: the deletion check, the baseline checks before and after with test counts, each ratchet probe, and the ADR paths and issue numbers. Then the sync line. Cite only checks that ran.
- `Uncertainty:` approximations (a scanner instead of a tokenizer), languages left out, unsure entries, pre-sync paths, an unverified deletion, the ratchet's known gaps, and the two figures: the estimate if every comment went, and the comment lines deleted this run (blank lines and inline edits apart). With nothing else to say, still give the two figures.
- `Decision:` what waits on the user (unsure kinds, unapproved groups, issue drafts to file, checks to run elsewhere), or "No approval needed". Then the remaining user action, such as reviewing the branch or opening a pull request.

## PARTIAL example

```text
Result: PARTIAL. Sorted 37 comments in services/sync/ (Tautology 21, Excuse 6, Stale 7, Decision Record 3) and stopped at Gate A: no user is present to approve, so nothing was changed.
Evidence: inventory by tokenizer for 12 Python files; Gate 0 took its no-change path (no sync, no branch, no checks); plan for 2 ADRs in audit.md.
Uncertainty: Estimate if every comment went: 64 lines (4.1% of 1,560 non-blank lines); comment lines deleted this run: 0. 4 machine-read comments are excluded (2 noqa, 1 license header, 1 doctest).
Decision: Approve, change or skip the Gate A plan (2 ADRs) to continue; Gates B to D follow.
```

## BLOCKED example

```text
Result: BLOCKED. Nothing was read or changed: /work/site is not a git repository.
Evidence: `git rev-parse --show-toplevel` failed with "not a git repository".
Uncertainty: None beyond the checks listed.
Decision: Run the audit inside a git repository, or run `git init` and commit the code first.
```

## Reader checks

Before you print the block, confirm these four checks:

1. **Result findable:** the first line states the status and what changed.
2. **Facts and assumptions separated:** each verified item names its check or command, and each approximation is labeled.
3. **Claims traceable:** each count and check cites a command result, a file, or an ID in `audit.md`.
4. **Next decision clear:** `Decision:` names the approval needed, or says none is needed, and names any remaining user action.

Agent checks cannot confirm that a human understood the report. Without a human reviewer's answer, label human understanding as unconfirmed.
