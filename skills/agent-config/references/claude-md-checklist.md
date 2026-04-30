# CLAUDE.md Verification Checklist

Audit standard for any `CLAUDE.md` file. Adapted from @zodchiii's post on writing CLAUDE.md files Claude actually follows. Use this verbatim during the `audit` flow and as the bar for `create` / `update`.

## 1. Length & instruction budget

- [ ] File is **under 80 lines** (ideally ~60 or less).
- [ ] Total instructions stay within ~100–150 after Claude's built-in system prompt (~50 instructions).
- [ ] No section is longer than necessary — Claude drops rules when the file gets too long.

## 2. Content quality (the "does this actually matter?" test)

- [ ] **Every line** passes: "Would removing this line cause Claude to make a specific mistake?"
- [ ] No personality fluff ("be a senior engineer", "think step by step", motivational language).
- [ ] No general advice Claude can figure out on its own.
- [ ] No duplication of facts already in auto-memory (`~/.claude/projects/<project>/memory/` — check with `/memory`).

## 3. Proper hierarchy (Global / Project / Local)

- [ ] Three-level split is in use:
  - Global → rules wanted in **every** project (`~/.claude/CLAUDE.md`)
  - Project → stack-specific / team context (`./CLAUDE.md`)
  - Local → personal quirks (`CLAUDE.local.md`, gitignored)
- [ ] Each file stays short and focused because of the split.

## 4. The 5 required sections

A CLAUDE.md should cover all five (or have a clear reason for omission):

- [ ] **Critical commands** — exact build/test/lint/run commands so Claude doesn't guess `npm test` when the project uses `pnpm` + `vitest`.
- [ ] **Architecture map** — high-level map of where things live and what belongs where. Not a full `ls` dump.
- [ ] **Hard rules** (the most important section)
  - ≤ 15 rules total.
  - Includes **negative rules** ("never commit `.env`", "never rewrite the whole file for a one-line change").
  - Uses emphasis markers that work (`IMPORTANT:`, `YOU MUST`).
- [ ] **Workflow preferences** — *how* you want Claude to work (minimal changes for small fixes, response format, when to ask vs. proceed).
- [ ] **What NOT to include** (explicit or evident by absence) — no auto-memory duplication, no one-off facts, no rules Claude already learned in-session.

## 5. Final quality checks

- [ ] Reads like a **technical brief** for onboarding a senior engineer, not a wish list.
- [ ] Focuses only on: stack + commands + architecture + hard rules + workflow.
- [ ] Updated whenever Claude makes a mistake — small fixes compound and prevent repeats.

## Quick self-test

For each line: *"If I removed this line, would Claude immediately start doing the wrong thing?"* If no → delete or move it.

A clean pass against this list means the file is production-grade.
