---
name: readme-to-landing-page
description: "Transform a project README.md into a conversion-optimized landing page using PAS, AIDA, or StoryBrand frameworks — hero, value prop, how it works, quick start, and CTA in pure GitHub-renderable markdown."
effort: high
license: MIT
metadata:
  version: 2.0.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# README to Landing Page

Transform a project's README.md into a concise, visual, developer-friendly landing page.

## Core Principle: Show, Don't Tell

Developers skim — they don't read walls of text. The output README must:

- **Prefer visuals over prose** — use mermaid diagrams for architecture, workflows, data flow
- **Be concise** — every sentence must earn its place; cut ruthlessly
- **Be scannable** — badges, tables, code blocks, diagrams; minimize paragraphs
- **Be direct** — lead with what matters, skip the preamble
- **No emoji** — never use emoji in headings, body text, badges, or section labels

If something can be a diagram, make it a diagram. If something can be a table, make it a table. If something can be a one-liner, don't write three sentences.

## Anti-Slop Rules

AI-generated READMEs have predictable tells that make developers distrust the content. The output must avoid all of these patterns. This matters because slop signals "nobody reviewed this" and kills credibility.

**Banned phrases** — never write these or close variants:

| Pattern | Why it's slop | Write instead |
|---|---|---|
| "Whether you're a ... or a ..." | Fake inclusivity, says nothing | Name the primary audience directly |
| "In today's fast-paced..." | Generic filler | Cut entirely |
| "Seamless/seamlessly" | Meaningless modifier | Describe what actually happens |
| "Robust/robust solution" | Empty adjective | State the specific capability |
| "Leverage/utilize" | Jargon for "use" | "use" |
| "Cutting-edge/state-of-the-art" | Unsubstantiated claim | Cite the specific technique or benchmark |
| "Elevate/supercharge/turbocharge" | Hype with no content | State the measurable improvement |
| "Dive deep/deep dive" | Padding | Cut or replace with "details" |
| "Harness the power of" | Filler | Name what it does |
| "It's worth noting that" | Throat-clearing | Cut — just state the thing |
| "Streamline your workflow" | Generic promise | Describe the specific workflow change |
| "Comprehensive solution" | Says nothing | State what it covers |
| "Game-changer/revolutionary" | Unearned superlative | Let the reader decide |
| "Look no further" | Salesy | Cut entirely |
| "Say goodbye to X" | Cliche | State what the tool does instead |

**Structural slop to avoid:**

- Padding paragraphs that repeat the headline in different words
- "Introduction" sections that delay the actual content
- Multiple sentences saying the same thing for emphasis
- Rhetorical questions ("Tired of X? Want to Y?")
- Exclamation marks for artificial enthusiasm
- Emoji in headings or body text
- Vague benefit claims without specifics ("saves you time", "boosts productivity")
- Filler transitions ("Furthermore", "Moreover", "Additionally", "In conclusion")

**The test:** Read each sentence and ask "does this give the reader information they didn't already have?" If not, cut it.

## Repo Sync Before Edits (mandatory)

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If working tree is dirty: `git stash push -u -m "pre-sync"`, sync, then `git stash pop`.
If `origin` is missing or conflicts occur, stop and ask the user.

## Workflow

### Step 1: Gather Context

Read project files to build a picture:

| File | Purpose |
|---|---|
| `README.md` | Source material (required) |
| `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` | Name, description, version |
| `CHANGELOG.md` | Momentum signals |
| `LICENSE` | Risk reversal ("MIT licensed") |
| `docs/` | Existing detailed docs to preserve |

Also check: GitHub stars, forks, download stats, notable users. If purpose or audience is unclear, ask.

### Step 2: Identify Audience & Value Prop

Determine these three things — write them down before proceeding:

1. **Who** — primary audience (developers, data scientists, ops teams, etc.)
2. **Pain** — what's frustrating about the status quo
3. **Benefit** — one sentence, becomes the H1 headline

### Step 3: Select Framework

| Project Type | Framework | Approach |
|---|---|---|
| CLI tools, libraries, infra | **PAS** | Problem → Agitate → Solution |
| Apps, platforms, end-user products | **AIDA** | Attention → Interest → Desire → Action |
| Strong narrative / user request | **StoryBrand** | Hero → Guide → Plan → CTA |

Tell the user which you picked. Let them override.

### Step 4: Back Up Original

```bash
cp README.md README.backup.md
```

### Step 5: Rewrite README.md

Follow this section flow. Skip sections that don't apply — but keep the core structure.

#### 5.1 Hero Section

