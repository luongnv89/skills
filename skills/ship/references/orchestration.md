# Orchestration Details

## Architecture

The main agent orchestrates: it runs the inline steps, applies each gate's outcome (`auto-mode.md`), and writes files. Subagents do the heavy reading in isolated context, in two waves, so the main conversation stays small and wave 2 builds on wave 1's results.

```
Main agent (orchestrator)
├── Step 1: Pre-flight (inline)
├── Step 2: Determine version (inline)
│
├── Step 3: Prepare changes
│   ├── Wave 1 (parallel)
│   │   ├── version-bumper       — every version source and old-version occurrence
│   │   └── changelog-generator  — CHANGELOG entry, GitHub notes, end-user notes
│   └── Wave 2 (parallel, reads wave 1 outputs)
│       ├── docs-updater         — README and docs narrative
│       └── landing-page-updater — version, end-user changelog, features, docs on the landing page
│
├── Step 4: Review — release-reviewer (mandatory in auto mode)
├── Step 5: Apply and sweep (inline)
├── Step 6: Build (inline)
├── Step 7: Commit, tag, push (inline)
├── Step 8: GitHub release (inline)
└── Step 9: Publish to registries (inline)
```

### Graceful degradation

If the Agent tool is not available (for example, on Claude.ai), run each agent file's task inline in the same order: wave 1, wave 2, then the review. This costs more context but follows the same logic.

## Workspace

```bash
WORKSPACE="$(mktemp -d "${TMPDIR:-/tmp}/ship-XXXXXX")"
mkdir -p "$WORKSPACE"/{version-bumper,changelog-generator,docs-updater,landing-page-updater}
```

## File ownership

Each file has one owner, so no two agents propose an edit to the same line:

Ownership follows the file's role, not its extension:

| Files | Owner |
|---|---|
| The history file (`CHANGELOG.md`, `CHANGES.*`, `HISTORY.*`, or `NEWS.*`) | changelog-generator |
| Landing-page files: every file that renders the landing site (entry page, partials, components, site pages), Markdown included, such as a Jekyll `index.md` | landing-page-updater, whole files, version strings included |
| Version strings in every other file | version-bumper |
| README and project docs narrative: Markdown/RST files and doc-site sources | docs-updater, except lines listed in `version-changes.json` |

The version-bumper and the docs-updater cannot see `landing_page_files` while they run, so they may propose lines in those files. The main agent drops those lines at apply time, and the reviewer does not count them as collisions.

## Wave 1 — spawn both in the same turn

**1. Version Bumper** — `agents/version-bumper.md`. Inputs:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: from Step 2 (empty on a first release)
- `NEW_VERSION`: from Step 2
- `OUTPUT_DIR`: `$WORKSPACE/version-bumper`

**2. Changelog Generator** — `agents/changelog-generator.md`. Inputs:
- `PROJECT_PATH`, `OLD_VERSION`, `NEW_VERSION`: as above
- `TAG`: the new tag name, such as `v1.3.0`
- `OUTPUT_DIR`: `$WORKSPACE/changelog-generator`

If an agent in either wave returns without its output files, re-spawn it once. If the files are still missing, stop: `BLOCKED — <agent> produced no output`. Never read a missing `landing-changes.json` as "no landing page".

## Wave 2 — spawn both in the same turn, after wave 1 returns

**3. Docs Updater** — `agents/docs-updater.md`. Inputs:
- `PROJECT_PATH`, `OLD_VERSION`, `NEW_VERSION`: as above
- `VERSION_CHANGES`: `$WORKSPACE/version-bumper/version-changes.json`
- `CHANGELOG_DIR`: `$WORKSPACE/changelog-generator`
- `OUTPUT_DIR`: `$WORKSPACE/docs-updater`

**4. Landing Page Updater** — `agents/landing-page-updater.md`. Inputs:
- `PROJECT_PATH`, `OLD_VERSION`, `NEW_VERSION`, `TAG`: as above
- `VERSION_CHANGES`, `CHANGELOG_DIR`: as for the docs updater
- `OUTPUT_DIR`: `$WORKSPACE/landing-page-updater`

The landing-page-updater first checks whether the project has a landing page: a marketing or home web page, distinct from the README and from API docs. If none exists, the common case for libraries and CLIs, it writes `landing_page_found: false` and the step is a no-op.

## Consolidated summary

Read the outputs and present them under four headings:

1. **Version changes** — `version-bumper/version-changes.md`, including any drift between version sources
2. **Changelog** — `changelog-generator/changelog-entry.md` and `user-notes.md`
3. **Doc updates** — `docs-updater/docs-changes.md`
4. **Landing page** — `landing-page-updater/landing-changes.md` with the status of its four items (version, end-user changelog, feature list, documentation), or "No landing page — skipped."

In interactive mode, ask: "Here's everything this release will change. Confirm, or tell me what to adjust." Wait for the answer. In auto mode, print the summary and continue to the review.

## Review

Spawn `agents/release-reviewer.md` with:
- `PROJECT_PATH`: the project root
- `WORKSPACE_DIR`: `$WORKSPACE`
- `OLD_VERSION`, `NEW_VERSION`: from Step 2
- `VERSION_RULE`: the Step 2 rule that chose `NEW_VERSION` (`argument`, a _Version rules_ row, or `commits`)

`PASS` and `NEEDS_FIX` handling: SKILL.md → Step 4.

## Apply changes

Apply in this order, so later edits build on already-bumped content. Before each edit, re-match its `old_line` or `old_text` against the current file. If it no longer matches, skip that edit and list it under `Uncertainty`.

1. Version strings from `version-changes.json`, except in files listed under `landing-changes.json` → `landing_page_files`. The landing-page-updater carries those lines.
2. The changelog, into the history file named by `changelog-metadata.json` → `history_file`. If `unreleased_section.found` is true, replace that section (its heading through the line before the next `## ` heading) with an empty `## Unreleased` heading followed by `changelog-entry.md`. Otherwise insert `changelog-entry.md` above the newest release entry, and create `CHANGELOG.md` with a `# Changelog` header if no history file exists. Never create `RELEASE_NOTES.md`.
3. Doc updates from `docs-changes.json`, except in files listed under `landing_page_files`.
4. Landing-page updates from `landing-changes.json`. Skip this when `landing_page_found` is false.

After applying, recompute each landing-page item's status: an `updated` item whose edits were all skipped is reported as "not updated: edit skipped" under `Uncertainty`, never as updated.
