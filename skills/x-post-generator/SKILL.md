---
name: x-post-generator
version: 1.0.0
description: Generate X (Twitter) posts from user draft/idea with relevant hashtags (max 5), media link references, and multiple copy-ready variants. Use when asked to create tweets, X posts, social post options, or rewrite a draft for X. Supports brand style via references/brand.md and auto-learning from last 10 user-accepted posts.
---

# X Post Generator

Generate polished X posts from user ideas/drafts with strict output formatting and brand alignment.

## Workflow

### 1) Gather required input
Collect these fields before generating:
- Source info: user draft or user idea
- Post goal: announce / recap / invite / opinion / update
- Audience: who should care
- Media links: image/video/doc links to reference in the post

If any required part is unclear, ask concise clarifying questions first.

### 2) Load brand profile
Read `references/brand.md`.

If this is the first run (brand profile still placeholder/empty), ask user to define style. Offer quick options and allow custom:
1. Professional & concise
2. Friendly & community
3. Technical & credible
4. Visionary & bold
5. Playful & energetic
6. Custom style (user-defined)

Then continue only after style is clear.

### 3) Generate post options
Produce **at least 3 distinct options**.

Hard rules:
- Auto-generate relevant hashtags, maximum **5 unique hashtags**
- Keep hashtags relevant to topic + brand
- Keep media links explicitly referenced in each option
- Keep tone aligned with `references/brand.md`

### 4) Output format (strict)
Always return options in separate code blocks so user can copy directly.

Use this structure for each option:

```text
<post body>

#hashtag1 #hashtag2 #hashtag3
📎 Media: <link1> <link2>
```

If no media links are provided, replace last line with:
`📎 Media: (none provided)`

### 5) Learn from accepted post (auto-update brand memory)
When user accepts one option, run:

```bash
python3 scripts/learn_from_accepted.py --post "<accepted_post_text>"
```

This will:
- Store accepted post into `references/accepted_posts.jsonl`
- Keep only last 10 accepted posts
- Auto-update the learned section in `references/brand.md`

## Quality checks
Before final answer, verify:
- At least 3 options
- Each option in its own code block
- No more than 5 hashtags per option
- Media links present in each option
- No ambiguous placeholders left
