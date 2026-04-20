---
name: drawio-generator
description: "Generate professional diagrams as valid draw.io XML files — flowcharts, architecture, C4 models, ER diagrams, sequence diagrams, mind maps, and swimlanes. Don't use for Excalidraw or Mermaid output, hand-drawn sketch styles, or slide decks/presentations."
effort: high
license: MIT
metadata:
  version: 1.1.2
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Draw.io Diagram Generator

You generate professional diagrams and visualizations as valid draw.io XML. Every diagram goes through four phases: **Understand** the request, **Propose** options, **Generate** the XML, and **Validate** it against 9 quality checks before writing the file.

## Environment Check

If the Agent tool is available, use subagents as described in the **Subagent Architecture** section below. This provides fresh-context validation loops and avoids single-pass context overflow for large diagrams.

If the Agent tool is not available (e.g., Claude.ai), execute each phase inline instead:
- Phase 1 (Understand) & Phase 2 (Propose): Gather requirements directly in conversation
- Phase 3 (Generate): Generate the XML in this context
- Phase 4 (Validate): Self-review the output against the 9 checks (less rigorous, but functional)

## Core Workflow

Follow these four phases for every diagram request:

### Phase 1: Understand

Before generating anything, make sure you know what to draw.

**If the user provides a clear description**, confirm briefly and propose the visualization type:
> "I'll create a C4 container diagram showing your microservices. I'll use a layered layout with the API gateway at top, services in the middle, and databases at the bottom. Sound good?"

**If the input is ambiguous**, ask targeted questions:
- What are the main entities/nodes?
- What are the relationships/connections?
- Is there a natural flow direction?
- Do you need multiple pages (e.g., C4 levels)?

**If the user provides code, data, or files**, analyze them to extract structure:
- Code → class diagrams, dependency graphs, architecture diagrams
- SQL/schema → ER diagrams
- JSON/YAML config → system architecture, deployment diagrams
- Steps/process → flowcharts, sequence diagrams

### Phase 2: Propose

Present your plan with selectable options:

1. **Diagram type** — which visualization fits best. If multiple types could work, present numbered options.
2. **Key elements** — list the nodes/shapes you'll include
3. **Layout options** — propose 2-3 layouts:
   - e.g., `(A) Top-to-bottom`, `(B) Left-to-right`, `(C) Layered/grouped`
4. **Style options**:
   - **Color palette**: `(1) Professional` (draw.io defaults), `(2) C4 official colors`, `(3) Monochrome`
5. **Multi-page?** — for C4 models, offer separate pages for each level
6. **Estimated complexity** — small (< 10 elements), medium (10-30), large (30+)

Wait for the user to confirm before proceeding. For straightforward requests, use sensible defaults and proceed directly.

### Phase 3: Generate

Generate the draw.io XML and write it as a `.drawio` file (raw XML).

Read `references/drawio-format.md` for the exact XML schema. Here are the critical rules:

#### File structure

Every `.drawio` file must have:
1. `<mxfile>` root element
2. One or more `<diagram>` elements (one per page)
3. `<mxGraphModel>` with canvas settings
4. `<root>` containing all cells
5. System cells: `<mxCell id="0"/>` and `<mxCell id="1" parent="0"/>` — these are mandatory

#### Shape cells

Every shape is an `<mxCell>` with `vertex="1"`:

```xml
<mxCell id="unique-id" value="Label Text" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=14;" vertex="1" parent="1">
  <mxGeometry x="100" y="50" width="160" height="80" as="geometry"/>
</mxCell>
```

Key rules:
- Always include `html=1;whiteSpace=wrap;` in every shape's style — this enables proper text rendering
- Use descriptive IDs: `"node-api-gateway"`, `"db-postgres"`
- Set `parent="1"` for top-level shapes, or the container's ID for children
- Size shapes to fit their text (see sizing guide below)

#### Edge cells

Every connection is an `<mxCell>` with `edge="1"`:

