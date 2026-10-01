# Writing the best AGENTS.md

How to write an `AGENTS.md` (or a standalone `CLAUDE.md`) that makes agents faster and more correct, not slower. Read it during Step 3. Loading rules are in `official-standards.md`. Which layer owns a rule is in `knowledge-routing.md`.

## What the evidence says

| Finding | Source | What it means for the file |
|---|---|---|
| LLM-generated context files lowered task success by 0.5–2% and raised cost by 20–23%. Developer-written files gained about 4% but still added steps | Gloaguen et al., ETH Zurich 2026 ([arXiv 2602.11988](https://arxiv.org/abs/2602.11988)) | Keep it minimal: only requirements the agent can't infer. Prune generated drafts hard |
| Codebase overviews did not help agents reach the relevant files sooner. Generated files helped (+2.7%) only when the repo's own docs were removed, so they mostly duplicate those docs | same | No overview, no directory tree, no restatement of the README |
| Agents act on what the file names. A tool the file mentioned was used 1.6 times per task, versus under 0.01 times when it wasn't mentioned | same | Every listed command gets run, so list the right ones |
| Agents run the checks the file lists and fix failures before finishing | [agents.md](https://agents.md) | "Done when" gets executed, not just read. Keep it fast |
| A good AGENTS.md cut median runtime by 28.6% and output tokens by 16.6%, with the same completion rate | Lulla et al. 2026 ([arXiv 2601.20404](https://arxiv.org/abs/2601.20404)) | A specific file pays off |
| Only about 15% of context files state security or performance requirements | Chatlatanagulchai et al. 2025 ([arXiv 2511.12884](https://arxiv.org/abs/2511.12884)) | Ask whether the repo has such limits, and state them if it does |
| An 8 KB docs index in AGENTS.md passed 100% of framework tasks, versus 79% for an on-demand skill | [Vercel 2026](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | For APIs newer than the model, a compact index of pointers beats pasted docs |
| Put commands early with their flags, show real examples instead of prose, use three-tier boundaries, and name the stack | [GitHub, 2,500 agent files](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) (studied persona files in `.github/agents/`, but the advice transfers) | The template order and the Never / Ask first split below |

## Rules

1. **Non-inferable only.** Keep a line only if removing it would cause a specific mistake. The agent can already read the tree, the README, the manifest, and the lockfile.
2. **Commands first, verbatim, with flags.** Copy them from the manifest or CI. Include the single-test form, because agents run one test far more often than the whole suite.
3. **Scope the checks.** Give file-scoped lint, typecheck, and test commands for iteration (`pnpm eslint --fix <file>`), and the full suite once, before handing back. Name both, and say when each one runs.
4. **Pin what a guess would get wrong**: the package manager, the runtime version, the test runner. Skip versions the manifest already states.
5. **Boundaries in two tiers.**
   - *Never*: secrets, generated or vendored paths, force-pushing, pushing to main.
   - *Ask first*: new dependencies, migrations, public API or schema changes, deleting files.
   - "Always" rules belong in Done when.
6. **Point, don't paste.** "New endpoints follow `src/api/users.ts`" beats a pasted snippet that drifts from the code. Inline a short snippet only when no file in the repo shows the pattern.
7. **State the security and performance limits the agent could break**, such as PII in logs, auth boundaries, hot paths, or bundle budgets. Include them only when they exist; never invent them.
8. **Stay portable.** Use plain Markdown.
   - Write pointers as backticked paths (`docs/billing.md`), not `@imports`. The AGENTS.md spec defines no import syntax, only Claude Code expands imports, and an import loads at launch anyway.
   - Keep Claude-only terms out: plan mode, hooks, `/commands`, skills.
9. **One idea per bullet, with no contradictions.** Add one clause of *why* only when a rule would surprise the reader. Use `IMPORTANT` or `YOU MUST` only on true hard rules.
10. **Keep it small, and keep rules near their code.** Stay under 200 lines per file; Codex stops reading at 32 KiB combined. Rules that belong to one package go in that package's `AGENTS.md`, since the closest file wins.

## Template

```markdown
# AGENTS.md

## Commands
- Install: `pnpm install` (pnpm 9 and Node 20, not npm)
- Dev: `pnpm dev`
- Test one: `pnpm vitest run path/to/file.test.ts`
- Test all: `pnpm test`
- Lint one file: `pnpm eslint --fix <file>`
- Typecheck: `pnpm tsc --noEmit`

## Constraints
- Never: edit `src/generated/` (run `pnpm codegen` instead), commit `.env*`, push to `main`
- Ask first: adding a dependency, changing a DB migration, renaming a public export

## Done when
- `pnpm lint && pnpm tsc --noEmit && pnpm test` pass (the same checks CI runs)
- New behavior has a test next to the code it covers

## Conventions
- Errors: throw `AppError` from `src/errors.ts`; never return `null` for a failure
- New API route: copy the shape of `src/api/users.ts`

## Read when needed
- Billing rules: `docs/billing.md`
- <framework> APIs newer than your training data: `docs/<framework>-<version>/index.md`

## Token Efficiency
(the block from token-efficiency-block.md)
```

Conventions lists only deltas from defaults. Add a `## Project` section (one to three sentences on invariants that must not break) or a `## Layout` section (only ownership that isn't obvious: what may be edited, and where tests live if that's unconventional) only when there's such a fact to state. Otherwise leave them out.

## Bad line, better line

| Bad | Why | Better |
|---|---|---|
| "This is a Next.js app built with React and TypeScript." | Inferable from `package.json` | Delete it |
| A 30-line tree of `src/` | Overviews don't speed up finding files | Delete it; name only the one surprising location |
| "Run the tests." | Unverifiable, so the agent guesses `npm test` | "`pnpm vitest run <file>` while iterating; `pnpm test` before handing back" |
| "Write clean, well-documented code." | Generic; it changes nothing | Delete it |
| "Be careful with the database." | Names no action | "Ask first before editing `migrations/`; never edit a merged migration" |
| `@docs/api.md` in AGENTS.md | Claude-only syntax that loads at launch | "API conventions: `docs/api.md`" |
| "Use plan mode for billing changes" in AGENTS.md | A Claude-only feature | Move it to `.claude/rules/billing.md`, or to the CLAUDE.md wrapper when one was requested |
