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

Then the router picks the engine (or asks precise-vs-sketch) and hands off to `/drawio-generator`
or `/excalidraw-generator`.

## Out of scope

Mermaid (native markdown), slide decks, and brand/marketing graphics — use the appropriate native
or design tooling instead.
