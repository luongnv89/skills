# JSON Fixer Agent

**Role**: Apply targeted fixes from validator report. Patch specific fields, never regenerate from scratch. Support max 3 validation cycles.

## Input

Receive from json-validator:
- Original JSON object
- Validation report with failed checks and fix priorities
- Cycle count (1, 2, or 3)

## Procedure

### Per-Check Fix Logic

Apply fixes in priority order from validator report.

#### Check 1: Valid JSON Structure
**If FAIL**: Report error — do not attempt to fix; return to generator.

#### Check 2: Required Fields Missing
**For each element missing fields**:
- Add missing field with default value:
  - `id`: use existing; if missing, assign unique ID
  - `type`: use from validator report; if missing, infer from context
  - `x`, `y`, `width`, `height`: use 0, 0, 100, 50 if missing
  - `angle`: 0
  - `strokeColor`: `"#A1A1A1"`
  - `backgroundColor`: `"transparent"`
  - `fillStyle`: `"solid"`
  - `strokeWidth`: 2
  - `strokeStyle`: `"solid"`
  - `roughness`: 0
  - `opacity`: 100
  - `groupIds`: `[]`
  - `frameId`: `null`
  - `roundness`: `null`
  - `isDeleted`: false
  - `boundElements`: `[]`
  - `updated`: timestamp
  - `link`: `null`
  - `locked`: false
  - `seed`: random number

- **For text elements**, also add:
  - `text`: empty string if missing
  - `fontSize`: 16 (minimum readable)
  - `fontFamily`: 1 (Virgil/hand-writing — default)
  - `textAlign`: `"center"`
  - `verticalAlign`: `"middle"`
  - `containerId`: `null` (unless bound to a shape)
  - `originalText`: same as `text`
  - `lineHeight`: 1.25
  - `autoResize`: true

- **For arrow/line elements**, also add:
  - `points`: `[[0, 0], [100, 100]]` if missing
  - `startBinding`: `{"elementId": null, "focus": 0.5, "gap": 0}`
  - `endBinding`: same structure
  - `startArrowhead`: `"arrow"`
  - `endArrowhead`: `"arrow"`

#### Check 3: Duplicate IDs
**For each duplicate ID**:
- Append suffix: `id_1`, `id_2`, etc.
- Update all references in `boundElements` and arrow bindings

#### Check 4: Broken Text Bindings
**For missing binding in container**:
- Add to container's `boundElements`: `{"id": "<text-id>", "type": "text"}`

**For missing binding in text**:
- Add `containerId` to text element: `"<container-id>"`
- Ensure `autoResize: true`

#### Check 5: Broken Arrow Bindings
**For arrow with missing start/end binding in target element**:
- Add to target's `boundElements`: `{"id": "<arrow-id>", "type": "arrow"}`

**For element with arrow binding but arrow missing reference**:
- Add to arrow: `startBinding` or `endBinding` with correct `elementId`

#### Check 6: Invalid Arrow Points
**If `points[0]` is not `[0, 0]`**:
- Prepend `[0, 0]` to points array

**If points array has < 2 entries**:
- Create default: `[[0, 0], [50, 50]]`

#### Check 7: Overlapping Shapes
**For each overlapping pair**:
- Shift the second element's `x` or `y` by at least 15px to clear overlap
- Maintain existing layout direction (don't rotate)

#### Check 8: Missing Entities
**If semantic completeness fails**:
- Cannot fix without regeneration; return to generator for revision

#### Check 9: Unreadable Text
**For `fontSize < 16`**:
- Set to 16

**For text with `strokeColor` same as `backgroundColor`**:
- Set `strokeColor` to a color that is visibly readable against the background

**For `lineHeight` not 1.25**:
- Set to 1.25

**For `autoResize: false`**:
- Set to true

#### Check 10: Text Doesn't Fit in Shape
**For each bound text element**:
1. Calculate required shape height: `line_count * fontSize * 1.25 + 40`
2. If current `height < required`:
   - Set shape `height` to required
   - Shift elements below by `(new_height - old_height)`
3. Calculate required shape width for longest line + 20px
4. If current `width < required`:
   - Set shape `width` to required
   - Adjust layout as needed

**For container labels bound to container**:
- Remove binding: set `containerId: null`
- Position near container top-left manually

### Output

Return patched JSON object with:
- `cycle_number`: 1, 2, or 3
- `fixes_applied`: [list of fixes with check number and action]
- `ready_for_validation`: true if all fixes applied; false if semantic/structure fixes needed
- Updated JSON object

### Constraints

- **No regeneration**: Only patch fields; never regenerate elements or arrows
- **Preserve IDs**: Keep original IDs where possible (only update duplicates)
- **Max 3 cycles**: If cycle == 3 and still failing, return with best-effort JSON; main agent decides next step
- **Binding consistency**: All two-way bindings must be updated in both directions
- **Text fit mandatory**: Always ensure bound text fits container

## Success Criteria

- All fixes from validator report applied
- No new errors introduced
- Ready for next validation cycle or file write
- If cycle == 3, JSON is "best-effort" even if some checks still fail
