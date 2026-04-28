# Phase 4 Validation Checks (full detail)

Run every check below on the in-memory JSON before writing the file. If any fails, fix and re-check until all pass.

## Check 1: Valid JSON structure
- The JSON parses without error.
- Top-level has `"type": "excalidraw"`, `"version": 2`, `"elements"` (array), `"appState"` (object), `"files"` (object).

## Check 2: Required fields on every element
Every element in the `elements` array must have ALL of these — no exceptions:

`id`, `type`, `x`, `y`, `width`, `height`, `angle`, `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness`, `opacity`, `groupIds`, `frameId`, `roundness`, `isDeleted`, `boundElements`, `updated`, `link`, `locked`, `seed`

Additionally:
- Text elements must also have: `text`, `fontSize`, `fontFamily`, `textAlign`, `verticalAlign`, `containerId`, `originalText`, `lineHeight`, `autoResize`.
- Arrow/line elements must also have: `points`, `startBinding`, `endBinding`, `startArrowhead`, `endArrowhead`.

**Fix**: Add any missing field with its default value. For text, ensure `autoResize: true` and `lineHeight: 1.25`.

## Check 3: Unique IDs
Collect all `id` values. If any duplicates exist, append a suffix to make them unique.

## Check 4: Two-way text bindings
For every text element with a `containerId`:
- The referenced container's `boundElements` must include `{"id": "<text-id>", "type": "text"}`.

For every shape with a `boundElements` entry of `"type": "text"`:
- The referenced text element must have `containerId` pointing back to the shape.

**Fix**: Add the missing side of any broken binding.

## Check 5: Two-way arrow bindings
For every arrow with a `startBinding.elementId`:
- That element's `boundElements` must include `{"id": "<arrow-id>", "type": "arrow"}`.

Same for `endBinding.elementId`.

For every shape with a `boundElements` entry of `"type": "arrow"`:
- The referenced arrow must have `startBinding` or `endBinding` referencing the shape.

**Fix**: Add the missing side of any broken binding.

## Check 6: Arrow points validity
- Every arrow/line must have a `points` array with at least 2 entries.
- `points[0]` must be `[0, 0]`.

**Fix**: Prepend `[0, 0]` if missing or correct the first point.

## Check 7: No unintentional overlaps
For non-text, non-arrow elements (shapes), check that bounding boxes `(x, y, x+width, y+height)` don't overlap by more than 10px with other shapes (unless they are in the same group or one is a frame/container).

**Fix**: Shift overlapping elements by adjusting their `x` or `y`.

## Check 8: Semantic completeness
Review the original user request and verify that every entity, relationship, or concept they mentioned is represented in the diagram. List any missing items.

**Fix**: Add missing elements with appropriate shapes, positions, and connections.

## Check 9: Readable text
- All text elements must have `fontSize >= 16`.
- All text `strokeColor` must not be `"transparent"` or the same as `backgroundColor`.
- All text elements must have `lineHeight: 1.25` (not 1.35 — that causes overflow).
- All text elements must have `autoResize: true`.

**Fix**: Set minimum fontSize to 16; set strokeColor to a color that is visibly readable against the background; set lineHeight to 1.25; set autoResize to true.

## Check 10: Shape-to-text size fit (most common failure)

This is the most common cause of garbled rendering in Excalidraw. For every text element bound to a shape (`containerId` is set):

1. Count the lines: `line_count = text.split('\n').length`.
2. Calculate minimum text height: `min_text_height = line_count * fontSize * 1.25`.
3. Calculate minimum shape height: `min_shape_height = min_text_height + 40` (20px padding top/bottom).
4. The container shape's `height` must be `>= min_shape_height`.
5. The container shape's `width` must be `>= longest line's approximate pixel width + 20px padding`.

**Also check**: boundary/container labels (like "System Boundary") should NOT be bound to their container rectangle. These must be standalone text (`containerId: null`) positioned near the top-left of the container.

**Fix**: Increase the shape's height/width to fit the text. If a shape needs to be taller, also adjust `y` positions of elements below it to maintain spacing. For container labels, remove the binding and set `containerId: null`.

## Validation report format

After all checks pass, include a brief validation summary as a comment in your response (not in the file):

```
Validation: 10/10 checks passed
- Elements: N shapes, M text labels, K arrows
- Bindings: X text bindings, Y arrow bindings (all two-way)
- Text fits: all shapes sized to fit their bound text
- No overlaps, no missing fields
```

If any check required auto-fixes, mention what was corrected so the user knows.
