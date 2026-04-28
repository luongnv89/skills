---
name: excalidraw-generator
description: "Generate professional diagrams as valid Excalidraw JSON files — flowcharts, architecture, ER diagrams, mind maps, sequence diagrams, wireframes, C4 models, and more. Understands text, code, schemas, or verbal descriptions. Don't use for draw.io/Mermaid output, polished production slide decks, or pixel-perfect brand graphics."
license: MIT
effort: high
metadata:
  version: 1.3.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Excalidraw Diagram Generator

Generate professional diagrams as valid Excalidraw JSON. Every diagram goes through four phases: **Understand** the request, **Propose** options, **Generate** the JSON, and **Validate** before writing the file.

This SKILL.md is intentionally compact to fit the agent's context budget (token-efficient body). Long-form details live in `references/` — read the linked file when you need depth.

## When to Use

Use when the user asks for a diagram, flowchart, architecture sketch, ER/class/sequence diagram, mind map, wireframe, or C4 model and wants the output as an Excalidraw file (or embedded in Markdown via the `excalidraw` fenced block).

## Environment Check

If the Agent tool is available, use the subagent review loop described in `references/style-and-iteration.md` (Subagent Architecture). It provides fresh-context validation and avoids single-pass context overflow.

If the Agent tool is unavailable (e.g., Claude.ai), execute every phase inline and self-review against the 10 checks (less rigorous, but functional).

## Core Workflow

### Phase 1: Understand

Confirm what to draw before generating anything.

- **Clear description** ("draw a flowchart of user authentication"): restate your understanding in one sentence and propose the visualization type.
- **Ambiguous input**: ask targeted questions — main entities/nodes, relationships, flow direction, style preference.
- **Code, data, schemas, or files**: extract structure (code → class/dependency/architecture; SQL → ER; JSON/YAML → architecture/deployment; steps → flowchart/sequence; org data → org chart/tree).

### Phase 2: Propose

Present a plan with selectable options:

1. **Diagram type** — see `references/diagram-types.md` for the catalogue. If multiple fit, present numbered options.
2. **Key elements** — list the nodes/shapes you'll include.
3. **Layout** — propose 2–3 choices (e.g., `(A) Top-to-bottom`, `(B) Left-to-right`, `(C) Radial`).
4. **Style** — see `references/style-and-iteration.md`. Pick rendering style (clean/hand-drawn/sketchy) and color scheme that fits the diagram's purpose. No fixed palette.
5. **Complexity** — small (<10 elements), medium (10–30), large (30+).

Wait for confirmation. If the user says "just do it" or the request is straightforward, use sensible defaults (hand-drawn, roughness 1, Virgil font, best-fit layout) and proceed.

### Phase 3: Generate

