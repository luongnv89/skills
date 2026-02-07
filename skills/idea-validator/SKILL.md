---
name: idea-validator
description: Critically evaluate and enhance app ideas, startup concepts, and product proposals. Use when users ask to "evaluate my idea", "review this concept", "is this a good idea", "validate my startup idea", or want honest feedback on technical feasibility and market viability. Creates project folder with idea.md and validate.md files for documentation.
---

# Idea Validator

Critically evaluate ideas with honest feedback on market viability, technical feasibility, and actionable improvements.

## Setup

0. **Ask storage location first (breaking change)**
   - Ask user where to store generated brainstorm docs.
   - If they don’t specify, suggest default root: `/home/luongnv/workspace/ideas`.
   - If that path does not exist, ask for an existing root path.

1. **Create project folder** under chosen root: `YYYY_MM_DD_<short_snake_case_name>/`
2. **Create `idea.md`**: Document the idea and clarifications
3. **Create `validate.md`**: Document evaluation and recommendations
4. **Echo the absolute project folder path** in your response so downstream skills can auto-pick it.

If no idea provided in `$ARGUMENTS`, ask user to describe their concept.

## Phase 1: Clarify the Idea

Ask user (via AskUserQuestion):
- What problem does this solve? Who has this pain?
- Who is your target user? Be specific.
- What makes this different from existing solutions?
- What does success look like in 6-12 months?

Update `idea.md` with responses.

## Phase 2: Gather Technical Context

Ask user:
- Preferred tech stack?
- Timeline and team size?
- Budget situation (bootstrapped/funded/side project)?
- Existing assets (code, designs, research)?

Update `idea.md` technical section.

## Phase 3: Critical Evaluation

Evaluate honestly and update `validate.md`:

**Market Analysis:**
- Similar existing products
- Market size and competition
- Unique differentiation

**Demand Assessment:**
- Evidence people will pay
- Problem urgency level

**Feasibility:**
- Can this ship in 2-4 weeks MVP?
- Minimum viable features
- Complex dependencies?

**Monetization:**
- Clear revenue path?
- Willingness to pay?

**Technical Risk:**
- Buildable with stated constraints?
- Key technical risks?

**Verdict:** `Build it` / `Maybe` / `Skip it`

**Ratings (1-10):**
- Creativity
- Feasibility
- Market Impact
- Technical Execution

## Phase 4: Improvements

Update `validate.md` with:

- **How to Strengthen**: Specific, actionable improvements
- **Enhanced Version**: Reworked, optimized concept
- **Implementation Roadmap**: Phased approach (if applicable)

## Tone

- **Brutally honest**: Don't sugarcoat fatal flaws
- **Constructive**: Every criticism includes a suggestion
- **Specific**: Concrete examples, not vague feedback
- **Balanced**: Acknowledge strengths alongside weaknesses

## README Maintenance (when running inside ideas repo)

If the current working directory looks like the root of an `ideas` repo (contains `README.md` + multiple `YYYY_MM_DD_*` idea folders):
- After creating/updating `idea.md` + `validate.md`, update the repo index table by running:
  - `python3 scripts/update_readme_ideas_index.py` (if the script exists)

If the script does not exist, update `README.md` manually by inserting/updating an `## Ideas index` table with:
- link to each `idea.md`
- PRD/tasks status
- verdict link to `validate.md`

## Output Summary

After all phases:
1. Confirm folder/files created
2. State verdict and key ratings
3. Top 3 strengths, top 3 concerns
4. Single most important next step

## File Templates

### idea.md
```markdown
# Idea: [Name]

## Original Concept
[From $ARGUMENTS]

## Clarified Understanding
[After Phase 1]

## Target Audience
[Specific user profile]

## Goals & Objectives
[Success criteria]

## Technical Context
- Stack:
- Timeline:
- Budget:
- Constraints:

## Discussion Notes
[Updates from conversation]
```

### validate.md
```markdown
# Validation: [Name]

## Quick Verdict
**[Build it / Maybe / Skip it]**

## Why
[2-3 sentence explanation]

## Similar Products
[Competitors]

## Differentiation
[Unique angle]

## Strengths
-

## Concerns
-

## Ratings
- Creativity: /10
- Feasibility: /10
- Market Impact: /10
- Technical Execution: /10

## How to Strengthen
[Actionable improvements]

## Enhanced Version
[Optimized concept]

## Implementation Roadmap
[Phased approach]
```
