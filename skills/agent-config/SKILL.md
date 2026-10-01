---
name: agent-config
description: "Create, update, or audit AGENTS.md (default) or CLAUDE.md agent instructions: set up, prune, add a rule, or merge CLAUDE.md or .cursorrules into one file Claude Code, Codex, and Cursor all read. Don't use for READMEs, skills, or subagents."
license: MIT
effort: medium
metadata:
  version: 2.0.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

## When to Use

Create, update, or audit the instruction files coding agents load every session. **`AGENTS.md` is the default output**: it's the open standard that Claude Code (v2.1.277+), Codex, Cursor, Copilot, and others read. Produce `CLAUDE.md` as the output only on an **explicit request**, meaning the user asks for a CLAUDE.md to be written or edited ("create a CLAUDE.md", "add X to CLAUDE.md"). Naming it as a *source* doesn't count ("migrate our CLAUDE.md to AGENTS.md"), and neither does a CLAUDE.md that already exists on disk. Skip READMEs and contributor docs, skills (`skill-creator`), and subagent files under `.claude/agents/` (`subagent-creator`).

## Core Principle

These files are **context, not enforced configuration**. They load every session, and the agent may still deviate from them.

- Short, always-on facts the agent cannot infer go in the file.
- Multi-step procedures go in a **skill**. Anything that must never happen goes in a `PreToolUse` **hook** plus permissions. Verification of the work goes in **tests or CI**.
- **Minimal beats complete.** Agents run every command the file lists and obey every rule, so each extra line costs steps and tokens on every task. LLM-generated files that restate the repo measured about 20% more cost with no success gain. This skill is an LLM writing such a file, so the prune pass in Step 3 is mandatory for new content.

Which layer owns an instruction: `references/knowledge-routing.md`. Loading rules and sources: `references/official-standards.md`.

## Prerequisites

- A git repo with `origin` set, for anything that writes. `audit` only needs read access.
- Tools: `git`, and write access to the target path.

## Mode Selector

```text
$ARGUMENTS
```

- **audit**: the user says `audit`, "review", or "check". Read-only.
- **write**: anything else (`create`, `update`, a specific change, or a path such as `packages/api/AGENTS.md`).

Every mode runs Step 1 first. After Step 1, a write run is a **targeted edit** when the user named a specific change to an existing file. Otherwise it's a **full pass**. Write runs continue with Steps 2–4; audit jumps to **Audit**.

## Repo Sync Before Edits (mandatory)

