# Writing the subagent system-prompt body

Everything below the frontmatter is the agent's **system prompt**. It defines who the agent is, what it does when invoked, and the shape of its output. A vague body produces a vague agent; an example-rich, structured body produces a reliable one.

## Single responsibility (test this first)

A subagent does **one job**. Before writing anything, state the job in one sentence with no "and" joining unrelated work:

- ✅ *"A read-only security auditor that flags auth and data-exposure bugs in changed files."*
- ✅ *"A debugger that finds the root cause of a failure and applies the minimal fix."*
- ❌ *"Reviews code **and** writes tests **and** updates the docs."* → that's three agents.

If the sentence needs "and", either the extra clause is a natural sub-step of one job (fine) or it's a second responsibility (split it). Overlapping, multi-concern agents are the most common subagent anti-pattern — they trigger unpredictably and do each job worse.

## The proven body structure

Use this five-part skeleton. It's the structure the source guideline's example agents follow, and it maps directly to how the main agent will invoke and consume the subagent.

```markdown
# <Title> Agent

You are an expert <specialty> specializing in <domain/focus>.

When invoked:
1. <first concrete action — usually orient: read the diff, capture the error>
2. <analysis step>
3. <produce-the-output step>

## <Process> (the how, expanded)

1. **<Phase>**
   - <concrete sub-step>
   - <concrete sub-step>
2. **<Phase>**
   - ...

## Output Format

For each <finding / fix / item>:
- **<Label>**: <what goes here>
- **<Label>**: <what goes here>

## Checklist

- [ ] <verifiable completion criterion>
- [ ] <verifiable completion criterion>
```

Why each part:
- **Role line** — sets identity and focus in one sentence. Keep it tight.
- **When invoked** — the ordered actions the agent takes immediately. This is what makes behavior repeatable across runs.
- **Process** — expands the *how* with concrete sub-steps. Be specific: name the commands (`git diff`, `grep -r`), the files, the order.
- **Output Format** — the single highest-value section for a delegatable agent. The main agent consumes this output; a fixed shape makes results parseable and comparable. Use labeled fields.
- **Checklist** — verifiable done-criteria so the agent doesn't stop early. Tie each box to a state the agent can check, not a vibe.

### Annotated reference example

This is a faithful, ground-truth shape (a debugger agent). Note how every section is concrete:

```markdown
---
name: debugger
description: "Debugging specialist for errors, test failures, and unexpected behavior. Use PROACTIVELY when encountering any issues."
tools: Read, Edit, Bash, Grep, Glob
model: inherit
---

# Debugger Agent

You are an expert debugger specializing in root cause analysis.

When invoked:
1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

## Debugging Process

1. **Analyze error messages and logs**
   - Read the full error message
   - Examine stack traces
2. **Check recent code changes**
   - Run git diff to see modifications
   - Identify potentially breaking changes
3. **Form and test hypotheses**
   - Start with the most likely cause
   - Add strategic debug logging

## Output Format

For each issue investigated:
- **Error**: Original error message
- **Root Cause**: Why it failed
- **Evidence**: How you determined the cause
- **Fix**: Specific code changes made
- **Testing**: How the fix was verified

## Checklist
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests pass
- [ ] No regressions introduced
```

Everything is actionable: real commands, ordered steps, labeled output, checkable boxes. Match that altitude — avoid filler like "be thorough" or "think carefully," which change nothing the agent does.

## Writing the `description` (the trigger)

The `description` decides whether the agent fires. It has two jobs: **pull in** the tasks that should invoke it and **push away** adjacent ones that shouldn't.

- State **when** to invoke and **what** the agent does. `description: "Reviews changed code for security and quality. Use PROACTIVELY after edits."` beats `description: "A code reviewer."`
- Add **`Use PROACTIVELY`** or **`MUST BE USED`** when the agent should auto-delegate without the user naming it. Omit when it should only run on explicit request.
- Name what it's **not** for when a sibling agent could grab the same task — *"Reviews code; not for writing new tests (use test-engineer)."* This is the equivalent of a skill's negative-trigger clause and prevents the wrong specialist firing.

## Tool access strategy

The body and the `tools` frontmatter must agree. A "read-only auditor" body with `Edit` in `tools` is a contradiction — and a risk.

1. Start from the minimal set the job needs.
2. Prefer read-only (`Read, Grep, Glob`) for any analysis/review agent.
3. Add `Edit`/`Write` only for agents whose job is to change code, and say so in the role line.
4. Scope `Bash` to command patterns where possible (`Bash(npm:*), Bash(git:*)`).
5. Use `disallowedTools` to explicitly forbid a dangerous tool an agent would otherwise inherit.

## Design Do / Don't

**Do:**
- Give each agent a single, sharp responsibility.
- Write detailed, example-rich prompts — name commands, files, output labels.
- Grant only the tools the job needs.
- Use a fixed Output Format so the main agent can consume results.
- Version-control project agents (`.claude/agents/`).

**Don't:**
- Create overlapping agents with near-identical purposes — they fight over triggers.
- Over-provision tools "just in case."
- Mix multiple concerns in one prompt.
- Leave the output shape unspecified.
- Pad the prompt with no-op exhortations ("be careful", "use good judgment") — replace each with a concrete step or a checklist item.
