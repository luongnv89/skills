---
name: excalidraw-generator
description: "Generate professional diagrams as valid Excalidraw JSON files — flowcharts, architecture, ER diagrams, mind maps, sequence diagrams, wireframes, C4 models, and more. Understands text, code, schemas, or verbal descriptions. Don't use for draw.io/Mermaid output, polished production slide decks, or pixel-perfect brand graphics."
effort: high
license: MIT
metadata:
  version: 1.2.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Excalidraw Diagram Generator

You generate professional diagrams and visualizations as valid Excalidraw JSON. Every diagram goes through four phases: **Understand** the request, **Propose** options, **Generate** the JSON, and **Validate** it against 10 quality checks before writing the file.

## Environment Check

If the Agent tool is available, use subagents as described in the **Subagent Architecture** section below. This provides fresh-context validation loops and avoids single-pass context overflow for large diagrams.

If the Agent tool is not available (e.g., Claude.ai), execute each phase inline instead:
- Phase 1 (Understand) & Phase 2 (Propose): Gather requirements directly in conversation
- Phase 3 (Generate): Generate the JSON in this context
- Phase 4 (Validate): Self-review the output against the 10 checks (less rigorous, but functional)

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
4. **Style options** — pick whatever feels most expressive for the diagram's purpose. No fixed palette or theme. Some dimensions to consider:
   - **Colors**: choose freely — light or dark background, vibrant or muted, semantic coloring by role/category
   - **Rendering style**: `(a) Clean/geometric` (roughness 0), `(b) Hand-drawn` (roughness 1 — default), `(c) Sketchy` (roughness 2, very informal)
5. **Estimated complexity** — small (< 10 elements), medium (10-30), large (30+)

Wait for the user to confirm or select their preferred options before proceeding. If the user said "just do it" or the request is straightforward, use sensible defaults (hand-drawn style, roughness 1, hand-writing font, best-fit layout) and proceed directly. Pick colors that feel natural for the diagram — no fixed palette required.

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

(Set `theme` and `viewBackgroundColor` to whatever suits the diagram — light, dark, or any color.)

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

**Fix**: Set minimum fontSize to 16; set strokeColor to a color that is visibly readable against the background if invisible; set lineHeight to 1.25; set autoResize to true.

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

Refer to the validation checks in Phase 4 and `references/excalidraw-format.md` for the complete JSON schema and format rules.

---

## Expected Output

For a request like "draw a flowchart of the user login process", the skill produces a file `login-flow.excalidraw` containing valid Excalidraw JSON:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "start-1", "type": "ellipse",
      "x": 300, "y": 40, "width": 120, "height": 56,
      "strokeColor": "#1e1e1e", "backgroundColor": "#b2f2bb",
      "fillStyle": "solid", "roughness": 1, "opacity": 100,
      "boundElements": [{"id": "txt-start", "type": "text"}],
      ...
    },
    {
      "id": "txt-start", "type": "text",
      "text": "Start", "fontSize": 18, "fontFamily": 1,
      "containerId": "start-1", "autoResize": true, "lineHeight": 1.25,
      ...
    },
    ...
  ],
  "appState": { "theme": "light", "viewBackgroundColor": "#ffffff" },
  "files": {}
}
```

Along with a validation summary in the response:
```
Validation: 10/10 checks passed
- Elements: 6 shapes, 6 text labels, 5 arrows
- Bindings: 6 text bindings, 10 arrow bindings (all two-way)
- Text fits: all shapes sized to fit their bound text
- No overlaps, no missing fields
```

## Edge Cases

- **Complex diagram (30+ elements)**: Spawn the subagent review loop (json-generator → json-validator → json-fixer) to avoid single-context degradation. Cap at 3 fix cycles before surfacing remaining issues to the user.
- **Text-heavy input (long labels, multi-line node text)**: Apply Check 10 strictly — calculate `min_shape_height = line_count * fontSize * 1.25 + 40` and increase container dimensions before writing the file. Garbled text is the most common failure mode.
- **Ambiguous relationships**: If connections between entities are unclear, ask the user to clarify direction and cardinality before generating rather than guessing and requiring regeneration.
- **User says "just do it"**: Use sensible defaults (hand-drawn style, roughness 1, Virgil font, best-fit layout) and skip the proposal step.
- **Large diagram with overlapping nodes**: Apply Check 7 — shift overlapping elements by adjusting `x`/`y` coordinates. Never allow bounding boxes to overlap by more than 10px outside of containers.
- **Iteration request on existing file**: Read the existing `.excalidraw` file first, preserve unchanged element IDs, apply only the requested modifications, then rewrite the file.

## Acceptance Criteria

- [ ] Output file is valid JSON with top-level keys `type`, `version`, `elements`, `appState`, `files`
- [ ] Every element has all required fields (id, type, x, y, width, height, strokeColor, backgroundColor, fillStyle, strokeWidth, strokeStyle, roughness, opacity, groupIds, frameId, roundness, isDeleted, boundElements, updated, link, locked, seed)
- [ ] Text elements include `fontSize >= 16`, `lineHeight: 1.25`, `autoResize: true`
- [ ] All IDs are unique within the `elements` array
- [ ] Text-to-shape bindings are two-way (containerId on text ↔ boundElements on shape)
- [ ] Arrow bindings are two-way (startBinding/endBinding on arrow ↔ boundElements on shape)
- [ ] Every arrow has `points[0] === [0, 0]` and at least 2 points
- [ ] No unintentional overlapping shapes (bounding boxes do not overlap by more than 10px)
- [ ] Every entity/relationship from the user's request is represented in the diagram
- [ ] All container shapes are sized to fit their bound text (Check 10 passes)
- [ ] Validation report (10/10 checks summary) is included in the response

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Phase-specific checks

**Phase 1 — Understand**
```
◆ Understand (step 1 of 4 — [diagram type])
··································································
  Requirements clarity:   √ pass
  Scope confirmed:        √ pass (entities and relationships identified)
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

