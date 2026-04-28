# Section Templates (Step 5)

Follow this section flow when rewriting README.md. Skip sections that don't apply — but keep the core structure.

## 5.1 Hero Section

```
[badges: stars, downloads, license, build status — shields.io format]

# [Value proposition in <=10 words — NOT the project name]

[1-2 sentences: what it does + why it matters]

[**Get Started ->**](#getting-started)
```

Keep the hero to **5 lines max** (excluding badges).

## 5.2 Architecture / How It Works (VISUAL)

This is the most important section. Replace text explanations with mermaid diagrams.

```markdown
## How It Works

` ` `mermaid
graph LR
    A[Input] --> B[Process]
    B --> C[Output]
` ` `
```

**Diagram type selection:**

| Project has... | Use |
|---|---|
| A pipeline / workflow | `graph LR` or `graph TD` flowchart |
| Client-server / microservices | `graph TD` architecture diagram |
| State transitions | `stateDiagram-v2` |
| Sequential steps | `sequenceDiagram` |
| Timeline / phases | `gantt` or `timeline` |
| Class structure | `classDiagram` |

Add **at most** 2-3 sentences of context around the diagram. The diagram is the explanation.

For multi-layer projects (CLI + library + server), use multiple small diagrams rather than one huge one.

## 5.3 Key Features

Present as a **table** or **short bullet list with bold lead**. No paragraphs. Each feature: **<=15 words**. Lead with the benefit, not the mechanism.

Good:
```markdown
| Feature | What you get |
|---|---|
| Zero config | Works out of the box — no setup files |
| 10x faster builds | Incremental compilation + smart caching |
| Type safe | Catch errors at compile time, not runtime |
```

Or:
```markdown
- **Zero config** — works out of the box
- **10x faster builds** — incremental compilation + smart caching
- **Type safe** — catch errors at compile time, not runtime
```

## 5.4 Quick Start

Each command or group of commands that can run independently gets its **own code block**. This lets users copy-paste one step at a time. Only combine commands in the same block if they genuinely must run together (piped, `&&`-chained).

Good — separate blocks for independent steps:
```markdown
## Quick Start

Install:

` ` `bash
npm install my-tool
` ` `

Initialize:

` ` `bash
my-tool init
` ` `

Run:

` ` `bash
my-tool run
` ` `
```

3-5 steps max. If the project needs more, link to full docs. Show the **fastest path to "hello world"** — nothing else.

## 5.5 Usage Examples (VISUAL)

Show, don't tell. Use realistic code blocks. Before/after comparisons are powerful. Include CLI output, generated files, or screenshots if the project has visual output.

## 5.6 Comparison (optional, if alternatives exist)

Use a table — never prose paragraphs.

```markdown
| | my-tool | alternative-a | alternative-b |
|---|:---:|:---:|:---:|
| Zero config | Yes | No | Partial |
| Speed | 120ms | 3.4s | 890ms |
```

## 5.7 Social Proof (optional, only if real data exists)

One line per proof point. Never fabricate. Skip entirely if there is nothing real to show.

```markdown
2,400+ GitHub stars · 50k weekly downloads · Used at Stripe, Vercel, Linear
```

## 5.8 FAQ (optional, 3-5 entries max)

Only include if there are genuine common questions. Keep answers to 1-2 sentences.

## 5.9 Final CTA

```markdown
## Get Started

` ` `bash
npm install my-tool
` ` `

[**Read the docs ->**](./docs) · [**View examples ->**](./examples) · MIT Licensed
```

If the CTA involves multiple steps, use separate code blocks — same rule as Quick Start.

## 5.10 Technical Details (collapsed)

Preserve all original technical content in `<details>` blocks:

```markdown
<details>
<summary>API Reference</summary>

[original content]

</details>
```
