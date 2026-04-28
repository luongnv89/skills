---
name: logo-designer
description: "Generate professional SVG logos from project context, producing 7 brand variants (mark, full, wordmark, icon, favicon, white, black) plus a showcase HTML page. Skip for raster-only logos, product illustrations, or full brand-guideline docs."
license: MIT
effort: medium
metadata:
  version: 1.2.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

## Environment Check

Before running this skill, verify:
- [ ] You're in a project directory with a README or package.json
- [ ] You have write access to create `/assets/logo/` directory
- [ ] The project directory is a git repository (optional, but recommended)

If any check fails, the skill will stop and ask for clarification.

## Subagent Architecture

This skill uses an **Explorer+Executor (A) + Review Loop (C)** architecture:

```
Phase 1: Brand Research
  ↓ (brand-researcher agent)
  ↓
Phase 2-3: SVG Generation (Interactive Style Selection)
  ↓ Main agent: interactive style selection with user
  ↓
Phase 3: Generate All 7 SVGs
  ↓ (svg-generator agent)
  ↓
Phase 4: SVG Validation
  ↓ (svg-reviewer agent)
  ↓
Final Output: 7 SVG files in /assets/logo/ + brand-showcase.html + Design Rationale
```

**Agents**:
1. `agents/brand-researcher.md` — Reads project files, produces structured brand brief
2. `agents/svg-generator.md` — Generates all 7 SVG files (mark, wordmark, full, icon, favicon, white, black)
3. `agents/svg-reviewer.md` — Validates SVG structure (viewBox, no rasters, all files present, correct names)

**Key Insight**: 7 SVG files generated inline is the single biggest context cost. Brand research across multiple project files adds to the burden. The reviewer acts as a quality gate to catch SVG structure issues before files are committed.

---

# Logo Designer

Design modern, professional logos by analyzing project context and generating SVG-based brand assets.

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

## Workflow

### Phase 1: Project Analysis

Automatically analyze the current project to understand brand context:

1. **Detect product identity** - Check these files in order:
   - `README.md` - Product name, description, tagline
   - `package.json` - Name, description, keywords
   - `pyproject.toml` - Project name and description
   - `Cargo.toml` - Package name and description
   - `go.mod` - Module name

2. **Find existing brand assets** - Search for:
   - `/docs/brand_kit.md`, `/.docs/brand_kit.md`, `brand_kit.md`
   - `/docs/prd.md`, `prd.md` - Product requirements with brand info
   - `/assets/logo/`, `/public/logo`, `/static/logo` - Existing logos
   - Tailwind config for existing color palette

3. **Identify project type** from codebase structure:
   - Developer/CLI/Open Source - `.github/`, CLI entry points, MIT license
   - SaaS/Productivity - Web app structure, auth, dashboard patterns
   - Startup - Lean structure, MVP patterns
   - Enterprise/B2B - Complex architecture, integrations
   - Consumer/Mobile - React Native, Flutter, mobile-first patterns

4. **Summarize findings** before proceeding:
   ```
   Product: [name]
   Type: [Developer Tool / SaaS / Startup / Enterprise / Consumer]
   Purpose: [1-sentence description]
   Audience: [target users]
   Existing colors: [hex codes if found, or "None detected"]
   Assets found: [list or "None"]
   ```

### Phase 2: Logo Design

Pick a style based on the detected project type (Developer/SaaS/Startup/Enterprise/Consumer), then design a minimalist, geometric mark that reads at every size from 16px favicon to hero banner. Use detected brand colors when present, else apply the Default Style Guide (dark base + neon-green highlights only — never as a fill). Confirm with the user how the product name should be cased in the wordmark before generating any text-bearing SVG.

See `references/design-principles.md` for the style table, full visual/color/typography rules, and the Default Style Guide palette with system status colors.

### Phase 3: Deliverables

Generate the canonical mark first, then derive 6 sibling variants from its exact path data so every file shares the same geometry. The `svg-generator` agent must receive the literal `d=""` strings — do not paraphrase shapes.

Output structure:

```
/assets/logo/
├── logo-mark.svg          # Canonical 64×64 mark (source of truth)
├── logo-full.svg          # 320×72 mark + wordmark
├── logo-wordmark.svg      # 180×40 text only
├── logo-icon.svg          # 512×512 app icon (centered, padded)
├── favicon.svg            # 16×16 simplified 2-layer mark
├── logo-white.svg         # 320×72 white (for dark backgrounds)
├── logo-black.svg         # 320×72 black (for light backgrounds)
└── brand-showcase.html    # Self-contained brand identity page
```