**Phase 2 — Propose**
```
◆ Propose (step 2 of 4 — [diagram type])
··································································
  Type selected:          √ pass ([diagram type] chosen)
  User approved:          √ pass | × fail — awaiting confirmation
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

**Phase 3 — Generate**
```
◆ Generate (step 3 of 4 — [diagram type])
··································································
  JSON valid:             √ pass
  File written:           √ pass ([filename].excalidraw)
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

**Phase 4 — Validate**
```
◆ Validate (step 4 of 4 — [diagram type])
··································································
  Quality checks 10/10:   √ pass | × fail — [checks failed]
  Text sizing correct:    √ pass | × fail — [elements affected]
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

---

## Style Guidelines

### Default style: Hand-drawn
- `roughness`: 1 (hand-drawn — the natural, expressive Excalidraw look)
- `strokeWidth`: 2
- `fontFamily`: 1 (Virgil — hand-writing font, the Excalidraw signature style)
- Colors: choose freely based on what communicates the diagram's meaning well — light or dark theme, vibrant or muted, whatever fits the content
- Use color purposefully to distinguish categories, layers, or semantic roles — but trust your judgment rather than a fixed palette

### Style variants

- **Sketchy** (`roughness: 2`, `fontFamily: 1`): Wireframes, brainstorming, very informal diagrams
- **Clean/geometric** (`roughness: 0`, `fontFamily: 2`): Precise, formal, presentation-ready
- **Code/technical** (`roughness: 0`, `fontFamily: 3`): Diagrams with code snippets or technical labels
- **Monochrome**: When the user wants something printable or minimal

Adapt the style to the diagram's purpose and the user's intent. The hand-drawn default works well for most cases — override when the content clearly calls for something different.

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

## Subagent Architecture

When the diagram complexity exceeds 30 elements, spawn a review loop to ensure quality without single-context degradation:

### Complexity Threshold Check

At the end of Phase 2 (Propose), estimate element count:
- **Small** (< 10 elements): Proceed inline (Phases 3-4 in main agent context)
- **Medium** (10-30 elements): Proceed inline with careful validation
- **Large** (> 30 elements): Spawn subagent review loop (recommended)

### Phase 3: Generate → `json-generator` subagent

Spawn `agents/json-generator.md` with the confirmed plan:
- Receives: diagram type, elements list, arrows list, style options, complexity estimate
- Outputs: Complete Excalidraw JSON object with all required fields per element
- Key constraint: Must size shapes to fit all bound text (Check 10 validation rule)

### Phase 4: Validate → Review Loop (max 3 cycles)

If complexity > 30:

1. **Cycle 1: Fresh Validation**
   - Spawn `agents/json-validator.md` with generated JSON
   - Receives: Complete JSON, original plan
   - Outputs: Structured validation report with PASS/FAIL for all 10 checks

2. **If NEEDS_FIX:**
   - Spawn `agents/json-fixer.md` with validation report
   - Receives: Original JSON, fix priorities, cycle number
   - Outputs: Patched JSON (never regenerated from scratch)
   - Constraint: Apply only targeted fixes; skip semantic/structure issues (require generator revision)

3. **If still NEEDS_FIX and cycle < 3:**
   - Return to step 1 (re-validate) with cycle++

4. **If cycle == 3 or PASS:**
   - Return to main agent for file write or user review

### Fallback (if Agent tool unavailable)

Execute validation inline with self-review against the 10 checks. Less rigorous but functional.

---

## Example: Simple Flowchart

For a request like "draw a flowchart of a login process":

**File**: `login-flow.excalidraw`

The output is a raw JSON file containing the full Excalidraw document with:
- Hand-drawn style (`roughness: 1`) with Virgil hand-writing font (`fontFamily: 1`)
- An ellipse "Start" node in a natural start color (e.g. soft green)
- Rectangle process nodes in a distinct fill
- A diamond "Valid?" decision node in a contrasting color
- An error rectangle in red tones
- Arrows connecting all nodes
- Each shape has bound text labels sized to fit their content
