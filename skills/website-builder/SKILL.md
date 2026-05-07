---
name: website-builder
description: "Execute the approved tasks.md to build a Vite + React + shadcn/ui + Tailwind CSS website deployable to GitHub Pages. Collects assets from the original site and creates new assets per plan. Emits builder metadata for the final report. Use when asked to build, implement, or code a website from a plan. Don't use for design review or planning — those are upstream phases."
license: MIT
effort: high
metadata:
  version: 1.0.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Website Builder

Executes the approved implementation plan (tasks.md) to build a working improved website using Vite + React + shadcn/ui + Tailwind CSS, deployable to GitHub Pages.

## When to Use

Trigger when the user asks to:
- Build a website from an implementation plan
- Implement a PRD or tasks list
- Code a Vite/React website from a spec

Do **not** use for design review or planning — those are upstream phases.

## Prerequisites

- `tasks.md` (Phase 4 plan) exists and is approved
- `prd.md` (Phase 3 proposal) exists for alignment reference
- Node.js and npm are available
- Git is available for repository management

## Tech Stack

- **Build tool**: Vite
- **Framework**: React (JSX)
- **UI components**: shadcn/ui
- **Styling**: Tailwind CSS
- **Deployment**: GitHub Pages (static assets)
- **Serverless**: no backend, no server-side runtime

## Workflow

```
1. Read tasks.md and prd.md
2. Sync to default branch
3. Execute tasks phase by phase (landing page first)
4. Collect assets from original site as specified
5. Create new assets as specified
6. Build and verify
7. Deploy to GitHub Pages
8. Emit builder metadata
```

## Repo Sync Before Edits (mandatory)

Before modifying any project files:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If dirty, stash first:

```bash
git stash push -u -m "website-builder: pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If origin is missing or rebase fails, stop and ask.

## Step 1: Read the Plan

Read `tasks.md` and `prd.md`:

```
Read file <path-to-tasks.md>
Read file <path-to-prd.md>
```

If either is missing, ask for paths.

## Step 2: Initialize Project

Create the Vite + React project:

```bash
npm create vite@latest . -- --template react
npm install
npx shadcn@latest init
npm install tailwindcss @tailwindcss/vite
npm install class-variance-authority clsx tailwind-merge lucide-react
```

Configure Tailwind and shadcn/ui. Set up the GitHub Pages deployment target.

## Step 3: Execute Tasks Phase by Phase

Process each phase from tasks.md in order. For each task:

1. Implement the specified components/features
2. Follow the PRD for improvement alignment
3. Collect assets from the original site as specified in the plan
4. Create new assets where specified
5. Verify the build succeeds: `npm run build`

### Phase 1: Landing Page

Build the landing/home page first. This must be independently usable:

- Hero section with headline, subtext, CTA
- Navigation
- Footer
- Responsive layout (mobile + desktop)
- Applied style from the PRD (colors, typography, spacing)

### Phase 2: Core Pages

Build additional pages per the plan:

- About, features, contact, or other specified pages
- Shared components (nav, footer, buttons)
- Routing between pages

### Phase 3: Optimization

Apply performance, SEO, and security improvements:

- Image optimization (compress, lazy load)
- Code splitting (Vite handles this by default)
- SEO meta tags, structured data, Open Graph tags
- Security headers via meta tags where applicable

## Step 4: Asset Management

For each asset listed in tasks.md:

- **[Collect]**: Fetch from the original site using `WebFetch` or direct URL access. Save to `public/assets/` or `src/assets/`.
- **[Create]**: Generate or write new assets. This includes:
  - Rewritten copy/text content
  - New component code
  - Generated SVG icons
  - Brand color values from the PRD

## Step 5: Build and Verify

After all tasks are complete:

```bash
npm run build
```

Verify:
- Build succeeds with no errors
- Output is static assets (no server required)
- Landing page renders correctly
- All pages are accessible via routing

## Step 6: Deploy to GitHub Pages

Create or update a GitHub repository for the site:

```bash
git init
git remote add origin git@gh-luongnv89:<user>/<repo>.git
git add .
git commit -m "chore: initial site build"
git push -u origin main
```

Configure GitHub Pages:
- Repository Settings → Pages → Source: `main` branch, `/ (root)`

Report the GitHub Pages URL.

## Step 7: Emit Builder Metadata

Write a JSON metadata file for the final report phase:

```json
{
  "url": "https://<user>.github.io/<repo>/",
  "timestamp": "2026-05-07T12:00:00Z",
  "tasks_completed": 12,
  "tasks_total": 12,
  "assets_collected": ["logo.png", "brand-colors.json", ...],
  "assets_created": ["cta-copy.txt", "hero-icon.svg", ...],
  "deviations": [],
  "build_output_size_kb": 450,
  "tech_stack": {
    "bundler": "vite",
    "framework": "react",
    "ui": "shadcn/ui",
    "css": "tailwindcss"
  }
}
```

Write to: `$PROJECT_DIR/builder-metadata.json`

## Acceptance Criteria

- [ ] Consumes approved tasks.md and prd.md without additional spec input
- [ ] Uses Vite + React + shadcn/ui + Tailwind CSS
- [ ] Produced site is serverless, front-end only, deployable to GitHub Pages
- [ ] Landing/home page built first and independently usable
- [ ] Asset collection and creation follow tasks.md plan
- [ ] GitHub Pages URL reported on completion
- [ ] Builder metadata emitted for website-clone-final-report

## Step Completion Reports

```
◆ Build Phase 1 — Landing Page
······································································
  Project initialized:    √ pass
  Landing page built:     √ pass
  Assets collected:       √ pass (<N>)
  Build succeeds:         √ pass
  ____________________________
  Result:                 PASS

◆ Build Phase 2 — Core Pages
······································································
  Pages built:            √ pass (<pages>)
  Routing configured:     √ pass
  ____________________________
  Result:                 PASS

◆ Build Phase 3 — Optimization
······································································
  Performance applied:    √ pass
  SEO applied:            √ pass
  Security applied:       √ pass
  ____________________________
  Result:                 PASS

◆ Deploy
······································································
  Repository created:     √ pass
  GitHub Pages configured: √ pass (<url>)
  Metadata emitted:       √ pass
  ____________________________
  Result:                 PASS
```