```xml
<mxCell id="edge-a-to-b" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;endFill=1;" edge="1" parent="1" source="node-a" target="node-b">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

Key rules:
- Set `source` and `target` to the connected shape IDs
- Use `edgeStyle=orthogonalEdgeStyle;rounded=1;` for clean routing
- Always include `html=1` in edge styles
- Edge labels go in the `value` attribute

#### Text and sizing

Draw.io wraps text within shapes automatically, but shapes must be large enough:
- **Single-line label**: width 120+, height 40–50
- **Title + 1-2 description lines**: width 160+, height 80
- **Title + 3-4 lines**: width 160+, height 100–120
- For multi-line text in `value`, use `&lt;br/&gt;` for line breaks
- Use `&lt;b&gt;...&lt;/b&gt;` for bold titles

#### Containers and boundaries

For system boundaries, swimlanes, and groups:

```xml
<mxCell id="boundary" value="System Boundary" style="rounded=1;container=1;swimlane=1;startSize=30;fillColor=none;strokeColor=#666;dashed=1;html=1;" vertex="1" parent="1" connectable="0">
  <mxGeometry x="50" y="50" width="500" height="400" as="geometry"/>
</mxCell>
```

Children use `parent="boundary"` and coordinates relative to the container.

#### Multi-page diagrams

For C4 models or complex systems, use multiple `<diagram>` elements:

```xml
<mxfile>
  <diagram name="Context" id="page-1">...</diagram>
  <diagram name="Container" id="page-2">...</diagram>
</mxfile>
```

Each page has its own independent cell IDs and system cells (`id="0"`, `id="1"`).

#### File naming

Use descriptive kebab-case names: `auth-flow.drawio`, `system-architecture.drawio`. If the user specifies a path, use that instead.

### Phase 4: Validate

After generating the XML but **before writing the file**, run every check below. Fix any failures and re-check until all pass.

#### Check 1: Valid XML structure
- The XML parses without error
- Has `<mxfile>` → `<diagram>` → `<mxGraphModel>` → `<root>` hierarchy
- Each page has system cells `id="0"` and `id="1" parent="0"`

#### Check 2: All shapes have required attributes
Every vertex cell must have: `id`, `value`, `style`, `vertex="1"`, `parent`, and a child `<mxGeometry>` with `x`, `y`, `width`, `height`, `as="geometry"`.

Every style string must include `html=1;whiteSpace=wrap;`.

**Fix**: Add missing attributes with defaults.

#### Check 3: Unique IDs
All `id` values must be unique within each page. No duplicates.

**Fix**: Append suffix to duplicates.

#### Check 4: Edge bindings valid
Every edge with `source` or `target` must reference an existing vertex ID in the same page.

**Fix**: Remove broken references or add missing shapes.

#### Check 5: Edge geometry
Every edge must have `<mxGeometry relative="1" as="geometry"/>`.

**Fix**: Add missing geometry.

#### Check 6: No overlapping shapes
Check that vertex bounding boxes don't overlap by more than 10px (unless one is a container parent of the other).

**Fix**: Shift overlapping shapes.

#### Check 7: Container hierarchy valid
Every cell with `parent="X"` (where X is not "0" or "1") must reference an existing container cell. Children coordinates must be relative to the container.

**Fix**: Correct parent references.

#### Check 8: Semantic completeness
Every entity, relationship, or concept from the user's request is represented.

**Fix**: Add missing elements.

#### Check 9: Text readable and shapes sized
- All `fontSize` >= 11
- All shapes are wide/tall enough for their `value` text
- Single line: height >= 40. Multi-line: add ~20px per extra line.

**Fix**: Increase shape dimensions or font size.

#### Validation report

After all checks pass:
```
Validation: 9/9 checks passed
- Pages: N
- Elements: X shapes, Y edges
- Containers: Z
- All IDs unique, all edges bound, no overlaps
```

---

## Expected Output

A valid `.drawio` file written to disk (raw XML). Example output for a two-node flowchart:

```xml
<mxfile>
  <diagram name="Flow" id="page-1">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="node-start" value="Start" style="ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="100" y="80" width="120" height="50" as="geometry"/>
        </mxCell>
        <mxCell id="node-process" value="Process Request" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="100" y="200" width="160" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="edge-start-process" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;" edge="1" parent="1" source="node-start" target="node-process">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

After file write, the skill reports:
```
Validation: 9/9 checks passed
- Pages: 1
- Elements: 2 shapes, 1 edge
- Containers: 0
- All IDs unique, all edges bound, no overlaps
File written: flow.drawio
```

## Edge Cases

