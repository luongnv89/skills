---
name: blog-draft
description: Draft a blog post from ideas and resources. Use when users want to write a blog post, create content from research, or draft articles. Guides through research, brainstorming, outlining, and iterative drafting with version control.
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
3. Present research summary to user

### 2. Brainstorm & Clarify

Present findings and ask:
- Main takeaway for readers?
- Target length? (short: 500-800, medium: 1000-1500, long: 2000+)
- Points to emphasize or exclude?

**Wait for user response.**

### 3. Outline

Create outline with:
- Meta info (audience, tone, length, main takeaway)
- Section structure with key points and supporting evidence
- Sources to cite

**Get user approval**, then save as `OUTLINE.md` and commit.

### 4. Draft

Write the full post following the outline. Use `assets/draft-template.md` for structure.

**Citation requirement**: Every statistic, comparison, or factual claim must cite its source using inline references [1] linked to a References section.

Save as `draft-v0.1.md` and commit.

### 5. Review & Iterate

Present draft and ask for feedback on:
- Overall impression
- Sections needing changes
- Tone adjustments
- Missing information

**If changes requested**: Increment version (v0.2, v0.3...), incorporate feedback, repeat review.

**If approved**: Optionally rename to `final.md` and summarize the creation process.

## Output Structure

```
blog-posts/YYYY-MM-DD-topic-name/
├── resources/
│   ├── source-1-name.md
│   └── source-2-name.md
├── OUTLINE.md
├── draft-v0.1.md
└── draft-v0.2.md (if iterated)
```

## Assets

- `assets/draft-template.md` - Blog post structure template
- `assets/outline-template.md` - Outline structure template
