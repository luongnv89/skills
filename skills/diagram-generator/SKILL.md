---
name: diagram-generator
description: "Generate a diagram and route to the right engine — draw.io XML (precise, editable, C4, swimlanes) or Excalidraw JSON (hand-drawn, sketch, wireframes). One entry for flowcharts, architecture, ER, sequence, mind maps. Don't use for Mermaid or slides."
license: MIT
effort: high
metadata:
  version: 1.0.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Diagram Generator

Single entry point for "make me a diagram". This umbrella picks the right engine and hands off to
it — both produce the same diagram taxonomy (flowchart, architecture, C4, ER, sequence, mind map)
through the same four phases (**Understand → Propose → Generate → Validate**); they differ only in
**output format and aesthetic**.

## Which engine?

| Pick | When the user wants... | Output | Nested skill |
|---|---|---|---|
| **draw.io** | Precise, professional diagrams to edit later in draw.io / diagrams.net / Confluence; official C4 styling; swimlanes; multi-page | `.drawio` XML | `drawio-generator` |
| **Excalidraw** | A hand-drawn, sketchy, whiteboard feel; wireframes; quick collaborative sketches | `.excalidraw` JSON | `excalidraw-generator` |

Routing rules:

- The user names a format or tool ("draw.io", "diagrams.net", "Excalidraw", "whiteboard sketch") → use that engine.
- The user names an editing target ("I'll tweak it in draw.io", "import to Confluence") → **draw.io**.
- The user wants a hand-drawn / sketch / wireframe look → **Excalidraw**.
- No format signal → ask one question: "Precise and editable (draw.io) or hand-drawn sketch (Excalidraw)?" Default to **draw.io** for architecture/C4/technical diagrams and **Excalidraw** for wireframes/brainstorms if the user says "just pick".
- The user asks for **Mermaid**, a slide deck, or brand/marketing graphics → out of scope; say so (Mermaid is native markdown; use a presentation or design tool for the others).

## How to use

Once the engine is chosen, invoke the nested skill by name — the runtime resolves names regardless
of filesystem path:

- `/drawio-generator` — generate draw.io XML
- `/excalidraw-generator` — generate Excalidraw JSON

Each engine owns its full workflow, `references/`, `agents/`, and validation checks. This umbrella
stays short to protect the agent's context budget; it only routes.

## Layout

This umbrella and its engines live together in one suite folder:

```
skills/diagram-generator/            ← this umbrella (router)
├── SKILL.md                         ← you are here
├── drawio-generator/                ← draw.io XML engine
└── excalidraw-generator/            ← Excalidraw JSON engine
```

Why nested: both engines serve one intent ("make a diagram") and differ only by output format, so a
single entry point removes the "which diagram skill do I use?" decision. Each engine stays
independently installable — the installers (`install.sh`, `remote-install.sh`) discover both
top-level and nested skills. This mirrors the `website-cloner` suite convention (see README
*Suite Folders*).

## Edge Cases

- **User explicitly wants both formats** — generate with one engine first, then offer to regenerate the same diagram in the other.
- **Ambiguous, no answer to the routing question** — default to draw.io and note the choice; the user can ask for an Excalidraw version.
- **A nested engine is not installed** — fall back to the one that is, and note the limitation.
