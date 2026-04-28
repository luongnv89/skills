# Anti-Patterns to Avoid

When drafting `CLAUDE.md` / `AGENTS.md`, **do not include**:

- Code style guidelines that linters/formatters already enforce
- Generic best practices Claude already knows ("write clean code")
- Long explanations of obvious patterns
- Copy-pasted code examples
- Information that changes frequently (versions, dates, ticket IDs)
- Instructions for specific one-time tasks
- File-by-file codebase descriptions

For each line, ask: *"Would removing this cause Claude to make mistakes?"* If not, cut it.

If Claude keeps ignoring a rule, the file is probably too long and the rule is getting lost. If Claude asks questions answered in the file, the phrasing is ambiguous — rewrite it.
