# draw.io XML Authoring Reference

Concrete rules for Phase 3 (Generate). For the full schema and palette tables, see `drawio-format.md`.

## File structure

Every `.drawio` file must have:
1. `<mxfile>` root element
2. One or more `<diagram>` elements (one per page)
3. `<mxGraphModel>` with canvas settings
4. `<root>` containing all cells
5. System cells: `<mxCell id="0"/>` and `<mxCell id="1" parent="0"/>` — these are mandatory

## Shape cells

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

## Edge cells

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

## Text and sizing

Draw.io wraps text within shapes automatically, but shapes must be large enough:
- **Single-line label**: width 120+, height 40–50
- **Title + 1-2 description lines**: width 160+, height 80
- **Title + 3-4 lines**: width 160+, height 100–120
- For multi-line text in `value`, use `&lt;br/&gt;` for line breaks
- Use `&lt;b&gt;...&lt;/b&gt;` for bold titles

## Containers and boundaries

For system boundaries, swimlanes, and groups:

```xml
<mxCell id="boundary" value="System Boundary" style="rounded=1;container=1;swimlane=1;startSize=30;fillColor=none;strokeColor=#666;dashed=1;html=1;" vertex="1" parent="1" connectable="0">
  <mxGeometry x="50" y="50" width="500" height="400" as="geometry"/>
</mxCell>
```

Children use `parent="boundary"` and coordinates relative to the container.

## Multi-page diagrams

For C4 models or complex systems, use multiple `<diagram>` elements:

```xml
<mxfile>
  <diagram name="Context" id="page-1">...</diagram>
  <diagram name="Container" id="page-2">...</diagram>
</mxfile>
```

Each page has its own independent cell IDs and system cells (`id="0"`, `id="1"`).

## File naming

Use descriptive kebab-case names: `auth-flow.drawio`, `system-architecture.drawio`. If the user specifies a path, use that instead.
