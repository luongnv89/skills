# Idea Validator

> Critically evaluate app ideas, startup concepts, and product proposals with market viability analysis.

## Highlights

- Multi-phase evaluation: clarify idea, gather context, critical analysis, improvements
- Rate creativity, feasibility, impact, and technical execution
- Deliver a clear verdict: Build it, Maybe, or Skip it
- Generate improvement suggestions and enhanced roadmap

## When to Use

| Say this... | Skill will... |
|---|---|
| "Evaluate my idea" | Run full validation with ratings |
| "Is this a good idea?" | Assess market viability and feasibility |
| "Validate my startup idea" | Analyze demand, competition, and risks |
| "Review this concept" | Provide verdict with improvements |

## How It Works

```mermaid
graph TD
    A["Clarify the Idea"] --> B["Gather Technical Context"]
    B --> C["Critical Evaluation"]
    C --> D["Rate & Verdict"]
    D --> E["Suggest Improvements"]
    style A fill:#4CAF50,color:#fff
    style E fill:#2196F3,color:#fff
```

## Installation

Install via [npx (Vercel)](https://www.npmjs.com/package/skills):

```bash
npx skills add https://github.com/luongnv89/skills --skill idea-validator
```

Or via [agent-skill-manager (asm)](https://www.npmjs.com/package/agent-skill-manager):

```bash
asm install github:luongnv89/skills --skill idea-validator
```

## Usage

```
/idea-validator <idea description>
```

## Output

- `idea.md` with concept, clarifications, and technical context
- `validate.md` with verdict, ratings, market analysis, and improvement roadmap
- Updated README ideas index table with GitHub links
