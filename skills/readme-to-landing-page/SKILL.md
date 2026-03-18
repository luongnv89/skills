---
name: readme-to-landing-page
description: Transform any project README.md into a persuasive, landing-page-structured markdown file using proven copywriting frameworks (PAS, AIDA, StoryBrand). Reads the existing README and project files, extracts the product story, and rewrites the README.md to follow a conversion-optimized section flow — hero, problem, solution, how it works, social proof, FAQ, and CTA — all in pure markdown that renders natively on GitHub. Use when users ask to "turn my README into a landing page", "make my README sell the project", "rewrite README as a landing page", "convert README to marketing style", "make my GitHub page more persuasive", "landing page my README", "optimize my README for conversions", or want their GitHub front page to persuade visitors rather than just inform them. Also trigger when a user has a dry technical README and wants more stars, users, or contributors — even if they don't explicitly mention "landing page".
license: MIT
metadata:
  version: 1.0.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# README to Landing Page

Transform a project's README.md into a persuasive, landing-page-structured markdown file that sells the project to visitors.

## Repo Sync Before Edits (mandatory)

Before modifying any project files, sync the current branch with remote:

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

## Why This Matters

GitHub renders README.md as the project's front page. Most READMEs explain *what* the project does — feature lists, install steps, API docs — but they don't *sell the idea*. A landing-page-structured README converts casual visitors into users and contributors by leading with the problem, presenting the solution as a story, and ending with clear calls to action. The technical content isn't lost — it's reorganized so it supports the narrative instead of burying the value proposition.

## Workflow

### Step 1: Gather Project Context

Read these files to build a complete picture:

