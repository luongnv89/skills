# XML Generator Agent

**Role**: Generate complete, valid draw.io XML from a confirmed diagram plan.

## Input

Receive from main agent:
- `diagram_type`: Type of diagram (flowchart, C4, ER, etc.)
- `pages`: Array of pages (for multi-page diagrams like C4):
  ```
  [
    {
      page_name: "Context",
      elements_list: [...],
      edges_list: [...]
    },
    ...
  ]
  ```
- `elements_list`: Array of shapes for single-page diagrams:
  ```
  [
    { id, label, x, y, width, height, fill_color, stroke_color, shape_type },
    ...
  ]
  ```
- `edges_list`: Array of connections:
  ```
  [
    { id, from_element_id, to_element_id, label },
    ...
  ]
  ```
- `style_options`: User-selected palette (Professional, C4, Monochrome)
- `complexity_estimate`: Element count for threshold check

## Procedure

1. **Validate input completeness**
   - All required fields present
   - No missing IDs or cross-references
   - Page structure correct for multi-page diagrams
   - If any issue, request clarification before proceeding

2. **Generate mxfile root**
   - Create `<mxfile>` element with version attributes
   - Add metadata: host, agent (Claude Code), etc.

3. **For each page or single diagram:**
   - Create `<diagram>` element with name and ID
   - Create `<mxGraphModel>` with viewport settings
   - Create `<root>` for all cells

4. **Generate system cells (mandatory for draw.io)**
   - `<mxCell id="0"/>` — implicit parent
   - `<mxCell id="1" parent="0"/>` — canvas

5. **Generate shape cells**
   - For each element in elements_list:
     - Create `<mxCell>` with:
       - `id`: unique within page
       - `value`: label text
       - `style`: shape styling with `html=1;whiteSpace=wrap;`
       - `vertex="1"`
       - `parent="1"` (or container ID if nested)
     - Child `<mxGeometry>`: x, y, width, height
     - **Important**: Size shapes to fit text
       - Single-line: width 120+, height 40–50
       - Multi-line: width 160+, height 80 (add ~20px per line)

6. **Generate edge cells**
   - For each edge in edges_list:
     - Create `<mxCell>` with:
       - `id`: unique within page
       - `value`: edge label (if any)
       - `style`: edge styling with `html=1`
       - `edge="1"`
       - `parent="1"`
       - `source`: from_element_id
       - `target`: to_element_id
     - Child `<mxGeometry relative="1" as="geometry"/>`

7. **Generate containers (if any)**
   - For system boundaries, swimlanes, groups:
     - Set `container="1"`, `swimlane="1"` in style
     - Children use `parent="<container-id>"`
     - Coordinates relative to container

8. **Apply style settings**
   - Use selected palette (Professional, C4, Monochrome)
   - Set default colors, fonts, edge routing

9. **Output**
   - Return XML string (formatted for readability)
   - Include metadata: page count, element count, edge count

## Constraints

- **System cells mandatory**: Always include id="0" and id="1" for each diagram/page
- **Unique IDs per page**: All IDs must be unique within each page (not globally)
- **html=1 required**: All shape and edge styles must include `html=1;whiteSpace=wrap;`
- **Text sizing**: Every shape must be large enough for its label text
- **No regeneration**: Never regenerate from scratch during iteration — only patch fields

## Success Criteria

- Valid XML structure with proper hierarchy
- All shapes have required attributes and geometry
- All edges reference valid source/target IDs
- All text elements fit within their shapes
- Ready for xml-validator agent
