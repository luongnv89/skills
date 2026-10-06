---
name: "idea-validator"
description: "Validate app/startup ideas with market, feasibility, commercial, and open-source competitor analysis. Use when asked to evaluate, validate, or score a product idea. Don't use for PRDs, go-to-market plans, or investor decks."
license: MIT
effort: max
metadata:
  version: 1.6.0
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

Run the steps in this order: Setup → Phase 1 Clarify → Phase 2 Technical Context → Phase 3 Competitive Landscape → Phase 4 Evaluate → Phase 5 Improve → Commit and Push → Final Report. Do not skip or reorder a step, except where an Edge Cases row says to stop. A stop after Setup step 4 still runs Commit and Push on the files written so far, then the Final Report. If the ideas root is the root of an `ideas` repo, also run README Maintenance after each file update (detection rule in that section).

Terms used throughout:
- **Ideas root** — the directory that holds every idea folder (resolved in Setup step 2).
- **Project folder** — `<ideas root>/YYYY_MM_DD_<short_snake_case_name>/`, holding this idea's `idea.md` and `validate.md`.
- **Status** — the run outcome, `COMPLETE`, `PARTIAL` or `BLOCKED`, chosen by the rules in Final Report.

## Repo Sync Before Edits (mandatory)

Run this in the ideas root, before Setup step 3 creates or changes any file. Skip it when the ideas root is not inside a git repository (`git -C <ideas root> rev-parse --git-dir` fails), and record that skip for the Final Report.

If `git status --porcelain` prints nothing, sync directly:

```bash
cd "<ideas root>"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If it prints anything, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, the pull fails, or the rebase or stash pop conflicts, stop and ask the user before continuing.

## Setup

1. **Get the idea.** Use the idea in `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user to describe the concept. If no description arrives, stop with status `BLOCKED`.
2. **Resolve the ideas root** (tool-agnostic; ask once per environment). Take the first that applies:
   1. The env var `IDEAS_ROOT`, if set.
   2. The path in `~/.config/ideas-root.txt`, if that file exists.
   3. The path in legacy `~/.openclaw/ideas-root.txt`, if that file exists. Copy the value into `~/.config/ideas-root.txt`.
   4. Otherwise, ask the user where to store generated docs. Suggest `~/workspace/ideas`. Save the answer to `~/.config/ideas-root.txt`.

   Ask again only when the user asks to change the location.
3. **Create the project folder** under the ideas root. If a folder with the same date and name already exists, reuse it and update its files instead of creating a second one.
4. **Create `idea.md`** with the idea and the clarifications.
5. **Create `validate.md`** for the evaluation and recommendations.
6. **Echo the absolute project folder path** in your response, so downstream skills can pick it up.

If the ideas root cannot be created or written, stop with status `BLOCKED` and name the path.

Read `references/file-templates.md` when creating either file or updating a section named in Phases 1-5. That file owns header names and order; the phase instructions own the content.

## Phase 1: Clarify the Idea

Ask the user these questions with the question tool (`AskUserQuestion` or equivalent). If no question tool exists, ask in plain chat. Skip a question that the idea description from Setup step 1 already answers.
- What problem does this solve? Who has this pain?
- Who is your target user? Be specific.
- What makes this different from existing solutions?
- What does success look like in 6-12 months?

Update `idea.md` with the responses. Write `unknown` for each question the user declines or cannot answer, and list it under Uncertainty in the Final Report. The target-user question is the exception: see Edge Cases.

## Phase 2: Gather Technical Context

Ask the user, with the same tool and skip rule as Phase 1:
- Preferred tech stack?
- Timeline and team size?
- Budget situation (bootstrapped/funded/side project)?
- Existing assets (code, designs, research)?

Update the `idea.md` Technical Context section. Write `unknown` for each unanswered item.

## Phase 3: Competitive Landscape Research

Before evaluating the idea, perform live web research to find what already exists in the space. Do not rely on memory or training data for market, pricing, traction, competitor, or open-source claims — web search is mandatory so the report reflects current information.

Use the available web search tool (`WebSearch`, `web_search`, or equivalent) to run at least 4 varied queries covering:

**Commercial tools/services** — SaaS products, mobile apps, enterprise platforms, paid APIs, agencies, marketplaces, and other commercial offerings solving the same or adjacent problem. Search the core problem statement plus keywords like "app", "tool", "platform", "SaaS", "startup", "pricing", "alternative", and audience-specific terms.

