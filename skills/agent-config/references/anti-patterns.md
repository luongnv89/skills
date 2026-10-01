# Anti-Patterns to Avoid

When drafting `AGENTS.md` or `CLAUDE.md`, **don't include**:

- Codebase overviews, directory trees, dependency lists, or anything the README or manifest already says. Agents read those directly, and overviews don't help them find the right files any sooner.
- Style rules that a linter or formatter already enforces.
- Generic best practices ("write clean code", "be careful"). The injected `## Token Efficiency` block is the one deliberate exception.
- Long explanations, tutorials, or API encyclopedias. Point to the doc instead.
- Pasted code examples. Point to an exemplar file instead (rule 6 in `agents-md-writing.md`).
- Information that changes often: dependency versions, dates, ticket IDs.
- Instructions for one-time tasks.
- Multi-step runbooks. Those belong in a skill (see `knowledge-routing.md`).
- Checks the agent shouldn't run on every task, because every listed command gets executed.

These structural failure modes are just as disqualifying:

- **Contradiction**: two rules that conflict, so the agent picks one at random.
- **Cross-file duplication**: the same rule in both `AGENTS.md` and `CLAUDE.md`, including a `CLAUDE.md` that holds a pasted copy of `AGENTS.md`. One file is the source of truth, and the other imports it.
- **Shadowed `AGENTS.md`**: a `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` at or above `AGENTS.md` that doesn't import it, so Claude Code silently ignores `AGENTS.md`.
- **Prose instead of an import**: "read AGENTS.md first" makes loading the file optional, while `@AGENTS.md` makes it certain.
- **A non-portable `AGENTS.md`**: `@imports`, plan mode, hooks, `/commands`, or skill names in the shared file, which other agents can't use.
- **Emphasis inflation**: `IMPORTANT` or `YOU MUST` on ordinary lines teaches the model to ignore those markers on the real hard rules.
- **`@import` as a token-saving device**: imported files still load at launch.
- **Prose standing in for a gate** *(audit-time)*: a must-never-happen rule written as a sentence instead of a `PreToolUse` hook, or "please test" instead of a test. Constraints written during create or update are expected, so raise this on `audit` as a routing recommendation.
- **The 400-line constitution**: past 200 lines, adherence drops and rules get lost.

For each line, ask: *"Would removing this cause the agent to make a specific mistake?"* If not, cut it.

If the agent keeps ignoring a rule, shorten the file, make the line more specific, move it closer to the files it governs, or enforce it with a hook. If the agent asks questions the file already answers, the phrasing is ambiguous, so rewrite it.
