<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Diagram Generator

> One entry point for diagrams. Routes "make me a diagram" to the right engine — draw.io XML for
> precise, editable technical diagrams, or Excalidraw JSON for a hand-drawn, whiteboard feel.

## Why an umbrella

Both engines produce the same diagram taxonomy (flowchart, architecture, C4, ER, sequence, mind
map) through the same four phases (Understand → Propose → Generate → Validate). They differ only in
output format and aesthetic. Instead of choosing between two similarly named skills, install the
umbrella and let it route.

## Engines

| Engine | Output | Best for |
|---|---|---|
| [drawio-generator](drawio-generator/) | `.drawio` XML | Precise, professional diagrams to edit in draw.io / diagrams.net / Confluence; C4; swimlanes; multi-page |
| [excalidraw-generator](excalidraw-generator/) | `.excalidraw` JSON | Hand-drawn, sketchy, whiteboard feel; wireframes; quick collaborative sketches |

## Install

Install the whole suite:

```bash
asm install github:luongnv89/skills:skills/diagram-generator
```

Or a single engine:

```bash
asm install github:luongnv89/skills:skills/diagram-generator/drawio-generator
asm install github:luongnv89/skills:skills/diagram-generator/excalidraw-generator
```

## Usage

```
/diagram-generator
```

Then the router picks the engine and hands off to `/drawio-generator` or `/excalidraw-generator`.
Routing goes in order: an existing file's extension (`.drawio` or `.excalidraw`), then a named tool
or editing target (draw.io, diagrams.net, Confluence, Excalidraw), then a hand-drawn, sketch or
wireframe look. With no signal it asks one question, precise and editable (draw.io) or hand-drawn
sketch (Excalidraw), and waits for the answer. A missing engine stops the run with its install
command; the router never switches to the other engine on its own.

## Output

The routed engine writes the diagram file (kebab-case `.drawio` or `.excalidraw`) and ends with its
four-line Final Report (`Result:`, `Evidence:`, `Uncertainty:`, `Decision:`). The router relays that
report unchanged. When the router stops before any engine runs (out of scope, no answer to the
routing question, missing engine), it writes its own `BLOCKED` report in the same four lines.

## Resources

| Path | Description |
|---|---|
| `references/final-report.md` | How the engine's Final Report is relayed, the router's three `BLOCKED` templates, fill rules, and reader checks |
| `evals/evals.json` | Routing evals: one case per engine, an existing-file update, no format signal, a named tool against a sketch look, a missing engine, both formats, and two negative triggers (Mermaid, slides) |
| `drawio-generator/` | The draw.io engine, a nested skill with its own SKILL.md, references, agents, and evals |
| `excalidraw-generator/` | The Excalidraw engine, a nested skill with its own SKILL.md, references, agents, and evals |

## Out of scope

Mermaid (native markdown), slide decks, and brand/marketing graphics — use the appropriate native
or design tooling instead.
