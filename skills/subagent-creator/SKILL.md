---
name: subagent-creator
description: "Create, evaluate, or improve Claude Code subagent files (.claude/agents/*.md) — the frontmatter + system prompt defining a delegatable specialist. Don't use for skills (skill-creator), CLAUDE.md/AGENTS.md (agent-config), or running an agent."
effort: high
metadata:
  version: 1.0.0
  author: "Luong NGUYEN <edgardo.montesdeoca@montimage.eu>"
---

# Subagent Creator

Create, evaluate, and improve **Claude Code subagents** — the `.md` files (in `.claude/agents/` for a project or `~/.claude/agents/` for personal use) whose YAML frontmatter plus system prompt define a specialist the main agent can delegate to with an isolated context window and restricted tools.

This is **not** about skills (`skill-creator` owns those) or `CLAUDE.md`/`AGENTS.md` (`agent-config` owns those). A subagent is one file: frontmatter (`name`, `description`, `tools`, `model`, …) + a system-prompt body.

## Pick the branch first

Three branches. Identify which one the user is on before doing anything else — they don't share a starting step.

| Branch | Trigger | Go to |
|--------|---------|-------|
| **Create** | "make a subagent that…", "I need an agent for X", no file exists yet | [Creating a subagent](#creating-a-subagent) |
| **Evaluate** | "review this agent", "is this subagent any good", "audit `.claude/agents/foo.md`" | [Evaluating a subagent](#evaluating-a-subagent) |
| **Improve** | "fix this agent", "this subagent isn't triggering / over-reaches", points at an existing file | [Improving a subagent](#improving-a-subagent) |

If the request is ambiguous ("look at my agent"), assume **Evaluate** and confirm before editing anything.

## Mandatory rules (all branches)

These apply on every write, regardless of branch.

### Repo Sync Before Edits (when target is a project repo)

A subagent written to `.claude/agents/` lives in a version-controlled repo. **Before creating or editing a file there**, sync to avoid clobbering remote work:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash → sync → pop. If `origin` is missing or a conflict occurs: **stop and ask the user.** Skip this section only when the target is `~/.claude/agents/` (personal, not a repo) — confirm the scope with the user before assuming.

### Frontmatter safety + version

- **Subagent file** `name` must be lowercase letters/digits/hyphens, no consecutive hyphens, and match the filename stem (`code-reviewer` → `code-reviewer.md`).
- Quote any frontmatter string value containing `:` `#` `-` `<` `>` `|` `,` `&` `?` `!` `[` `]` `{` `}` `*` to keep YAML valid. `description` almost always needs quotes.
- This **SKILL.md** itself follows the catalog's own rule: bump `metadata.version` on every edit.

### Scope check (one question, not an interview)

Confirm **where the file goes** — `.claude/agents/<name>.md` (project, team-shared, version-controlled) or `~/.claude/agents/<name>.md` (personal, cross-project). This decides Repo Sync above and nothing else. The source guideline encodes the rest of the intent, so don't over-interview.

---

## Creating a subagent

Goal: one well-formed `<name>.md` file that triggers reliably, stays in its lane, and holds only the tools it needs.

### 1. Capture the specialist in one sentence

A good subagent has a **single responsibility**. Force the purpose into one sentence: *"A read-only security auditor that flags auth and data-exposure bugs in changed files."* If you need "and" to join two unrelated jobs, that's two subagents. Read `references/system-prompt-guide.md` → *Single responsibility* if the scope feels fuzzy.

### 2. Choose frontmatter

Start from the **minimal set** and add only what the job demands. Read `references/frontmatter-schema.md` for every field, which are safe-and-common vs. advanced-and-rot-prone, and the tool-restriction syntax.

Minimal viable frontmatter:

```yaml
---
name: <kebab-name>
description: "<when to invoke + what it does. Add 'Use PROACTIVELY' to encourage auto-delegation.>"
tools: Read, Grep, Bash   # omit entirely to inherit ALL tools
model: inherit            # inherit | sonnet | opus | haiku
---
```

Decisions, in order:
- **`description`** — the primary trigger. Say *when* to invoke and *what* it does. Add `Use PROACTIVELY` (or `MUST BE USED`) when the agent should auto-delegate. This is the single highest-leverage field; see the description guidance in `references/system-prompt-guide.md`.
- **`tools`** — least privilege. Prefer read-only (`Read, Grep, Glob`) for analysis/review agents; add `Edit`/`Write` only for agents that change code; scope `Bash` to patterns (`Bash(npm:*), Bash(git:*)`) when you can. **Omitting `tools` inherits everything** — only do that for general-purpose agents.
- **`model`** — `inherit` is the safe default. Use `haiku` for fast/cheap search agents, `opus` for hard reasoning.
- Anything beyond these (`maxTurns`, `isolation`, `memory`, `context`, `hooks`, …) → consult `references/frontmatter-schema.md` first; most subagents need none of them.

### 3. Write the system-prompt body

The body is the agent's system prompt. Use the proven structure — **role → when invoked → process → output format → checklist**. Read `references/system-prompt-guide.md` for the full template, the "be example-rich" guidance, and an annotated example. Start from a template in `assets/templates/` (`reviewer-agent.md` for read-only analysis agents, `worker-agent.md` for agents that edit code) rather than a blank file.

### 4. Write the file and validate

Write to the path confirmed in the scope check. Then verify it parses and follows the design rules — run the evaluation rubric against your own draft (it's the same checklist; see [Evaluating](#evaluating-a-subagent)). At minimum confirm: frontmatter parses, `name` matches filename, `tools` is least-privilege, description has both a *when* and a *what*.

Emit a Step Completion Report:

```
◆ Create subagent (step 4 of 4 — <name>.md)
··································································
  Frontmatter parses:    √ pass
  name == filename:      √ pass
  Single responsibility: √ pass
  Tools least-privilege: √ pass (read-only: Read, Grep)
  Description: when+what: √ pass
  ____________________________
  Result:                PASS
```

---

## Evaluating a subagent

Goal: a verdict on an existing subagent file against design best practices — **a checklist audit, not an eval harness.** No test runs, no benchmarks; the source guideline defines quality by design principles, so grade against those.

1. Read the target file (frontmatter + body). Identify its claimed responsibility.
2. Walk **every** item in `references/evaluation-rubric.md` — frontmatter validity, single responsibility, least-privilege tools, description quality (trigger clarity + proactive hint), system-prompt structure, and the anti-patterns list.
3. Score each item `√ pass` / `× fail` / `~ partial` with a one-line reason.
4. Output findings as before/after suggestions. **In Evaluate mode, do not silently edit the file** — surface the fixes and let the user decide (or switch to Improve).

Emit a Step Completion Report with one check per rubric category and an overall `PASS | FAIL | PARTIAL`.

---

## Improving a subagent

Goal: apply concrete fixes to an existing file and leave it measurably better.

1. Run the **Evaluate** branch first (above) to get the findings list. Don't skip — fixing without auditing misses the systemic issues.
2. Apply Repo Sync Before Edits if the file is in a project repo.
3. Apply fixes, ordered by impact:
   - **Triggering problems** (under/over-firing) → rewrite `description`: sharpen *when*, add/adjust `Use PROACTIVELY`, name what it's *not* for. Highest leverage.
   - **Over-reach** (agent does too much) → split responsibilities or tighten the body's scope.
   - **Over-provisioned tools** → reduce to least privilege; prefer read-only.
   - **Weak body** → impose the role → when-invoked → process → output → checklist structure.

   See `references/system-prompt-guide.md` for the patterns behind each fix.
4. Re-run the rubric to confirm the findings are resolved and nothing regressed.
5. Emit a Step Completion Report showing each prior `× fail` now `√ pass`.

---

## Final summary

Close any create/evaluate/improve run with three short lists:

- **Checked** — rubric categories inspected (frontmatter, responsibility, tools, description, body structure, anti-patterns).
- **Verified** — what proves the result (frontmatter parses, file path written, rubric pass).
- **Improved** — concrete changes by field/concern (or `none — review only` for an Evaluate run).

---

## Reference files

- `references/frontmatter-schema.md` — every frontmatter field: required vs. optional, safe-and-common vs. advanced, tool-restriction syntax, file-location precedence. Read before choosing frontmatter.
- `references/system-prompt-guide.md` — how to write the system-prompt body: single-responsibility test, the role→when→process→output→checklist template, description-writing, an annotated example, design Do/Don't.
- `references/evaluation-rubric.md` — the pass/fail checklist for Evaluate and the self-check in Create. The anti-pattern list lives here.

## Templates

- `assets/templates/reviewer-agent.md` — read-only analysis/review agent (Read, Grep, Glob; no edits).
- `assets/templates/worker-agent.md` — agent that edits code (Read, Edit, Bash, …).
