# Token Efficiency Block

Insert this section verbatim, once, into the source-of-truth file. That file is `AGENTS.md` by default, or `CLAUDE.md` on the claude-only branch. Never copy the block into a `CLAUDE.md` wrapper, because the `@AGENTS.md` import already brings it in.

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
