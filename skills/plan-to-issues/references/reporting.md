# Step Completion Reports

Emitted after every phase.

```text
◆ [Phase Name] (phase N of 7 — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

## Per-phase check names

- **Preflight:** `Tools present`, `gh ready`, `Repo writable`, `API budget`, `Skills installed`,
  `Bundled files`, `Input resolved`
- **Parse / draft:** `Input resolved`, `Task count matches` (file path) or `Draft confirmed`
  (fresh conversation) or `Source restored` (`--epic` resume), `Fields complete`, `Deps
  resolvable`, `Critical path recorded`
- **Labels:** `Set computed`, `Existing checked`, `Missing created`, `Dropped recorded`
- **Epic:** `Existing epic checked`, `Epic created`, `Epic labelled`, `Source marker bound`
- **File issues:** `Batches run`, `Duplicates skipped`, `Labels applied`, `Parent markers present`,
  `Sub-issues registered`, `Dependency pass`
- **Plan map:** `Render exit 0`, `Sentinels intact`, `Every issue listed once`, `No status asserted`
- **Verify:** `Epic re-read`, `Children re-read`, `Repairs applied`, `Unresolved 0`
- **Sync (one report):** `Sentinels found`, `Children fetched`, `Unmapped listed`, `Map rewritten`

## Expected output

A successful Create run from a plan file:

```text
Source:    file docs/MODERNIZATION_PLAN.md (Pre + P0–P4, 10 sprints, 50 tasks)
Epic:      #100 Epic: Modernize acme-api — Pre + P0–P4
Labels:    12 required, 5 created, 0 dropped
Issues:    50 filed, 0 skipped (0 already existed), 0 failed
Map:       6 phases, 6 milestones, critical path Pre.1 → Pre.2 → 0.1 → 2.4
Verify:    epic re-read √ · 50/50 children re-read √ · 0 repairs

https://github.com/acme/acme-api/issues/100
```

From a conversation:

```text
Source:    conversation "Harden the ingest path" (1 phase, 6 tasks, draft confirmed)
Epic:      #212 Epic: Harden the ingest path
Labels:    5 required, 2 created, 0 dropped
Issues:    6 filed, 0 skipped, 0 failed
Map:       1 phase, 0 milestones, critical path 1.1 → 1.2 → 1.5
Verify:    epic re-read √ · 6/6 children re-read √ · 0 repairs
Re-run this backlog with: /plan-to-issues --from-conversation --epic 212

https://github.com/acme/acme-api/issues/212
```