Before a write run changes anything, sync with the remote. `audit` skips this. `git fetch` is the read-only dry run.

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin                       # dry-run: read-only preview
git status                             # validate clean tree
git pull --rebase origin "$branch"     # only after confirmation
```

If the tree is dirty, back it up with `git stash push -u -m "pre-sync-backup"`, sync, then run `git stash pop`. **Stop and confirm** with the user if any of these happen: the directory isn't a git repo, `origin` is missing, the HEAD is detached, the branch has no upstream, the pull or rebase fails, or the pop fails. Never overwrite an existing agent file without reading it and showing a diff.

## Step 1: Resolve the target (every mode)

1. The output is `AGENTS.md` in the repo root, or the path the user gave. It's `CLAUDE.md` only on an explicit request (see When to Use).
2. **Shadow check.** By default, Claude Code reads `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` exists in the launch directory or any directory above it; `~/.claude/CLAUDE.md` doesn't count. A subdirectory's `AGENTS.md` loads only when that directory has no CLAUDE file of its own. Any file that counts *shadows* `AGENTS.md`. From the repo root, list CLAUDE files above the root and inside the repo:

   ```bash
   root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"; d="$(dirname "$root")"
   while :; do for f in CLAUDE.md .claude/CLAUDE.md CLAUDE.local.md; do p="$d/$f"
     { [ -e "$p" ] || [ -L "$p" ]; } && [ "$p" != "$HOME/.claude/CLAUDE.md" ] && echo "ABOVE-REPO $(ls -l "$p")"
   done; [ "$d" = / ] && break; d="$(dirname "$d")"; done
   find "$root" \( -name node_modules -o -name .git \) -prune -o \( -name CLAUDE.md -o -name CLAUDE.local.md -o -name AGENTS.md \) -print |
     while read -r p; do ls -l "$p"; grep -qE '^@(\.\.?/)*AGENTS\.md' "$p" 2>/dev/null && echo "  -> imports AGENTS.md" || true; done
   ```

3. **Classify every CLAUDE file found. Each gets its own action**:

| File | Action |
|---|---|
| Above the repo root (for example `~/CLAUDE.md`) | **Never edit it.** Warn that it blocks `AGENTS.md` in every repo below it, and suggest moving its content to `~/.claude/CLAUDE.md`, which doesn't count |
| `CLAUDE.local.md` | **Never edit it.** Warn that it stops Claude from reading `AGENTS.md` for its owner. Suggest `@AGENTS.md` as its first line, or `/config` → **Project instructions** → `claude-md-and-agents-md`. That setting is per-user and ignored in project settings |
| A symlink to `AGENTS.md` | Nothing to do. Write to the link's target, because Edit and Write refuse to write through symlinks |
| Already imports `AGENTS.md` | Keep it, holding only Claude-only lines |
| In the repo, no import | **Migrate**: move shared rules to `AGENTS.md`, and shrink the file to the import plus its Claude-only lines. Import paths are relative to the file, so `.claude/CLAUDE.md` uses `@../AGENTS.md` |

4. **Pick the branch:**
   - **wrapper**: the user asked for both files.
   - **claude-only**: an explicit CLAUDE.md request and no `AGENTS.md`.
   - **wrapper**: an explicit CLAUDE.md request, and `AGENTS.md` exists. Write the CLAUDE.md as the import plus Claude-only lines, and touch `AGENTS.md` only if asked.
   - **migrate**: any in-repo CLAUDE file needs migrating.
   - **agents-only**: everything else.

**Claude-only lines** name Claude Code features: plan mode, `/commands`, skills, hooks, subagents, or MCP tools. They stay in a CLAUDE file that already exists or was requested. Otherwise they go to `.claude/rules/<topic>.md`, which loads alongside `AGENTS.md` without shadowing it. Never create a `CLAUDE.md` just to hold them.

**When the user reports that `AGENTS.md` isn't loading and the shadow check is clean**, check the environment before rewriting any content: `claude --version` (v2.1.277+), the **Project instructions** value in `/config`, and whether the `agents-md` plugin is enabled (`official-standards.md` → Claude Code).

Done when the output path(s), the branch, each CLAUDE file's action, and the raw shadow-check output are shown.

## Step 2: Analyze the project (full pass)

Collect only what an agent would otherwise get wrong:

- **Commands** from manifests and CI (`package.json` scripts, `pyproject.toml`, `Makefile`, `.github/workflows/*`): install, dev, test all **and** one, lint, and typecheck, with the flags CI uses.
- **Pins**: the package manager and runtime version, wherever a guess would fail (`pnpm`, not `npm`).
- **Boundaries**: generated, vendored, and secret paths, and actions that need a human first.
- **Existing rules** in agent files, `.cursor/rules/`, `.cursorrules`, and `.github/copilot-instructions.md`. Keep what is still true, and leave those files in place.

Done when every command you will write was read from a file. If no manifest or CI defines a command, write none for it and ask the user; never guess one.

## Step 3: Draft

For a **targeted edit**, make the requested change, add the token-efficiency block if it's missing, and change nothing else. List other prune candidates in the report, but don't apply them. For a **full pass**, read `references/agents-md-writing.md` first. It holds the template, the writing rules, and the evidence behind them. Then:

1. **Fill the template.** **Commands**, **Constraints** (*Never* and *Ask first*), and **Done when** are required. Project, Layout, Conventions, and Read when needed appear only when they hold a fact the agent cannot infer.
2. **Prune pass.** Delete every line that fails the deletion test: *"would removing this cause a specific mistake?"* Also delete any overview, directory tree, dependency list, or restatement of the README. Move Claude-only lines to the place Step 1 names.
3. Add opt-in blocks from `references/optional-blocks.md` only when the user asks for them.
4. **Append the token-efficiency block** (see below) last.

Done when every remaining line is a command, a pin, a constraint, or a pointer.

## Step 4: Write and verify

- **Show before writing.** For a new file, show the draft. For an existing file, show the diff. Write once the user approves, or right away if the request already said to apply the change.
- **Verify**:
  - `wc -l` is under 200 for each file.
  - `grep -c '^## Token Efficiency'` returns 1 in the source of truth and 0 everywhere else.
  - Each wrapper's first line is the `AGENTS.md` import.
  - Re-running the shadow check shows no in-repo CLAUDE file shadowing `AGENTS.md`.
- **Report how to confirm the load.** In Claude Code v2.1.280+, `/memory` lists `AGENTS.md`. In Codex, run `codex --ask-for-approval never "Summarize the current instructions."`. Clients that cannot read `AGENTS.md` need a one-line `CLAUDE.md` holding `@AGENTS.md`: Claude Code before v2.1.277, and some Bedrock or telemetry-off sessions before v2.1.281. Offer that file, but don't create it unasked.

## Audit (read-only)

1. Read these together, because shadowing and drift only show up across the set:
   - `AGENTS.md`
   - every file the shadow check found
   - any `AGENTS.override.md`
   - `.claude/settings.json` and `.claude/settings.local.json`, for hooks
2. Walk `references/agents-md-checklist.md`, and report every item as pass, fail, or N/A with a one-line reason. Its loading section catches CLAUDE files that shadow without importing, prose telling Claude to "read AGENTS.md", a `SessionStart` hook that prints `AGENTS.md`, and an `AGENTS.override.md` that Codex reads instead.
3. Cross-check `references/anti-patterns.md`.
4. **Route and enforce.** For every failing line, name its home from `references/knowledge-routing.md`. A rule a machine can check gets its gate **and** loses its prose.
5. Modify nothing; `git status` must be unchanged. End with the overall verdict. Suggest `/memory` to see what loaded, and `/doctor prompt-audit` (v2.1.283+) for a second pass.

## Token Efficiency Block (always inject)

Append the fenced block from `references/token-efficiency-block.md` once, as the last section of the source-of-truth file. The source of truth is the root `AGENTS.md`, or `CLAUDE.md` on the claude-only branch. Never add the block to a wrapper, a nested package file, or a `.claude/rules/` file: those load alongside the root file, and a second copy would double it. It is the one deliberate exception to "no general advice": these are always-on rules for how the agent spends its context window. Non-negotiable: add it on every write run where the source of truth lacks it, including a targeted edit, and say so in the report. The one exception is the wrapper branch: don't edit an `AGENTS.md` that already exists just to add the block; report that it's missing instead.

## Step Completion Reports

After each step, output:

```
◆ [Step Name] ([step N of M])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Use `√` for pass and `×` for fail. Adapt the check names to each step.

## Acceptance Criteria

- [ ] The branch, each CLAUDE file's action, and the shadow-check output are shown.
- [ ] Without an explicit CLAUDE.md request, no new `CLAUDE.md` was created.
- [ ] After the run, every in-repo CLAUDE file either imports `AGENTS.md` or is a symlink to it. Files above the repo and `CLAUDE.local.md` were left unedited, and the user was warned about them.
- [ ] The repo was synced, or the user explicitly authorised skipping the sync.
- [ ] The token-efficiency block appears exactly once, in the source of truth, unless the wrapper branch reported it missing.
- [ ] The source-of-truth file is under 200 lines and passes sections 1–3 and 5–7 of `references/agents-md-checklist.md`. Wrappers and rules files pass sections 1–3 and 6.
- [ ] No rule appears in both `AGENTS.md` and a CLAUDE file.
- [ ] New content has no anti-pattern from `references/anti-patterns.md`.
- [ ] Write runs end with `Result: PASS`. Audit runs report every checklist item, give each failing line a routing recommendation, leave `git status` unchanged, and end with the overall verdict.

## Expected Output

| Branch | Files after the run |
|---|---|
| agents-only | `AGENTS.md`: Commands, Constraints, Done when, any optional sections, then `## Token Efficiency` |
| migrate / wrapper | `AGENTS.md` as above, plus each CLAUDE file reduced to the `@AGENTS.md` import and its Claude-only lines |
| claude-only | `CLAUDE.md` with the full content and the token block |
| audit | no writes; a checklist report with routing, ending `Result: PASS`, `PARTIAL`, or `FAIL` |

A sample file is in `references/agents-md-writing.md`. A sample audit report is in `references/agents-md-checklist.md`.

## Edge Cases

- **Monorepo**: prefer one `AGENTS.md` per package over a growing root file. Codex and most agents give priority to the closest file. Claude reads the root file plus each subdirectory's file on demand, and a CLAUDE file shadows the `AGENTS.md` in its own directory. Ask which scope to edit.
- **A CLAUDE file that tells Claude in prose to read `AGENTS.md`, or holds a pasted copy of it** (from `/init` or `/import`): it lacks the import, so migrate it.
- **A request for `AGENTS.override.md` or `AGENTS.local.md`**: Codex reads `AGENTS.override.md` *instead of* that directory's `AGENTS.md`, and Claude reads neither. Say so before writing one.
- **Personal files** (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`): audit and propose only. Never rewrite a personal file from a repo-scoped run.
- **A multi-step procedure**: don't inline it. Propose a skill, and leave a one-line pointer.
- **A draft over 200 lines**: path-scope rules, extract procedures to a skill, or link out before writing.