After writing all 7 files, read back mark, full, icon, white, and black variants and verify `d=""` strings are identical (or correctly scaled via `transform`). Fix divergences before continuing.

See `references/svg-deliverables.md` for full variant specifications, scale calculations, favicon simplification rules, and SVG requirements.

### Phase 4–5: Documentation & Brand Showcase

After SVGs are written, output the design rationale (symbol meaning, color choices, typography reasoning), a hex-code color specification, and a Tailwind config snippet. Then generate `/assets/logo/brand-showcase.html` — a self-contained presentation page (hero, design concept, variant grid, palette, typography, dev reference, footer) and open it in the browser.

See `references/brand-showcase.md` for the full HTML page structure, design guidelines, and the documentation template.

## Expected Output

For a CLI tool called "fastbuild", the skill produces:

```
/assets/logo/
├── logo-mark.svg          — 64×64 abstract "F" mark (canonical geometry)
├── logo-full.svg          — 320×72 mark + "FASTBUILD" wordmark
├── logo-wordmark.svg      — 180×40 text-only wordmark
├── logo-icon.svg          — 512×512 mark centered in rounded square
├── favicon.svg            — 16×16 simplified 2-layer mark
├── logo-white.svg         — 320×72 full logo in white (for dark backgrounds)
├── logo-black.svg         — 320×72 full logo in black (for light backgrounds)
└── brand-showcase.html    — self-contained brand identity presentation page
```

Design rationale summary presented to the user:
```
Product: fastbuild
Type: Developer/CLI Tool
Symbol: Abstract "F" from stacked horizontal speed bars
Colors: #0A0A0A base, #00FF41 neon green accent (borders and highlights only)
Typography: Inter Bold for wordmark
```

## Edge Cases

- **No project context found**: Ask the user for product name, product type, and one-sentence purpose before generating anything.
- **Existing brand colors detected**: Use them instead of the default dark/neon-green palette; confirm with the user before proceeding.
- **User does not specify wordmark casing**: Ask explicitly — do not assume README casing matches the desired logo stylization (e.g., "fastBuild" vs "FASTBUILD" vs "fastbuild").
- **SVG geometry diverges across variants**: After writing all 7 files, read back mark, full, icon, white, and black variants and verify `d=""` path strings are identical (or correctly scaled); fix before finishing.
- **No git repository**: Skip the branch and sync steps; write directly to the current directory and note this in the summary.
- **favicon.svg complexity**: At 16×16 the full mark is unreadable — always simplify to 2 layers (outer + inner) and drop the middle detail layer; preserve proportional geometry.
- **User rejects the proposed style**: Iterate on Phase 2 (style selection) until the user approves before generating any SVG files.

## Acceptance Criteria

- [ ] All 7 SVG files are written to `/assets/logo/` with the correct filenames
- [ ] `logo-mark.svg` is created first and its `d=""` path strings are used verbatim in all derived variants
- [ ] Every SVG has a correct `viewBox` attribute and contains no embedded rasters
- [ ] Monochrome variants (`logo-white.svg`, `logo-black.svg`) differ from `logo-full.svg` only in color, not geometry
- [ ] `favicon.svg` is a simplified 2-layer version of the mark at 16×16
- [ ] `brand-showcase.html` is written and opens correctly in a browser
- [ ] Design rationale (symbol meaning, color choices, typography) is documented in the response
- [ ] Color specification includes hex codes for all palette roles
- [ ] Wordmark casing is confirmed with the user before any SVG containing text is generated

## Step Completion Reports

After each phase, emit a `◆ [Phase] (step N of 4)` status block listing per-check pass/fail and a final `Result:` line (PASS | FAIL | PARTIAL). Keep the agent's context budget tight by reusing the template — do not re-paraphrase it per phase.

See `references/step-reports.md` for the full report template, per-phase check lists, and a worked Analysis Summary example.

## Notes

- Always show logo previews on both light (#FAFAFA) and dark (#0A0A0A) backgrounds
- Ask the user how they want the product name formatted in the wordmark before generating — do not assume README casing
- If no project context is found, ask the user for: product name, type, and purpose
- Prefer simplicity — a logo should be recognizable at 16x16 pixels
- **Consistency is non-negotiable**: every variant must be visually recognizable as the same logo. The mark shape, number of layers, and accent elements must match across all files. The only things that change between variants are: color (monochrome), scale (favicon, icon), and presence of wordmark. If you cannot verify that paths match, the deliverable is incomplete.
