<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Subagent Creator

> Create, evaluate, and improve Claude Code subagent definition files (`.claude/agents/*.md` or `~/.claude/agents/*.md`) — the YAML frontmatter + system prompt that defines a delegatable specialist.

A subagent is one Markdown file: frontmatter (`name`, `description`, `tools`, `model`, …) plus a system-prompt body. This skill builds new ones, audits existing ones against design best practices, and fixes the ones that misfire or over-reach. It is **not** for skills (use `skill-creator`) or `CLAUDE.md`/`AGENTS.md` (use `agent-config`).

## Highlights

- **Three branches** — Create from scratch, Evaluate against a design rubric, or Improve an existing file. The skill picks the branch from your request.
- **Least-privilege by default** — steers tool access toward read-only for reviewers, scoped Bash for workers, full inheritance only for genuine general-purpose agents.
- **Ground-truth templates** — start from a read-only reviewer or a code-editing worker template instead of a blank file.
- **Design-audit rubric** — a six-category pass/fail checklist (frontmatter, single responsibility, tools, description, body structure, anti-patterns), not an eval harness.
- **Repo-safe** — pulls latest before writing into a version-controlled `.claude/agents/` directory.

## When to Use

| Say this… | Skill will… |
|---|---|
| "Create a subagent that reviews changed code for security" | Scaffold a single-responsibility reviewer with least-privilege tools and a structured system prompt |
| "Audit `.claude/agents/debugger.md`" | Walk the design rubric and report before/after fixes without editing |
| "This agent isn't triggering" / "it does too much" | Diagnose and fix the `description`, tool set, or body scope |
| "Is this subagent any good?" | Score it against the rubric and give a PASS / FAIL / PARTIAL verdict |

## Usage

```
/subagent-creator
```

Or describe the task ("make me a test-writing agent", "review my code-reviewer agent") and the skill triggers on its own.

## Resources

| Path | Description |
|---|---|
| `references/frontmatter-schema.md` | Every frontmatter field — required vs. optional, common vs. advanced, tool-restriction syntax, file precedence |
| `references/system-prompt-guide.md` | How to write the body: single-responsibility test, the role→when→process→output→checklist template, description-writing, Do/Don't |
| `references/evaluation-rubric.md` | The six-category design-audit checklist + anti-pattern list |
| `assets/templates/reviewer-agent.md` | Read-only analysis/review agent starter |
| `assets/templates/worker-agent.md` | Code-editing worker agent starter |

## Output

A single, valid subagent `.md` file (Create/Improve), or a rubric-scored audit report with before/after suggestions (Evaluate). Every run ends with a Step Completion Report and a Checked / Verified / Improved summary.
