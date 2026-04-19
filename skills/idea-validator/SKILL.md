---
name: idea-validator
description: Evaluate app ideas and startup concepts across market viability, technical feasibility, and competitive landscape. Use when asked to validate, review, or score a product idea.
effort: max
license: MIT
metadata:
  version: 1.3.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Idea Validator

Critically evaluate ideas with honest feedback on market viability, technical feasibility, and actionable improvements.

## When to Use

Trigger this skill when the user asks to:
- Evaluate, validate, or score an app idea or startup concept
- Get honest feedback on whether an idea is worth building
- Research what competitors already exist in a space
- Turn a vague concept into a structured validation report

## Instructions

Follow the 5-phase pipeline in order: Clarify → Technical Context → Competitive Landscape Research → Critical Evaluation → Improvements. Do not skip phases or reorder them.

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Setup

0. **Resolve storage location (tool-agnostic, ask once per environment)**
   - Prefer env var `IDEAS_ROOT` if set.
   - Else use shared marker file: `~/.config/ideas-root.txt`.
   - Backward compatibility: if shared marker is missing but legacy `~/.openclaw/ideas-root.txt` exists, reuse its value and write it into `~/.config/ideas-root.txt`.
   - If no marker exists (new environment), ask user once where to store generated docs.
   - Suggested default: `~/workspace/ideas`.
   - Save chosen root to `~/.config/ideas-root.txt`.
   - Only ask again if the user explicitly asks to change location.

1. **Create project folder** under resolved root: `YYYY_MM_DD_<short_snake_case_name>/`
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

## Phase 3: Competitive Landscape Research

Before evaluating the idea, search the internet to find what already exists in the space. This grounds the analysis in real-world data instead of guessing about competitors — it prevents the user from unknowingly building something that's already been done, and reveals gaps they can exploit.

Use WebSearch to find:

**Direct competitors** — products/services solving the same problem for the same audience. Search for the core problem statement plus keywords like "app", "tool", "platform", "SaaS", "startup". Try 2-3 different search queries to cover variations (e.g., both the problem description and the solution category).

**Adjacent solutions** — products that solve a related problem or serve the same audience differently. These reveal how users currently cope without the proposed solution.

**Failed attempts** — startups or products that tried something similar and shut down. Search for "[concept] startup failed", "[concept] post-mortem", or check product directories. Understanding why predecessors failed is often more valuable than knowing who succeeded.

For each competitor found, capture:
- **Name and URL**
- **What they do** (one sentence)
- **Pricing model** (free, freemium, paid, enterprise)
- **Apparent traction** (user reviews, app store ratings, social media presence, funding if findable)
- **Key weakness or gap** the user's idea could exploit

Aim for 3-8 competitors total (direct + adjacent). If fewer than 3 are found, that's a signal — either the market is very niche (potential opportunity) or the search terms need refining.

Update `validate.md` with a **## Competitive Landscape** section containing:
1. A summary table of competitors found
2. A "white space" analysis — what's missing in the current market
3. Honest assessment: is the user's differentiation real or imagined given what exists?

If WebSearch is unavailable, note it in the report and proceed to Phase 4 with best-effort analysis based on general knowledge. Flag that the competitive section should be verified manually.

## Phase 4: Critical Evaluation

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

## Phase 5: Improvements

Update `validate.md` with:

- **How to Strengthen**: Specific, actionable improvements
- **Enhanced Version**: Reworked, optimized concept
- **Implementation Roadmap**: Phased approach (if applicable)

## Expected Output

After all phases complete, the output includes:

```
## Quick Verdict
**Build it**

## Ratings
| Dimension         | Score |
|-------------------|-------|
| Creativity        | 7/10  |
| Feasibility       | 8/10  |
| Market Impact     | 6/10  |
| Technical Execution | 8/10 |

## Top Concerns
1. Three direct competitors already exist with significant traction
2. Monetization path unclear — target users expect free tools
3. MVP scope likely exceeds 2-4 week estimate
```

## Edge Cases

- **No clear target user**: If the idea is too broad (e.g., "an app for everyone"), push back in Phase 1 — ask the user to name one specific person who has this pain today. Do not proceed to evaluation without a defined user segment.
- **Duplicate idea already exists**: If Phase 3 research finds a near-identical product, surface it immediately with evidence (URL, feature comparison) and ask whether the user still wants to proceed. Evaluation continues only if the user identifies a genuine differentiator.
- **Technical feasibility unclear**: If the idea requires unproven technology, undisclosed APIs, or capabilities the stated team cannot build, flag it as a hard blocker in Phase 4 and lower the Feasibility score accordingly. Do not give a `Build it` verdict when fundamental technical risk is unresolved.