**Open-source solutions** — GitHub/GitLab repositories, self-hosted tools, packages, frameworks, templates, and OSS alternatives that solve the same problem or provide a strong foundation. Search with terms like "open source", "GitHub", "self-hosted", "OSS", "alternative", "library", and relevant package registry names. If no credible OSS option is found, document the queries tried and state that no maintained open-source baseline was found.

**Adjacent solutions** — products or projects that solve a related problem or serve the same audience differently. These reveal how users currently cope without the proposed solution.

**Failed attempts** — startups, products, or OSS projects that tried something similar and stalled, shut down, or were abandoned. Search for "[concept] startup failed", "[concept] post-mortem", "[concept] abandoned GitHub", or check product directories.

For each competitor or OSS project found, capture:
- **Name and URL**
- **Type** (commercial, open-source, hybrid, adjacent, failed/abandoned)
- **What they do** (one sentence)
- **Pricing or license** (free, freemium, paid, enterprise, OSS license if available)
- **Traction or health** (reviews, ratings, users, funding, GitHub stars/forks, recent commits, open issues, community activity)
- **Key weakness or gap** the user's idea could exploit
- **Reuse/build-on potential** for open-source options (fork, plugin, library dependency, contribution path, or not suitable)

Aim for 3-8 total competitors, with at least one commercial and one open-source search path. If fewer than 3 credible results are found, record that in validate.md as a signal: the market is niche, the terms need refining, or the idea is framed in unfamiliar language.

When an open-source solution already solves a meaningful part of the idea, compare license fit, maintenance health, architecture, extensibility, deployment burden, and community before recommending a greenfield build. Decide whether the user should build on it, fork it, contribute to it, or differentiate sharply.

Update `validate.md` with a **## Competitive Landscape** section containing:
1. A summary table of commercial and open-source competitors found
2. An **Open-source Alternatives & Reuse Potential** analysis
3. A "white space" analysis — what's missing in the current market
4. Honest assessment: is the user's differentiation real or imagined given what exists?
5. A build-vs-base recommendation when OSS foundations exist

If web search is unavailable or blocked, stop and ask the user whether to continue without it. If the user says yes, label the Competitive Landscape section `Not verified by live search` and set the status to `PARTIAL`. If the user says no, stop with status `BLOCKED`. Never silently replace live research with general knowledge.

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

**Ratings (1-10):** Creativity, Feasibility, Market Impact, Technical Execution. Give each score a one-line reason.

**Verdict.** Take the first rule that matches:
1. `Skip it` — Phase 3 found a near-identical product and the user named no genuine differentiator, or a hard blocker exists that the stated team and budget cannot remove.
2. `Maybe` — any of: an unresolved hard technical risk, a maintained OSS project that covers most of the idea with no chosen build-on path, demand or willingness to pay with no evidence, or a Feasibility score below 6.
3. `Build it` — none of the above.

Write the verdict with the rule that produced it and a 2-3 sentence rationale.

## Phase 5: Improvements

Update `validate.md` with:

- **How to Strengthen**: Specific, actionable improvements, each tied to a concern from Phase 4
- **Enhanced Version**: Reworked, optimized concept
- **Implementation Roadmap**: Phased approach (if applicable)

## Edge Cases

- **No clear target user**: If the idea is too broad (e.g., "an app for everyone"), push back in Phase 1: ask the user to name one specific person who has this pain today. Do not start Phase 3 until a user segment is defined. If the user still names none, stop with status `PARTIAL` and save `idea.md`.
- **Duplicate idea already exists**: If Phase 3 finds a near-identical product, show it immediately with evidence (URL, feature comparison) and ask whether the user wants to proceed. Continue only if the user names a genuine differentiator. If the user stops, run Phase 4 with the verdict `Skip it` (rule 1), skip Phase 5, and set the status to `PARTIAL`.
- **Open-source solution already exists**: If Phase 3 finds a maintained OSS project that covers much of the idea, treat "build from scratch" as a higher-risk recommendation. Decide whether to build on, fork, contribute to, or differentiate from the project before giving a `Build it` verdict.
- **Technical feasibility unclear**: If the idea needs unproven technology, undisclosed APIs, or capabilities the stated team cannot build, flag it as a hard blocker in Phase 4 and lower the Feasibility score. The verdict rules then exclude `Build it`.
- **Web search unavailable**: follow the last paragraph of Phase 3.
- **Ideas root is not a git repository**: write the files, skip Repo Sync and Commit and Push, and set the status to `PARTIAL`. Do not run `git init` unless the user asks.
- **Push still fails after one retry**: stop and ask the user (Commit and Push). Report the commit hash and set the status to `PARTIAL`.

## Step Completion Reports

After completing each step from Setup through Phase 5, output a status report in this format:

