# Orchestration Details

## Architecture

This skill uses a **main-agent-as-orchestrator** pattern. The main agent handles user communication, confirmation gates, and lightweight steps. Heavy work (scanning files, generating changelogs, updating docs) is delegated to subagents that run in isolated context — keeping the main conversation clean and enabling parallel execution.

```
Main Agent (orchestrator)
├── Step 1: Pre-flight checks (inline)
├── Step 2: Determine version (inline — needs user input)
│
├── Steps 3-6: Spawn subagents in parallel ──────────────┐
│   ├── version-bumper    — scan & propose version changes │
│   ├── changelog-generator — generate changelog from git  │
│   ├── docs-updater      — find & propose doc updates      │
│   └── landing-page-updater — update landing page (if any) │
│                                                          │
├── Collect results, present to user for confirmation  ◄───┘
├── Spawn: release-reviewer — independent quality check
│
├── Step 7: Build (inline — needs user confirmation)
├── Step 8: Commit, tag, push (inline — needs user confirmation)
├── Step 9: GitHub Release (inline — needs user confirmation)
└── Step 10: Publish to registries (inline — needs user confirmation)
```

### Graceful degradation
If the Agent tool is not available (e.g., Claude.ai), execute steps 3-6 inline instead of spawning subagents. Follow the same logic described in each agent file, but run it directly in the main conversation. This is less context-efficient but functionally identical.

## Repo Sync Before Edits (mandatory)

See the "Repo Sync Before Edits (mandatory)" section in `SKILL.md` for the required sync commands. Run them before Steps 3-6 touch any files.

## Steps 3-6: Parallel Subagent Execution

Once the user confirms the version number, create a workspace directory and spawn four subagents in the same turn (parallel execution).

### Setup workspace

```bash
WORKSPACE="/tmp/release-workspace-$(date +%s)"
mkdir -p "$WORKSPACE"/{version-bumper,changelog-generator,docs-updater,landing-page-updater}
```

### Spawn subagents (all in the same turn)

**1. Version Bumper** — Read `agents/version-bumper.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version
- `OUTPUT_DIR`: `$WORKSPACE/version-bumper`

**2. Changelog Generator** — Read `agents/changelog-generator.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version
- `OUTPUT_DIR`: `$WORKSPACE/changelog-generator`

**3. Docs Updater** — Read `agents/docs-updater.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version
- `CHANGELOG_SUMMARY`: brief summary of changes from Step 2 analysis (e.g., "3 features, 2 fixes, 0 breaking changes")
- `OUTPUT_DIR`: `$WORKSPACE/docs-updater`

**4. Landing Page Updater** — Read `agents/landing-page-updater.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version
- `CHANGELOG_SUMMARY`: same summary passed to the docs-updater
- `OUTPUT_DIR`: `$WORKSPACE/landing-page-updater`

This agent first detects whether the project even has a landing page (a marketing/home web page, distinct from the README and from API docs). If none exists — the common case for libraries and CLIs — it returns an empty result and the step is a no-op. If one exists, it proposes release-narrative updates (hero/CTA copy, "What's New", feature highlights, download/changelog links). It deliberately leaves raw version-string bumps to the version-bumper to avoid editing the same line twice.

### Collect and present results

After all four subagents complete, read their output files and present a consolidated summary to the user:

1. **Version changes** — read `$WORKSPACE/version-bumper/version-changes.md` and show which files will be updated
2. **Changelog** — read `$WORKSPACE/changelog-generator/changelog-entry.md` and show the formatted entry
3. **Doc updates** — read `$WORKSPACE/docs-updater/docs-changes.md` and show proposed documentation changes
4. **Landing page** — read `$WORKSPACE/landing-page-updater/landing-changes.md`. If `landing_page_found` is false, note "No landing page — skipped." Otherwise show the proposed landing-page changes.

Present all four together: "Here's the full picture of what this release will change. Review and confirm, or tell me what to adjust."

### Independent review (optional but recommended)

After the user has seen the proposed changes, spawn the release-reviewer subagent for an independent quality check. It also reads the landing-page report and flags any cross-agent collision (two agents targeting the same file/line). Read `agents/release-reviewer.md` for the full prompt. Spawn with:
- `PROJECT_PATH`: the project root
- `WORKSPACE_DIR`: `$WORKSPACE`
- `OLD_VERSION`: confirmed old version
- `NEW_VERSION`: confirmed new version

If the reviewer returns `NEEDS_FIX`, present the issues to the user and address them before proceeding. If `PASS`, continue.

### Apply changes

Only after user confirmation, apply all changes **in this order** so later edits build on already-bumped content and never collide:
1. Update version strings in all files identified by the version-bumper
2. Prepend the changelog entry to `CHANGELOG.md` (create the file with a `# Changelog` header if it doesn't exist). Do NOT create or update a `RELEASE_NOTES.md` file
3. Apply documentation updates identified by the docs-updater
4. Apply landing-page updates identified by the landing-page-updater (skip if no landing page was found). If a landing-page change overlaps a line the version-bumper already changed (flagged under `version_overlap` or by the reviewer), apply it only once — re-match against the current file contents before editing.
