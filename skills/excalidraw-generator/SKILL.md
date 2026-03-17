---
name: excalidraw-generator
description: Generate diagrams, schemas, charts, flowcharts, architecture diagrams, mind maps, ER diagrams, sequence diagrams, Gantt charts, org charts, wireframes, Venn diagrams, and any other visualization as Excalidraw JSON. Use this skill whenever the user asks to create, draw, diagram, visualize, sketch, or chart anything — including flowcharts, system architecture, database schemas, mind maps, org charts, process flows, network topology, class diagrams, state machines, timelines, roadmaps, Kanban boards, SWOT analysis, comparison matrices, bar charts, wireframes, user flows, sitemaps, dependency graphs, C4 models, swimlane diagrams, or any kind of visual representation. Also trigger when the user says "excalidraw", "draw this", "make a diagram of", "visualize this", "sketch this out", "chart this", or shares data/code/structure they want turned into a visual. Even if the user doesn't explicitly say "diagram", if they describe relationships, flows, hierarchies, or structures that would benefit from visualization, suggest this skill.
---

# Excalidraw Diagram Generator

You generate professional diagrams and visualizations as valid Excalidraw JSON. Every diagram goes through four phases: **Understand** the request, **Propose** options, **Generate** the JSON, and **Validate** it against 10 quality checks before writing the file.

## Core Workflow

Follow these four phases for every diagram request:

### Phase 1: Understand

Before generating anything, make sure you know what to draw.

**If the user provides a clear description** (e.g., "draw a flowchart of user authentication"), confirm your understanding briefly and propose the visualization type. For example:
> "I'll create a flowchart showing the auth flow: login → validate → MFA check → session create. I'll use a top-to-bottom layout with decision diamonds for the conditional branches. Sound good?"

**If the input is ambiguous**, ask targeted questions:
- What are the main entities/nodes?
- What are the relationships/connections between them?
- Is there a natural flow direction (e.g., chronological, hierarchical)?
- Any specific style preference?

**If the user provides code, data, or files**, analyze them to extract structure:
- Code → class diagrams, dependency graphs, architecture diagrams
- SQL/schema → ER diagrams
- JSON/YAML config → system architecture, deployment diagrams
- List of steps → flowcharts, sequence diagrams
- Org data → org charts, tree structures

### Phase 2: Propose

Present your plan with selectable options so the user can pick:

1. **Diagram type** — which visualization fits best (see `references/diagram-types.md` for the full catalog). If multiple types could work, present them as numbered options.
2. **Key elements** — list the nodes/shapes you'll include
3. **Layout options** — propose 2-3 layout choices for the user to pick from:
   - e.g., `(A) Top-to-bottom flow`, `(B) Left-to-right flow`, `(C) Radial/centered`
4. **Style options** — propose color palette and roughness as selectable options:
   - **Color palette**: `(1) Professional` (blue/green/orange), `(2) Pastel` (soft tones), `(3) Monochrome` (grays)
   - **Rendering style**: `(a) Hand-drawn` (roughness 1, Excalidraw signature look), `(b) Clean/geometric` (roughness 0, precise lines), `(c) Sketchy` (roughness 2, very informal)
5. **Estimated complexity** — small (< 10 elements), medium (10-30), large (30+)

Wait for the user to confirm or select their preferred options before proceeding. If the user said "just do it" or the request is straightforward, use sensible defaults (Professional palette, Hand-drawn style, best-fit layout) and proceed directly.

### Phase 3: Generate

Generate the Excalidraw JSON and write it as a `.excalidraw` file (raw JSON, no wrapper).

