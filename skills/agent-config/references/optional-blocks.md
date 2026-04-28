# Optional Blocks (Workflow + Coding Discipline)

Add these blocks to generated `CLAUDE.md` / `AGENTS.md` only when the user explicitly asks for orchestration rigor or stricter coding workflow rules.

## Workflow Orchestration (Balanced)

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

## Mandatory Coding Discipline Block

```markdown
1. Before writing any code, describe your approach and wait for approval.
2. If the requirements I give you are ambiguous, ask clarifying questions before writing any code.
3. After you finish writing any code, list the edge cases and suggest test cases to cover them.
4. If a task requires changes to more than 3 files, stop and break it into smaller tasks first.
5. When there's a bug, start by writing a test that reproduces it, then fix it until the test passes.
6. Every time I correct you, reflect on what you did wrong and come up with a plan to never make the same mistake again.
```

Insert verbatim — do not paraphrase. Both blocks are opt-in.