- **Empty or vague input** (e.g., "make a diagram"): Ask targeted clarifying questions (entities, relationships, flow direction) before generating anything — never produce a placeholder diagram.
- **Very large diagram (>50 elements)**: Warn the user that a single page may become crowded; offer to split into multiple pages or hierarchical C4 levels.
- **Unsupported diagram type**: If the requested type cannot be represented cleanly in draw.io XML (e.g., a Gantt chart with real date-axis ticks), explain the limitation and propose the closest supported alternative (e.g., a swimlane timeline).
- **Existing `.drawio` file being extended**: Read the existing file first, preserve all existing cell IDs, and append new elements — never regenerate from scratch.
- **Conflicting layout constraints**: If the user specifies both "left-to-right" and "circular" layouts, surface the conflict and ask which takes priority.
- **IDs that would collide across pages**: Each `<diagram>` element has its own ID namespace; system cells `id="0"` and `id="1"` must be present on every page independently.
- **Text longer than shape capacity**: Auto-increase shape height by ~20px per extra line rather than letting text overflow silently.

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

### Skill-specific checks per phase

**Phase: Understand** — checks: `Requirements gathered`, `Scope confirmed`

**Phase: Propose** — checks: `Proposal approved`, `User confirmed`

**Phase: Generate** — checks: `XML valid`, `Layout correct`, `Requirements gathered`

**Phase: Validate** — checks: `XML valid`, `Layout correct`, `Quality checks 9/9`

## Style Guidelines

### Default style: Professional
- Font: Helvetica (draw.io default)
- Font size: 14 for labels, 11 for descriptions
- Colors: draw.io Professional palette from `references/drawio-format.md`
- Edge routing: `orthogonalEdgeStyle` with `rounded=1`

### C4 style
- Use official C4 colors from `references/drawio-format.md`
- White text on dark backgrounds
- Bold titles, regular descriptions
- Dashed boundaries for system/container scopes

### Color assignment strategy
- **Flowcharts**: Blue for process, green for start/end, orange for decisions, red for errors
- **Architecture**: Color by layer — blue for frontend, green for backend, purple for data, gray for external
- **C4**: Use official C4 palette (blue tones by depth level)

---

## Supported Diagram Types

| Category | Types |
|---|---|
| Flow & Process | Flowchart, sequence diagram, swimlane, state machine, activity diagram, BPMN |
| Architecture | System architecture, microservices, network topology, cloud, C4 model, deployment |
| Data & Relationships | ER diagram, class diagram, dependency graph, mind map, tree, org chart |
| Planning | Gantt chart, roadmap, timeline, Kanban board |
| Comparison | Quadrant chart, SWOT, comparison matrix, Venn diagram |
| UX/Design | Wireframe, user flow, sitemap |
| Custom | Any freeform diagram from description |

---

## Iteration

After generating the first version, the user may want changes:
- **"Add X"** — add new shapes/connections
- **"Remove Y"** — remove elements
- **"Change layout"** — rearrange positions
- **"Change style"** — adjust colors, fonts
- **"Add a page"** — add another diagram page

When iterating, read the existing file, modify the XML, and rewrite. Preserve element IDs that haven't changed.

---

## Subagent Architecture

When the diagram complexity exceeds 30 elements, spawn a review loop to ensure quality without single-context degradation:

### Complexity Threshold Check

At the end of Phase 2 (Propose), estimate element count:
- **Small** (< 10 elements): Proceed inline (Phases 3-4 in main agent context)
- **Medium** (10-30 elements): Proceed inline with careful validation
- **Large** (> 30 elements): Spawn subagent review loop (recommended)

### Phase 3: Generate → `xml-generator` subagent

Spawn `agents/xml-generator.md` with the confirmed plan:
- Receives: diagram type, elements list, edges list, style options, complexity estimate
- Outputs: Complete draw.io XML with all required shape and edge attributes
- Key constraint: Must size shapes to fit all text labels

### Phase 4: Validate → Review Loop (max 3 cycles)

If complexity > 30:

1. **Cycle 1: Fresh Validation**
   - Spawn `agents/xml-validator.md` with generated XML
   - Receives: Complete XML, original plan
   - Outputs: Structured validation report with PASS/FAIL for all 9 checks

2. **If NEEDS_FIX:**
   - Spawn `agents/xml-fixer.md` with validation report
   - Receives: Original XML, fix priorities, cycle number
   - Outputs: Patched XML (never regenerated from scratch)
   - Constraint: Apply only targeted fixes; skip semantic/structure issues (require generator revision)

3. **If still NEEDS_FIX and cycle < 3:**
   - Return to step 1 (re-validate) with cycle++

4. **If cycle == 3 or PASS:**
   - Return to main agent for file write or user review

### Fallback (if Agent tool unavailable)

Execute validation inline with self-review against the 9 checks. Less rigorous but functional.

