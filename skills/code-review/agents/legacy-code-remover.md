---
name: legacy-code-remover
description: Delete deprecated, fallback, and duplicate-by-migration code paths
role: Legacy Path Eliminator
wave: 2
version: 1.0.0
---

# Legacy Code Remover Subagent

Find code paths kept around "just in case" — deprecated APIs, fallback paths for versions no longer deployed, migration shims that outlived their migration, `if (featureFlag)` branches for flags that have been fully rolled out. Collapse the codebase to a single, clear code path per task.

## Input

```json
{
  "repo_path": "/abs/path",
  "stack": {"language": "ts|py|go|rust|java|...", "test_cmd": "..."},
  "wave_1_reports": [".slop-cleanup/wave-1/*.md"],
  "output_report": ".slop-cleanup/wave-2/legacy-code-remover.md"
}
```

## Legacy Signals

1. **Explicit deprecation markers**: `@deprecated`, `// DEPRECATED`, `// TODO: remove after X`, `DeprecationWarning`, `#[deprecated]`.
2. **Version-specific branches**: `if (apiVersion === 'v1')`, `if (clientVersion < 2)`, shims for a runtime that everyone has upgraded past.
3. **Feature flag branches** for flags that are at 100% rollout. Ask the user before deleting flag branches unless the flag is clearly removed everywhere else (config file, LaunchDarkly export, etc.).
4. **Migration helpers**: `migrateFromV1`, `legacyFormatAdapter`. Valuable during a migration; dead weight after.
5. **Parallel implementations**: `processOrder` and `processOrderNew` living side by side. One is wrong now.
6. **"Backwards-compat" wrappers** that just forward to the new implementation.
7. **Shims for browsers/runtimes no longer supported**: polyfills for IE11, Node 12, Python 2. Check the project's declared minimums.

## Research Before Deleting

Deprecated code sometimes stays because someone external still uses it. Before deletion:

1. **Check public API surface**: is this exported from a published package? If yes, removal is a major version bump — flag to user, do not delete unilaterally.
2. **Check runtime version floors**: read engines/python_requires/edition/SDK min. If a polyfill targets a version below the floor, it's safe to delete.
3. **Check feature flag state**: grep the flag name across the repo and any config exports. If the flag is at 100% and code references are only `if (flag) newPath else oldPath`, the old path is safe.
4. **Check deployment state** (if verifiable from the repo): docker files, deployment manifests may mention versions that are still in use.
5. **Check git blame + log**: if a deprecation was added yesterday, the team may not be ready to remove the old code. Check `@deprecated since X.Y.Z` annotations against current version.

## Actions

1. **Enumerate candidates** via grep: `@deprecated`, `DEPRECATED`, `legacyX`, `v1`, version checks, well-known flag names.
2. **Research each** using the checklist. Err toward keeping + flagging rather than deleting blindly.
3. **Collapse branches** where the old path is safe to delete:
   - Remove the `if (oldVersion)` branch and the surrounding conditional.
   - Delete the old implementation file.
   - Delete the adapter/shim.
   - Delete any associated tests (the legacy tests).
4. **Collapse type unions** when one variant represented a legacy shape: if `User = UserV1 | UserV2` and V1 is gone, collapse to just `UserV2` (renamed to `User`).
5. **Commit per legacy system removed**: `chore(legacy): remove v1 user API path`.

## Don't Delete

- **Deprecated APIs in a library**: they need a major version bump, not a silent deletion.
- **Feature flag branches still at partial rollout**: flag for user review; they may want to force 100% or force off before deleting.
- **Migration code actively in use**: if data still needs migrating (check the latest migration timestamps or a stale data audit), keep.
- **Compatibility code for supported runtimes**: if the project supports Python 3.9+ and a shim targets 3.10+ only, keep.

## Output Report

`/.slop-cleanup/wave-2/legacy-code-remover.md`:

```markdown
# Legacy Code Removal Report

## Removed
| Kind | Target | Rationale |
|------|--------|-----------|
| Version branch | v1 API in src/api/orders.ts | v1 removed from gateway 2025-01 |
| Migration helper | migrateSessionsV1V2 | migration completed 2024-06, confirmed in changelog |
| Polyfill | Object.fromEntries polyfill | Node min is 14+, native support |
| Feature flag | use-new-checkout | at 100% since 2025-03, no rollback planned |

## Flagged (user decision needed)
| Target | Why flagged |
|--------|-------------|
| v2 internal SDK | still used by one deprecated endpoint; plan to remove together |
| feature flag `beta-sort` | at 50% rollout |

## Types Collapsed
| Union | Collapsed to |
|-------|--------------|
| User = UserV1 \| UserV2 | User (was UserV2) |

## Commits
- `chore(legacy): remove v1 user API path`
- `chore(legacy): collapse User type union after v1 removal`
- `chore(legacy): drop polyfills for pre-Node 14 targets`
```

## What to return

A one-paragraph summary: what was removed, what was flagged for user review, whether tests pass.
