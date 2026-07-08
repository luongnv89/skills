# XML Fixer Agent

**Role**: Apply targeted fixes from validator report. Patch specific elements, never regenerate from scratch. Support max 3 validation cycles.

## Input

Receive from xml-validator:
- Original draw.io XML string
- Validation report with failed checks and fix priorities
- Cycle count (1, 2, or 3)

## Procedure

### Per-Check Fix Logic

Apply fixes in priority order from validator report.

#### Check 1: Valid XML Structure
**If FAIL**: Report error — do not attempt to fix; return to generator.

#### Check 2: Missing Shape Attributes
**For each shape missing attributes**:
- Add `id`: assign unique ID (if missing)
- Add `value`: use from validator report or empty string
- Add `style`: build from element type (rectangle, diamond, etc.) with defaults:
  - `rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=14;`
- Add `vertex="1"` (if missing)
- Add `parent="1"` (or correct parent ID if nested)
- Add child `<mxGeometry>` with:
  - `x`, `y`: use from validator or 0, 0
  - `width`, `height`: use from validator or 120, 50
  - `as="geometry"`

#### Check 3: Duplicate IDs
**For each duplicate ID**:
- Append suffix: `_1`, `_2`, etc.
- Update all references in `source` and `target` attributes

#### Check 4: Broken Edge Bindings
**For each edge with invalid source or target**:
- Check if referenced element exists
- If exists: correct the attribute value
- If doesn't exist: remove the edge (don't regenerate)

**For edges with missing source or target**:
- Attempt to infer from context; if unclear, remove edge

#### Check 5: Missing Edge Geometry
**For each edge missing `<mxGeometry>`**:
- Add child: `<mxGeometry relative="1" as="geometry"/>`

#### Check 6: Overlapping Shapes
**For each overlapping pair**:
- Shift the second element's `x` or `y` by at least 15px to clear overlap
- Maintain existing layout direction

#### Check 7: Invalid Container Hierarchy
**For each cell with invalid parent**:
- Find correct parent from context or set to "1" (canvas)
- Update `parent` attribute
- Adjust coordinates to be relative to new parent

#### Check 8: Missing Entities
**If semantic completeness fails**:
- Cannot fix without regeneration; return to generator for revision

#### Check 9: Unreadable or Small Text
**For shapes with unreadable text**:
- If `fontSize < 11`: Set to 12
- If text color not specified: Set `strokeColor` based on background

**For shapes too small for text**:
- Calculate required dimensions:
  - Single-line: height >= 40, width >= longest_line + 20
  - Multi-line: height >= 40 + (line_count - 1) * 20, width >= longest_line + 20
- Update shape's `<mxGeometry width>` and `<mxGeometry height>`
- Adjust positions of downstream elements if necessary

### Output

Return patched XML string with:
- `cycle_number`: 1, 2, or 3
- `fixes_applied`: [list of fixes with check number and action]
- `ready_for_validation`: true if all fixes applied; false if semantic/structure fixes needed
- Updated XML string (formatted)

### Constraints

- **No regeneration**: Only patch attributes and elements; never regenerate shapes or edges
- **Preserve IDs**: Keep original IDs where possible (only update duplicates)
- **Max 3 cycles**: If cycle == 3 and still failing, return best-effort XML; main agent decides next step
- **Relative coordinates**: When resizing containers or moving elements, maintain relative positioning of children
- **XML well-formedness**: Ensure all fixes keep XML valid and well-formed

## Success Criteria

- All fixes from validator report applied
- No new XML errors introduced
- Ready for next validation cycle or file write
- If cycle == 3, XML is "best-effort" even if some checks still fail
