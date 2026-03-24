# Excalidraw Diagram Generator

> Generate any type of diagram, chart, or visualization as Excalidraw JSON — from flowcharts to architecture diagrams to mind maps.

## Highlights

- Supports 25+ diagram types across 8 categories (flow, architecture, data, planning, comparison, charts, UX, custom)
- Interactive workflow: analyzes input, proposes visualization type with selectable options, iterates until clear
- Built-in validation: 10 automated quality checks with auto-fix before writing output
- Subagent architecture for large diagrams (30+ elements): fresh-context generator, validator, and fixer agents
- Outputs native `.excalidraw` files by default (can embed in `.md` on request)
- Automatically extracts structure from code, SQL, config files, or plain descriptions
- Multiple color palettes: professional, pastel, monochrome

## When to Use

| Say this... | Skill will... |
|---|---|
| "Draw a flowchart of user authentication" | Create a flowchart with process steps, decisions, and error paths |
| "Visualize my database schema" | Generate an ER diagram from your SQL or schema description |
| "Sketch the system architecture" | Build a layered architecture diagram with services and connections |
| "Create a mind map about project planning" | Produce a radial mind map with branches and sub-topics |
| "Make a sequence diagram for the API flow" | Generate actor lanes with chronological message arrows |
| "I need a Kanban board layout" | Create columns with cards for workflow visualization |

## How It Works

```mermaid
graph TD
    A["1. Understand Input"] --> B["2. Propose Options"]
    B --> C["3. Generate JSON"]
    C --> D["4. Validate (10 checks)"]
    D -->|Pass| E["Write File"]
    D -->|Fail| F["Auto-fix & Re-check"]
    F --> D
    style A fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
    style D fill:#f08c00,color:#fff
```

## Installation

Install via [npx (Vercel)](https://www.npmjs.com/package/skills):

```bash
npx skills add https://github.com/luongnv89/skills --skill excalidraw-generator
```

Or via [agent-skill-manager (asm)](https://www.npmjs.com/package/agent-skill-manager):

```bash
asm install github:luongnv89/skills:skills/excalidraw-generator
```

## Usage

```
/excalidraw-generator
```

## Supported Diagram Types

| Category | Types |
|---|---|
| Flow & Process | Flowchart, sequence diagram, swimlane, state machine, activity diagram |
| Architecture | System architecture, microservices, network topology, cloud, C4 model, deployment |
| Data & Relationships | ER diagram, class diagram, dependency graph, mind map, tree, org chart |
| Planning | Gantt chart, roadmap, timeline, Kanban board |
| Comparison | Quadrant chart, SWOT analysis, comparison matrix, Venn diagram |
| Data Visualization | Bar chart, pie chart, line chart, table/grid |
| UX/Design | Wireframe, user flow, sitemap |
| Custom | Any freeform diagram from description |

## Resources

| Path | Description |
|---|---|
| `agents/json-generator.md` | Generate Excalidraw JSON diagrams from user descriptions and requirements |
| `agents/json-validator.md` | Validate Excalidraw JSON output against schema and quality standards |
| `agents/json-fixer.md` | Repair malformed or invalid Excalidraw JSON files |
| `references/excalidraw-format.md` | Complete Excalidraw JSON schema and element reference |
| `references/diagram-types.md` | All supported diagram types with layout guidance |

## Output

Generates native `.excalidraw` files (raw JSON) by default. Can also embed in a `.md` file with a fenced code block on request.
