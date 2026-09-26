---
name: website-builder
description: "Build an approved Vite/React/Tailwind plan, collect assets, verify static output, deploy to GitHub Pages, and emit metadata. Use for implementing tasks.md. Don't use for design review, planning, backend services, or unapproved specs."
license: MIT
effort: high
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
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
- `website-analyzer` is installed for the comparable post-deployment audit

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
8. Re-audit the deployed URL for comparable after metrics
9. Emit builder metadata
```

## Dependency Preflight (mandatory)

Step 7 re-audits the deployed site by invoking the sibling `website-analyzer` skill. Detect it
**before** the repo sync below, the first step that changes anything:

```bash
asm list -p claude --json | grep -q '"website-analyzer"' || {
  echo "Missing sibling skill: website-analyzer" >&2
  echo "Install it:      asm install github:luongnv89/skills:skills/website-cloner/website-analyzer -p claude --yes" >&2
  echo "No asm yet:      npm install -g agent-skill-manager" >&2
  echo "Verify:          asm list -p claude --json | grep 'website-analyzer'" >&2
  echo "Step 7 will be skipped and the result capped at PARTIAL." >&2
}
```

A missing `website-analyzer` is **not a stop**: print the block, skip Step 7's re-audit, and return
`PARTIAL` — the same degrade Step 7 documents for a failed re-audit. Steps 1–6 never invoke it.

## Repo Sync Before Edits (mandatory)

Choose the repository branch before modifying project files:

1. **Existing git worktree with `origin`:** preserve dirty changes, then sync before edits.
2. **New project with no git repository or remote:** skip fetch/pull, initialize the project, and add the approved remote only during deployment.
3. **Existing repository with an unexpectedly missing `origin`:** stop and ask; do not assume it is a new project.

For the existing-worktree branch, run:

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

If rebase or stash restoration fails, stop and ask. Never discard user changes.

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

Configure Tailwind and shadcn/ui. Set up the GitHub Pages deployment target. In `vite.config.js` (or `.ts`), make the build base explicit so the workflow can select `/` for a user/organization Pages repository and `/<repo>/` for a project Pages repository:

```js
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
})
```

Use `import.meta.env.BASE_URL` for public asset URLs. For a client-routed SPA, prefer `HashRouter`; if the approved plan requires `BrowserRouter`, set its `basename` from `import.meta.env.BASE_URL` and provide a tested Pages 404 fallback. Do not leave root-relative asset or route URLs that bypass the configured base.

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

Create `.github/workflows/deploy-pages.yml`. Pages must deploy the verified Vite `dist/` artifact through GitHub Actions—not the repository root or a branch folder:

```yaml
name: Deploy Vite site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
      - uses: actions/configure-pages@v5
      - run: npm ci
      - name: Configure Vite base path
        shell: bash
        run: |
          repo_name="${GITHUB_REPOSITORY#*/}"
          if [[ "$repo_name" == *.github.io ]]; then
            echo "VITE_BASE_PATH=/" >> "$GITHUB_ENV"
          else
            echo "VITE_BASE_PATH=/$repo_name/" >> "$GITHUB_ENV"
          fi
      - run: npm run build
      - name: Verify static artifact
        run: test -f dist/index.html
      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy Pages artifact
        id: deployment
        uses: actions/deploy-pages@v4
```

Create or update the GitHub repository for the site, run the repository's required secret scan, then commit and push the project including `package-lock.json`, `vite.config.*`, and the workflow. In Repository Settings → Pages, select **GitHub Actions** as the source; never select `main / (root)` or `/docs` for this Vite build.

Verify the completed workflow uploaded `dist/`, the deploy job succeeded, and its `page_url` responds. Confirm project Pages uses `https://<user>.github.io/<repo>/`, while `<user>.github.io` repositories use the root URL. Report the deployed URL from the workflow output.

## Step 7: Re-audit the Deployed Site

After the GitHub Pages URL responds successfully, run the same analyzer used for the baseline:

```text
/website-analyzer "https://<user>.github.io/<repo>/" --output "$PROJECT_DIR/after-analysis.json"
```

