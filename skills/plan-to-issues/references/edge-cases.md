# Edge cases

The full catalogue. SKILL.md keeps only the three that change the main path; everything
else lives here. Read this when a run hits something unusual.

- **Plan phase with no tasks** ("nothing found in this phase") — the dashboard keeps the phase with
  `— no tasks in plan`. Never renumber or drop a phase.
- **`--phase` filter** — unfiled phases still appear in the dashboard, marked `— not filed`, so the
  epic never implies work that was skipped is complete.
- **> 100 tasks** — print the count and confirm before filing; GitHub secondary rate limits make an
  unattended 100+ batch unreliable.
- **Rate limited mid-batch** — `/issue-creator` retries with backoff and reports per item. Re-run
  Create mode: **idempotent re-run** skips what landed and files the rest.
- **Epic already exists** — reuse it (`references/epic-identity.md` step 1). If the user wants a
  fresh epic, they close the old one first; this skill never orphans children by silently
  re-parenting.
- **Deferred findings** — the plan's Deferred table is rendered in the dashboard as a table. Deferred
  work is a decision, not a backlog item: no issues are filed for it.
- **Plan file deleted before a sync** — sync still refreshes states from the tracker and notes
  `plan file not found — unmapped-task check skipped`.
- **Non-GitHub remote** — stop at Phase 0. `gh` is the only supported tracker driver.
- **Issues disabled, or the repo archived** — stop at preflight probe G4. There is nothing to file into,
  and no partial run to salvage.
- **Two `gh` accounts logged in** — preflight probe G2 names the active one and asks for confirmation
  before filing. Fifty issues authored by the wrong identity is a painful thing to undo.
- **Read-only or triage-only permission** — `TRIAGE` proceeds with label *creation* disabled (existing
  labels still apply); `READ`/`NONE` stops, since neither labels nor the epic dashboard could be
  written. `--dry-run` still works and is offered.
- **Sync on a foreign issue** — no sentinels, so stop (Sync step 1). Never clobber a body this skill
  did not author.
- **Task depends on an id not in the plan** — record it in the report and render the dependency in
  the dashboard as `⚠ unknown dep <id>`; do not invent an issue for it.

