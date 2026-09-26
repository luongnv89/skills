---
name: convert-documents-to-markdown
description: "Convert Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV, and PDF files to GitHub-Flavored Markdown when you cannot read the document directly. Don't use for text or Markdown files you can already read, or for creating or editing documents."
license: MIT
compatibility: "Requires Node.js 20+ (runs via npx, no install). Optional FIRECRAWL_API_KEY raises hosted-OCR limits."
effort: low
metadata:
  version: 1.1.0
  author: "Firecrawl — mirrored by Luong NGUYEN <luongnv89@gmail.com>"
---

# Convert documents to Markdown

## When to use

Use this skill when a file's contents are locked in a binary or office format you cannot read directly. Do not use it for `.md`, `.txt`, or other text files — read those as-is — and do not use it to create or edit documents; it only converts to Markdown.

## Prerequisites

- Node.js 20+ on `PATH` — anydoc runs through `npx`, no install.
- Optional: `FIRECRAWL_API_KEY` for higher limits on the hosted OCR path (rule 5).

## Repo Sync Before Edits (mandatory)

When `-o <path>` writes the Markdown output inside a git worktree, sync before the write to avoid clobbering remote work:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash → sync → pop. If `origin` is missing or a conflict occurs: **stop and ask the user.** Skip this section when writing to stdout or to a path outside any git repository.

## Instructions

Run the anydoc CLI:

```bash
npx -y @firecrawl/anydoc@0.2.4 <file>              # Markdown to stdout
npx -y @firecrawl/anydoc@0.2.4 <file> -o out.md    # write to a file
npx -y @firecrawl/anydoc@0.2.4 - --format csv < f  # read stdin
```

Rules:

1. Supported inputs: `.doc`, `.docx`, `.docm`, `.odt`, `.rtf`, `.epub`, `.pdf`, `.ppt`, `.pps`, `.pot`, `.pptx`, `.pptm`, `.ppsx`, `.ppsm`, `.odp`, `.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.ods`, `.csv`.
2. The format is detected from the file content. Pass `--format <name>` only when detection cannot work: CSV from stdin, or a missing or wrong extension.
3. Exit codes: 0 success, 1 the document could not be converted, 2 usage error, 3 pages of a PDF need OCR. Failures print one `anydoc: <message>` line to stderr. The CLI never prompts.
4. For a large document, write to a file with `-o` and read the parts you need instead of streaming everything into context.
5. Scanned and image-only pages need OCR, which anydoc does not do, so the document exits 3. Rerun with `--ocr hosted` to send it to [Firecrawl Parse](https://firecrawl.dev/parse) — this uploads the file to Firecrawl's hosted API, so confirm with the user first. No signup needed. Pass `--api-key` or set `FIRECRAWL_API_KEY` for higher limits.
6. Inside a Node, Python, or Rust codebase, prefer the library over shelling out: `@firecrawl/anydoc` on npm, `firecrawl-anydoc` on PyPI, `anydoc` on crates.io. Each exposes the same `to_markdown` / `toMarkdown` API.

## Example

```bash
npx -y @firecrawl/anydoc@0.2.4 report.docx -o report.md
```

Expected output: exit 0 and `report.md` holds the document as GitHub-Flavored Markdown — headings, lists, and tables preserved. On failure the CLI prints one `anydoc: <message>` line to stderr and exits non-zero.

## Edge cases

- Corrupted or unsupported file → exit 1; report the stderr message instead of retrying blindly.
- CSV piped on stdin, or a file with a missing or wrong extension → pass `--format <name>`; a bad invocation exits 2.
- Scanned or image-only PDF pages → exit 3; only resubmit with `--ocr hosted` after telling the user the file leaves the machine.
- A format outside rule 1's list (e.g. `.png`, `.html`, `.md`) → do not convert; read text formats directly.

## Attribution

Mirrored from [firecrawl/anydoc](https://github.com/firecrawl/anydoc), `skills/convert-documents-to-markdown/`, at upstream commit `1c737ec8216777cd382fcd3fc2e0a47637a8fa30` (2026-08-27). License: MIT, © Sideguide Technologies Inc. — `LICENSE` sits next to this file. The `npx` commands pin `@firecrawl/anydoc@0.2.4`; see `references/attribution.md` for the pin rationale and bump procedure.
