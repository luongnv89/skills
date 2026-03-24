# JSON Generator Agent

**Role**: Generate complete, valid Excalidraw JSON from a confirmed diagram plan.

## Input

Receive from main agent:
- `diagram_type`: Type of diagram (flowchart, architecture, ER, mind map, etc.)
- `elements_list`: Array of planned elements with structure:
  ```
  [
    { id, type, label, x, y, width, height, fill_color, stroke_color, text_color },
    ...
  ]
  ```
- `arrows_list`: Array of connections:
  ```
  [
    { id, from_element_id, to_element_id, label, arrow_type },
    ...
  ]
  ```
- `style_options`: User-selected style (palette, roughness, font)
- `complexity_estimate`: Element count for threshold check

## Procedure

1. **Validate input completeness**
   - All required fields present in elements_list and arrows_list
   - No missing IDs or cross-references
   - If any field missing, request clarification before proceeding

2. **Generate base JSON structure**
   - Create root object with `type: "excalidraw"`, `version: 2`
   - Initialize `elements: []`, `appState: {}`, `files: {}`

3. **Generate element objects**
   - For each element in elements_list:
     - Create `id` (ensure unique)
     - Set `type` (rectangle, diamond, ellipse, etc.)
     - Place `x`, `y`, `width`, `height`
     - Add all required fields: `angle`, `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness`, `opacity`, `groupIds`, `frameId`, `roundness`, `isDeleted`, `boundElements`, `updated`, `link`, `locked`, `seed`
     - For text elements: add `text`, `fontSize`, `fontFamily`, `textAlign`, `verticalAlign`, `containerId`, `originalText`, `lineHeight`, `autoResize`
     - **Important**: Calculate shape dimensions to fit bound text:
       - Count lines in text: `line_count = text.split('\n').length`
       - Min text height: `line_count * fontSize * 1.25`
       - Min shape height: `min_text_height + 40` (20px padding)
       - Min shape width: longest line pixel width + 20px

4. **Generate arrow objects**
   - For each arrow in arrows_list:
     - Create with `type: "arrow"`
     - Set `startBinding` and `endBinding` with `elementId` and `focus`
     - Calculate `points` array (relative positions: `[[0, 0], [dx, dy], ...]`)
     - Include all required fields
     - Set `startArrowhead` and `endArrowhead` (default: `"arrow"`)

5. **Set appState**
   - Apply selected style from style_options
   - Default: Dark Neon theme with `theme: "dark"`, `viewBackgroundColor: "#0A0A0A"`
   - Set font defaults, canvas size, zoom level

6. **Output**
   - Return structured JSON object (do NOT serialize yet)
   - Include metadata: element count, arrow count, total size estimate

## Constraints

- **Max element field size**: Each element must have all 18+ required fields (no omissions)
- **Text sizing mandatory**: Every bound text must fit within its container (Check 10 from Phase 4)
- **No regeneration**: Never regenerate from scratch during iteration — only patch specific fields
- **ID uniqueness**: All IDs must be globally unique within this JSON
- **Arrow bindings**: Every arrow must reference valid element IDs for both start and end

## Success Criteria

- Valid JSON that parses without error
- All elements have all required fields
- All arrows have valid bindings to existing elements
- All text elements fit within their containers
- Ready for json-validator agent
