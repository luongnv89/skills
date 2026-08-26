# Sync mode — refresh the epic dashboard

The full procedure behind SKILL.md's *Sync mode* summary. Read this when running
`/plan-to-issues sync <epic#>`.

`/plan-to-issues sync <epic#>` refreshes the dashboard so the epic reflects reality. It creates
nothing and edits exactly one body. Run the reduced preflight first (Phase 0 — env and gh groups only).

1. Fetch the epic. **No dashboard sentinels → stop**: `✗ Issue #N has no plan dashboard — is this
   the right epic?` Never overwrite a body this skill did not write.
2. Parse the child issue numbers and their task ids out of the dashboard checklist lines.
3. Fetch live states in one call: `gh issue list --state all --limit 500 --json number,state,title`.
   Filter to the dashboard's numbers; a number missing from the result is rendered `⚠ missing`, not
   silently dropped.
4. Re-parse the plan when it is still present, to detect **unmapped** plan tasks added since the
   last run. List them under `Not filed` in the dashboard and print the create-mode hint. Sync never
   files them itself.
5. Re-render and write back between the sentinels, exactly as Phase 5.

**Completion criteria:** every child number in the old dashboard appears in the new one with a state
of open, closed, or `⚠ missing`; per-phase and overall counts recomputed; the `Last synced` date
updated; the region outside the sentinels is unchanged.

