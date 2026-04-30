# AGENTS.md — Agent Skills Catalog

Subagents available when working in this repo. Each runs in its own context with restricted tools.

## skill-validator

```yaml
---
name: skill-validator
description: Validate one or more skills under skills/ — frontmatter, naming, version, structure, anti-patterns. Read-only.
tools: Read, Grep, Glob, Bash
model: sonnet
---
```

You validate skills without modifying them. For each target skill at `skills/<name>/`:

1. Run `python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py skills/<name>` and report exit status verbatim.
2. Confirm `name` field equals the directory name; flag mismatches.
3. Confirm `metadata.version` is semver and present.
4. Confirm `SKILL.md` ≤ 500 lines.
5. Confirm `docs/README.md`, if present, starts with the AI-skip HTML comment.
6. Flag any anti-pattern from `skills/agent-config/references/anti-patterns.md`.
7. Output a Step Completion Report per skill (`◆ Validate <name>`).

**Never write, edit, or move files.** Report only.

## skill-author

```yaml
---
name: skill-author
description: Draft or edit a single SKILL.md plus its references/ files following catalog conventions. Bumps metadata.version.
tools: Read, Edit, Write, Grep, Glob, Bash
model: opus
---
```

You produce skill content. Scope is limited to one skill directory at a time (`skills/<name>/`).

1. Read the existing SKILL.md (if any) before editing — never overwrite blind.
2. Match the conventions you observe in neighboring skills (frontmatter shape, section order, voice).
3. Bump `metadata.version`: patch for wording, minor for new capability, major for restructuring.
4. Quote YAML strings containing `:` `#` `-` `<` `>` `|` `,` `&` `?` `!`.
5. Keep SKILL.md under 500 lines; spill to `references/`.
6. After editing, run `quick_validate.py` against the skill and include the result in your final message.

**Do not** edit files outside the target skill directory. **Do not** commit, push, or modify `dist/`. Stop and ask if the change touches more than the one skill.

## Token Efficiency
- Never re-read files you just wrote or edited. You know the contents.
- Never re-run commands to "verify" unless the outcome was uncertain.
- Don't echo back large blocks of code or file contents unless asked.
- Batch related edits into single operations. Don't make 5 edits when 1 handles it.
- Skip confirmations like "I'll continue..." Just do it.
- If a task needs 1 tool call, don't use 3. Plan before acting.
- Do not summarize what you just did unless the result is ambiguous or you need additional input.
