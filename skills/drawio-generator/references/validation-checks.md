# Phase 4 Validation Checks

After generating the XML but **before writing the file**, run every check below. Fix any failures and re-check until all pass.

## Check 1: Valid XML structure
- The XML parses without error
- Has `<mxfile>` → `<diagram>` → `<mxGraphModel>` → `<root>` hierarchy
- Each page has system cells `id="0"` and `id="1" parent="0"`

## Check 2: All shapes have required attributes
Every vertex cell must have: `id`, `value`, `style`, `vertex="1"`, `parent`, and a child `<mxGeometry>` with `x`, `y`, `width`, `height`, `as="geometry"`.

Every style string must include `html=1;whiteSpace=wrap;`.

**Fix**: Add missing attributes with defaults.

## Check 3: Unique IDs
All `id` values must be unique within each page. No duplicates.

**Fix**: Append suffix to duplicates.

## Check 4: Edge bindings valid
Every edge with `source` or `target` must reference an existing vertex ID in the same page.

**Fix**: Remove broken references or add missing shapes.

## Check 5: Edge geometry
Every edge must have `<mxGeometry relative="1" as="geometry"/>`.

**Fix**: Add missing geometry.

## Check 6: No overlapping shapes
Check that vertex bounding boxes don't overlap by more than 10px (unless one is a container parent of the other).

**Fix**: Shift overlapping shapes.

## Check 7: Container hierarchy valid
Every cell with `parent="X"` (where X is not "0" or "1") must reference an existing container cell. Children coordinates must be relative to the container.

**Fix**: Correct parent references.

## Check 8: Semantic completeness
Every entity, relationship, or concept from the user's request is represented.

**Fix**: Add missing elements.

## Check 9: Text readable and shapes sized
- All `fontSize` >= 11
- All shapes are wide/tall enough for their `value` text
- Single line: height >= 40. Multi-line: add ~20px per extra line.

**Fix**: Increase shape dimensions or font size.

## Validation report

After all checks pass:
```
Validation: 9/9 checks passed
- Pages: N
- Elements: X shapes, Y edges
- Containers: Z
- All IDs unique, all edges bound, no overlaps
```
