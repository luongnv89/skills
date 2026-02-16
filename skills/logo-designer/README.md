# Logo Designer

> Design professional, modern logos with automatic project context detection and multiple SVG deliverables.

## Highlights

- Analyze project type (CLI, SaaS, Startup, Enterprise, Consumer) for style selection
- Apply design principles: simplicity, scalability, memorability, versatility
- Generate 7 SVG variants (full, mark, wordmark, icon, favicon, white, black)
- Provide color specs with hex codes and Tailwind config

## When to Use

| Say this... | Skill will... |
|---|---|
| "Create a logo" | Design logo based on project analysis |
| "Design a logo for X" | Generate brand identity with SVG files |
| "Make a favicon" | Create icon and favicon variants |
| "Generate brand identity" | Full logo suite with color specs |

## How It Works

```mermaid
graph TD
    A["Analyze Project Context"] --> B["Select Design Style"]
    B --> C["Generate SVG Logos"]
    C --> D["Document Design Rationale"]
    style A fill:#4CAF50,color:#fff
    style D fill:#2196F3,color:#fff
```

## Usage

```
/logo-designer
```

## Output

- 7 SVG files in `/assets/logo/` (full, mark, wordmark, icon, favicon, white, black)
- Design rationale document with color specifications
- Brand kit suggestions with Tailwind config
