---
name: agent-config
description: Create or update CLAUDE.md and AGENTS.md files following official best practices. Use when asked to create, update, audit, or improve project configuration files for AI agents, or when users mention "CLAUDE.md", "AGENTS.md", "agent config", or "agent instructions".
effort: medium
license: MIT
metadata:
  version: 1.1.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## User Input

```text
$ARGUMENTS
```

Consider user input for:
- `create` - Create new file from scratch
- `update` - Improve existing file
- `audit` - Analyze and report on current file quality
- A specific path (e.g., `src/api/CLAUDE.md` for directory-specific instructions)

## Step 1: Determine Target File

If not specified in user input, ask the user which file type to work with:

**CLAUDE.md** - Project context file loaded at the start of every conversation. Contains:
- Bash commands Claude cannot guess
- Code style rules that differ from defaults
- Testing instructions and preferred test runners
- Repository etiquette (branch naming, PR conventions)
- Architectural decisions specific to the project
- Developer environment quirks (required env vars)
- Common gotchas or non-obvious behaviors

**AGENTS.md** - Custom subagent definitions file. Contains:
- Specialized assistant definitions
- Tool permissions for each agent
- Model preferences (opus, sonnet, haiku)
- Focused instructions for isolated tasks

## CLAUDE.md Guidelines

Based on official Claude Code documentation.

### Core Principle

CLAUDE.md is a special file Claude reads at the start of every conversation. Include Bash commands, code style, and workflow rules. This gives Claude persistent context **it cannot infer from code alone**.

### What to Include

| ✅ Include | ❌ Exclude |
|-----------|-----------|
| Bash commands Claude cannot guess | Anything Claude can figure out by reading code |
| Code style rules that differ from defaults | Standard language conventions Claude already knows |
| Testing instructions and preferred test runners | Detailed API documentation (link to docs instead) |
| Repository etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to your project | Long explanations or tutorials |
| Developer environment quirks (required env vars) | File-by-file descriptions of the codebase |
| Common gotchas or non-obvious behaviors | Self-evident practices like "write clean code" |

### Quality Test

For each line, ask: *"Would removing this cause Claude to make mistakes?"* If not, cut it.

If Claude keeps ignoring a rule, the file is probably too long and the rule is getting lost. If Claude asks questions answered in CLAUDE.md, the phrasing might be ambiguous.

### Example Format

```markdown
# Code style
- Use ES modules (import/export) syntax, not CommonJS (require)
- Destructure imports when possible (eg. import { foo } from 'bar')

# Workflow
- Be sure to typecheck when you're done making a series of code changes
- Prefer running single tests, and not the whole test suite, for performance
```

### File Locations

- **Home folder (`~/.claude/CLAUDE.md`)**: Applies to all Claude sessions
- **Project root (`./CLAUDE.md`)**: Check into git to share with your team
- **Local only (`CLAUDE.local.md`)**: Add to `.gitignore` for personal overrides
- **Parent directories**: Useful for monorepos where both `root/CLAUDE.md` and `root/foo/CLAUDE.md` are pulled in automatically
- **Child directories**: Claude pulls in child CLAUDE.md files on demand

### Import Syntax

CLAUDE.md files can import additional files using `@path/to/import` syntax:

```markdown
See @README.md for project overview and @package.json for available npm commands.

# Additional Instructions
- Git workflow: @docs/git-instructions.md
- Personal overrides: @~/.claude/my-project-instructions.md
```

### Emphasis for Critical Rules

Add emphasis (e.g., "IMPORTANT" or "YOU MUST") to improve adherence for critical rules.

## AGENTS.md Guidelines

Custom subagents run in their own context with their own set of allowed tools. Useful for tasks that read many files or need specialized focus.

### Agent Definition Format

```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: opus
---
You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling

Provide specific line references and suggested fixes.
```

### Required Fields

- **name**: Identifier to invoke the agent
- **description**: What the agent does (helps Claude decide when to use it)
- **tools**: Comma-separated list of allowed tools (Read, Grep, Glob, Bash, Edit, Write, etc.)

### Optional Fields

- **model**: Preferred model (opus, sonnet, haiku)