- **README.md** (required) — the source material
- **package.json** / **pyproject.toml** / **Cargo.toml** / **go.mod** — project name, description, version, keywords
- **CHANGELOG.md** — recent milestones and momentum signals
- **LICENSE** — for the risk-reversal CTA ("MIT licensed, free forever")
- **docs/** folder — any existing detailed documentation to preserve

Also check for social proof data:
- GitHub stars, forks, contributor count (from the repo itself)
- Download stats if mentioned in existing README
- Notable users, companies, or testimonials

If the project's purpose or target audience is unclear from the files, ask the user before proceeding.

### Step 2: Identify Audience & Value Proposition

Determine:
1. **Who is this for?** — developers, designers, data scientists, ops teams, end users?
2. **What pain does it solve?** — what's frustrating about the status quo?
3. **What's the core benefit in one sentence?** — this becomes the H1 headline

If the project serves multiple audiences, pick the primary one and mention others secondarily. If you're unsure, ask.

### Step 3: Select Copywriting Framework

Choose the framework that fits the project type:

**PAS (Problem-Agitate-Solution)** — best for developer tools and infrastructure
- Identify the pain point
- Amplify the consequences of not solving it
- Present the project as the solution

**AIDA (Attention-Interest-Desire-Action)** — best for end-user products and libraries
- Bold headline grabs attention
- Build interest with relatable scenarios
- Create desire with benefits and proof
- Prompt action with clear CTA

**StoryBrand** — best when the user requests it, or for projects with a strong narrative
- The user/developer is the hero
- The project is the guide with a plan
- CTA leads to success, avoids failure

Default to PAS for CLI tools, libraries, and infrastructure. Default to AIDA for apps, platforms, and end-user products. Tell the user which framework you chose and why, and let them override.

### Step 4: Back Up the Original

This step is mandatory — always create the backup before any changes:

```bash
cp README.md README.backup.md
```

Inform the user: "I've saved your original README as `README.backup.md`."

### Step 5: Rewrite README.md

Follow this section flow. Every section should earn its place — skip sections that don't apply (e.g., social proof if there's genuinely nothing to show), but the core structure should stay intact.

#### Hero Section (top of README)

- **Badge row**: GitHub stars, npm/PyPI downloads, license, build status, version — whatever's relevant. Use shields.io badge format.
- **H1 headline**: The value proposition in 10 words or fewer. Not the project name — the *benefit*. The project name can appear in the badge row or subtitle.
- **Subheadline**: 2 sentences expanding the value. What it does + why it matters.
- **Primary CTA**: Bold link pointing to the installation section or docs. Use action verb + specific outcome: "Get Started in 30 Seconds", "Start Optimizing Now" — never "Click Here".

#### Problem Section

- H2 heading (e.g., "The Problem", "Sound Familiar?", or something that fits the tone)
- 2-3 bullet points describing the pain in relatable, specific terms
- Use "you" language — the reader should see themselves in the problem
- Emotional but honest — no manufactured urgency

#### Solution Section

- H2 heading (e.g., "How [Project] Fixes This", "The Solution", "What [Project] Does")
- 3-5 key features written as **benefits**, not feature dumps
  - "Ship 10x faster" not "Has CI integration"
  - "Zero config" not "Supports config file format X"
  - Include specific numbers when available (benchmarks, size reduction, speed)
- Brief comparison to alternatives if the original README mentioned them

#### How It Works

- H2 heading
- 3-4 numbered steps extracted from the existing install/usage sections
- Each step: concise, action-oriented, starts with a verb
- End with a secondary CTA link

#### Social Proof

- H2 heading (e.g., "Trusted by Developers", "Used in Production")
- GitHub stars, fork count, download numbers — with actual values
- Notable users or companies if mentioned anywhere in the project
- Testimonial quotes if available, otherwise placeholder format the maintainer can fill in
- Skip this section entirely if there's no real data — don't fabricate social proof

#### FAQ

- H2 heading
- 5-7 entries as **bold question** / paragraph answer
- Derive from common objections:
  - Is it free? (license info)
  - Is it maintained? (last commit, release frequency)
  - How does it compare to X? (if alternatives exist)
  - How do I get started? (link back to install)
  - Can I use it in production? (stability signals)
- Address real concerns — don't pad with trivial questions

#### Final CTA

- H2 heading (e.g., "Get Started", "Start [Doing the Thing]")
- Reinforced value proposition in 1-2 sentences
- Risk reversal: open source, free, MIT licensed, easy to uninstall
- Bold CTA link

#### Technical Details (collapsed)

Preserve the original technical content that doesn't fit the narrative flow:
- API reference
- Configuration options
- Advanced usage
- Contributing guide
- Detailed architecture

Wrap each in a `<details>` block with a descriptive `<summary>`:

```markdown
<details>
<summary>API Reference</summary>

[original content here]

</details>
```

This keeps technical depth accessible without overwhelming the landing page flow.

### Step 6: Apply Copywriting Polish

Review the full rewrite and apply these principles throughout:

- **Active voice, present tense** — "dockslim analyzes your Dockerfile" not "your Dockerfile will be analyzed"
- **Benefits over features** — always ask "so what?" about each feature and write the answer instead
- **Specific numbers** — "80% smaller" not "much smaller", "2,400+ stars" not "popular"
- **Short, scannable sentences** — if a sentence has a comma, consider splitting it
- **"You" language** — the reader is the subject, not the project
- **Power words where genuine** — proven, instant, effortless, lightweight, blazing-fast — but only when the project actually delivers on them
- **Multiple CTAs** — at least in hero, after how-it-works, and at the end
- **CTA format** — `[**Action Verb + Outcome →**](#section)` — bold, with arrow

### Step 7: Present to User

Show the user the rewritten README.md and explain:
1. Which copywriting framework you used and why
2. What sections you added/reorganized
3. Where original technical content ended up (collapsed sections)
4. That `README.backup.md` contains their original

Ask: "How does this look? Anything you'd like me to adjust — tone, section order, emphasis, specific wording?"

Do NOT commit unless the user explicitly asks.

## Guidelines

- Never fabricate data. If you don't have star counts or download numbers, either look them up or leave placeholders the maintainer can fill in.
- Don't be sleazy. Landing page structure doesn't mean manipulative copy — it means leading with value and making the project easy to understand at a glance.
- Respect the project's voice. A serious security tool shouldn't sound like a startup pitch deck. Match the energy of the project while making it more persuasive.
- The H1 is a value proposition, not the project name. The project name should appear prominently (badges, first sentence) but the headline sells the benefit.
- Preserve all original content. Nothing should be deleted — only reorganized. Technical details move into collapsed sections, not the trash.
- One primary audience. If the README tries to speak to everyone, it speaks to no one. Pick the primary audience and mention others.

## Error Handling

### No README.md found
Inform the user: "I don't see a README.md in this project. Would you like me to create one from scratch based on the project files?" Then proceed with the landing page structure using project context files.

### README is already marketing-style
If the README already follows a landing page structure, tell the user what you found and offer to refine specific sections rather than doing a full rewrite.

### Insufficient project context
If neither the README nor project files give enough information to write compelling copy (e.g., the README is just a title and the project has 3 files with no comments), ask the user to describe: what the project does, who it's for, and what problem it solves.
