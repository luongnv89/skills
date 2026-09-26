# AGENTS.md — Agent Skills Catalog

Subagents available when working in this repo. Each runs in its own context with restricted tools.

## Registered agents

- [`skill-reviewer`](.claude/agents/skill-reviewer.md) — Reviews skill files for quality, best practices, and adherence to skill creation guidelines. Tools: `Read`, `Grep`, `Glob`.
- [`skill-packager`](.claude/agents/skill-packager.md) — Validates and packages skills into distributable `.skill` files without publishing them. Tools: `Read`, `Grep`, `Glob`, `Bash`.
- [`skill-tester`](.claude/agents/skill-tester.md) — Tests skill functionality by simulating usage scenarios and validating outputs. Tools: `Read`, `Grep`, `Glob`, `Bash`.
- [`skill-documenter`](.claude/agents/skill-documenter.md) — Generates concise documentation for skills, focusing on usage examples and trigger phrases. Tools: `Read`, `Grep`, `Glob`.

## Shared validation and authoring policies

### Validation

For each target skill at `skills/<name>/`:

1. Run `python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py skills/<name>` and report exit status verbatim.
2. Confirm `name` field equals the directory name; flag mismatches.
3. Confirm `metadata.version` is semver and present.
4. Confirm `SKILL.md` ≤ 500 lines.
5. Confirm `docs/README.md`, if present, starts with the AI-skip HTML comment.
6. Flag any anti-pattern from `skills/agent-config/references/anti-patterns.md`.
7. Output a Step Completion Report per skill (`◆ Validate <name>`).

**Never write, edit, or move files.** Report only.

### Authoring

When producing skill content, scope is limited to one skill directory at a time (`skills/<name>/`).

1. Read the existing SKILL.md (if any) before editing — never overwrite blind.
2. Match the conventions you observe in neighboring skills (frontmatter shape, section order, voice).
3. Bump `metadata.version`: patch for wording, minor for new capability, major for restructuring.
4. Quote YAML strings containing `:` `#` `-` `<` `>` `|` `,` `&` `?` `!`.
5. Keep SKILL.md under 500 lines; spill to `references/`.
6. After editing, run `quick_validate.py` against the skill and include the result in your final message.

**Suite / umbrella folders.** Some products ship as a suite: an umbrella skill at `skills/<umbrella>/`
plus child skills at `skills/<umbrella>/<child>/` (e.g. `website-cloner`, `diagram-generator`). Each
SKILL.md — umbrella and every child — is validated independently: its `name` must equal its **own**
directory name, and it bumps its own `metadata.version`. Keep the umbrella lean (route or orchestrate
only) and push depth into each child. Installers discover both levels, so nesting a skill needs no
installer change.

**Do not** edit files outside the target skill directory. **Do not** commit, push, or modify `dist/`. Stop and ask if the change touches more than the one skill.

## Token Efficiency
- Never re-read files you just wrote or edited. You know the contents.
- Never re-run commands to "verify" unless the outcome was uncertain.
- Don't echo back large blocks of code or file contents unless asked.
- Batch related edits into single operations. Don't make 5 edits when 1 handles it.
- Report results and blockers plainly; skip filler like "I'll continue...".
- If a task needs 1 tool call, don't use 3.