## Acceptance Criteria

- [ ] All 5 phases are completed in order (Clarify → Technical Context → Competitive Landscape → Evaluation → Improvements)
- [ ] Competitive landscape research is performed via web search with at least 2-3 queries; competitors table populated in `validate.md`
- [ ] A clear verdict (`Build it` / `Maybe` / `Skip it`) is given with a supporting rationale
- [ ] All four ratings (Creativity, Feasibility, Market Impact, Technical Execution) are provided as scores out of 10
- [ ] `idea.md` and `validate.md` are committed and pushed to the remote repository
- [ ] GitHub links to both files are reported in the completion message

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

**Setup**
```
◆ Setup (step 1 of 6 — [idea name])
··································································
  Storage resolved:   √ pass ([path])
  Folder created:     √ pass ([YYYY_MM_DD_name/])
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 1 — Clarify**
```
◆ Clarify (step 2 of 6 — [idea name])
··································································
  Questions answered: √ pass ([N] responses collected)
  idea.md updated:    √ pass | × fail — [missing sections]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 2 — Gather Technical Context**
```
◆ Gather Technical Context (step 3 of 6 — [idea name])
··································································
  Context sources identified: √ pass ([N] inputs collected)
  Technical feasibility assessed: √ pass | × fail — [gaps noted]
  idea.md technical section updated: √ pass | × fail — [missing fields]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 3 — Competitive Landscape**
```
◆ Competitive Landscape (step 4 of 6 — [idea name])
··································································
  Web searches executed: √ pass ([N] queries run)
  Competitors found:     √ pass ([N] direct + [N] adjacent)
  Failed attempts checked: √ pass | × fail — [no results or skipped]
  validate.md updated:   √ pass | × fail — [missing sections]
  ____________________________
  Result:                PASS | FAIL | PARTIAL
```

**Phase 4 — Evaluate**
```
◆ Evaluate (step 5 of 6 — [idea name])
··································································
  Feasibility scored: √ pass ([score]/10)
  Market assessed:    √ pass | × fail — [gaps in analysis]
  validate.md updated:√ pass | × fail — [missing sections]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 5 — Improve**
```
◆ Improve (step 6 of 6 — [idea name])
··································································
  Enhancements identified:    √ pass ([N] improvements listed)
  Recommendations added:      √ pass | × fail — [what's missing]
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

## Tone

- **Brutally honest**: Don't sugarcoat fatal flaws
- **Constructive**: Every criticism includes a suggestion
- **Specific**: Concrete examples, not vague feedback
- **Balanced**: Acknowledge strengths alongside weaknesses

## README Maintenance (when running inside ideas repo)

If the current working directory looks like the root of an `ideas` repo (contains `README.md` + multiple `YYYY_MM_DD_*` idea folders):
- After creating/updating `idea.md` + `validate.md`, update `README.md` by inserting/updating an `## Ideas index` table with:
- link to each `idea.md`
- PRD/tasks status
- verdict link to `validate.md`

## Commit and push (mandatory)

After file updates are complete:
- Commit immediately with a clear message.
- Push immediately to remote.
- If push is rejected: `git fetch origin && git rebase origin/main && git push`.

Do not ask for additional push permission once this skill is invoked.

## Reporting with GitHub links (mandatory)
When reporting completion, include:
- GitHub link to `idea.md`
- GitHub link to `validate.md`
- GitHub link to `README.md` when it was updated
- Commit hash

Link format (derive `<owner>/<repo>` from `git remote get-url origin`):
- `https://github.com/<owner>/<repo>/blob/main/<relative-path>`

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

## Competitive Landscape

| Competitor | What They Do | Pricing | Traction | Key Weakness |
|---|---|---|---|---|
| [Name](URL) | [One sentence] | [Model] | [Evidence] | [Gap to exploit] |

### White Space Analysis
[What's missing in the current market]

### Differentiation Assessment
[Is the proposed differentiation real or imagined given existing competitors?]

### Failed Predecessors
[Products that tried and failed — and why]

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
