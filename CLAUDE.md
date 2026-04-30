# CLAUDE.md — Agent Skills Catalog

Project context for Claude when working in this repo. Skill **definitions** live here; the runtime that loads them lives in `~/.claude/skills/` (out of scope for edits).

## Critical commands

- Validate a skill: `python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py skills/<skill-name>`
- Package a skill: `python3 ~/.claude/skills/skill-creator/scripts/package_skill.py skills/<skill-name>`
- Scaffold a new skill: `python3 ~/.claude/skills/skill-creator/scripts/init_skill.py <name> --path skills/`
- Local install dry-run: `bash install.sh` (interactive TUI; never pipe to non-tty without flags)

There is **no** `npm`, `pnpm`, `make`, or `pytest` in this repo. Don't invent test commands.

## Architecture map

- `skills/<name>/SKILL.md` — required skill definition with YAML frontmatter (`name`, `description`, `metadata.version`, `metadata.author`).
- `skills/<name>/references/` — on-demand docs the agent loads when the skill triggers.
- `skills/<name>/scripts/` — executable helpers shipped with the skill.
- `skills/<name>/agents/` — subagent prompts.
- `skills/<name>/docs/README.md` — human-only catalog page; **must** start with the AI-skip HTML comment.
- `install.sh` / `remote-install.sh` — end-user installers (bash, no deps).
- `dist/` — generated `.skill` bundles. Never edit by hand.
- `*-workspace/` — scratch dirs for individual skills. Never commit working files there.
- Root `*.md` files (CHANGELOG, CONTRIBUTING, etc.) — repo-level governance, not skill content.

## Hard rules

1. **IMPORTANT:** Bump `metadata.version` (semver) on every SKILL.md edit. No exceptions.
2. **IMPORTANT:** Quote any frontmatter string containing `:` `#` `-` `<` `>` `|` `,` `&` `?` `!` to keep YAML valid.
3. **YOU MUST** keep each `SKILL.md` under 500 lines. Split overflow into `references/`.
4. **YOU MUST** start every `docs/README.md` with the AI-skip HTML comment (see existing skills for the boilerplate).
5. Never edit anything under `~/.claude/skills/` or `~/.claude/CLAUDE.md` from this repo.
6. Never edit `dist/` artifacts; regenerate via `package_skill.py` instead.
7. Never commit `*-workspace/` contents, `.claude/scheduled_tasks.lock`, or local scratch files.
8. Never commit secrets, `.env`, or anything matching `**/credentials*`.
9. **NEVER add `Co-Authored-By: Claude`** to any commit message.
10. Do not commit or push without an explicit user request — drafting the message is fine, executing isn't.
11. Use Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`). Breaking changes go in the body, not the title.
12. Skill `name` field must exactly match the parent directory name (lowercase, hyphens, no consecutive hyphens).
13. Do not rewrite a whole SKILL.md for a one-line change. Use targeted edits.
14. When a skill mutates a git repo, its SKILL.md must contain a "Repo Sync Before Edits" section.
15. Run `quick_validate.py` against any skill you touched before declaring done.

## Workflow preferences

- Small fix → minimal diff, no surrounding cleanup. Don't refactor opportunistically.
- New skill → scaffold with `init_skill.py`, fill SKILL.md, add `docs/README.md`, validate, then propose CHANGELOG entry under `## Unreleased`.
- When unsure which skill owns a behavior, grep `skills/*/SKILL.md` before creating a new one.
- Cross-skill renames: update SKILL.md frontmatter, directory name, and any catalog references in `README.md` in the same commit.
- Prefer editing existing `references/*.md` over inflating SKILL.md.
- Ask before destructive ops (`rm -rf`, `git reset --hard`, force-push, branch delete).

## Token Efficiency
- Never re-read files you just wrote or edited. You know the contents.
- Never re-run commands to "verify" unless the outcome was uncertain.
- Don't echo back large blocks of code or file contents unless asked.
- Batch related edits into single operations. Don't make 5 edits when 1 handles it.
- Skip confirmations like "I'll continue..." Just do it.
- If a task needs 1 tool call, don't use 3. Plan before acting.
- Do not summarize what you just did unless the result is ambiguous or you need additional input.
