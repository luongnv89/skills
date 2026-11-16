# Self-Test Checklist

Run these checks before declaring success. If any check fails, follow SKILL.md: regenerate the failing part once and re-run every check; a check that still fails is recorded as failed and the run is `PARTIAL`.

1. `grep -c "^### Task " tasks.md` — must be >= 15.
2. `python3 -c 'import re,sys; text=open(sys.argv[1], encoding="utf-8").read(); headings=re.findall(r"^#{1,6}[ \t]+Task\b.*$", text, re.M); canonical=re.compile(r"^### Task ([0-9]+\.[0-9]+):.*$"); assert headings; matches=[canonical.fullmatch(heading) for heading in headings]; assert all(matches), headings; ids=[match.group(1) for match in matches]; assert len(ids) == len(set(ids)), ids' tasks.md` — every task-like heading must be a full canonical `### Task <sprint>.<index>:` heading, and duplicate IDs fail even when titles differ.
3. Every `Depends On` and `Blocks` ID also appears as a task heading (no dangling or fabricated references).
4. No task has itself in its own dependency chain (no cycles).
5. Each `### Task` block contains all four labels: `**Description**`, `**Acceptance Criteria**`, `**Dependencies**`, `**PRD Reference**`.
6. Indices are unique across each sprint even when tasks belong to different workstreams; workstream names never appear in task IDs.
7. Same-sprint edges are represented in both directions: `A` in `B`'s
   `depends_on` exactly matches `B` in `A`'s `blocks`; the resolver adds the
   reciprocal `blocks` entry for a verified cross-sprint dependency in its
   normalized combined map.