**Default output: `.excalidraw` file** — always write the raw JSON object directly to a `.excalidraw` file. This is the native format that Excalidraw, VS Code (with the Excalidraw extension), and Obsidian can open directly.

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {
    "theme": "light",
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

**Embedding in Markdown**: If the user explicitly asks to embed the diagram in a `.md` file, or says they want a Markdown file, create the `.excalidraw` file first, then create a companion `.md` file that references or embeds it. Use a fenced code block with the `excalidraw` language tag:

```markdown
# [Diagram Title]

[Brief description]

` ` `excalidraw
<paste the same JSON here>
` ` `
```

(The triple backticks above are escaped for this document — use real triple backticks in output.)

**File naming**: Use descriptive kebab-case names in the current working directory: `auth-flow.excalidraw`, `database-schema.excalidraw`. If the user specifies a path, use that instead.

### Phase 4: Validate

After generating the JSON but **before writing the file**, run every check below on the in-memory JSON. If any check fails, fix the issue and re-check until all pass. Only write the file once validation is clean.

#### Check 1: Valid JSON structure
- The JSON parses without error
- Top-level has `"type": "excalidraw"`, `"version": 2`, `"elements"` (array), `"appState"` (object), `"files"` (object)

#### Check 2: Required fields on every element
Every element in the `elements` array must have ALL of these fields — no exceptions:
`id`, `type`, `x`, `y`, `width`, `height`, `angle`, `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness`, `opacity`, `groupIds`, `frameId`, `roundness`, `isDeleted`, `boundElements`, `updated`, `link`, `locked`, `seed`

Additionally:
- Text elements must also have: `text`, `fontSize`, `fontFamily`, `textAlign`, `verticalAlign`, `containerId`, `originalText`, `lineHeight`, `autoResize`
- Arrow/line elements must also have: `points`, `startBinding`, `endBinding`, `startArrowhead`, `endArrowhead`

**Fix**: Add any missing field with its default value. For text, ensure `autoResize: true` and `lineHeight: 1.25`.

#### Check 3: Unique IDs
Collect all `id` values. If any duplicates exist, append a suffix to make them unique.

#### Check 4: Two-way text bindings
For every text element with a `containerId`:
- The referenced container's `boundElements` must include `{"id": "<text-id>", "type": "text"}`

For every shape with a `boundElements` entry of `"type": "text"`:
- The referenced text element must have `containerId` pointing back to the shape

**Fix**: Add the missing side of any broken binding.

#### Check 5: Two-way arrow bindings
For every arrow with a `startBinding.elementId`:
- That element's `boundElements` must include `{"id": "<arrow-id>", "type": "arrow"}`

Same for `endBinding.elementId`.

For every shape with a `boundElements` entry of `"type": "arrow"`:
- The referenced arrow must have `startBinding` or `endBinding` referencing the shape

**Fix**: Add the missing side of any broken binding.

#### Check 6: Arrow points validity
- Every arrow/line must have `points` array with at least 2 entries
- `points[0]` must be `[0, 0]`

**Fix**: Prepend `[0, 0]` if missing or correct the first point.

#### Check 7: No unintentional overlaps
For non-text, non-arrow elements (shapes), check that bounding boxes `(x, y, x+width, y+height)` don't overlap by more than 10px with other shapes (unless they are in the same group or one is a frame/container).

**Fix**: Shift overlapping elements by adjusting their `x` or `y`.

#### Check 8: Semantic completeness
Review the original user request and verify that every entity, relationship, or concept they mentioned is represented in the diagram. List any missing items.

**Fix**: Add missing elements with appropriate shapes, positions, and connections.

#### Check 9: Readable text
- All text elements must have `fontSize >= 16`
- All text `strokeColor` must not be `"transparent"` or same as `backgroundColor`
- All text elements must have `lineHeight: 1.25` (not 1.35 — that causes overflow)
- All text elements must have `autoResize: true`

**Fix**: Set minimum fontSize to 16; set strokeColor to `"#1e1e1e"` if invisible; set lineHeight to 1.25; set autoResize to true.

#### Check 10: Shape-to-text size fit

This is the most common cause of garbled rendering in Excalidraw. For every text element bound to a shape (`containerId` is set):

1. Count the lines: `line_count = text.split('\n').length`
2. Calculate minimum text height: `min_text_height = line_count * fontSize * 1.25`
3. Calculate minimum shape height: `min_shape_height = min_text_height + 40` (20px padding top/bottom)
4. The container shape's `height` must be >= `min_shape_height`
5. The container shape's `width` must be >= longest line's approximate pixel width + 20px padding

**Also check**: boundary/container labels (like "System Boundary") should NOT be bound to their container rectangle. These must be standalone text (`containerId: null`) positioned near the top-left of the container.

**Fix**: Increase the shape's height/width to fit the text. If a shape needs to be taller, also adjust `y` positions of elements below it to maintain spacing. For container labels, remove the binding and set `containerId: null`.

#### Validation report

After all checks pass, include a brief validation summary as a comment in your response (not in the file):
```
Validation: 10/10 checks passed
- Elements: N shapes, M text labels, K arrows
- Bindings: X text bindings, Y arrow bindings (all two-way)
- Text fits: all shapes sized to fit their bound text
- No overlaps, no missing fields
```

If any check required auto-fixes, mention what was corrected so the user knows.

---

## Generating Valid Excalidraw JSON

Read `references/excalidraw-format.md` for the exact JSON schema. Here are the critical rules:

### Every element MUST have ALL required fields

Missing fields cause Excalidraw to error or render incorrectly. The minimum required fields for every element are: `id`, `type`, `x`, `y`, `width`, `height`, `angle`, `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness`, `opacity`, `groupIds`, `frameId`, `roundness`, `isDeleted`, `boundElements`, `updated`, `link`, `locked`, `seed`.

### ID generation

Use descriptive, unique IDs: `"node-auth"`, `"arrow-auth-to-db"`, `"text-auth-label"`. This makes the JSON readable and debuggable. Never use duplicate IDs.

### Text inside shapes

This is a two-way binding AND a sizing relationship — both must be correct or text renders as garbled characters:

1. The shape's `boundElements` must include `{"id": "text-id", "type": "text"}`
2. The text's `containerId` must reference the shape's ID
3. Text must have `autoResize: true` and `lineHeight: 1.25`
4. Text `x` = shape.x + 10, `y` = shape.y + 10
5. Text `width` = shape.width - 20 (10px padding each side)
6. **Shape height must fit the text**: count lines, multiply by `fontSize * 1.25`, add 40px padding. A shape that is too small for its text is the #1 cause of rendering bugs.
7. Keep bound text to 1-3 lines when possible. For longer descriptions, use a taller shape (160px+) or place description as standalone text outside.
8. Boundary/container labels (like "System Boundary") must be **standalone text** (`containerId: null`), NOT bound to the container shape.

### Arrow connections

Also a two-way binding:
1. Source shape's `boundElements` must include `{"id": "arrow-id", "type": "arrow"}`
2. Target shape's `boundElements` must include `{"id": "arrow-id", "type": "arrow"}`
3. Arrow's `startBinding` must reference source shape ID
4. Arrow's `endBinding` must reference target shape ID
5. Arrow `points`: first point is always `[0, 0]`, last point is the offset to the target

### Layout spacing

Use consistent spacing from `references/excalidraw-format.md`:
- Node width: 200px, height: 80px
- Horizontal gap: 80px, vertical gap: 60px
- Grid cell: 280px (node + gap)
- Arrow gap: 8px from node border

### Seed values

Every element needs a `seed` — a positive integer used for roughness rendering. Use incrementing values starting from 1000: 1000, 1001, 1002, etc. Each element must have a unique seed.

---

## Style Guidelines

### Default style: Professional
- `roughness`: 1 (hand-drawn look — this is Excalidraw's signature)
- `strokeWidth`: 2
- `fontFamily`: 1 (Virgil — Excalidraw's hand-drawn font)
- Color palette from `references/excalidraw-format.md` Professional section
- Use color purposefully — different colors for different categories or layers, not random

### When to use other styles

- **Clean/geometric** (`roughness: 0`, `fontFamily: 2`): Technical diagrams, ER diagrams, architecture docs
- **Sketchy** (`roughness: 2`, `fontFamily: 1`): Wireframes, brainstorming, informal diagrams
- **Monochrome**: When the user wants something printable or formal

### Color assignment strategy

Assign colors by semantic meaning:
- **Flowcharts**: Blue for process steps, green for start/end, orange for decisions, red for error paths
- **Architecture**: Color by layer (blue = frontend, green = backend, purple = data, orange = external)
- **Status-based**: Green = active/success, yellow = warning, red = error/blocked, gray = inactive

---

## Supported Diagram Types

Read `references/diagram-types.md` for the full catalog with layout guidance. Summary:

| Category | Types |
|---|---|
| Flow & Process | Flowchart, sequence diagram, swimlane, state machine, activity diagram |
| Architecture | System architecture, microservices, network topology, cloud, C4 model, deployment |
| Data & Relationships | ER diagram, class diagram, dependency graph, mind map, tree, org chart |
| Planning | Gantt chart, roadmap, timeline, Kanban board |
| Comparison | Quadrant chart, SWOT, comparison matrix, Venn diagram |
| Data Viz | Bar chart, pie chart (legend-based), line chart, table/grid |
| UX/Design | Wireframe, user flow, sitemap |
| Custom | Any freeform diagram from description |

If the user's request doesn't clearly map to one type, suggest the best fit and explain why.

---

## Iteration

After generating the first version, the user may want changes. Common requests:

- **"Add X"** — add new nodes/connections
- **"Remove Y"** — remove elements (don't just set `isDeleted: true`, actually remove them from the array)
- **"Change layout"** — rearrange positions
- **"Change style"** — adjust colors, roughness, fonts
- **"Make it bigger/smaller"** — scale node sizes and gaps
- **"More detail"** — break high-level nodes into sub-components

When iterating, read the existing file, modify the JSON, and rewrite. Preserve element IDs that haven't changed so the user's manual edits (if any) in Excalidraw are compatible.

---

## Example: Simple Flowchart

For a request like "draw a flowchart of a login process":

**File**: `login-flow.excalidraw`

The output is a raw JSON file containing the full Excalidraw document with:
- An ellipse "Start" node at the top
- Rectangle nodes for "Enter Credentials", "Validate", "Create Session"
- A diamond for "Valid?" decision
- An error rectangle for "Show Error"
- Arrows connecting all nodes
- Each shape has bound text labels
- Green for start/end, blue for process, orange for decision, red for error path
