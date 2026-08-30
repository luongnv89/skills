# CLAUDE.md / AGENTS.md Verification Checklist

Audit standard for any agent config file. Walk it verbatim during the `audit` flow. Sections 1–3 and 5–7 are the bar for `create` and `update`; section 4 (Enforceability) is reported on audit and does not fail a create/update run. Budgets and their sources: `official-standards.md`. Layer decisions: `knowledge-routing.md`.

## 1. Length & instruction budget

- [ ] File is **under 200 lines** (sweet spot 40–150).
- [ ] Combined agent-config context stays under Codex's 32 KiB default budget.
- [ ] No section is longer than necessary — adherence drops as the file grows.
- [ ] Nothing relies on `@import` to reduce context; imported files still load at launch.

## 2. Content quality (the "does this actually matter?" test)

- [ ] **Every line** passes: "Would removing this cause a real, specific mistake?"
- [ ] No personality fluff ("be a senior engineer", "think step by step", motivational language).
- [ ] No general advice the agent can figure out on its own — the injected `## Token Efficiency` block is expected here and is not a violation.
- [ ] Nothing inferable from the tree, README, or package manifest (directory listings, dependency lists, generic architecture recaps).
- [ ] No duplication of facts already in auto-memory (`~/.claude/projects/<project>/memory/` — check with `/memory`).

## 3. Routing (is this the right layer?)

- [ ] Every line is an always-on fact — not a procedure, not a folder-only rule.
- [ ] Multi-step procedures live in a skill, not in the root file.
- [ ] Folder-only conventions live in a nested `AGENTS.md` or `.claude/rules/*.md` with `paths:`.
- [ ] Personal taste lives in the user-level file, not the committed one.
- [ ] Three-level split is in use: global (`~/.claude/CLAUDE.md`), project (`./CLAUDE.md`, `./AGENTS.md`), local (`CLAUDE.local.md`, gitignored).

## 4. Enforceability (context is not config)

Walked on **audit**; reported, not a create/update blocker. `create` / `update` may emit constitution Constraints as pins the agent reads. The "machine-checkable rule gets a hook **and** loses its prose" bar is an audit finding to route, not a create blocker.

- [ ] Rules that must **never** be violated are backed by a `PreToolUse` hook and permissions, not prose alone.
- [ ] "Verify your work" obligations are backed by tests, CI, or a `PostToolUse` hook.
- [ ] Any machine-checkable rule that already has a hook or test has had its prose **deleted**, not kept alongside.
- [ ] `IMPORTANT` / `YOU MUST` appears only on true hard rules, not scattered for emphasis.

## 5. The 5 required sections

A root config file should cover all five (or have a clear reason for omission). Names in **bold** are the `AGENTS.md` template headings; a template-following create passes this section.

- [ ] **Commands** (Critical commands) — exact build/test/lint/run commands, including single-test runs, so the agent doesn't guess `npm test` when the project uses `pnpm` + `vitest`. Pin the package manager and language version when the model would guess wrong.
- [ ] **Layout** (Architecture map) — where things live and what belongs where. Not a full `ls` dump.
- [ ] **Constraints** (Hard rules) — ≤ 15 total, including **negative rules** ("never commit `.env`", "don't push to main unless asked").
- [ ] **Conventions** (Workflow preferences) — *how* the agent should work: minimal diffs for small fixes, branch/commit/PR etiquette, when to ask versus proceed.
- [ ] **Done when** — the exact lint/typecheck/test commands that define completion, plus whether new behavior needs a test.

## 6. Consistency & drift

- [ ] No two rules in the file contradict each other.
- [ ] No rule is duplicated between `AGENTS.md` and `CLAUDE.md`. When both exist, `CLAUDE.md` opens with `@AGENTS.md` and carries only Claude-specific extras.
- [ ] Every pointer target (`docs/y.md`, a named skill) actually exists.

## 7. Final quality checks

- [ ] Reads like a **technical brief** for onboarding a senior engineer, not a wish list.
- [ ] Every bullet is a command, a pin, a constraint, or a pointer.
- [ ] Short enough to read in one screen.
- [ ] Updated whenever the agent makes the same mistake twice — small fixes compound and prevent repeats.

## Quick self-test

For each line: *"If I removed this line, would the agent immediately start doing the wrong thing?"* If no → delete it, or move it to the layer that owns it.

A clean pass against this list means the file is production-grade.
