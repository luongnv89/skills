# Anti-Patterns to Avoid

When drafting `CLAUDE.md` / `AGENTS.md`, **do not include**:

- Code style guidelines that linters/formatters already enforce
- Generic best practices the agent already knows ("write clean code", "be careful") — the injected `## Token Efficiency` block is the one deliberate exception
- Anything visible from the tree, README, or package manifest — directory listings, dependency lists, generic architecture recaps
- Long explanations of obvious patterns, tutorials, or API encyclopedias (link instead)
- Copy-pasted code examples
- Information that changes frequently (versions, dates, ticket IDs)
- Instructions for specific one-time tasks
- File-by-file codebase descriptions
- Multi-step runbooks — those belong in a skill (`knowledge-routing.md`)

Structural failure modes, equally disqualifying:

- **Contradiction** — two rules that conflict; the agent picks one at random.
- **Cross-file duplication** — the same rule in both `AGENTS.md` and `CLAUDE.md`. One is the source of truth; the other points at it.
- **Emphasis inflation** — `IMPORTANT` / `YOU MUST` on ordinary lines, which trains the model to ignore the markers on real hard rules.
- **`@import` as a token-saving device** — imported files still load at launch, so imports organize but never shrink context.
- **Prose standing in for a gate** *(audit-time)* — a must-never-happen rule written as a sentence instead of a `PreToolUse` hook, or "please test" instead of a test. Constitution Constraints pins on create/update are expected; this finding is raised on `audit` as a routing recommendation, not as a create blocker.
- **The 400-line constitution** — past 200 lines, adherence drops and rules get lost.

For each line, ask: *"Would removing this cause the agent to make a specific mistake?"* If not, cut it.

If the agent keeps ignoring a rule, the remedies in order: shorten the file, make the line more specific, move it closer to the files it governs, or enforce it with a hook. If the agent asks questions the file already answers, the phrasing is ambiguous — rewrite it.
