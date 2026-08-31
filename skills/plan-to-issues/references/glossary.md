# Glossary

The full definitions of the terms SKILL.md uses. Read once before Phase 0.


- **input** — what is being converted: a **plan file** at any path, or **conversational intent**
  from the user's turns. Resolution rules: `references/input-resolution.md`.
- **task** — one atomic unit of work: a `Task <id>: <title>` block in a plan file, or one confirmed
  row of a conversation draft. One task, one issue.
- **worklist** — the structured parse of the input: phases → sprints → tasks, plus milestones,
  dependencies, and deferred rows. One schema for both inputs; see `references/plan-parsing.md`.
- **label set** — the deterministic labels derived from a task: `phase:<p>`, one type label,
  `dim:<d>` per closed dimension, `priority:<p>`. Rules in `references/labels.md`.
- **epic plan map** — the phase-grouped block in the epic body, between **map sentinels**
  `<!-- plan-dashboard:start -->` / `<!-- plan-dashboard:end -->`. It is **static**: it names which
  issue implements which task and asserts no issue status, so it never goes stale as work proceeds.
  Only the region between the sentinels is ever rewritten.
- **source marker** — the comment binding an epic to its input:
  `<!-- plan-to-issues:plan=<path> -->` on the file path (unchanged from 1.x, so epics created by
  earlier versions keep resolving), or `<!-- plan-to-issues:conversation=<slug> -->` on the
  conversation path. An epic carries exactly one kind, never both.
- **source-faithful** — every word of every issue traces to the input text. Never open source files,
  never predict affected files, never add analysis the input did not contain.
- **idempotent re-run** — a task that already has an issue under this epic is skipped. Automatic on
  the file path; **operator-supplied** on the conversation path (`references/input-resolution.md`).
- **verify-by-re-read** — confirm every mutation by reading the object back (`gh issue view --json`),
  never by trusting an exit code.

