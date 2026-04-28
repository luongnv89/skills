# Token Efficiency Block

Insert this verbatim section into every generated `CLAUDE.md` and `AGENTS.md` file:

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

This block keeps generated configs aligned with the agent's context budget and avoids repeated re-reads or echoes.
