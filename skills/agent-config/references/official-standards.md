# Official Standards: AGENTS.md, Claude Code, Codex

The rules this skill enforces, and where they come from. For evidence on *what* to write, see `agents-md-writing.md`.

## AGENTS.md (the open standard)

- A README **for agents**, in plain Markdown, with no required fields or schema. The Agentic AI Foundation (Linux Foundation) stewards it. Codex, Cursor, Copilot, Jules, Aider, Zed, Factory, and Claude Code, among others, read it.
- **The closest file wins.** A nested `AGENTS.md` in a monorepo package takes precedence over its ancestors, and an explicit user prompt overrides every file.
- Agents run the checks the file lists and fix failures before they finish.

## Claude Code: which file it reads

Claude Code reads `AGENTS.md` natively from **v2.1.277**, through a built-in `agents-md` plugin. With the default setting, `claude-md-or-agents-md`:

| The repository has | Claude reads |
|---|---|
| `AGENTS.md`, and no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` in the working directory or above | `AGENTS.md` |
| `AGENTS.md` plus any of those CLAUDE files | the CLAUDE files only |
| a `CLAUDE.md` that imports `@AGENTS.md` | `CLAUDE.md`, with `AGENTS.md` included once (never twice) |

- **Files that don't count toward that check**, and load alongside `AGENTS.md`: `~/.claude/CLAUDE.md`, the managed-policy `CLAUDE.md`, and `.claude/rules/*.md`.
- **What Claude reads**:
  - At session start, every `AGENTS.md` and `.claude/AGENTS.md` from the working directory up.
  - On demand, a subdirectory's `AGENTS.md`, when Claude reads a file there and that directory has no CLAUDE file.
  - Inside `AGENTS.md`, `@path` imports are expanded and `claudeMdExcludes` applies.
- **What Claude never reads**: `AGENTS.local.md`, `AGENTS.override.md`, or anything under `.agents/`.
- **The Project instructions setting** (in `/config`) has four values:
  - `claude-md-or-agents-md` is the default.
  - `claude-md-and-agents-md` reads both: each directory's CLAUDE files first, then its `AGENTS.md`.
  - `claude-md` reads CLAUDE files only.
  - `managed-only` reads only the organization's managed instructions.

  It can be set in user or managed settings (`pluginConfigs["agents-md@builtin"].options.instructionFiles`) but is **ignored in project and local settings**. A repo cannot force it, so the `@AGENTS.md` import is the only fix that can be committed for a shadowed `AGENTS.md`.
- **When there's no AGENTS.md support**, Claude reads CLAUDE files only:
  - before v2.1.277;
  - when the `agents-md` plugin is disabled;
  - sometimes, in the first session after upgrading from v2.1.276 or earlier;
  - before v2.1.281, in some Bedrock or telemetry-off sessions.

  The fix is a `CLAUDE.md` that holds `@AGENTS.md`.
- **How a directly read AGENTS.md differs from CLAUDE.md**:
  - `InstructionsLoaded` hooks don't fire.
  - The `AGENTS.md` of a directory added with `--add-dir` doesn't load.
  - An external `@path` import loads only if external imports were already approved for the project.
- **Old workarounds**:
  - A `CLAUDE.md` containing `@AGENTS.md` can stay; it never loads the file twice.
  - For prose telling Claude to read `AGENTS.md`, delete the file or replace the prose with the import.
  - A `CLAUDE.md` symlinked to `AGENTS.md` works and reads once. Edit and Write won't write through the link, though. Windows clones also check the link out as a one-line text file unless `core.symlinks` is on, so prefer the import when anyone uses Windows.
  - Remove a `SessionStart` hook that prints `AGENTS.md`, because it adds a second copy.
- **Commands that cause drift**: `/init` writes a `CLAUDE.md`, which then shadows `AGENTS.md`. `/import` appends a one-time *copy* of `AGENTS.md` into `CLAUDE.md`. Replace the copy with `@AGENTS.md`.

## Claude Code: memory rules for both files

- These files are context, not enforcement. They're delivered as a user message after the system prompt. To block an action no matter what, use a `PreToolUse` hook plus permissions.
- Keep each file **under 200 lines**. Claude Code warns at startup when a file, or the combined set, runs long. The hard cap is 4 MiB, and larger files are skipped.
- `@imports` organize files but **don't shrink context**, because imported files load at launch. Path-scoped `.claude/rules/*.md` files (with `paths:` frontmatter) load only when Claude reads a matching file. Rules without `paths:` load at launch.
- Add a line when the agent repeats a mistake, when a review catches a repo fact, or when a teammate would need it. Multi-step procedures go in skills. Folder-only rules go in path-scoped rules or nested files.
- Commit and PR rules compete with Claude's built-in git instructions. Turn those off with the `includeGitInstructions` setting, and set trailers with `attribution`.
- Revisit the file after major model releases. Rules that worked around an older model's limits become overhead.

## OpenAI Codex

- **Global scope**: Codex reads `~/.codex/AGENTS.override.md`, or else `~/.codex/AGENTS.md`.
- **Project scope**: from the git root down to the working directory, Codex reads, per directory, `AGENTS.override.md`, or else `AGENTS.md`, or else a name from `project_doc_fallback_filenames`. It reads at most one file per directory.
- Files are concatenated root to leaf, so closer files come later and win. Codex stops at `project_doc_max_bytes`, which defaults to **32 KiB**, and skips empty files.

## Size budget

| Scope | Budget |
|---|---|
| Per file, target | **under 200 lines** (sweet spot 40–150) |
| Codex, combined | 32 KiB |
| Claude, hard cap | 4 MiB (larger files are skipped) |

When a file runs over budget, fix it in this order:

1. Path-scope folder rules into a nested `AGENTS.md` or `.claude/rules/*.md`.
2. Extract procedures into a skill.
3. Replace pasted docs with a pointer.

Never `@import` to save tokens. In monorepos, use nested per-package files plus `claudeMdExcludes` for directories the team never touches.

## Verifying the file works

- **Claude Code**:
  - At session start, look for the line `no CLAUDE.md found; AGENTS.md loaded: <path>`.
  - `/memory` lists the path (v2.1.280+).
  - `/context` shows CLAUDE files under **Memory files**.
  - `/doctor` trims what Claude can infer (v2.1.206+).
  - `/doctor prompt-audit` audits `CLAUDE.md`, `CLAUDE.local.md`, and `AGENTS.md` for stale or conflicting rules (v2.1.283+).
- **Codex**: run `codex --ask-for-approval never "Summarize the current instructions."`.
- **Any agent**: give the agent a task the file should constrain. If it ignores a line, shorten the file, make the line more specific, move it closer to the files it governs, or enforce it with a hook.
