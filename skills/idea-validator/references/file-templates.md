# File Templates

The canonical markdown structure for `idea.md` and `validate.md`. Read this when creating or updating either file (Setup step 2/3, and each phase's "Update `idea.md`/`validate.md`" instruction). The field content itself is defined by the phase instructions in SKILL.md — this file only owns header names, order, and placeholder format; do not restate phase guidance here when updating it.

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

## Competitive Landscape

| Competitor | Type | What They Do | Pricing / License | Traction / Health | Reuse Potential | Key Weakness |
|---|---|---|---|---|---|---|
| [Name](URL) | [Commercial / OSS / Hybrid / Adjacent / Failed] | [One sentence] | [Model or license] | [Evidence] | [Fork/build-on/plugin/reference/not suitable] | [Gap to exploit] |

### Commercial Tools & Services
[Commercial competitors, pricing, traction, and market positioning]

### Open-source Alternatives & Reuse Potential
[Maintained OSS projects, license/health, and whether to build on, fork, contribute, or avoid rebuilding]

### White Space Analysis
[What's missing in the current market]

### Differentiation Assessment
[Is the proposed differentiation real or imagined given existing commercial and open-source competitors?]

### Build vs. Base Recommendation
[Whether to build from scratch, build on existing OSS, fork, contribute, or narrow the idea]

### Failed Predecessors
[Products or OSS projects that tried and failed, stalled, or were abandoned — and why]

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
