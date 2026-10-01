# AGENTS.md — Agent Skills Catalog

## Project
Skill **definitions** live in `skills/<name>/`. Installed copies under `~/.claude/skills/` and `~/.agents/skills/` are the runtime, not the source: edit only this repo.

## Commands
- Validate one skill: `python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py skills/<name>`
- Score one skill: `asm eval skills/<name>` (`--json` for per-category scores)
- Package: `python3 ~/.claude/skills/skill-creator/scripts/package_skill.py skills/<name>` (writes `dist/`)
- Scaffold: `python3 ~/.claude/skills/skill-creator/scripts/init_skill.py <name> --path skills/`
- Check every `evals/evals.json`: `python3 scripts/validate-evals.py`
- Trigger evals (tests the *installed* copy): `python3 scripts/run-skill-evals.py <name> --runs 3`
- Local install: `bash install.sh`. It's an interactive TUI that installs for real, takes no flags, and needs a TTY
- There is no npm, pnpm, make, or pytest here. Don't invent test commands.

## Constraints
- Never: edit installed skill copies (`~/.claude/skills/`, `~/.agents/skills/`) from this repo
- Never: hand-edit `dist/`; regenerate it with `package_skill.py`
- Never: commit `*-workspace/`, `.asm-improver/`, `.claude/scheduled_tasks.lock`, secrets, `.env`, or `**/credentials*`
- Never: commit or push without an explicit user request (drafting the message is fine)
- Ask first: destructive ops (`rm -rf`, `git reset --hard`, force-push, branch delete)
- Ask first: a change that touches more than one skill

## Conventions
- Every SKILL.md edit bumps `metadata.version` (patch for wording, minor for a new capability, major for a restructure), and the skill's row in the root `README.md` shows the same version
- Quote any frontmatter string containing `:` `#` `-` `<` `>` `|` `,` `&` `?` `!`
- `name` equals the skill's own directory name, suite children included (`skills/<umbrella>/<child>/`). Each suite SKILL.md validates and versions independently
- SKILL.md stays under 500 lines and 3000 words; overflow goes to `references/`
- `docs/README.md` opens with the AI-skip HTML comment (copy it from any existing skill)
- A skill that mutates a git repo has a `## Repo Sync Before Edits (mandatory)` section. A skill that invokes another skill has a `## Dependency Preflight (mandatory)` section
- Small fix: make a minimal, targeted diff. Never rewrite a SKILL.md for a one-line change or refactor opportunistically
- New skill: run `init_skill.py`, fill in SKILL.md, add `docs/README.md`, validate, then add a CHANGELOG entry under `## Unreleased`
- Before creating a skill, grep `skills/*/SKILL.md` for one that already owns the behavior
- Renaming a skill: change the frontmatter `name`, the directory, and the `README.md` catalog references in the same commit
- Commits use Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`). Breaking changes go in the body, not the title

## Done when
- `quick_validate.py` exits 0 for every skill you touched
- `asm eval` gives an overall score above 85, and at least 8 in each of: structure, description, prompt-engineering, context-efficiency, safety, testability, naming. `license` scores 5 across the whole catalog by design, so never add per-skill LICENSE files
- `python3 scripts/validate-evals.py` passes whenever an `evals/evals.json` changed

## Read when needed
- Contribution workflow and the eval runner: `CONTRIBUTING.md`
- What doesn't belong in agent instruction files: `skills/agent-config/references/anti-patterns.md`

## Token Efficiency
- Never re-read files you just wrote or edited. You know the contents.
- Never re-run commands to "verify" unless the outcome was uncertain.
- Don't echo back large blocks of code or file contents unless asked.
- Batch related edits into single operations. Don't make 5 edits when 1 handles it.
- Report results and blockers plainly; skip filler like "I'll continue...".
- If a task needs 1 tool call, don't use 3.
