# AGENTS.md / CLAUDE.md Verification Checklist

The audit standard for any agent instruction file. Walk it verbatim during `audit`. Sections 1–3 and 5–7 are the bar for `create` and `update`. Section 4 is reported on audit only. For budgets and sources, see `official-standards.md`; for writing rules, `agents-md-writing.md`; for layers, `knowledge-routing.md`.

## 1. Length & budget

- [ ] Each file is **under 200 lines** (sweet spot 40–150).
- [ ] All instruction files combined stay under Codex's 32 KiB.
- [ ] Nothing relies on `@import` to reduce context.

## 2. Content quality

- [ ] **Every line** passes the test: "Would removing this cause a specific mistake?"
- [ ] No overview, directory tree, dependency list, or restatement of the README. The agent reads those directly.
- [ ] No personality fluff or generic advice. The injected `## Token Efficiency` block is the one exception.
- [ ] Every command is copy-pasteable and was read from a manifest or CI. The single-test form is present.
- [ ] Every listed check is one the agent should really run on each task. Slow suites say *when* to run them.
- [ ] Nothing duplicates facts already in auto memory (check with `/memory`).

## 3. Routing

- [ ] Every line is an always-on fact, not a procedure and not a folder-only rule.
- [ ] Procedures live in a skill. Folder-only rules live in a nested `AGENTS.md` or in `.claude/rules/*.md` with `paths:`.
- [ ] `AGENTS.md` contains no Claude-only lines. Those live in `.claude/rules/` or the wrapper.
- [ ] Personal taste lives in a user-level file, not in the committed one.

## 4. Enforceability (audit only)

Walked on **audit**, where it's reported but doesn't block a create or update. `create` and `update` may write Constraints the agent reads. The bar "a machine-checkable rule gets a hook **and** loses its prose" is an audit finding to route, not a create blocker.

- [ ] Rules that must **never** be broken are backed by a `PreToolUse` hook and permissions, not prose alone.
- [ ] "Verify your work" obligations are backed by tests, CI, or a `PostToolUse` hook.
- [ ] Any machine-checkable rule that already has a hook or test has had its prose **deleted**, not kept alongside.
- [ ] `IMPORTANT` / `YOU MUST` appears only on true hard rules.

## 5. Required sections

Applies to the source-of-truth file only. Wrappers and rules files are exempt.


- [ ] **Commands**: install, dev, test one and all, lint, and typecheck. The package manager and runtime are pinned wherever a guess would fail.
- [ ] **Constraints**: split into *Never* and *Ask first*, with at most 15 in total. Includes security or performance limits when the repo has them.
- [ ] **Done when**: the exact commands that define completion, plus whether new behavior needs a test.
- [ ] Optional sections (Project, Layout, Conventions, Read when needed) exist only when they hold a fact the agent can't infer. An empty or inferable optional section fails.

## 6. Loading, consistency & drift

- [ ] Claude Code will load the file: every `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` at or above it either imports `AGENTS.md` or is a symlink to it (see `official-standards.md`, section "Claude Code: which file it reads").
- [ ] No CLAUDE file tells Claude in prose to read `AGENTS.md`, and none holds a pasted copy of it (from `/init` or `/import`).
- [ ] No `SessionStart` hook in `.claude/settings*.json` prints `AGENTS.md` into context.
- [ ] No `AGENTS.override.md` silently replaces an `AGENTS.md` for Codex.
- [ ] `AGENTS.md` has no `@imports` and no Claude-only terms.
- [ ] No two rules contradict, and no rule appears in both `AGENTS.md` and `CLAUDE.md`.
- [ ] Every pointer target exists: `docs/y.md`, a named skill, an exemplar file.

## 7. Final checks

- [ ] Reads like a technical brief for a senior engineer's first day, not a wish list.
- [ ] Every bullet is a command, a pin, a constraint, or a pointer.
- [ ] Gets updated whenever the agent makes the same mistake twice.

## Sample audit report

```
◆ Audit (step 1 of 1)
··································································
  Length budget:       √ pass — 64 lines
  Content quality:     × fail — 18-line directory tree; "write clean code"
  Routing:             × fail — 12-line deploy runbook belongs in a skill
  Enforceability:      × fail — "never commit .env" has no PreToolUse hook
  Required sections:   × fail — no Ask-first tier; Done when missing
  Loading & drift:     × fail — CLAUDE.md shadows AGENTS.md (no @AGENTS.md import)
  Anti-patterns:       × fail — 2 found
  Token block:         √ pass
  ____________________________
  Result:              PARTIAL
```

Follow the block with the routing recommendations, one per failing line, then the top three fixes.
