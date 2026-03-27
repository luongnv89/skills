---
name: excalidraw-generator
description: Generate diagrams and visualizations as Excalidraw JSON files — flowcharts, architecture, ER diagrams, mind maps, sequence diagrams, org charts, wireframes, C4 models, swimlanes, and more. Trigger when user asks to draw, diagram, visualize, sketch, or chart anything, says "excalidraw", "draw this", "make a diagram of", "visualize this", or shares data/structures that would benefit from visualization. Also suggest when the user describes relationships, flows, or hierarchies even without saying "diagram".
effort: high
license: MIT
metadata:
  version: 1.1.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
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
4. **Style options** — propose color palette and roughness as selectable options:
   - **Color palette**: `(1) Dark Neon` (dark base + neon green accent — default), `(2) Professional Light` (blue/green/orange on white), `(3) Pastel` (soft tones), `(4) Monochrome` (grays)
   - **Rendering style**: `(a) Clean/geometric` (roughness 0, precise lines — default, best readability), `(b) Hand-drawn` (roughness 1, Excalidraw signature look), `(c) Sketchy` (roughness 2, very informal)
5. **Estimated complexity** — small (< 10 elements), medium (10-30), large (30+)

Wait for the user to confirm or select their preferred options before proceeding. If the user said "just do it" or the request is straightforward, use sensible defaults (Dark Neon palette, Clean/geometric style, Helvetica font, best-fit layout) and proceed directly.

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
    "theme": "dark",
    "viewBackgroundColor": "#0A0A0A"
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

**Fix**: Set minimum fontSize to 16; set strokeColor to `"#FAFAFA"` (dark theme) or `"#1e1e1e"` (light theme) if invisible; set lineHeight to 1.25; set autoResize to true.

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

### Default style: Dark Neon
- `roughness`: 0 (clean/geometric — precise lines for maximum readability)
- `strokeWidth`: 2
- `fontFamily`: 2 (Helvetica — clean sans-serif for best readability on dark backgrounds)
- `appState.theme`: `"dark"` with `viewBackgroundColor`: `"#0A0A0A"`
- Color palette: Dark Neon from `references/excalidraw-format.md` (dark base + neon green accent, matching logo-designer brand)
- Use color purposefully — different semantic colors for different categories or layers, not random
- Node text color: `"#FAFAFA"` for high contrast on dark fills
- Arrow/annotation text: `"#A1A1A1"` (muted) for secondary information

### When to use other styles

- **Professional Light** (`roughness: 1`, `fontFamily: 2`, light background): When the user wants a light theme
- **Hand-drawn** (`roughness: 1`, `fontFamily: 1`): When the user explicitly wants the Excalidraw hand-drawn look
- **Sketchy** (`roughness: 2`, `fontFamily: 1`): Wireframes, brainstorming, informal diagrams
- **Monochrome**: When the user wants something printable or formal

### Color assignment strategy (Dark Neon palette)

Assign colors by semantic meaning:
- **Flowcharts**: Info blue (`#3B82F6`) for process steps, Accent green (`#00FF41`) for start/end, Warning amber (`#F59E0B`) for decisions, Danger red (`#EF4444`) for error paths
- **Architecture**: Info blue = frontend, Accent green = backend/API, Purple (`#A855F7`) = data layer, Teal (`#14B8A6`) = external services
- **Status-based**: Accent green = active/success, Warning amber = warning, Danger red = error/blocked, Muted (`#A1A1A1`) = inactive

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
- Dark background (`#0A0A0A`), dark theme enabled
- Clean geometric shapes (`roughness: 0`) with Helvetica font (`fontFamily: 2`)
- An ellipse "Start" node — neon green stroke (`#00FF41`) with dim green fill (`#0A2A0A`)
- Rectangle process nodes — info blue stroke (`#3B82F6`) with dim blue fill (`#0A1A2E`)
- A diamond "Valid?" decision — warning amber stroke (`#F59E0B`) with dim amber fill (`#2A1A0A`)
- An error rectangle — danger red stroke (`#EF4444`) with dim red fill (`#2A0A0A`)
- All text in `#FAFAFA` for high contrast
- Arrows in muted `#A1A1A1` connecting all nodes
- Each shape has bound text labels
