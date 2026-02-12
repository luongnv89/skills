---
name: blog-draft
version: 1.3.0
description: Draft a blog post from ideas and resources, keep blogs/README.md in sync with status/public links, and always report GitHub app deep links (+ web fallback) to new/updated files in completion replies.
---

## User Input

```text
$ARGUMENTS
```

User should provide:
- **Topic**: The main concept or theme
- **Resources**: URLs, files, or references (optional)
- **Audience/Tone**: Who it's for and style preference (optional)

**For existing posts**: If updating an existing draft, skip to the Iteration section.

## Workflow

### 1. Setup & Research

1. Create project folder: `blog-posts/YYYY-MM-DD-topic-slug/`
2. For each resource, fetch/read and save summaries to `resources/source-N-name.md`
3. Add/update `blog-posts/status.json` entry for this slug:
   - `status`: `draft`
   - `public_url`: empty string
   - `title`: working title
4. Present research summary to user

### 2. Brainstorm & Clarify

Present findings and ask:
- Main takeaway for readers?
- Target length? (short: 500-800, medium: 1000-1500, long: 2000+)
- Points to emphasize or exclude?

**Wait for user response.**

### 3. Title & Outline

#### Generate SEO-Optimized Title

Follow [references/seo-title-guide.md](references/seo-title-guide.md) to create click-worthy titles:

1. Identify primary keyword from topic
2. Generate 5 title options using these patterns:
   - **Keyword + Benefit**: "SEO Title Tags: Master Optimization in 5 Steps"
   - **Number + Keyword + Outcome**: "7 Proven Tips to Boost Your Blog Traffic"
   - **How to + Keyword + Outcome**: "How to Write Headlines That Get Clicks"
   - **Keyword + Audience + Year**: "React Hooks for Beginners (2026 Guide)"
3. Validate: 45-65 characters, keyword near start, specific benefit included
4. Present options to user for selection

#### Create Outline

Include:
- Selected title and 2-3 alternates for A/B testing
- Meta info (audience, tone, length, main takeaway, primary keyword)
- Section structure with key points and supporting evidence
- Sources to cite

**Get user approval**, then save as `OUTLINE.md` and commit.

### 4. Draft

Write the full post following the outline. Use `assets/draft-template.md` for structure.

**Citation requirement**: Every statistic, comparison, or factual claim must cite its source using inline references [1] linked to a References section.

Save as `draft-v0.1.md` and commit.

### 5. SEO Content Optimization

Before review, optimize content for search engines. See [references/seo-content-guide.md](references/seo-content-guide.md) for details.

#### Checklist

- [ ] **Primary keyword** in first 100 words
- [ ] **Keyword density** 1-2% (natural usage, no stuffing)
- [ ] **H2/H3 headings** include keyword variations
- [ ] **Meta description** written (150-160 chars, includes keyword + CTA)
- [ ] **URL slug** is short, keyword-rich, hyphenated
- [ ] **Internal links** to related content (2-3 minimum)
- [ ] **External links** to authoritative sources
- [ ] **Image alt text** descriptive with keywords where natural
- [ ] **Readability** short paragraphs (2-4 sentences), bullet points, scannable
- [ ] **Featured snippet optimization** direct answers, lists, or tables for key questions

Save SEO-optimized version and commit.

### 6. Review, Status, and Iterate

Present draft and ask for feedback on:
- Overall impression
- Sections needing changes
- Tone adjustments
- Missing information

If changes requested:
- Increment version (v0.2, v0.3...), incorporate feedback, repeat review.

If paused/not publishing now:
- Set status to `on-hold` in `blog-posts/status.json`.

If approved and published:
- Set status to `complete` in `blog-posts/status.json`.
- Set `public_url` to final published blog URL.

If still in progress:
- Keep status `draft`.

### 7. Sync Blog Tracker README (mandatory)

After any draft creation, status change, or publish URL update, run from the `blogs/` repo root:

```bash
python3 scripts/update_blog_drafts_readme.py
```

This updates `blogs/README.md` to list all blog drafts with:
- created date
- link to latest draft (or outline)
- status (`draft`, `complete`, `on-hold`)
- public blog link for completed posts

### 8. Report with GitHub app deep links (mandatory)
When reporting any blog draft result, include:
- GitHub app deep link(s) to created/updated draft files (`OUTLINE.md`, `draft-v*.md`, `status.json`, `README.md` if changed)
- Web fallback link(s)
- Commit hash

Deep-link format:
- `github://openRepo/luongnv89/blogs?branch=main&filepath=<relative-path>`

Web fallback format:
- `https://github.com/luongnv89/blogs/blob/main/<relative-path>`

## Output Structure

```
blog-posts/
├── status.json
├── YYYY-MM-DD-topic-name/
│   ├── resources/
│   │   ├── source-1-name.md
│   │   └── source-2-name.md
│   ├── OUTLINE.md
│   ├── draft-v0.1.md
│   └── draft-v0.2.md (if iterated)
README.md
```

## Resources

- `references/seo-title-guide.md` - SEO title optimization patterns and checklist
- `references/seo-content-guide.md` - SEO content optimization (keywords, meta, links, readability)
- `assets/draft-template.md` - Blog post structure template
- `assets/outline-template.md` - Outline structure template
