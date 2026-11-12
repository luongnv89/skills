# JSON Validator Agent

**Role**: Run all 10 validation checks independently on Excalidraw JSON, return structured pass/fail report for fixes.

## Input

Receive from json-generator:
- Complete Excalidraw JSON object
- Metadata: original plan, element count, arrow count

## Procedure

Run each check independently. Record result as PASS or FAIL with remediation details.

### Check 1: Valid JSON Structure
- JSON parses without error
- Top-level has: `type: "excalidraw"`, `version: 2`, `elements` (array), `appState` (object), `files` (object)

**Fail remediation**: Describe syntax error or missing top-level key

---

### Check 2: Required Fields on Every Element
All elements must have ALL these fields:
`id`, `type`, `x`, `y`, `width`, `height`, `angle`, `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness`, `opacity`, `groupIds`, `frameId`, `roundness`, `isDeleted`, `boundElements`, `updated`, `link`, `locked`, `seed`

Additionally:
- **Text elements**: must have `text`, `fontSize`, `fontFamily`, `textAlign`, `verticalAlign`, `containerId`, `originalText`, `lineHeight`, `autoResize`
- **Arrow/line elements**: must have `points`, `startBinding`, `endBinding`, `startArrowhead`, `endArrowhead`

**Fail remediation**: List elements missing fields and their missing fields

---

### Check 3: Unique IDs
Collect all `id` values. No duplicates allowed.

**Fail remediation**: List duplicate IDs and suggested unique suffixes

---

### Check 4: Two-way Text Bindings
For every text element with `containerId`:
- The referenced container's `boundElements` must include `{"id": "<text-id>", "type": "text"}`

For every shape with a `boundElements` entry of `type: "text"`:
- The referenced text element must have `containerId` pointing back

**Fail remediation**: List broken bindings (specify which direction is missing)

---

### Check 5: Two-way Arrow Bindings
For every arrow with `startBinding.elementId`:
- That element's `boundElements` must include `{"id": "<arrow-id>", "type": "arrow"}`

Same for `endBinding.elementId`.

For every shape with a `boundElements` entry of `type: "arrow"`:
- The referenced arrow must have `startBinding` or `endBinding` referencing the shape

**Fail remediation**: List broken arrow bindings and suggested fixes

---

### Check 6: Arrow Points Validity
- Every arrow/line must have `points` array with at least 2 entries
- `points[0]` must be `[0, 0]`

**Fail remediation**: List arrows with invalid points, suggest fix (prepend `[0, 0]` or correct structure)

---

### Check 7: No Unintentional Overlaps
For non-text, non-arrow elements (shapes), check that bounding boxes `(x, y, x+width, y+height)` don't overlap by more than 10px with other shapes (unless in same group or one is frame/container).

**Fail remediation**: List overlapping element pairs and suggested position shifts

---

### Check 8: Semantic Completeness
Review the original diagram plan. Verify every entity, relationship, or concept mentioned is represented.

**Fail remediation**: List missing entities/relationships

---

### Check 9: Readable Text
- All text elements must have `fontSize >= 16`
- All text `strokeColor` must not be `"transparent"` or same as `backgroundColor`
- All text elements must have `lineHeight: 1.25` (not 1.35)
- All text elements must have `autoResize: true`

**Fail remediation**: List text elements failing each sub-check

---

### Check 10: Shape-to-Text Size Fit
For every text element bound to a shape (`containerId` is set):
1. Count lines: `line_count = text.split('\n').length`
2. Min text height: `line_count * fontSize * 1.25`
3. Min shape height: `min_text_height + 40`
4. Container shape's `height` must be >= `min_shape_height`
5. Container shape's `width` must fit longest line + 20px padding

Also: Container/boundary labels should NOT be bound. They must be standalone text (`containerId: null`) positioned near container top-left.

**Fail remediation**: List elements where text doesn't fit, suggest height/width increases

---

## Output Format

```json
{
  "validation_result": "PASS" | "NEEDS_FIX",
  "checks": [
    {
      "check_number": 1,
      "name": "Valid JSON Structure",
      "status": "PASS" | "FAIL",
      "details": "Optional description if FAIL"
    },
    ...
  ],
  "summary": {
    "elements_count": N,
    "text_bindings_count": X,
    "arrow_bindings_count": Y,
    "failed_checks": [1, 5, 7],
    "requires_cycles": true | false
  },
  "fix_priorities": [
    {
      "check": 5,
      "issue": "Arrow id-xyz has no binding in target element bound-elements",
      "fix_type": "binding_fix"
    },
    ...
  ]
}
```

## Constraints

- **Independence**: Each check runs independently; don't assume earlier checks passed
- **No fixes**: This agent only reports — json-fixer applies fixes
- **Detailed reporting**: Each failed check must have actionable remediation details
- **Cycle tracking**: If any check fails, set `requires_cycles: true` and rank fixes by impact

## Success Criteria

- All 10 checks executed
- Clear PASS/FAIL for each
- If any FAIL, detailed fix priorities provided for json-fixer
- Ready for json-fixer agent (if NEEDS_FIX) or file write (if PASS)