### Best Practices for Agents

1. Keep agent instructions focused on a single domain
2. Be specific about what the agent should look for
3. Request concrete output formats (line references, specific fixes)
4. Limit tool access to what's actually needed

## Execution Flow

### For `create` or default:

1. Ask which file type (CLAUDE.md or AGENTS.md) if not specified
2. Analyze the project:
   - Check for existing files at standard locations
   - Identify technology stack, project type, development tools
   - Review README.md, CONTRIBUTING.md, package.json, etc.
3. Draft the file following guidelines above
4. If the user explicitly asked to apply now, write directly; otherwise present draft for review
5. Finalize at the appropriate location

### For `update`:

1. Read existing file
2. Audit against best practices
3. Identify:
   - Content to remove (redundant, obvious, style rules)
   - Content to condense
   - Missing essential information
4. If the user explicitly asked to apply now, implement directly; otherwise present changes for review
5. Finalize updates in place

### For `audit`:

1. Read existing file
2. Generate a report with:
   - Assessment of content quality
   - List of anti-patterns found
   - Percentage of truly useful vs redundant content
   - Specific recommendations for improvement
3. Do NOT modify the file, only report

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Determine Target File** — checks: `File detection`, `File type identified`, `Location confirmed`

**Phase: Analyze Project** — checks: `File detection`, `Best practices`, `Content structure`, `Location accuracy`

**Phase: Draft / Audit** — checks: `Content quality`, `Anti-patterns removed`, `Essential info present`, `Format compliance`

**Phase: Finalize** — checks: `File written`, `Import syntax valid`, `Token efficiency block present`, `No redundant content`

## Token Efficiency

IMPORTANT: Always include the following section in generated CLAUDE.md and AGENTS.md files to ensure efficient token usage:

```markdown
## Token Efficiency
- Never re-read files you just wrote or edited. You know the contents.
- Never re-run commands to "verify" unless the outcome was uncertain.
- Don't echo back large blocks of code or file contents unless asked.
- Batch related edits into single operations. Don't make 5 edits when 1 handles it.
- Skip confirmations like "I'll continue..." Just do it.
- If a task needs 1 tool call, don't use 3. Plan before acting.
- Do not summarize what you just did unless the result is ambiguous or you need additional input.
```

## Workflow Orchestration (optional, when requested)

When users ask for stronger execution discipline, include a concise orchestration block in generated CLAUDE.md/AGENTS.md.

Use this pattern (keep it short and enforceable):

```markdown
## Workflow Orchestration (Balanced)
- For non-trivial tasks (3+ steps, architecture choices, or unclear dependencies), write a short plan first.
- If assumptions break, stop and re-plan before continuing.
- Use subagents strategically for parallel exploration; keep one focused goal per subagent.
- Do not mark tasks done without evidence (tests, logs, diffs, or output proof).
- Prefer elegant solutions for non-trivial work; keep simple fixes minimal.
- If logs/tests clearly show root cause, fix directly; ask only when risk or ambiguity is high.
- Capture lessons after corrections in durable docs to reduce repeat mistakes.

Core bias:
- Simplicity first
- Root-cause over patchwork
- Minimal-impact changes
```

Do not inject this section blindly—add it when the user asks for orchestration/process rigor.

## Mandatory Coding Discipline Block (when requested)

When users ask for stricter coding workflow rules, include this exact numbered block in generated config files:

```markdown
1. Before writing any code, describe your approach and wait for approval.
2. If the requirements I give you are ambiguous, ask clarifying questions before writing any code.
3. After you finish writing any code, list the edge cases and suggest test cases to cover them.
4. If a task requires changes to more than 3 files, stop and break it into smaller tasks first.
5. When there’s a bug, start by writing a test that reproduces it, then fix it until the test passes.
6. Every time I correct you, reflect on what you did wrong and come up with a plan to never make the same mistake again.
```

## Anti-Patterns to Avoid

**DO NOT include:**
- Code style guidelines (use linters/formatters)
- Generic best practices Claude already knows
- Long explanations of obvious patterns
- Copy-pasted code examples
- Information that changes frequently
- Instructions for specific one-time tasks
- File-by-file codebase descriptions

