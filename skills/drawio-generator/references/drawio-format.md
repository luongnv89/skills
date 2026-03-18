# Draw.io XML Format Reference

This reference documents the exact XML structure that draw.io (diagrams.net) expects. Read this when generating any diagram to ensure valid output.

## Table of Contents

1. [File Structure](#file-structure)
2. [mxCell Elements](#mxcell-elements)
3. [Shape Types](#shape-types)
4. [Style Syntax](#style-syntax)
5. [Edges and Connections](#edges-and-connections)
6. [Text and Labels](#text-and-labels)
7. [Groups and Containers](#groups-and-containers)
8. [Swimlanes](#swimlanes)
9. [Multi-Page Diagrams](#multi-page-diagrams)
10. [Color Palettes](#color-palettes)
11. [Layout Constants](#layout-constants)

---

## File Structure

Every `.drawio` file follows this XML structure:

```xml
<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z" version="24.0.0" type="device">
  <diagram name="Page-1" id="page-1">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- All diagram elements go here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Required system cells

Every diagram MUST have these two cells — without them the file won't load:

```xml
<mxCell id="0"/>
<mxCell id="1" parent="0"/>
```

- `id="0"` — the root cell (internal graph root)
- `id="1"` — the default layer (all visible elements are children of this)

### mxGraphModel attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `dx`, `dy` | numbers | Canvas offset |
| `grid` | 0 or 1 | Show grid |
| `gridSize` | 10 | Grid spacing |
| `guides` | 1 | Show alignment guides |
| `tooltips` | 1 | Show tooltips |
| `connect` | 1 | Allow connections |
| `arrows` | 1 | Show arrows |
| `page` | 1 | Show page boundary |
| `pageScale` | 1 | Page zoom |
| `pageWidth` | 1169 | A4 landscape width |
| `pageHeight` | 827 | A4 landscape height |
| `math` | 0 | LaTeX math support |
| `shadow` | 0 | Drop shadows |

---

## mxCell Elements

Every shape, edge, and container is an `<mxCell>`. Key attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique identifier (use descriptive IDs) |
| `value` | string | Text label (supports HTML when `html=1` in style) |
| `style` | string | Semicolon-separated style properties |
| `vertex` | "1" | Present on shapes (not edges) |
| `edge` | "1" | Present on edges (not shapes) |
| `parent` | string | Parent cell ID — usually `"1"` (default layer), or a container ID |
| `source` | string | Source vertex ID (edges only) |
| `target` | string | Target vertex ID (edges only) |
| `connectable` | "0" | Disable connections to this cell |

### Geometry

Every cell has a child `<mxGeometry>`:

```xml
<mxCell id="shape1" value="Label" style="..." vertex="1" parent="1">
  <mxGeometry x="100" y="50" width="200" height="100" as="geometry"/>
</mxCell>
```

- `x`, `y` — position (top-left corner). Origin (0,0) is top-left of canvas.
- `width`, `height` — dimensions in pixels
- `as="geometry"` — required attribute

For edges, use `relative="1"`:

```xml
<mxCell id="edge1" style="..." edge="1" parent="1" source="a" target="b">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

---

## Shape Types

Set the shape via the `shape=` key in the style string. If omitted, defaults to rectangle.

### Basic Shapes

| Shape | Style Key | Notes |
|-------|-----------|-------|
| Rectangle | _(default, no shape= needed)_ | Add `rounded=1` for rounded corners |
| Ellipse | `shape=ellipse;perimeter=ellipsePerimeter` | Circle if width=height |
| Diamond | `shape=rhombus;perimeter=rhombusPerimeter` | Decision node |
| Cylinder | `shape=cylinder;perimeter=cylinderPerimeter` | Database icon |
| Cloud | `shape=cloud;perimeter=cloudPerimeter` | Cloud/external |
| Person | `shape=umlActor` | Stick figure |
| Document | `shape=document` | Page with folded corner |
| Folder | `shape=folder` | File folder |
| Terminator | `shape=terminator` | Rounded ends (flowchart start/end) |
| Parallelogram | `shape=parallelogram` | Data I/O |
| Triangle | `shape=triangle;perimeter=trianglePerimeter` | Pointing up |
| Hexagon | `shape=hexagon;perimeter=hexagonPerimeter2` | Process/prepare |
| Process | `shape=process` | Rectangle with side bars |

### C4 Model Shapes

For C4 diagrams, use standard shapes with C4 styling conventions:

| C4 Element | Shape | Style |
|------------|-------|-------|
| Person | `shape=umlActor` | Blue fill, person label + description |
| Software System | Rectangle, `rounded=1` | Blue fill for internal, gray for external |
| Container | Rectangle | Colored by type (blue=app, green=db, purple=queue) |
| Component | Rectangle | Lighter color, smaller |
| System Boundary | Rectangle, `container=1;swimlane=1` | Dashed stroke, transparent fill |

---

## Style Syntax

Styles are semicolon-separated `key=value` pairs:

```
rounded=1;whiteSpace=wrap;html=1;fillColor=#a5d8ff;strokeColor=#1971c2;fontSize=14;
```

### Fill and Stroke

| Key | Values | Default |
|-----|--------|---------|
| `fillColor` | Hex color or `none` | `#ffffff` |
| `strokeColor` | Hex color or `none` | `#000000` |
| `strokeWidth` | Number (pixels) | 1 |
| `dashed` | 0 or 1 | 0 |
| `dashPattern` | e.g., `3 3` | — |
| `opacity` | 0–100 | 100 |
| `shadow` | 0 or 1 | 0 |
| `glass` | 0 or 1 | 0 |
| `gradientColor` | Hex color | — |

### Shape Geometry

| Key | Values | Default |
|-----|--------|---------|
| `rounded` | 0 or 1 | 0 |
| `arcSize` | 0–100 | 20 |
| `aspect` | `fixed` | — |
| `rotation` | Degrees (0–360) | 0 |

### Text and Labels

| Key | Values | Default |
|-----|--------|---------|
| `html` | 0 or 1 | 1 (always use 1) |
| `whiteSpace` | `wrap` | `wrap` |
| `fontSize` | Number | 12 |
| `fontFamily` | Font name | Helvetica |
| `fontColor` | Hex color | `#000000` |
| `fontStyle` | Bitmask: 1=bold, 2=italic, 4=underline | 0 |
| `align` | `left`, `center`, `right` | `center` |
| `verticalAlign` | `top`, `middle`, `bottom` | `middle` |
| `spacing` | Number (pixels) | 0 |
| `spacingTop` | Number | 0 |
| `spacingBottom` | Number | 0 |
| `spacingLeft` | Number | 0 |
| `spacingRight` | Number | 0 |

### Container and Group

| Key | Values | Purpose |
|-----|--------|---------|
| `container` | 1 | Makes this cell a container |
| `swimlane` | 1 | Adds a header bar |
| `collapsible` | 0 or 1 | Allow collapse |
| `startSize` | Number | Header height (px) |
| `recursiveResize` | 0 or 1 | Resize children |

---

## Edges and Connections

Edges connect shapes via `source` and `target` attributes:

```xml
<mxCell id="edge1" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;endFill=1;" edge="1" parent="1" source="shape1" target="shape2">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Edge Routing Styles

| Style | Effect |
|-------|--------|
| `edgeStyle=orthogonalEdgeStyle` | Right-angle routing (most common) |
| `edgeStyle=elbowEdgeStyle` | Single elbow bend |
| `edgeStyle=entityRelationEdgeStyle` | ER-style routing |
| `curved=1` | Smooth curves |
| _(no edgeStyle)_ | Straight line |

### Arrow Types

| Key | Values |
|-----|--------|
| `endArrow` | `classic`, `block`, `open`, `oval`, `diamond`, `diamondThin`, `none` |
| `startArrow` | Same as endArrow |
| `endFill` | 0 (open) or 1 (filled) |
| `startFill` | 0 or 1 |
| `endSize` | Number (arrow size) |
| `startSize` | Number |

### Connection Points

Control where edges attach to shapes:

| Key | Value | Meaning |
|-----|-------|---------|
| `exitX` | 0.0–1.0 | Exit point horizontal (0=left, 0.5=center, 1=right) |
| `exitY` | 0.0–1.0 | Exit point vertical (0=top, 0.5=middle, 1=bottom) |
| `entryX` | 0.0–1.0 | Entry point horizontal |
| `entryY` | 0.0–1.0 | Entry point vertical |
| `exitDx`, `exitDy` | Pixels | Exit offset |
| `entryDx`, `entryDy` | Pixels | Entry offset |

### Common Edge Presets

```xml
<!-- Solid arrow, orthogonal routing -->
edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;endFill=1;

<!-- Dashed arrow -->
edgeStyle=orthogonalEdgeStyle;dashed=1;endArrow=classic;endFill=1;html=1;

<!-- Bidirectional arrow -->
edgeStyle=orthogonalEdgeStyle;endArrow=classic;startArrow=classic;endFill=1;startFill=1;html=1;

<!-- No arrow (plain line) -->
edgeStyle=orthogonalEdgeStyle;endArrow=none;endFill=0;html=1;
```

---

## Text and Labels

### Simple text

Set the `value` attribute on any mxCell:

```xml
<mxCell id="s1" value="Hello World" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
```

### Multi-line and formatted text

Use HTML entities in the `value` attribute (with `html=1` in style):

```xml
value="&lt;b&gt;Title&lt;/b&gt;&lt;br/&gt;Description line 1&lt;br/&gt;Description line 2"
```

Common HTML entities:
- `&lt;b&gt;...&lt;/b&gt;` — bold
- `&lt;i&gt;...&lt;/i&gt;` — italic
- `&lt;br/&gt;` — line break
- `&lt;font color=&quot;#999&quot;&gt;...&lt;/font&gt;` — colored text
- `&lt;font style=&quot;font-size: 11px&quot;&gt;...&lt;/font&gt;` — sized text

### Standalone text (no shape)

```xml
<mxCell id="label1" value="Annotation text" style="text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
  <mxGeometry x="100" y="50" width="120" height="30" as="geometry"/>
</mxCell>
```

### Sizing shapes for text

Draw.io auto-wraps text within shape boundaries. Size shapes to fit:
- **Single line**: height 40–50px
- **2–3 lines**: height 60–80px
- **4–5 lines (with title)**: height 100–120px
- **Width**: 120px minimum, 160–200px for descriptive labels
- Use `whiteSpace=wrap` so text wraps within the shape

---

## Groups and Containers

### Container (children move with parent)

```xml
<!-- Container shape -->
<mxCell id="group1" value="Group Title" style="rounded=1;container=1;swimlane=1;startSize=30;fillColor=#f5f5f5;strokeColor=#666;dashed=1;" vertex="1" parent="1" connectable="0">
  <mxGeometry x="50" y="50" width="400" height="300" as="geometry"/>
</mxCell>

<!-- Child shapes — parent is the container, not "1" -->
<mxCell id="child1" value="Inside" style="rounded=1;..." vertex="1" parent="group1">
  <mxGeometry x="20" y="40" width="120" height="60" as="geometry"/>
</mxCell>
```

Key points:
- Container has `container=1` in style
- Children set `parent="group1"` (the container ID)
- Children coordinates are **relative to the container**
- Add `swimlane=1;startSize=30` for a header bar

---

## Swimlanes

```xml
<!-- Swimlane container -->
<mxCell id="lane1" value="Department A" style="swimlane=1;startSize=30;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="50" y="50" width="600" height="200" as="geometry"/>
</mxCell>

<!-- Content inside swimlane -->
<mxCell id="step1" value="Process Step" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="lane1">
  <mxGeometry x="40" y="50" width="120" height="60" as="geometry"/>
</mxCell>
```

- `startSize` controls header height
- `horizontal=0` for vertical swimlanes

---

## Multi-Page Diagrams

Add multiple `<diagram>` elements inside `<mxfile>`:

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Context" id="page-context">
    <mxGraphModel>
      <root>
        <mxCell id="0"/><mxCell id="1" parent="0"/>
        <!-- Context diagram elements -->
      </root>
    </mxGraphModel>
  </diagram>
  <diagram name="Container" id="page-container">
    <mxGraphModel>
      <root>
        <mxCell id="0"/><mxCell id="1" parent="0"/>
        <!-- Container diagram elements -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Each page has its own independent set of cell IDs.

---

## Color Palettes

### Professional (default)

| Role | Fill | Stroke |
|------|------|--------|
| Primary (blue) | `#dae8fc` | `#6c8ebf` |
| Secondary (green) | `#d5e8d4` | `#82b366` |
| Accent (red/pink) | `#f8cecc` | `#b85450` |
| Warning (orange) | `#ffe6cc` | `#d6b656` |
| Purple | `#e1d5e7` | `#9673a6` |
| Teal | `#d5e8d4` | `#0c8599` |
| Gray (external) | `#f5f5f5` | `#666666` |
| Dark | `#333333` | `#000000` |

### C4 Palette

| C4 Element | Fill | Stroke | Font Color |
|------------|------|--------|------------|
| Person | `#08427b` | `#073b6f` | `#ffffff` |
| Internal System | `#1168bd` | `#0b4884` | `#ffffff` |
| External System | `#999999` | `#6b6b6b` | `#ffffff` |
| Container | `#438dd5` | `#3c7fc0` | `#ffffff` |
| Component | `#85bbf0` | `#5d99c6` | `#000000` |
| Database | `#438dd5` | `#3c7fc0` | `#ffffff` |

---

## Layout Constants

| Constant | Value | Use |
|----------|-------|-----|
| NODE_WIDTH | 160 | Standard shape width |
| NODE_HEIGHT | 80 | Standard shape height (2-3 lines) |
| NODE_HEIGHT_TALL | 120 | Shape with title + description (4-5 lines) |
| H_GAP | 60 | Horizontal gap between shapes |
| V_GAP | 50 | Vertical gap between shapes |
| GRID_CELL_H | 220 | NODE_WIDTH + H_GAP |
| GRID_CELL_V | 130 | NODE_HEIGHT + V_GAP |
| CONTAINER_PAD | 30 | Padding inside containers |
| SWIMLANE_HEADER | 30 | Height of swimlane header |
| TITLE_SIZE | 20 | Title font size |
| LABEL_SIZE | 14 | Normal label font size |
| SMALL_SIZE | 11 | Description/annotation font size |
