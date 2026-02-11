---
name: x-post-generator
version: 1.1.1
description: Generate X (Twitter) posts from user draft/idea with relevant hashtags (max 5), optional media link references (only when provided), and multiple copy-ready variants optimized for Telegram one-tap copy. Use when asked to create tweets, X posts, social post options, or rewrite a draft for X. Supports brand style via references/brand.md and auto-learning from last 10 user-accepted posts.
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
- If media links are provided, reference them explicitly in each option
- If media links are not provided, do not add a media line
- Keep tone aligned with `references/brand.md`

### 4) Output format (strict, Telegram copy-first)
Always format output so Telegram users can copy each proposal in one tap.

Rules:
- Return **only** option labels + fenced code blocks (no extra commentary before/after).
- Put exactly one full post per code block.
- Keep plain text inside code blocks (no markdown bullets inside).
- Use triple backticks with `text` language.

Use this structure:

Option 1
```text
<post body>

#hashtag1 #hashtag2 #hashtag3
📎 Media: <link1> <link2>
```

Option 2
```text
<post body>

#hashtag1 #hashtag2 #hashtag3
📎 Media: <link1> <link2>
```

Option 3
```text
<post body>

#hashtag1 #hashtag2 #hashtag3
📎 Media: <link1> <link2>
```

If no media links are provided, omit the media line entirely.

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
- Each option in its own `text` code block
- No more than 5 hashtags per option
- Media line present only when media links are provided; absent otherwise
- No ambiguous placeholders left
- No extra commentary outside option labels + code blocks
