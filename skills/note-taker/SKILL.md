---
name: note-taker
description: Capture chat notes (text, voice, image) into the git-backed notes repo, summarize and organize them, extract tasks into KANBAN.md, and commit/push changes. Use when user says they want to take a note, save a note, capture this, or manage their notes/backlog.
argument-hint: "[optional title or tags]"
disable-model-invocation: true
---

# Note Taker (Git-managed)

This skill maintains NEO’s private notes system in:
`/home/luongnv/workspace/notes`

**Rule:** This skill has side effects (writes + commits + pushes) so it must be user-invoked.

## Workflow

### 1) Intake
Accept input as:
- **Text**: the message content
- **Voice**: summarize (do not store full transcript unless user asks)
- **Image**: keep the image file and reference it from the note

If the user provides multiple items, treat each as a separate note unless they explicitly want a single combined note.

### 2) Decide filename + folder
Create processed notes at:
- `notes/YYYY/MM/YYYY-MM-DD--<slug>.md`

Use a short, stable slug (kebab-case). If unsure, ask for a title.

### 3) Write the note
Use the template in `assets/note-template.md`.
Minimum sections:
- Summary (short)
- Details (only what matters)
- Tasks (checkboxes)
- Attachments (paths)

### 4) Store attachments
- Images → `assets/images/YYYY/MM/<slug>--N.<ext>`
- Audio (optional, if available & <10MB) → `assets/audio/YYYY/MM/<slug>.<ext>`

### 5) Redact secrets (mandatory)
Before committing, scan the note (and any pasted snippets) for:
- API keys / tokens / passwords / private keys

If found:
- replace with `[REDACTED_SECRET]`
- if ambiguity remains, **ask before commit**

### 6) Extract tasks → Kanban
Update `KANBAN.md`:
- Add new tasks to **Backlog**
- Each task should include a link to the note path

### 7) Commit (and push if remote exists)
Commit message conventions:
- `note: add <short-title>`
- `kanban: add tasks from <slug>`
- `note: update <slug>`

If git remote is configured, push.

## Daily routines
- End-of-day: list today’s notes + propose re-organization (tags / merges / splits)
- Daily 10–15min: review Backlog → pick → move to In Progress → Done

## References
- Repo process rules: `/home/luongnv/workspace/notes/AGENTS.md`
- Redaction + workflow policy: `/home/luongnv/workspace/notes/POLICY.md`
