# Sync mode — re-render the epic plan map

The full procedure behind SKILL.md's *Sync mode* summary. Read this when running
`/plan-to-issues sync <epic#>`.

**Sync is no longer part of the working loop.** The map carries no issue state, so nothing in it
goes stale as work proceeds — open/closed lives in the epic's **sub-issues panel**, which GitHub
maintains. Run sync only when the *set* of issues or the *plan* changes: more tasks filed, a task
added to the plan, a child re-parented. Running it after an issue merely closes is a no-op that
rewrites the body to identical bytes.

It creates nothing and edits exactly one body. Run the reduced preflight first (Phase 0 — env and
gh groups only).

1. Fetch the epic. **No map sentinels → stop**: `✗ Issue #N has no plan map — is this
   the right epic?` Never overwrite a body this skill did not write.

   An epic created but never filled (Phase 3 wrote the sentinel pair; Phase 4 was interrupted) has
   an **empty** pair. That is a valid epic, not a foreign issue, so sync proceeds: step 2 finds no
   children, step 4 lists every plan task as `(not filed)`, and the render shows a map with no issue
   numbers. Report it as `⚠ epic has no filed children — run /plan-to-issues to file them` rather
   than presenting an empty map as finished work.
2. Parse the child issue numbers and their task ids out of the map's task lines, matching the full
   task-line grammar (`^- #N — <task-id>`) rather than a bare `#N — id`. A plan title that cites an
   issue number would otherwise inject a phantom child — see `references/epic-dashboard.md` ->
   *Sync algorithm*.
3. Fetch the epic's registered children in one call:
   `gh api repos/{owner}/{repo}/issues/<epic>/sub_issues --jq '.[].number'`. Compare against the
   numbers parsed in step 2 — a child registered on the epic but absent from the map is one the map
   must gain; a number in the map that is no longer a child is one it must lose. Issue *state* is
   deliberately not fetched: the map does not render it.
4. Re-parse the plan when it is still present, to detect **unmapped** plan tasks added since the
   last run. They render in their phase as `- (not filed) — <id> <title>`, and the create-mode hint
   is printed. Sync never files them itself.
5. Re-render and write back between the sentinels, exactly as Phase 5. The plan-binding marker sits
   outside the sentinels and is preserved byte-for-byte like the rest of the body.

**Completion criteria:** every issue registered as a sub-issue of the epic appears exactly once in
the new map under its own phase; every plan task with no issue renders `(not filed)`; the rendered
date is updated; and the region outside the sentinels — the plan-binding marker included — is
unchanged. No status, count or percentage is asserted anywhere in the block, so there is nothing for
a later issue close to falsify.

