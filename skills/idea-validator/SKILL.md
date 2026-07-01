---
name: "idea-validator"
description: "Validate app/startup ideas with market, feasibility, commercial, and open-source competitor analysis. Use when asked to evaluate, validate, or score a product idea. Don't use for PRDs, go-to-market plans, or investor decks."
license: MIT
effort: max
metadata:
  version: 1.5.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Idea Validator

Critically evaluate ideas with honest feedback on market viability, technical feasibility, and actionable improvements.

## When to Use

Trigger this skill when the user asks to:
- Evaluate, validate, or score an app idea or startup concept
- Get honest feedback on whether an idea is worth building
- Research what competitors already exist in a space, including commercial tools/services and open-source alternatives
- Turn a vague concept into a structured validation report

## Instructions

Follow the 5-phase pipeline in order: Clarify → Technical Context → Competitive Landscape Research → Critical Evaluation → Improvements. Do not skip phases or reorder them. One conditional branch applies on top of the pipeline: if the working directory is the root of an `ideas` repo, also do the README Maintenance step below after each file update — see that section for the detection rule.

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

Before evaluating the idea, perform live web research to find what already exists in the space. Do not rely on memory or training data for market, pricing, traction, competitor, or open-source claims — web search is mandatory so the report reflects the most up-to-date information.

Use the available web search tool (`WebSearch`, `web_search`, or equivalent) to run at least 4-6 varied queries covering:

**Commercial tools/services** — SaaS products, mobile apps, enterprise platforms, paid APIs, agencies, marketplaces, and other commercial offerings solving the same or adjacent problem. Search the core problem statement plus keywords like "app", "tool", "platform", "SaaS", "startup", "pricing", "alternative", and audience-specific terms.

**Open-source solutions** — GitHub/GitLab repositories, self-hosted tools, packages, frameworks, templates, and OSS alternatives that solve the same problem or provide a strong foundation. Search with terms like "open source", "GitHub", "self-hosted", "OSS", "alternative", "library", and relevant package registry names. If no credible OSS option is found, document the queries tried and state that no maintained open-source baseline was found.

**Adjacent solutions** — products or projects that solve a related problem or serve the same audience differently. These reveal how users currently cope without the proposed solution.

**Failed attempts** — startups, products, or OSS projects that tried something similar and stalled, shut down, or were abandoned. Search for "[concept] startup failed", "[concept] post-mortem", "[concept] abandoned GitHub", or check product directories. Understanding why predecessors failed is often more valuable than knowing who succeeded.

For each competitor or OSS project found, capture:
- **Name and URL**
- **Type** (commercial, open-source, hybrid, adjacent, failed/abandoned)
- **What they do** (one sentence)
- **Pricing or license** (free, freemium, paid, enterprise, OSS license if available)
- **Traction or health** (reviews, ratings, users, funding, GitHub stars/forks, recent commits, open issues, community activity)
- **Key weakness or gap** the user's idea could exploit
- **Reuse/build-on potential** for open-source options (fork, plugin, library dependency, contribution path, or not suitable)

Aim for 3-8 total competitors and at least one commercial and one open-source search path. If fewer than 3 credible results are found, that's a signal — either the market is niche, the terms need refining, or the idea may be framed in unfamiliar language.

When an open-source solution already solves a meaningful part of the idea, evaluate more carefully before recommending a greenfield build. Compare license fit, maintenance health, architecture, extensibility, deployment burden, community, and whether the user should build on it, fork it, contribute to it, or differentiate sharply instead of redoing it.

Update `validate.md` with a **## Competitive Landscape** section containing:
1. A summary table of commercial and open-source competitors found
2. An **Open-source Alternatives & Reuse Potential** analysis
3. A "white space" analysis — what's missing in the current market
4. Honest assessment: is the user's differentiation real or imagined given what exists?
5. A build-vs-base recommendation when OSS foundations exist

If web search is unavailable or blocked, stop and ask the user before proceeding. Do not silently replace live research with general knowledge.

## Phase 4: Critical Evaluation

Evaluate honestly and update `validate.md`:

**Market Analysis:**
- Similar commercial products and open-source solutions
- Market size and competition
- Unique differentiation

**Demand Assessment:**
- Evidence people will pay
- Problem urgency level

**Feasibility:**
- Can this ship in 2-4 weeks MVP?
- Minimum viable features
- Complex dependencies?
- Could an existing OSS project be reused, forked, extended, or used as a reference instead of starting from scratch?

**Monetization:**
- Clear revenue path?
- Willingness to pay?

**Technical Risk:**
- Buildable with stated constraints?
- Key technical risks?
- License, maintenance, and dependency risks if building on open source?

**Duplication / Reuse Risk:**
- Is the idea mostly a reimplementation of an existing commercial or OSS solution?
- Is there a credible build-on, plugin, fork, or contribution path that would reduce risk?

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
- **Open-source solution already exists**: If Phase 3 finds a maintained OSS project that covers much of the idea, treat "build from scratch" as a higher-risk recommendation. Analyze whether to build on, fork, contribute to, or differentiate from the project before giving a `Build it` verdict.
- **Technical feasibility unclear**: If the idea requires unproven technology, undisclosed APIs, or capabilities the stated team cannot build, flag it as a hard blocker in Phase 4 and lower the Feasibility score accordingly. Do not give a `Build it` verdict when fundamental technical risk is unresolved.

## Acceptance Criteria

- [ ] All 5 phases are completed in order (Clarify → Technical Context → Competitive Landscape → Evaluation → Improvements)
- [ ] Competitive landscape research is performed via live web search with at least 4 varied queries
- [ ] Commercial tools/services and open-source solutions are both checked; if no credible OSS option is found, the attempted OSS queries are documented
- [ ] Competitors table and Open-source Alternatives & Reuse Potential analysis are populated in `validate.md`
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

Per-phase check blocks (Setup, Phase 1-5) live in `references/step-completion-reports.md` — read the block matching the phase you just completed.

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

The canonical `idea.md` and `validate.md` header structure lives in `references/file-templates.md`. Read it when creating either file (Setup step 2/3) or updating a section named in Phases 1-5 above — that file owns header names and order; phase instructions above own what content goes in them.