```
[badges: stars, downloads, license, build status — shields.io format]

# [Value proposition in ≤10 words — NOT the project name]

[1-2 sentences: what it does + why it matters]

[**Get Started →**](#getting-started)
```

Keep the hero to **5 lines max** (excluding badges).

#### 5.2 Architecture / How It Works (VISUAL)

This is the most important section. Replace text explanations with mermaid diagrams.

Use the right diagram type for the project:

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

Add **at most** 2-3 sentences of context around the diagram — not more. The diagram is the explanation.

If the project has multiple layers (e.g., CLI + library + server), use multiple small diagrams rather than one huge one.

#### 5.3 Key Features

Present as a **table** or **short bullet list with bold lead**. No paragraphs.

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

Bad (too wordy):
```markdown
## Features

Our tool provides a zero-configuration experience that allows you to get started
without any setup files. It also features builds that are up to 10x faster thanks
to incremental compilation and smart caching strategies...
```

Each feature: **≤15 words**. Lead with the benefit, not the mechanism.

#### 5.4 Quick Start

Each command or group of commands that can run independently gets its **own code block**. This lets users copy-paste one step at a time without editing. Only combine commands in the same block if they genuinely must run together (e.g., piped commands, or commands joined with `&&`).

Good — separate blocks for independent steps:
```markdown
## Quick Start

Install:

` ` `bash
npm install my-tool
` ` `

Initialize a new project:

` ` `bash
my-tool init
` ` `

Run:

` ` `bash
my-tool run
` ` `
```

Bad — one block forcing the user to manually select lines:
```markdown
## Quick Start

` ` `bash
npm install my-tool
my-tool init
my-tool run
` ` `
```

Commands that depend on each other and run as a unit can share a block:
```markdown
` ` `bash
cd my-project && my-tool init
` ` `
```

3-5 steps max. If the project needs more, link to full docs. Show the **fastest path to "hello world"** — nothing else.

#### 5.5 Usage Examples (VISUAL)

Show, don't tell. Use code blocks with realistic examples:

```markdown
## Usage

` ` `typescript
// Before: 12 lines of boilerplate
const result = myTool.do(input)
// After: done
` ` `
```

If the project has a visual output (CLI output, generated files, screenshots), include them. Before/after comparisons are powerful.

#### 5.6 Comparison (optional, if alternatives exist)

Use a table — never prose paragraphs:

```markdown
## Comparison

| | my-tool | alternative-a | alternative-b |
|---|:---:|:---:|:---:|
| Zero config | Yes | No | Partial |
| Speed | 120ms | 3.4s | 890ms |
| Bundle size | 12kb | 145kb | 67kb |
```

#### 5.7 Social Proof (optional, only if real data exists)

One line per proof point. Never fabricate.

```markdown
## Adoption

2,400+ GitHub stars · 50k weekly downloads · Used at Stripe, Vercel, Linear
```

Skip entirely if there's nothing real to show.

#### 5.8 FAQ (optional, 3-5 entries max)

Only include if there are genuine common questions. Keep answers to 1-2 sentences.

#### 5.9 Final CTA

```markdown
## Get Started

` ` `bash
npm install my-tool
` ` `

[**Read the docs →**](./docs) · [**View examples →**](./examples) · MIT Licensed
```

If the CTA involves multiple steps (e.g., install then run), use separate code blocks — same rule as Quick Start.

#### 5.10 Technical Details (collapsed)

Preserve all original technical content in `<details>` blocks:

```markdown
<details>
<summary>API Reference</summary>

[original content]

</details>

<details>
<summary>Configuration</summary>

[original content]

</details>
```

### Step 6: Self-Review Checklist

Before presenting to the user, verify:

| Check | Rule |
|---|---|
| Code blocks | Each independently-runnable command is in its own block (copy-paste friendly) |
| Mermaid diagrams | ≥1 diagram showing how the project works |
| Hero length | ≤5 lines (excluding badges) |
| Feature descriptions | ≤15 words each |
| Quick Start | ≤5 commands |
| Paragraphs | No paragraph exceeds 3 sentences |
| Total prose | Diagrams + tables + code ≥ 50% of content |
| Original content | All preserved in `<details>` blocks |
| Fabricated data | None — real numbers or placeholders only |
| No emoji | Zero emoji anywhere in the output |
| No slop phrases | None of the banned phrases from Anti-Slop Rules |
| No filler | Every sentence adds information the reader didn't have |
| No rhetorical questions | No "Tired of X?" or "Want to Y?" patterns |

If any check fails, fix it before presenting.

### Step 7: Present to User

Briefly explain:
1. Framework chosen
2. Where original content lives (`README.backup.md` + collapsed sections)

