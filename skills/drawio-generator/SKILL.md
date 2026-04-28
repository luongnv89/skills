---
name: drawio-generator
description: "Generate professional diagrams as valid draw.io XML files — flowcharts, architecture, C4 models, ER diagrams, sequence diagrams, mind maps, and swimlanes. Don't use for Excalidraw or Mermaid output, hand-drawn sketch styles, or slide decks/presentations."
license: MIT
effort: high
metadata:
  version: 1.2.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Draw.io Diagram Generator

Generate professional diagrams as valid draw.io XML. Every request flows through four phases — **Understand**, **Propose**, **Generate**, **Validate** — before the file is written. Body content is intentionally lean to respect the agent's context budget; depth lives in `references/`.

## Environment Check

If the Agent tool is available, use subagents per the **Subagent Architecture** section. This provides fresh-context validation loops and avoids single-pass context overflow on large diagrams.

If the Agent tool is unavailable (e.g., Claude.ai), execute each phase inline:
- Phase 1 & 2: Gather requirements directly in conversation
- Phase 3: Generate the XML in this context
- Phase 4: Self-review against the 9 checks (less rigorous, but functional)

## Core Workflow

### Phase 1: Understand

Confirm what to draw before generating anything.

- **Clear request** — restate briefly and propose a visualization type:
  > "I'll create a C4 container diagram with a layered layout: API gateway on top, services in the middle, databases at the bottom. Sound good?"
- **Ambiguous input** — ask targeted questions: main entities, relationships, flow direction, multi-page need.
- **Code, schema, or config provided** — extract structure:
  - Code → class/dependency/architecture
  - SQL/schema → ER diagram
  - JSON/YAML config → architecture, deployment
  - Steps/process → flowchart, sequence

### Phase 2: Propose

Present a numbered plan and wait for confirmation. For straightforward requests, use sensible defaults and proceed.

1. **Diagram type** (offer alternatives if multiple fit)
2. **Key elements** — list nodes/shapes
3. **Layout** — e.g. `(A) Top-to-bottom`, `(B) Left-to-right`, `(C) Layered`
4. **Style** — `(1) Professional`, `(2) C4 official`, `(3) Monochrome`
5. **Multi-page?** — for C4, offer one page per level
6. **Estimated complexity** — small (<10), medium (10–30), large (30+)

### Phase 3: Generate

Generate the draw.io XML and write a `.drawio` file (raw XML).

Read `references/xml-authoring.md` for shape/edge/container syntax, sizing rules, multi-page structure, and file naming. Read `references/drawio-format.md` for the full XML schema and color palettes.

Critical rules every shape must follow:
- Always include `html=1;whiteSpace=wrap;` in the style string
- Use descriptive kebab-case IDs (`node-api-gateway`)
- Provide `<mxGeometry x y width height as="geometry"/>` sized to fit the label
- Edges need `source`, `target`, and `<mxGeometry relative="1" as="geometry"/>`

### Phase 4: Validate

Run all 9 checks before writing the file. Fix and re-check until every check passes. See `references/validation-checks.md` for the full check list, fix patterns, and the validation-report template.

Summary of checks:

1. Valid XML structure (mxfile → diagram → mxGraphModel → root, system cells present)
2. All shapes have required attributes (`html=1;whiteSpace=wrap;` mandatory)
3. Unique IDs per page
4. Edge `source`/`target` reference existing vertices
5. Every edge has `<mxGeometry relative="1" as="geometry"/>`
6. No overlapping shapes (>10px)
7. Container hierarchy valid; child coordinates relative to container
8. Semantic completeness — every requested entity/relationship is represented
9. Text readable: `fontSize` ≥ 11, shapes sized to fit `value`

---

## Expected Output

A valid `.drawio` file written to disk (raw XML). Minimal example:

```xml
<mxfile>
  <diagram name="Flow" id="page-1">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" page="1" pageWidth="1169" pageHeight="827">
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

## Acceptance Criteria

Verify these for every run:

- [ ] A `.drawio` file is written to disk with valid XML (parses without error).
- [ ] Every page contains system cells `id="0"` and `id="1" parent="0"`.
- [ ] Every shape style includes `html=1;whiteSpace=wrap;` and every edge has `<mxGeometry relative="1" as="geometry"/>`.
- [ ] Edge `source`/`target` attributes resolve to existing vertex IDs in the same page.
- [ ] No two vertex bounding boxes overlap by >10px (containers excluded).
- [ ] All `fontSize` values ≥ 11; shapes are sized so labels fit without overflow.
- [ ] The validation report prints `9/9 checks passed`. Given the user's request, then every entity and relationship described is represented in the output.

## Edge Cases

- **Empty or vague input** ("make a diagram"): ask targeted clarifying questions before generating — never produce a placeholder.
- **Very large diagram (>50 elements)**: warn that one page will be crowded; offer multi-page or hierarchical C4.
- **Unsupported diagram type** (e.g., Gantt with real date-axis ticks): explain the limitation and propose the closest supported alternative (e.g., swimlane timeline).
- **Existing `.drawio` file extension**: read it first, preserve existing cell IDs, append new elements — never regenerate from scratch.
- **Conflicting layout constraints**: surface the conflict and ask which takes priority.
- **Cross-page ID collision**: each `<diagram>` has its own ID namespace; system cells `id="0"` and `id="1"` must be present on every page independently.
- **Text exceeds shape capacity**: auto-grow shape height ~20px per extra line rather than letting text overflow silently.

---

## Step Completion Reports

After completing each major step, output a status report:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Per-phase checks:
- **Understand** — `Requirements gathered`, `Scope confirmed`
- **Propose** — `Proposal approved`, `User confirmed`
- **Generate** — `XML valid`, `Layout correct`, `Requirements covered`
- **Validate** — `XML valid`, `Layout correct`, `Quality checks 9/9`

## Style Guidelines

- **Professional (default)** — Helvetica, fontSize 14 for labels / 11 for descriptions, draw.io Professional palette, `orthogonalEdgeStyle` with `rounded=1`.
- **C4** — official C4 colors, white text on dark fills, bold titles, dashed boundaries.
- **Color assignment** — flowcharts: blue=process, green=start/end, orange=decision, red=error. Architecture: color by layer (frontend/backend/data/external). C4: depth-by-blue.

Full palettes and tokens: `references/drawio-format.md`.

---

## Supported Diagram Types

| Category | Types |
|---|---|
| Flow & Process | Flowchart, sequence, swimlane, state machine, activity, BPMN |
| Architecture | System, microservices, network, cloud, C4, deployment |
| Data & Relationships | ER, class, dependency graph, mind map, tree, org chart |
| Planning | Gantt, roadmap, timeline, Kanban |
| Comparison | Quadrant, SWOT, comparison matrix, Venn |
| UX/Design | Wireframe, user flow, sitemap |
| Custom | Any freeform diagram |

## Iteration

When iterating on an existing diagram, read the file, modify the XML in place, and rewrite. Preserve element IDs that haven't changed. Common requests: add/remove elements, change layout, adjust style, add a page.

---

## Subagent Architecture

When a diagram exceeds 30 elements, spawn a review loop to avoid single-context degradation.

**Complexity threshold (set at end of Phase 2):**
- Small (<10): proceed inline
- Medium (10–30): proceed inline with careful validation
- Large (>30): spawn the subagent review loop

**Phase 3 — `agents/xml-generator.md`**
- Receives: diagram type, elements, edges, style, complexity
- Outputs: complete draw.io XML with all required attributes
- Constraint: shapes sized to fit text labels

**Phase 4 — review loop (max 3 cycles)**

1. **Validate** — spawn `agents/xml-validator.md`. Outputs PASS/FAIL for all 9 checks.
2. **Fix** — if NEEDS_FIX, spawn `agents/xml-fixer.md` with the report. Patches XML; never regenerates. Skips semantic/structure issues (those require generator revision).
3. **Re-validate** with cycle++ until PASS or cycle == 3.
4. Return to main agent for file write or user review.

**Fallback** — without the Agent tool, validate inline using `references/validation-checks.md`. Less rigorous but functional.
