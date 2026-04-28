# Self-Test Checklist

Run these checks before declaring success. If any check fails, fix `tasks.md` before reporting completion.

1. `grep -c "^### Task " tasks.md` — must be >= 15.
2. `grep -E "^### Task [0-9]+\.[0-9]+" tasks.md | sort -u` — every task ID unique.
3. Every `Depends On` ID also appears as a task heading (no dangling references).
4. No task has itself in its own dependency chain (no cycles).
5. Each `### Task` block contains all four labels: `**Description**`, `**Acceptance Criteria**`, `**Dependencies**`, `**PRD Reference**`.
