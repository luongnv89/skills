# Supported Diagram Types

This reference covers all supported visualization types, when to use each, and how to structure them in Excalidraw elements.

## Table of Contents

1. [Flow & Process](#flow--process)
2. [Architecture & Systems](#architecture--systems)
3. [Data & Relationships](#data--relationships)
4. [Planning & Timeline](#planning--timeline)
5. [Comparison & Analysis](#comparison--analysis)
6. [Data Visualization](#data-visualization)
7. [UX & Design](#ux--design)
8. [Custom & Freeform](#custom--freeform)

---

## Flow & Process

### Flowchart
**When**: Showing step-by-step processes, algorithms, decision trees.
**Elements**: Rectangles (steps), diamonds (decisions), ellipses (start/end), arrows (flow).
**Layout**: Top-to-bottom or left-to-right. Decision branches split horizontally.
```
[Start] → [Step 1] → <Decision?> → Yes → [Step 2] → [End]
                          ↓ No
                      [Step 3]
```

### Sequence Diagram
**When**: Showing interactions between actors/systems over time.
**Elements**: Rectangles (actors at top), dashed vertical lines, horizontal arrows (messages), thin rectangles (activation bars).
**Layout**: Actors spaced horizontally. Messages flow top-to-bottom chronologically.
```
[Actor A]     [Actor B]     [Actor C]
    |             |             |
    |---request-->|             |
    |             |---forward-->|
    |             |<--response--|
    |<--result----|             |
```

### Swimlane Diagram
**When**: Showing process flow across different departments/roles/systems.
**Elements**: Large rectangles (lanes with headers), process nodes inside lanes, arrows crossing lanes.
**Layout**: Horizontal lanes stacked vertically. Process flows left-to-right within and across lanes.

### State Machine
**When**: Showing states and transitions of a system/object.
**Elements**: Rounded rectangles (states), arrows with labels (transitions), filled circle (initial state), bullseye (final state).
**Layout**: Arrange states in a logical flow. Group related states.

### Activity Diagram
**When**: Showing parallel activities, forks, and joins.
**Elements**: Rounded rectangles (activities), diamonds (decisions), thick horizontal bars (fork/join), arrows.
**Layout**: Top-to-bottom with parallel branches side by side.

---

## Architecture & Systems

### System Architecture
**When**: Showing high-level system components and their connections.
**Elements**: Large rectangles (systems/services), smaller rectangles inside (components), arrows (data flow/communication).
**Layout**: Layered — clients at top, services in middle, data stores at bottom.

### Microservice Diagram
**When**: Showing service-to-service communication.
**Elements**: Rectangles (services), cylinders (databases — use rectangle with rounded top), arrows with protocol labels (HTTP, gRPC, events).
**Layout**: Arrange by domain. API gateway at top, services in middle, shared infra at bottom.

### Network Topology
**When**: Showing network infrastructure.
**Elements**: Rectangles/ellipses (devices), lines (connections), dashed rectangles (subnets/zones).
**Layout**: Hierarchical — internet at top, firewalls, then internal zones.

### Cloud Architecture
**When**: Showing cloud infrastructure (AWS, GCP, Azure).
**Elements**: Rectangles with labels (cloud services), dashed rectangles (VPCs, regions), arrows (data flow).
**Layout**: Group by region/VPC. Show external traffic entering from top.

### C4 Model
**When**: Showing software architecture at different zoom levels.
**Levels**:
- **Context**: System in center, users and external systems around it
- **Container**: Applications, databases, file systems within the system boundary
- **Component**: Internal modules within a container
**Elements**: Rectangles with title + description text, person shapes (rectangle with small ellipse head), dashed boundary rectangles.

### Deployment Diagram
**When**: Showing where software runs.
**Elements**: 3D-ish rectangles (servers/nodes), rectangles inside (deployed components), arrows (communication).
**Layout**: Group by environment or physical location.

---

## Data & Relationships

### ER Diagram (Entity-Relationship)
**When**: Showing database schema.
**Elements**: Rectangles (entities with field lists), lines/arrows with cardinality labels (1, *, 1..*, etc.).
**Layout**: Related entities close together. Primary entities in center.
**Text**: Use monospace font (fontFamily: 3) for field names. Bold key fields.

### Class Diagram
**When**: Showing OOP structure.
**Elements**: Rectangles divided into 3 sections (name, attributes, methods), arrows (inheritance, composition, association).
**Layout**: Parent classes above children. Related classes adjacent.
**Arrows**: Open triangle head = inheritance, filled diamond = composition, open diamond = aggregation.

### Dependency Graph
**When**: Showing module/package dependencies.
**Elements**: Rectangles (modules), arrows pointing from dependent to dependency.
**Layout**: Tree or layered graph. Root/entry points at top.

### Mind Map
**When**: Brainstorming, organizing ideas around a central topic.
**Elements**: Central ellipse/rectangle (main topic), branches (lines), smaller shapes (subtopics).
**Layout**: Central node in middle. Branches radiate outward. Use different colors per branch.

### Tree Structure
**When**: Showing hierarchies — file systems, taxonomies, decision trees.
**Elements**: Rectangles (nodes), lines (parent-child).
**Layout**: Root at top, children below. Center children under parents.

### Org Chart
**When**: Showing organizational hierarchy.
**Elements**: Rectangles (people/roles with name + title), lines (reporting).
**Layout**: CEO at top, expanding downward. Center subordinates under managers.

---

## Planning & Timeline

### Gantt Chart (simplified)
**When**: Showing project schedule with tasks and durations.
**Elements**: Rectangles (task bars) of varying widths, text labels, vertical dashed lines (milestones), horizontal lines (time axis).
**Layout**: Tasks stacked vertically. Time flows left-to-right. Color by status or category.

### Roadmap
**When**: Showing planned features/milestones over time.
**Elements**: Horizontal lanes (categories/themes), rectangles (items), vertical lines (time markers).
**Layout**: Time flows left-to-right. Categories stacked vertically.

### Timeline
**When**: Showing events in chronological order.
**Elements**: Horizontal line (time axis), vertical ticks, rectangles/text (events), arrows pointing to timeline.
**Layout**: Horizontal flow. Events alternate above and below the timeline to avoid overlap.

### Kanban Board
**When**: Showing work items across stages.
**Elements**: Large rectangles (columns: To Do, In Progress, Done), smaller rectangles (cards) inside columns.
**Layout**: Columns side by side. Cards stacked vertically within columns.

---

## Comparison & Analysis

### Quadrant Chart
**When**: Plotting items on two axes (e.g., effort vs. impact, urgency vs. importance).
**Elements**: Large cross (two lines), axis labels (text), ellipses or rectangles (items) placed in quadrants, quadrant labels.
**Layout**: Center cross. Place items by their relative position. Label each quadrant.

### SWOT Analysis
**When**: Strategic analysis — Strengths, Weaknesses, Opportunities, Threats.
**Elements**: 2x2 grid of rectangles, header text in each, bullet points as text.
**Layout**: Fixed 2x2 grid. S(top-left), W(top-right), O(bottom-left), T(bottom-right).

### Comparison Matrix
**When**: Comparing features/options across criteria.
**Elements**: Grid of rectangles (cells), header row and column, check/cross text or colored fills.
**Layout**: Table grid. Headers shaded differently.

### Venn Diagram
**When**: Showing overlapping sets/concepts.
**Elements**: 2-3 overlapping ellipses (semi-transparent), text labels in each section and overlap.
**Layout**: Circles overlap in center. Labels in unique and shared regions.

---

## Data Visualization

### Bar Chart
**When**: Comparing values across categories.
**Elements**: Rectangles (bars), text (labels, values), lines (axes).
**Layout**: Vertical bars on horizontal axis. Or horizontal bars for many categories.

### Pie Chart (approximate)
**When**: Showing proportions of a whole.
**Elements**: Colored wedge-shapes using lines and fills (approximate with colored rectangles in a legend + a labeled circle), or use a stacked bar as alternative.
**Note**: Excalidraw doesn't have arc primitives. Use a legend-based representation or approximate with colored segments described in a circle.

### Line Chart (approximate)
**When**: Showing trends over time.
**Elements**: Lines connecting data points, ellipses (data points), text (axis labels), lines (axes).
**Layout**: X-axis (time) horizontal, Y-axis (value) vertical.

### Table / Grid
**When**: Showing structured data.
**Elements**: Rectangles (cells), text inside cells, thicker borders for headers.
**Layout**: Fixed grid. Header row colored differently.

---

## UX & Design

### Wireframe
**When**: Sketching UI layouts.
**Elements**: Rectangles (containers, buttons, inputs), text (labels, placeholders), lines (dividers).
**Layout**: Use device frame (rectangle at standard ratio). Arrange elements per standard UI patterns.
**Style**: Use roughness: 2 for hand-drawn feel. Gray fills for placeholders.

### User Flow
**When**: Showing user journey through an app/website.
**Elements**: Rectangles (screens/pages), diamonds (decisions), arrows (navigation).
**Layout**: Left-to-right or top-to-bottom flow. Branch on decisions.

### Sitemap
**When**: Showing website/app page hierarchy.
**Elements**: Rectangles (pages), lines (navigation hierarchy).
**Layout**: Home page at top, sections below, pages below sections. Tree structure.

---

## Custom & Freeform

For any diagram that doesn't fit the above categories:
1. Break the concept into nodes (things) and edges (relationships)
2. Choose shapes that semantically match (rectangles for containers, ellipses for concepts, diamonds for decisions)
3. Choose a layout pattern: hierarchical, radial, grid, or flow
4. Apply consistent styling and spacing
