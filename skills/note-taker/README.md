# Note Taker

> Capture chat notes (text, voice, image, video, file) into a git-backed repo with task extraction.

## Highlights

- Accept multi-format input: text, voice, images, video, and file attachments
- Embed images in markdown and redact secrets automatically
- Extract tasks to KANBAN.md with backlinks to source notes
- Commit, push, and report GitHub links for all changes

## When to Use

| Say this... | Skill will... |
|---|---|
| "Take a note" | Capture and store a new note |
| "Save a note about X" | Create structured note with metadata |
| "Capture this" | Store content with attachments |
| "Manage my notes" | Organize notes and extract tasks |

## How It Works

```mermaid
graph TD
    A["Accept Input"] --> B["Write Note File"]
    B --> C["Store Attachments"]
    C --> D["Extract Tasks to KANBAN"]
    D --> E["Commit & Push"]
    style A fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
```

## Usage

```
/note-taker <content>
```

## Resources

| Path | Description |
|---|---|
| `assets/` | Note templates and formatting guides |
| `scripts/` | Redaction check script |

## Output

- Note file at `notes/YYYY/MM/YYYY-MM-DD--<slug>.md` with embedded images
- Attachment files stored alongside the note
- Updated KANBAN.md with extracted tasks
- Updated README index with GitHub links to all changes
