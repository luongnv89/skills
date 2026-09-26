---
name: diagram-generator
description: "Generate a diagram and route to the right engine — draw.io XML (precise, editable, C4, swimlanes) or Excalidraw JSON (hand-drawn, sketch, wireframes). One entry for flowcharts, architecture, ER, sequence, mind maps. Don't use for Mermaid or slides."
license: MIT
effort: high
metadata:
  version: 1.2.0
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
- No format signal → ask one question: "Precise and editable (draw.io) or hand-drawn sketch (Excalidraw)?" Keep routing blocked until the user answers. Only after explicit delegation such as "just pick", "choose for me", or "use the default", choose **draw.io** for architecture/C4/technical diagrams and **Excalidraw** for wireframes/brainstorms.
- The user asks for **Mermaid**, a slide deck, or brand/marketing graphics → out of scope; say so (Mermaid is native markdown; use a presentation or design tool for the others).

## Dependency Preflight (mandatory)

Routing above selects exactly one engine — `drawio-generator` or `excalidraw-generator` — which
"How to use" then invokes by name. Once routing picks `engine`, and **before** invoking it, verify
that engine is installed:

```bash
engine=drawio-generator   # or excalidraw-generator — whichever routing selected
asm list -p claude --json | grep -q "\"$engine\"" || {
  echo "Missing required skill: $engine" >&2
  echo "Install it:      asm install github:luongnv89/skills:skills/diagram-generator/$engine -p claude --yes" >&2
  echo "Verify:          asm list -p claude --json | grep '\"$engine\"'" >&2
  echo "No asm yet:      npm install -g agent-skill-manager" >&2
  echo "Stop — never substitute the other engine; if it is installed, the user may re-request it explicitly." >&2
  exit 1
}
```

A missing routed engine stops the run before any output is written.

## How to use

Once the engine is chosen, invoke the nested skill by name — the runtime resolves names regardless
of filesystem path:

- `/drawio-generator` — generate draw.io XML
- `/excalidraw-generator` — generate Excalidraw JSON

Each engine owns its full workflow, `references/`, `agents/`, and validation checks. This umbrella
stays short to protect the agent's context budget; it only routes.

## Prerequisites

1. Confirm at least one nested engine is installed and callable.
2. Require enough diagram content to identify nodes, relationships, and intended audience; ask for
   missing essentials before routing.
3. Check whether the requested output path already exists. Let the selected engine run its own
   confirmation, backup, dry-run, error, and rollback safeguards before any overwrite.

## Example

```text
Input: "Draw a sketchy onboarding wireframe for mobile."
Route: excalidraw-generator
Expected output: one validated .excalidraw JSON artifact
```

## Acceptance Criteria

Verify every routed run:

- Exactly one engine is selected unless the user explicitly requests both formats.
- The selected engine matches the requested format, editing target, or aesthetic.
- The nested workflow reaches its Validate phase and produces its expected output artifact.
- The artifact passes the engine's structural checks; validation errors are reported, not hidden.
- Existing files are not overwritten without the selected engine's required confirmation or backup.

## Step Completion Reports

After routing, emit:

```text
◆ Route Diagram
  Engine available:    √ pass
  Route justified:     √ pass
  Output validated:    √ pass
  Result:              PASS | FAIL | PARTIAL
```

Use `× fail — reason` when a check fails. Report PASS only after the nested engine's acceptance
criteria and expected result are verified.

## Edge Cases

- **User explicitly wants both formats** — generate with one engine first, then offer to regenerate the same diagram in the other.
- **Ambiguous, no answer to the routing question** — keep routing blocked and ask the question again; silence or timeout is not approval to choose an engine. Apply the routing heuristics only when the user explicitly delegates the choice (for example, "just pick", "choose for me", or "use the default").
- **Routed engine is unavailable** — the Dependency Preflight stops the run with its install command; the other engine is only an alternative the user may re-request explicitly. Never substitute silently or invent output under the wrong engine.
