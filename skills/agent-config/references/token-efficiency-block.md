# Token Efficiency Block

Insert this verbatim section once into the source-of-truth file — `AGENTS.md` when writing both (or when `AGENTS.md` already exists), otherwise the single target. Do not copy it into the `CLAUDE.md` wrapper; that file opens with `@AGENTS.md` and inherits the block.

```markdown
## Token Efficiency
- Never re-read files you just wrote or edited. You know the contents.
- Never re-run commands to "verify" unless the outcome was uncertain.
- Don't echo back large blocks of code or file contents unless asked.
- Batch related edits into single operations. Don't make 5 edits when 1 handles it.
- Report results and blockers plainly; skip filler like "I'll continue...".
- If a task needs 1 tool call, don't use 3.
```

This block keeps generated configs aligned with the agent's context budget and avoids repeated re-reads or echoes.