Ask for feedback. Do NOT commit unless asked.

## Expected Output

For a CLI tool called "fastbuild", the rewritten README.md opens with:

```markdown
![stars](https://img.shields.io/github/stars/acme/fastbuild)
![license](https://img.shields.io/badge/license-MIT-blue)

# Incremental builds in under a second

fastbuild watches your source tree and recompiles only changed modules —
no config files, no daemon, no warm-up time.

[**Get Started →**](#getting-started)

## How It Works

` ` `mermaid
graph LR
    A[Source files] --> B[fastbuild watcher]
    B --> C{Changed?}
    C -->|Yes| D[Compile changed modules]
    C -->|No| E[Skip]
    D --> F[Output bundle]
` ` `

| Feature | What you get |
|---|---|
| Zero config | Works out of the box — no setup files |
| Incremental | Recompiles only changed modules |
| Fast | < 1s on codebases with 10k+ files |
```

Original content is preserved in `README.backup.md` and in `<details>` blocks at the end of the new README.

## Edge Cases

- **No README.md found**: Offer to create one from scratch using project manifest files (package.json, pyproject.toml, etc.).
- **README is already marketing-style**: Offer targeted section-by-section refinements instead of a full rewrite; preserve what's already working.
- **Insufficient context to determine value prop**: Ask the user directly — what it does, who it's for, and what problem it solves — before proceeding with the rewrite.
- **No real social proof or adoption data**: Skip the social proof section entirely; never fabricate stars, download counts, or user testimonials.
- **Highly technical README (API reference, config specs)**: Preserve all technical content in `<details>` blocks; the landing page sections should be brief and scannable rather than comprehensive.
- **Project with no visual output**: Focus on code-before/after comparisons and terminal output snippets instead of screenshots.
- **README longer than 300 lines**: Preserve the full original in README.backup.md and summarize the original technical sections as collapsed `<details>` blocks to keep the rewritten README scannable.

## Acceptance Criteria

- [ ] Original README is backed up to `README.backup.md` before any rewrite
- [ ] Rewritten README uses one of the three frameworks (PAS, AIDA, or StoryBrand) and names which one was chosen
- [ ] H1 is the value proposition (≤10 words), not the project name
- [ ] At least one mermaid diagram shows how the project works
- [ ] Hero section is ≤5 lines (excluding badges)
- [ ] Each feature description is ≤15 words
- [ ] Quick Start section has ≤5 steps; each independently-runnable command is in its own code block
- [ ] No banned slop phrases appear in the output
- [ ] All original technical content is preserved in `<details>` blocks
- [ ] No fabricated data — real numbers or `[placeholder]` markers only
- [ ] Zero emoji in the output
- [ ] Self-review checklist (13 checks) passes before presenting to the user

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Phase-specific checks

**Step 1-2 — Context Gathering**
```
◆ Context Gathering (step 1 of 7 — project analysis)
··································································
  Project files read:       √ pass
  Value prop identified:    √ pass (one-sentence benefit drafted)
  Audience defined:         √ pass (primary audience named)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 3 — Framework Selection**
```
◆ Framework Selection (step 3 of 7 — copywriting framework)
··································································
  Framework chosen:         √ pass (PAS | AIDA | StoryBrand)
  Sections mapped:          √ pass (section flow planned)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Steps 4-5 — Rewrite**
```
◆ Rewrite (step 5 of 7 — README transformation)
··································································
  Backup created:           √ pass (README.backup.md written)
  Sections written:         √ pass (hero → CTA flow complete)
  CTAs placed:              √ pass (primary CTA in hero + footer)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 6-7 — Review**
```
◆ Review (step 6 of 7 — quality gate)
··································································
  Checklist passed:         √ pass (13/13 checks green)
  User approved:            √ pass
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

## Guidelines

- **One code block per copy-paste unit.** Commands that can run independently must be in separate code blocks so the user can click-to-copy one step at a time. Only combine commands that must run together (piped, `&&`-chained, or tightly coupled). This is the main objective — the output should be copy-paste friendly.
- **Never fabricate data.** Use real numbers or leave `[placeholder]` markers.
- **Respect the project's voice.** A security tool ≠ a startup pitch.
- **H1 = value proposition**, not the project name.
- **Preserve all original content** in collapsed sections.
- **One primary audience.** Don't try to speak to everyone.
- **When in doubt, cut text.** A shorter README that gets read beats a longer one that doesn't.

## Error Handling

- **No README.md found** → Offer to create from scratch using project files.
- **Already marketing-style** → Offer targeted refinements, not full rewrite.
- **Insufficient context** → Ask: what it does, who it's for, what problem it solves.