Write a `.excalidraw` file (raw JSON, no wrapper) in the current working directory. Use kebab-case names (`auth-flow.excalidraw`). The required envelope:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": { "theme": "light", "viewBackgroundColor": "#ffffff" },
  "files": {}
}
```

Set `theme` and `viewBackgroundColor` to whatever suits the diagram. For full element schema and field defaults, see `references/excalidraw-format.md`.

**Embedding in Markdown**: if the user asks to embed the diagram in a `.md` file, write the `.excalidraw` first, then a companion `.md` that references it via a fenced block tagged `excalidraw` containing the same JSON.

### Phase 4: Validate

Before writing the file, run all 10 checks on the in-memory JSON. Fix and re-check until all pass. Full check definitions and fix recipes are in `references/validation-checks.md`. Quick summary:

1. **Valid JSON** — top-level keys present.
2. **Required fields** — every element has the full field list (id, type, geometry, styling, `boundElements`, `seed`, etc.). Text adds `text/fontSize/fontFamily/textAlign/verticalAlign/containerId/originalText/lineHeight/autoResize`. Arrows add `points/startBinding/endBinding/startArrowhead/endArrowhead`.
3. **Unique IDs** — no duplicates.
4. **Two-way text bindings** — `containerId` ↔ `boundElements` `{type:"text"}`.
5. **Two-way arrow bindings** — `startBinding/endBinding` ↔ `boundElements` `{type:"arrow"}`.
6. **Arrow points** — `points` length ≥ 2 and `points[0] === [0,0]`.
7. **No unintentional overlaps** — bounding boxes don't overlap by more than 10px (unless grouped or inside a frame).
8. **Semantic completeness** — every entity/relationship the user mentioned is represented.
9. **Readable text** — `fontSize ≥ 16`, visible `strokeColor`, `lineHeight: 1.25` (never 1.35), `autoResize: true`.
10. **Shape-to-text size fit** — see below; this is the #1 failure mode.

#### Check 10 — shape sizing (always verify)

For every text element with `containerId`:

1. `line_count = text.split('\n').length`
2. `min_text_height = line_count * fontSize * 1.25`
3. `min_shape_height = min_text_height + 40` (20px padding top/bottom)
4. The container shape's `height` must be `>= min_shape_height`.
5. The container shape's `width` must be `>= longest_line_pixel_width + 20`.

Boundary/container labels (e.g., "System Boundary") must be standalone text with `containerId: null`, positioned near the top-left of the container — never bound to it.

**Fix**: increase the shape's height/width to fit the text and shift elements below it to keep spacing. Always set `lineHeight: 1.25` and `autoResize: true` on text. Never patch individual outputs — fix this skill's instructions if a new failure pattern emerges.

After all checks pass, emit the validation summary (10/10 passed, element counts, binding counts, "all shapes sized to fit", any auto-fixes applied).

## Step Completion Reports

After each phase, output a status block. Templates and check labels for each phase live in `references/step-reports.md`. Result line is `PASS | FAIL | PARTIAL`.

## Expected Output

For "draw a flowchart of the user login process": file `login-flow.excalidraw` containing valid Excalidraw JSON, plus a validation summary in the response. Example fragment:

```json
{
  "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
  "elements": [
    {"id": "start-1", "type": "ellipse", "x": 300, "y": 40, "width": 120, "height": 56,
     "boundElements": [{"id": "txt-start", "type": "text"}]},
    {"id": "txt-start", "type": "text", "text": "Start", "fontSize": 18, "fontFamily": 1,
     "containerId": "start-1", "lineHeight": 1.25, "autoResize": true}
  ],
  "appState": {"theme": "light", "viewBackgroundColor": "#ffffff"}, "files": {}
}
```

Expected response includes:
```
Validation: 10/10 checks passed
- Elements: 6 shapes, 6 text labels, 5 arrows
- Bindings: 6 text bindings, 10 arrow bindings (all two-way)
- Text fits: all shapes sized to fit their bound text
- No overlaps, no missing fields
```

## Edge Cases

- **30+ elements** — spawn the subagent review loop in `references/style-and-iteration.md`; cap at 3 fix cycles.
- **Text-heavy nodes** — apply Check 10 strictly; bigger shapes, never smaller text.
- **Ambiguous relationships** — ask before guessing; saves a regeneration cycle.
- **"Just do it"** — defaults (hand-drawn, roughness 1, Virgil, best-fit layout); skip the proposal.
- **Iteration on an existing file** — read the file, preserve unchanged IDs, modify only the requested parts, rewrite.

See `references/style-and-iteration.md` for extended edge cases, iteration patterns, and style variants.

## Acceptance Criteria

- [ ] Output file is valid JSON with top-level `type`, `version`, `elements`, `appState`, `files`.
- [ ] Every element has all required fields (per `references/validation-checks.md` Check 2).
- [ ] Text elements have `fontSize >= 16`, `lineHeight: 1.25`, `autoResize: true`.
- [ ] All element IDs are unique.
- [ ] Text-to-shape bindings are two-way (`containerId` ↔ `boundElements`).
- [ ] Arrow bindings are two-way (`startBinding`/`endBinding` ↔ `boundElements`).
- [ ] Every arrow has `points[0] === [0,0]` and length ≥ 2.
- [ ] No bounding boxes overlap by more than 10px (outside groups/frames).
- [ ] Every entity/relationship from the user's request is represented.
- [ ] Every container shape is sized to fit its bound text (Check 10).
- [ ] Validation report (10/10 summary) is included in the response.

## Supported Diagram Types

Full catalogue with layout guidance: `references/diagram-types.md`. Categories: Flow & Process, Architecture, Data & Relationships, Planning, Comparison, Data Viz, UX/Design, Custom. If the request doesn't map cleanly to one type, propose the closest fit and explain why.

## References

- `references/validation-checks.md` — full text of all 10 Phase-4 checks plus fix recipes.
- `references/excalidraw-format.md` — Excalidraw JSON schema and field defaults.
- `references/diagram-types.md` — diagram-type catalogue with layout guidance.
- `references/style-and-iteration.md` — style variants, iteration patterns, subagent architecture, extended edge cases.
- `references/step-reports.md` — step completion report templates per phase.
- `agents/json-generator.md`, `agents/json-validator.md`, `agents/json-fixer.md` — subagent specs for the large-diagram review loop.