```
◆ [Step Name] ([step N of 6] — [idea name])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Use `√` for pass, `×` for fail, and `—` to add brief context. The per-phase check blocks live in `references/step-completion-reports.md`; read the block matching the step you just completed.

## Tone

- **Brutally honest**: Name each fatal flaw plainly in Concerns
- **Constructive**: Pair every criticism with a suggestion
- **Specific**: Back each claim with a competitor, number, or quoted user answer
- **Balanced**: List strengths alongside weaknesses

## README Maintenance (when running inside ideas repo)

Run this when the ideas root contains a `README.md` and at least two `YYYY_MM_DD_*` idea folders. After each update to `idea.md` or `validate.md`, insert or update an `## Ideas index` table in that `README.md` with one row per idea:
- link to the idea's `idea.md`
- PRD/tasks status: `PRD` if a `prd.md` exists in the folder, `tasks` if a `tasks.md` exists, else `none`
- verdict, linked to the idea's `validate.md`

## Commit and Push (mandatory)

Skip this step when the ideas root is not a git repository (see Edge Cases). Otherwise, run it after Phase 5, or at an earlier stop (see Instructions):

1. Stage only the files this run wrote: `git add <project folder>/idea.md <project folder>/validate.md`, plus `README.md` when README Maintenance changed it. Never run `git add -A`.
2. Run `git diff --cached --name-only` to confirm that only those files are staged. If another file is staged, unstage it with `git restore --staged <file>`.
3. Commit with the message `docs(ideas): validate <short_snake_case_name>`.
4. Push to the current branch.
5. If the push is rejected, rebase and retry once: `branch="$(git rev-parse --abbrev-ref HEAD)" && git fetch origin && git rebase "origin/$branch" && git push`.
6. If the push still fails (`origin` missing, rebase conflict, repeated rejection), stop and ask the user before continuing.

Invoking this skill authorizes the commit and push. Do not ask for push permission again. Never force-push or run `git reset` in the ideas repo; resolve a rebase conflict only after the user's confirmation.

## Final Report

The expected output of every run, stops included, is one summary in concise chat text: the main result stays visible without opening a file, and the full detail lives in `validate.md`. Honor a different format only if the user asks for one. Take the status from the first rule that matches:

1. `BLOCKED` — no idea description, the ideas root cannot be written, or the user declined to continue without web search.
2. `PARTIAL` — a step was skipped or stopped early, Phase 3 ran without live search, or the files were not committed and pushed.
3. `COMPLETE` — Setup through Commit and Push all finished.

The summary carries these lines, in order:
- `Result:` the status, then the verdict and the four ratings when Phase 4 ran; for `PARTIAL` or `BLOCKED`, the step where the run stopped and why.
- `Evidence:` the project folder path; the GitHub links to `idea.md`, `validate.md` and, when changed, `README.md`; the commit hash; the number of live queries run and competitors found. Cite only checks that ran.
- `Strengths:` and `Concerns:` the top 3 of each.
- `Uncertainty:` each `unknown` answer, each claim that rests on an assumption instead of a source, and each skipped check. Write `none within the checks run` when there are none.
- `Decision:` `No approval needed.` (commit and push are authorized by invocation), or the question the run stopped on.
- `Next step:` the single most important action for the user.

Build each GitHub link from `git remote get-url origin` and the current branch: `https://github.com/<owner>/<repo>/blob/<branch>/<relative-path>`. The example summary and the fill rules live in `references/final-report.md`.

## Acceptance Criteria

- [ ] Setup, Phases 1-5, and Commit and Push run in order, or the run stops on an Edge Cases row with the matching status
- [ ] Competitive landscape research is performed via live web search with at least 4 varied queries
- [ ] Commercial tools/services and open-source solutions are both checked; if no credible OSS option is found, the attempted OSS queries are documented
- [ ] Competitors table and Open-source Alternatives & Reuse Potential analysis are populated in `validate.md`
- [ ] The verdict (`Build it` / `Maybe` / `Skip it`) names the verdict rule that produced it and a rationale
- [ ] All four ratings (Creativity, Feasibility, Market Impact, Technical Execution) are provided as scores out of 10
- [ ] Only the files this run wrote are committed, and the commit is pushed (or the status is `PARTIAL`)
- [ ] The Final Report opens with `Result:` and the status, and carries `Evidence:`, `Uncertainty:` and `Decision:` lines
- [ ] Reader checks pass: the result is findable, facts and assumptions are separated, claims are traceable, and the next decision is clear (`references/final-report.md` → *Reader checks*; scenario cases in `evals/evals.json`)
