# Knowledge Routing — which layer owns each instruction

Before writing a line into `AGENTS.md` or `CLAUDE.md`, decide whether the root file is its home at all. Most audit findings are routing errors, not wording errors.

## Routing table

| Kind of instruction | Home | Why |
|---|---|---|
| Always-on facts | Root `AGENTS.md` / `CLAUDE.md` | Loaded every session |
| Folder-only conventions | Nested `AGENTS.md`, or `.claude/rules/*.md` with `paths:` | Loads only when those files are touched |
| Multi-step procedure | A skill (`SKILL.md`) | Body loads only when invoked |
| Isolated research or audit | A subagent | Own context; only a summary returns |
| Must-never-happen stop | `PreToolUse` hook + permissions | Not model-dependent |
| Verification of work | Tests / CI / `PostToolUse` hook | "Please test" is a request; a gate is a gate |
| Personal taste | User-level file (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`) | Not shared, not rewritten by the repo agent |

The root file is the constitution. A 30-line deploy checklist inside it is a skill in the wrong place.

## File scopes

- **Shared source of truth** — repo-root `AGENTS.md`, readable by any agent.
- **Claude wrapper** — repo-root `CLAUDE.md` that opens with `@AGENTS.md`, then carries only Claude-specific extras.
- **Personal taste** — `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`. The user writes these; never let a repo-scoped agent rewrite a personal file.
- **Local overrides** — `CLAUDE.local.md` / `AGENTS.override.md`, gitignored.
- **Org policy** — a managed enterprise `CLAUDE.md`, if IT ships one.

Commit the project files. Review them like code. Give the root file an owner.

## Section order for `AGENTS.md`

```markdown
# AGENTS.md

## Project
[2–4 sentences. What it is. Invariants that must not break.]

## Commands
- Install: …
- Dev: …
- Test (all / one): …
- Lint / types: …
- Add a dependency: … (ask first)

## Layout
[Package/app map only. What may be edited. Where tests live.]

## Conventions
[Only deltas from defaults. One short example if needed.]

## Constraints
- Never edit generated/ or commit .env
- Don't push or commit to main unless asked
- Preserve existing public APIs

## Done when
- [exact lint] [exact types] [exact tests] pass
- New behavior has a test

## Read when needed
- Billing → `docs/billing.md`
- Release → skill `release`
```

## The `CLAUDE.md` wrapper

When a repo already has `AGENTS.md`, `CLAUDE.md` stays thin — never a second copy:

```markdown
@AGENTS.md

## Claude-only
- Use plan mode for changes under `src/billing/`.
- Prefer a single-test run while iterating.
```

## Writing rules

- Markdown headers and bullets. No dense paragraphs.
- One idea per bullet. Two rules that contradict each other let the agent pick one at random.
- Concrete enough to verify: "Use 2-space indentation" over "format code properly"; "Run `npm test` before committing" over "test your changes"; "API handlers live in `src/api/handlers/`" over "keep files organized".
- Prefer exact commands the agent can run verbatim.
- Explain *why* only when the constraint is surprising — one line of rationale, never a lecture.
- Use `IMPORTANT` / `YOU MUST` only on true hard rules. Overuse trains the model to ignore emphasis.
- Never copy a rule that already lives elsewhere; point at the source of truth in one line.

## Maintaining it as a feedback loop

Add a rule only when one of these is true:

- the agent made the **same** mistake twice
- a review found a fact the agent should have known
- you typed the same correction in two consecutive sessions
- a new teammate would need it

Then: check for duplicates and contradictions before keeping the edit; if the rule is machine-checkable, add a hook or a test and **delete the prose**; batch updates, because one bad session is noise and two is a pattern; periodically re-prune, since instruction value expires as models improve.
