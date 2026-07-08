# Style guidelines, iteration, and subagent architecture

## Style Guidelines

### Default style: Hand-drawn
- `roughness`: 1 (the natural, expressive Excalidraw look)
- `strokeWidth`: 2
- `fontFamily`: 1 (Virgil — hand-writing font, the Excalidraw signature style)
- Colors: choose freely based on what communicates the diagram's meaning well — light or dark theme, vibrant or muted.
- Use color purposefully to distinguish categories, layers, or semantic roles.

### Style variants
- **Sketchy** (`roughness: 2`, `fontFamily: 1`): wireframes, brainstorming, very informal diagrams.
- **Clean/geometric** (`roughness: 0`, `fontFamily: 2`): precise, formal, presentation-ready.
- **Code/technical** (`roughness: 0`, `fontFamily: 3`): diagrams with code snippets or technical labels.
- **Monochrome**: when the user wants something printable or minimal.

Adapt the style to the diagram's purpose and the user's intent. The hand-drawn default works well for most cases — override when the content clearly calls for something different.

## Iteration

After generating the first version, the user may request changes. Common requests:

- **"Add X"** — add new nodes/connections.
- **"Remove Y"** — remove elements (don't just set `isDeleted: true`, actually remove them from the array).
- **"Change layout"** — rearrange positions.
- **"Change style"** — adjust colors, roughness, fonts.
- **"Make it bigger/smaller"** — scale node sizes and gaps.
- **"More detail"** — break high-level nodes into sub-components.

When iterating, read the existing file, modify the JSON, and rewrite. Preserve element IDs that haven't changed so the user's manual edits (if any) in Excalidraw remain compatible.

## Subagent Architecture

When diagram complexity exceeds 30 elements, spawn a review loop to ensure quality without single-context degradation.

### Complexity threshold check (end of Phase 2)
- **Small** (< 10 elements): proceed inline (Phases 3-4 in main agent context).
- **Medium** (10-30 elements): proceed inline with careful validation.
- **Large** (> 30 elements): spawn subagent review loop (recommended).

### Phase 3: Generate → `agents/json-generator.md`
- Receives: diagram type, elements list, arrows list, style options, complexity estimate.
- Outputs: complete Excalidraw JSON object with all required fields per element.
- Key constraint: shapes must be sized to fit all bound text (Check 10).

### Phase 4: Validate → review loop (max 3 cycles)
1. **Cycle 1: fresh validation** — spawn `agents/json-validator.md` with the generated JSON. Outputs structured validation report with PASS/FAIL for all 10 checks.
2. **If NEEDS_FIX**: spawn `agents/json-fixer.md` with the validation report. Outputs patched JSON (never regenerated from scratch). Apply only targeted fixes; skip semantic/structure issues (those require generator revision).
3. **If still NEEDS_FIX and cycle < 3**: return to step 1 (re-validate) with cycle++.
4. **If cycle == 3 or PASS**: return to main agent for file write or user review.

### Fallback (Agent tool unavailable)
Execute validation inline with self-review against the 10 checks. Less rigorous but functional.

## Edge cases (extended)

- **Complex diagram (30+ elements)**: spawn the subagent review loop above. Cap at 3 fix cycles before surfacing remaining issues to the user.
- **Text-heavy input (long labels, multi-line node text)**: apply Check 10 strictly — `min_shape_height = line_count * fontSize * 1.25 + 40`. Garbled text is the most common failure mode.
- **Ambiguous relationships**: if connections between entities are unclear, ask the user to clarify direction and cardinality before generating rather than guessing and requiring regeneration.
- **User says "just do it"**: use sensible defaults (hand-drawn style, roughness 1, Virgil font, best-fit layout) and skip the proposal step.
- **Large diagram with overlapping nodes**: apply Check 7 — shift overlapping elements by adjusting `x`/`y` coordinates. Never allow bounding boxes to overlap by more than 10px outside of containers.
- **Iteration request on existing file**: read the existing `.excalidraw` file first, preserve unchanged element IDs, apply only the requested modifications, then rewrite the file.