Require the analyzer's structured `performance`, `seo`, and `security` objects. The comparable
performance fields are `lcp_estimate_seconds`, unitless `cls_estimate`,
`ttfb_estimate_seconds`, `total_page_weight_kb`, and `request_count`. Preserve analyzer `null`
values and caveats; do not turn estimates into measured values. If deployment or the re-audit
fails, record the error and return `PARTIAL` rather than inventing an after snapshot.

## Step 8: Emit Builder Metadata

Write a JSON metadata file for the final report phase. Copy the post-deployment analyzer objects
without changing their field names or units:

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
  "after_snapshot_source": "after-analysis.json",
  "after_snapshot_status": "complete | partial | unavailable",
  "performance": {
    "lcp_estimate_seconds": 1.8,
    "cls_estimate": 0.03,
    "ttfb_estimate_seconds": 0.2,
    "total_page_weight_kb": 650,
    "request_count": 32,
    "notes": "estimated from static analysis"
  },
  "security": {
    "https": true,
    "mixed_content": false,
    "security_headers": ["strict-transport-security"],
    "exposed_metadata": [],
    "note": "Surface-level check only. Not a full security audit."
  },
  "seo": {
    "score": 94,
    "title_tag": "present",
    "meta_description": "present",
    "heading_structure": "h1:1 h2:4",
    "alt_text_coverage": 1.0,
    "structured_data": "present",
    "canonical_url": "present",
    "robots_sitemap": "robots=ok | sitemap=found",
    "dimension_scores": {
      "meta_tags": 95,
      "heading_structure": 85,
      "image_alt_text": 100,
      "structured_data": 100,
      "crawlability": 90
    }
  },
  "tech_stack": {
    "bundler": "vite",
    "framework": "react",
    "ui": "shadcn/ui",
    "css": "tailwindcss"
  }
}
```

`build_output_size_kb` is the complete build artifact size, not page weight; never use it as
`performance.total_page_weight_kb`. Write metadata to `$PROJECT_DIR/builder-metadata.json`.

## Acceptance Criteria

Verify the expected output before deployment is marked complete:

- `npm run build` exits 0 and `dist/index.html` exists.
- `.github/workflows/deploy-pages.yml` runs `npm ci` and `npm run build`, uploads exactly `dist/` as a Pages artifact, and deploys it with the required Pages permissions and environment.
- The workflow-derived `VITE_BASE_PATH` is `/` for user/organization Pages and `/<repo>/` for project Pages; Vite, internal routes, and asset URLs use that base consistently.
- Every approved task is represented in `tasks_completed` or named in `deviations`; assert `tasks_completed <= tasks_total`.
- Internal routes and collected asset paths resolve under the GitHub Pages base path, including a direct-refresh check for every supported route strategy.
- `builder-metadata.json` parses and contains the URL, task counts, asset lists, deviations, output size, exact tech stack, after-snapshot status, and structured performance/SEO/security objects.
- A `PASS` result requires a responsive Pages URL and a complete comparable after snapshot with every required performance field, SEO overall/dimension score, and security check non-null.
- Deployment, analyzer, or required after-value gaps are recorded and force `PARTIAL`; a metadata write failure is `FAIL`.
- No credentials, local paths, or secret environment values appear in generated assets or metadata.

## Edge Cases

- Existing repository or remote: inspect `git status` and `git remote -v`; confirm the target before changing either.
- Dirty working tree: preserve user changes and follow the mandatory sync guardrail; never discard them.
- Build succeeds but deployment fails: keep the verified local build, record the error, set the after snapshot unavailable, and return `PARTIAL`.
- Deployment succeeds but the re-audit is incomplete: preserve nulls and analyzer caveats, set `after_snapshot_status` to `partial`, and return `PARTIAL`.
- A task conflicts with the approved PRD: stop that task and ask; do not silently reinterpret the plan.

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
  After snapshot:         √ complete | × partial ([missing])
  Metadata emitted:       √ pass
  ____________________________
  Result:                 PASS | PARTIAL | FAIL
```
