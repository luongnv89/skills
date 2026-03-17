# Excalidraw JSON Format Reference

This reference documents the exact JSON structure that Excalidraw expects. Read this when generating any diagram to ensure valid output.

## Table of Contents

1. [Top-Level Structure](#top-level-structure)
2. [Common Element Properties](#common-element-properties)
3. [Element Types](#element-types)
4. [Text Binding](#text-binding)
5. [Arrow Bindings](#arrow-bindings)
6. [Groups](#groups)
7. [Color Palettes](#color-palettes)
8. [Layout Constants](#layout-constants)

---

## Top-Level Structure

Every `.excalidraw` file is JSON with this structure:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "theme": "light",
    "viewBackgroundColor": "#ffffff",
    "gridMode": false
  },
  "files": {}
}
```

- `elements`: Array of all visual elements
- `appState`: Editor settings (keep minimal — theme and background are sufficient)
- `files`: Empty object unless embedding images

---

## Common Element Properties

Every element MUST include ALL of these properties:

```json
{
  "id": "unique-string-id",
  "type": "rectangle",
  "x": 0,
  "y": 0,
  "width": 200,
  "height": 100,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 1,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "roundness": { "type": 3 },
  "isDeleted": false,
  "boundElements": null,
  "updated": 1700000000000,
  "link": null,
  "locked": false,
  "seed": 12345
}
```

### Property Details

| Property | Type | Values |
|----------|------|--------|
| `id` | string | Any unique string. Use descriptive IDs like `"node-auth-service"` or `"arrow-1-to-2"` |
| `type` | string | `"rectangle"`, `"ellipse"`, `"diamond"`, `"arrow"`, `"line"`, `"text"`, `"freedraw"`, `"frame"` |
| `x`, `y` | number | Top-left corner position. Origin (0,0) is top-left of canvas |
| `width`, `height` | number | Dimensions in pixels |
| `angle` | number | Rotation in radians. 0 = no rotation |
| `strokeColor` | string | Hex color for border, e.g. `"#1e1e1e"` |
| `backgroundColor` | string | Fill color. `"transparent"` for no fill |
| `fillStyle` | string | `"solid"`, `"hachure"`, `"cross-hatch"` |
| `strokeWidth` | number | 1 (thin), 2 (normal), 4 (thick) |
| `strokeStyle` | string | `"solid"`, `"dashed"`, `"dotted"` |
| `roughness` | number | 0 (clean/geometric), 1 (hand-drawn), 2 (very sketchy) |
| `opacity` | number | 0–100 |
| `groupIds` | string[] | Array of group IDs this element belongs to |
| `roundness` | object/null | `{"type": 3}` for rounded corners, `null` for sharp |
| `seed` | number | Random integer for roughness rendering. Use any positive integer |
| `boundElements` | array/null | Array of `{"id": "...", "type": "text"}` or `{"id": "...", "type": "arrow"}` |

---

## Element Types

### Rectangle
Standard box shape. Use for nodes, containers, cards.

```json
{
  "type": "rectangle",
  "roundness": { "type": 3 }
}
```

### Ellipse
Circle or oval. Use for start/end states, entities.

```json
{
  "type": "ellipse",
  "roundness": { "type": 2 }
}
```

### Diamond
Rhombus shape. Use for decision nodes, conditions.

```json
{
  "type": "diamond",
  "roundness": { "type": 2 }
}
```

### Text
Standalone or bound to a container.

```json
{
  "type": "text",
  "text": "Hello World",
  "fontSize": 20,
  "fontFamily": 1,
  "textAlign": "center",
  "verticalAlign": "middle",
  "containerId": null,
  "originalText": "Hello World",
  "autoResize": true,
  "lineHeight": 1.25
}
```

| Property | Values |
|----------|--------|
| `fontSize` | 16 (small), 20 (normal), 28 (heading), 36 (title) |
| `fontFamily` | 1 (Virgil/hand-drawn), 2 (Helvetica), 3 (Cascadia/code) |
| `textAlign` | `"left"`, `"center"`, `"right"` |
| `verticalAlign` | `"top"`, `"middle"` |
| `containerId` | ID of parent shape, or `null` for standalone text |

### Arrow
Connecting line with arrowhead(s).

```json
{
  "type": "arrow",
  "points": [[0, 0], [200, 0]],
  "startBinding": null,
  "endBinding": null,
  "startArrowhead": null,
  "endArrowhead": "arrow",
  "roundness": { "type": 2 }
}
```

| Property | Values |
|----------|--------|
| `points` | Array of [x, y] offsets from element's (x, y). First point is always [0, 0] |
| `startArrowhead` | `null`, `"arrow"`, `"dot"`, `"bar"`, `"triangle"` |
| `endArrowhead` | `null`, `"arrow"`, `"dot"`, `"bar"`, `"triangle"` |

### Line
Same as arrow but defaults to no arrowheads.

```json
{
  "type": "line",
  "points": [[0, 0], [200, 0]],
  "startBinding": null,
  "endBinding": null,
  "startArrowhead": null,
  "endArrowhead": null
}
```

### Frame
Container that clips child elements.

```json
{
  "type": "frame",
  "name": "Frame Title"
}
```
Children reference the frame via their `frameId` property.

---

## Text Binding

To place text inside a shape:

1. Create the shape with `boundElements` referencing the text:
```json
{
  "id": "box-1",
  "type": "rectangle",
  "boundElements": [{"id": "text-box-1", "type": "text"}]
}
```

2. Create the text with `containerId` referencing the shape:
```json
{
  "id": "text-box-1",
  "type": "text",
  "containerId": "box-1",
  "textAlign": "center",
  "verticalAlign": "middle",
  "autoResize": true,
  "lineHeight": 1.25,
  "x": <shape.x + 10>,
  "y": <shape.y + 10>,
  "width": <shape.width - 20>,
  "height": <calculated from line count>
}
```

### Critical: Sizing shapes to fit their text

Excalidraw does NOT auto-resize shapes to fit text. If a shape is too small for its bound text, the text overflows and renders as garbled/overlapping characters. You MUST size shapes based on their text content.

**Calculate required height** before creating the shape:
- `line_count` = number of `\n` in the text + 1
- `text_height` = `line_count * fontSize * lineHeight`
- `shape_height` = `text_height + 40` (20px padding top + 20px padding bottom)
- Minimum shape height: 60px (for single-line text)

**Example calculation** for text "MMT Probe\n[C / Libpcap]\nReal-time packet\ncapture & analysis":
- line_count = 4
- text_height = 4 * 16 * 1.25 = 80px
- shape_height = 80 + 40 = 120px minimum

**Keep bound text short** — ideally 1-3 lines for node labels. If you need more detail, use a larger shape (width 240+, height 160+) or put the description as standalone text below the shape instead of inside it.

### Boundary / container labels

For labeling a boundary or container rectangle (like "System Boundary" or "VPC"), do NOT bind the label text to the container — this causes the text to render at the wrong position. Instead, use **standalone text** positioned near the top-left corner of the container:

```json
{
  "id": "boundary-label",
  "type": "text",
  "containerId": null,
  "text": "System Boundary",
  "x": <boundary.x + 10>,
  "y": <boundary.y + 8>
}
```

### Text properties that matter for rendering

- **`autoResize`: true** — always set this on text elements so Excalidraw can reflow text properly
- **`lineHeight`: 1.25** — use 1.25 for all text (not 1.35 which causes overflow)
- **`width`**: for bound text, set to `shape.width - 20` (10px padding each side)
- **`height`**: set to `line_count * fontSize * lineHeight` (Excalidraw will adjust on load, but an approximate value prevents rendering glitches on first render)

---

## Arrow Bindings

To connect an arrow to shapes:

1. Add arrow reference to BOTH source and target shapes:
```json
{
  "id": "box-1",
  "boundElements": [{"id": "arrow-1", "type": "arrow"}]
}
```

2. Set arrow bindings:
```json
{
  "id": "arrow-1",
  "type": "arrow",
  "startBinding": {
    "elementId": "box-1",
    "focus": 0,
    "gap": 8
  },
  "endBinding": {
    "elementId": "box-2",
    "focus": 0,
    "gap": 8
  }
}
```

- `focus`: -1 to 1, where 0 is center of the element edge
- `gap`: pixels between arrow tip and element border (use 8)

### Arrow Positioning with Bindings

When an arrow connects two shapes:
- Arrow `x`, `y` = position of the source shape's edge
- `points[0]` = `[0, 0]` (start)
- `points[last]` = offset to target shape's edge
- Excalidraw auto-adjusts bound arrow positions on load, so approximate positions work

---

## Groups

Group elements by giving them the same group ID:

```json
// Element 1
{ "groupIds": ["group-a"] }
// Element 2
{ "groupIds": ["group-a"] }
```

Nested groups: `"groupIds": ["inner-group", "outer-group"]`

---

## Color Palettes

### Professional (default)
| Role | Color |
|------|-------|
| Primary | `"#1971c2"` (blue) |
| Secondary | `"#2f9e44"` (green) |
| Accent | `"#e03131"` (red) |
| Warning | `"#f08c00"` (orange) |
| Purple | `"#9c36b5"` |
| Teal | `"#0c8599"` |
| Stroke | `"#1e1e1e"` |
| Light fill | `"#a5d8ff"` (blue), `"#b2f2bb"` (green), `"#ffc9c9"` (red) |
| Background | `"#ffffff"` |

### Pastel
| Role | Color |
|------|-------|
| Blue | `"#dbe4ff"` |
| Green | `"#d3f9d8"` |
| Yellow | `"#fff3bf"` |
| Pink | `"#fcc2d7"` |
| Purple | `"#e5dbff"` |
| Orange | `"#ffe8cc"` |
| Stroke | `"#495057"` |

### Monochrome
| Role | Color |
|------|-------|
| Dark | `"#343a40"` |
| Medium | `"#868e96"` |
| Light | `"#dee2e6"` |
| Lightest | `"#f1f3f5"` |
| Stroke | `"#1e1e1e"` |

---

## Layout Constants

Use these spacing values for consistent layouts:

| Constant | Value | Use |
|----------|-------|-----|
| NODE_WIDTH | 200 | Standard node/box width (use 240 if text is long) |
| NODE_HEIGHT | 80 | Minimum for 1-2 lines. Use 120 for 3-4 lines, 160 for 5-6 lines |
| NODE_PADDING | 20 | Text padding inside nodes (10px each side) |
| H_GAP | 80 | Horizontal gap between nodes |
| V_GAP | 60 | Vertical gap between nodes |
| ARROW_GAP | 8 | Gap between arrow tip and node |
| TITLE_FONT_SIZE | 28 | Diagram title |
| LABEL_FONT_SIZE | 20 | Node labels |
| SMALL_FONT_SIZE | 16 | Annotations, descriptions |
| SWIMLANE_HEADER | 40 | Height of swimlane header |
| GRID_CELL | 280 | NODE_WIDTH + H_GAP for grid layouts |

### Layout Algorithms

**Horizontal flow** (left to right):
- x = col * GRID_CELL
- y = row * (NODE_HEIGHT + V_GAP)

**Vertical flow** (top to bottom):
- x = col * GRID_CELL
- y = row * (NODE_HEIGHT + V_GAP)

**Tree layout**:
- Center parent above children
- Spread children evenly with H_GAP

**Grid layout** (for many nodes):
- cols = ceil(sqrt(n))
- Arrange in row-major order
