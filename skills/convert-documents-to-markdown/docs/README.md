<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Convert Documents to Markdown

> Convert office documents, ebooks, spreadsheets, and PDFs to GitHub-Flavored Markdown with a single `npx` command.

Mirrored from [firecrawl/anydoc](https://github.com/firecrawl/anydoc) (`skills/convert-documents-to-markdown/`) at upstream commit [`1c737ec`](https://github.com/firecrawl/anydoc/commit/1c737ec8216777cd382fcd3fc2e0a47637a8fa30) (2026-08-27). License: MIT — © Sideguide Technologies Inc. (see [`LICENSE`](../LICENSE)).

## Highlights

- One `npx` call — no install, just needs Node.js 20+
- Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV, and PDF → GitHub-Flavored Markdown
- Format auto-detected from file content; `--format` only needed for stdin or wrong extensions
- `-o out.md` writes large documents to a file instead of flooding context
- Scanned PDFs exit 3; `--ocr hosted` resubmits them to Firecrawl's hosted Parse API

## When to Use

| Say this... | Skill will... |
|---|---|
| "Extract this .docx as Markdown" | Run `npx -y @firecrawl/anydoc@0.2.4 report.docx` |
| "Get the numbers out of this .xlsx" | Convert the spreadsheet to Markdown tables |
| "Read this PDF" | Convert it; exit 3 means pages are image-only and need `--ocr hosted` |
| "Convert slides to text" | Handle `.ppt`/`.pptx`/`.odp` → Markdown |

## Supply-chain pin

The `npx` invocations pin `@firecrawl/anydoc@0.2.4` (published 2026-08-27) rather than floating on `latest`. Bump procedure is documented in `references/attribution.md`.
