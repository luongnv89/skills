# Change Summary

The report every doc-manager run ends with, including a run that stops early. It is concise terminal text: four labeled items, then one per-doc table. Use the same format on a read-only tree; there the summary also carries the emitted diff and the inline validation script.

## Required items, in this order

| Item | Content |
|---|---|
| `Result:` | The status word first, then one sentence on what changed. |
| `Evidence:` | The Step 4 checks actually run and what each one showed: FLAG grep count, links checked, orphan check, each `validate-<name>.sh --check` exit code. |
| `Uncertainty:` | Open `FLAG`s, operator prerequisites that leave `--check` non-zero, and anything not checked (for example, Mermaid not rendered because `mmdc` is missing). Label inferences as inferences. |
| `Decision:` | What the user must approve or answer: open `FLAG` questions, the deletion of user-authored prose, a commit. If nothing is needed, write `No approval needed.` |

## Status rules

Every run gets exactly one status. When more than one seems to fit, use the first match in this order: `BLOCKED`, `FAIL`, `PARTIAL`, `COMPLETE`.

- `BLOCKED — {reason}` — the run stopped before Step 2 began, so no file was edited: the user did not confirm the scope, the repo sync failed, or a prerequisite failed.
- `FAIL — {reason}` — Step 2 began (editing may have started), and then either the run stopped before Step 4 finished (an edit or check errored, a conflict appeared, or the user stopped it), or Step 4 finished with a check the agent could have satisfied still failing (an agent-fixable `--check` failure, a broken internal link, an orphaned doc). `Uncertainty:` lists any files already edited, so the user can review or revert them.
- `PARTIAL — {reason}` — Step 4 finished with no agent-fixable failure, but at least one doc is `flagged`, or a `--check` run is non-zero only because of documented operator prerequisites.
- `COMPLETE` — Step 4 finished, every doc in scope is `updated` or `verified-current`, no `FLAG` remains, and each runbook script's agent-satisfiable checks pass.

A `validate-<name>.sh` exit 0 proves only that its listed checks passed, not that the runbook was executed end to end. Say so when a reader could assume more.

## Per-doc table

| Doc | Status | Change | Cites added | Open FLAGs |
|---|---|---|---|---|

`Status` is `updated`, `verified-current`, or `flagged`. In a `FAIL` or `BLOCKED` run, a doc the run did not reach is `unknown`. Use `—` for an empty cell.

## Example

```
Result:       PARTIAL — 3 docs reconciled, 1 claim flagged
Evidence:     FLAG grep: 1 marker (docs/deployment.md:14), listed below
              Links: 23 internal links resolve; orphans: none
              validate-deploy.sh --check: exit 1 (operator prereq, see Uncertainty)
Uncertainty:  The deploy region in docs/deployment.md:14 is not in the code
              Operator prereq: $DEPLOY_TOKEN unset, so --check exits 1 here
              Mermaid not rendered: mmdc not installed
Decision:     Confirm the deploy region (eu-west-1 or us-east-1). No commit made.

| Doc                | Status           | Change              | Cites added | Open FLAGs |
|--------------------|------------------|---------------------|-------------|------------|
| README.md          | updated          | port 3000 → 8080    | 4           | —          |
| docs/api.md        | verified-current | —                   | 0           | —          |
| docs/deployment.md | flagged          | validate script     | 6           | 1          |
```

## Reader checks

A summary is understandable when a reader can:

1. Find the result and its status in the first line, without reading the table.
2. Tell verified facts (each tied to a check or a `path:line`) apart from open FLAGs and inferences.
3. Trace each claim to its evidence: a check output, a cite, or a file path.
4. Name the next decision, or see `No approval needed.`

Agent inspection cannot confirm these. Ask the user whether the four checks hold. If the user gives no feedback, report human understanding as unconfirmed.
