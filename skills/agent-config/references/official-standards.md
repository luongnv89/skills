# Official Standards — Anthropic + AGENTS.md

The rules this skill enforces, and where they come from. Read before drafting or auditing.

## Anthropic — Claude Code memory & best practices

- `CLAUDE.md` is loaded every session and is **context, not enforced configuration**. Claude may still deviate. To block an action regardless of what Claude decides, use a `PreToolUse` hook plus permissions.
- **Target under 200 lines.** Longer files cost tokens and measurably reduce adherence. The hard load cap is 4 MiB; anything larger is skipped entirely.
- Write what you would otherwise have to re-explain. Add a line when the same mistake happens twice, a review catches a repo-specific fact, or a new teammate would need it.
- Multi-step procedures and folder-only rules do **not** belong in the root file — move them to a skill or a path-scoped rule.
- `@imports` organize files but **do not shrink context**: imported files still load at launch. Path-scoped `.claude/rules/*.md` files (with a `paths:` key) load only when matching files are touched.
- Tooling: `/init` drafts the file, `/context` confirms it loaded, `/doctor` prunes what Claude can infer from the repo.

## AGENTS.md standard + OpenAI Codex

- `AGENTS.md` is a README **for agents**: setup, commands, style deltas, tests, PR rules, security. Plain Markdown, no required schema, any agent can read it.
- **Closest file wins.** Nested `AGENTS.md` files override ancestors; the personal global file lives at `~/.codex/AGENTS.md`.
- Keep it small — Codex's default combined budget is **32 KiB**.
- Maintain it as a feedback loop: when the agent is wrong twice, add a rule; when it reads too much, add routing pointers instead of prose.

## Size budget (one number governs)

| Scope | Budget |
|---|---|
| Per file, target | **under 200 lines** |
| Practical sweet spot | **40–150 lines** |
| Codex combined budget | 32 KiB |
| Claude hard load cap | 4 MiB (larger files are skipped) |

Earlier revisions of this skill enforced an 80-line ceiling sourced from community write-ups. The official figure supersedes it: audit against **under 200 lines**, and treat anything past 150 as a prompt to path-scope or extract.

When a file outgrows the budget, in this order:

1. Path-scope folder-specific rules into `.claude/rules/*.md` or a nested `AGENTS.md`.
2. Extract multi-step procedures into a skill.
3. Replace pasted documentation with a pointer: "before X, read `docs/y.md`".
4. Do **not** reach for `@import` to save tokens — imports still load at launch.

In monorepos, prefer nested per-package files plus `claudeMdExcludes` for directories the team never touches.

## Verifying the file actually works

- `/context` — confirm the file loaded at all.
- `/doctor` — cut anything Claude can infer from the repo.
- Give the agent a task the file is supposed to constrain. If a line is ignored, the official remedies, in order: shorten the file, make the line more specific, move it closer to the files it governs, or stop relying on prose and enforce it with a hook.
- Watch for drift: the same rule living in both `AGENTS.md` and `CLAUDE.md` is a documented failure mode, not redundancy.
