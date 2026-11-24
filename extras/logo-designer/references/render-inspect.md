# Render and Inspect (Gates 1–3)

The `d=""` read-back and `svg-reviewer` prove that the variants match each other, not
that the mark is good. Only a render shows a weak composition, a gap that closes at
16 px, or ink that vanishes on a light tab bar. Three gates render the files and look
at them, each before the step it guards. The main agent runs them, because it can
read a PNG as an image. `svg-reviewer` stays a markup review.

| Gate | Runs | Guards |
|------|------|--------|
| 1. Canonical mark | After `logo-mark.svg` is written | Deriving the 6 variants |
| 2. Favicon | After `favicon.svg` is written | `svg-reviewer` (Phase 4) |
| 3. Shipped files | After the Phase 3b PNGs and `brand-showcase.html` | A `COMPLETE` Final Report |

A render nobody looked at is not a pass. Open every preview with the image-reading
tool (Read on the PNG). Name each finding by file, size and background.

## Setup (start of Phase 3)

Detect the rasterizer once, by `references/png-export.md` *Step 2*, and reuse it in
Phase 3b. Previews go to a temporary directory, never into `/assets/logo/` or `png/`,
which hold only deliverables:

```bash
preview="$(mktemp -d)"
```

Render an SVG at `S`×`S` px on background `BG`:

| Tool | Command |
|------|---------|
| `rsvg-convert` | `rsvg-convert -w S -h S -b 'BG' IN.svg -o OUT.png` |
| `magick` | `magick -background 'BG' -density D IN.svg -resize 'SxS!' -flatten OUT.png` (`D` = 72 × S ÷ viewBox width, rounded up) |
| `inkscape` | `inkscape IN.svg --export-type=png --export-filename=OUT.png -w S -h S --export-background='BG' --export-background-opacity=1` |
| Chrome | The `references/png-export.md` command with `--default-background-color=` set to `BG` as 8 hex digits (`FAFAFAFF`, `0A0A0AFF`). If a run writes no file, run it once more |

**Enlarge the small renders before looking.** A 16 px PNG shown as is gets smoothed
by the viewer, and a closed gap looks open. With `magick`, scale it with nearest
neighbour so each pixel stays a square:

```bash
magick OUT.png -filter point -resize 800% OUT-x8.png
```

Do this for every 16 and 32 px render. Without `magick`, view the renders unenlarged
and put `16 px renders viewed unenlarged` on the Final Report's `Uncertainty:` line.

## Gate 1: canonical mark, before any variant

Run it as soon as `logo-mark.svg` exists, before `svg-generator` derives anything.

1. Render `logo-mark.svg` at 16, 32, 64 and 512 px on the brand background
   (`references/svg-deliverables.md`). Enlarge the 16 and 32 px renders.
2. Look at each render:
   - **512 px:** the shape draws `brief.mark_idea`; it is optically centered, layers that
     share a role share one stroke width, and edges sit on the grid.
   - **64 and 16 px:** the silhouette is still recognisable; every gap between layers
     shows as background pixels, not a tinted blur; no two layers merge.
   - **Every size:** no glow, blur or halo, no gradient, no shadow, and no initial-only
     mark unless the brief records its idea or the user's request.
3. **Cut before deriving.** Use the fewest layers that carry the idea
   (`references/design-principles.md`, *Fewest layers*). For each layer and accent,
   render a copy without it at 64 and 16 px. If neither render changes in a way you
   can see, cut that layer from `logo-mark.svg`. A layer the user asked for by
   name in Phase 2 is cut only after the user agrees. The cut is reduce-only: Gate 1
   never adds a layer. Remove the layer's entry from `brief.decisions.layers` before
   `svg-reviewer` runs, since its layer-count check reads that list. Record
   `{"layer": "...", "reason": "no visible change at 64 or 16 px"}` in
   `brief.decisions.cut_layers`, and name the cut in the Phase 3 step report.
4. **Fail:** redraw `logo-mark.svg` and run Gate 1 again. After three failed redraws,
   show the user the findings with the renders and ask for a direction. A changed
   decision goes back through Phase 2. Never derive variants from a failing mark.
5. **Pass:** give `svg-generator` the gated mark's literal `d=""` strings.

## Gate 2: favicon, before svg-reviewer

Run it after `svg-generator` writes `favicon.svg`, and finish it before Phase 4. A
fix edits `favicon.svg` only, so no other variant changes.

1. **Separation after thickening (geometry).** In the favicon's `0 0 16 16` viewBox,
   1 unit is 1 px at 16 px. Between every two distinct elements (layers, accent,
   tile edge), measure the clearance from edge to edge, counting half of each
   stroke width. It must be at least 1 unit, and the two edges of a 1-unit gap must
   sit on whole units. A gap from 7 to 8 renders as one clean background column. A
   1-unit gap from 7.5 to 8.5 renders as two half-tinted columns, and a 0.72-unit
   gap as one tinted column: both read as touching. Make a gap that cannot sit on
   whole units at least 2 units wide. Thickening a stroke for the favicon must never
   take a gap below this; when both cannot fit, drop the smaller element.
2. **Ink against tab colors, then the tile.** Measure the silhouette layer against
   `#FAFAFA` and `#0A0A0A` (`references/svg-deliverables.md`, *Step 4*). Recolor
   first: use a palette color that reaches 3:1 against both. Only when no palette
   color does, give `favicon.svg` its own tile: a full-canvas rounded square
   (`<path>` or `<rect>` covering `0 0 16 16`, radius about 3) in a palette color
   that the mark reaches 3:1 against. Measure the mark against the tile from then on.
   The Default Style Guide needs the tile: no default color reaches 3:1 on both tab
   colors (`#00FF41` is about 1.3:1 on `#FAFAFA`). The tile is part of the favicon,
   so the browser's tab color still never changes. It is the only allowed exception
   to "fix a failing color, never the background".
3. **Render and look.** Render `favicon.svg` at 16, 32 and 48 px on `#FAFAFA` and on
   `#0A0A0A` (six PNGs). Enlarge the 16 and 32 px renders. Check that each element
   is still distinct with background pixels between, the shape reads as
   `logo-mark.svg`, the ink or the tile stands out on both tab colors, and no detail
   is under 1 px. An accent stays only when it reads as its own element with the
   clearance above in the 16 px render; otherwise drop it.
4. **Fail:** fix `favicon.svg`, then run Gate 2 again before Phase 4.

## Gate 3: shipped files, before COMPLETE

Run it after the Phase 3b dimension check and after `brand-showcase.html` is
written. `$CHROME` is the Chrome or Chromium binary from `references/png-export.md`
*Step 2*.

1. **Every PNG.** Open each file in `png/`. It must show the same shape as its SVG,
   with no substituted font and nothing clipped. A white or transparent PNG is hard
   to judge on its own, so also view it on its intended background:
   `magick IN.png -background '#0A0A0A' -flatten "$preview/IN-on-bg.png"`, or render
   its SVG on that background with the setup table.
2. **Showcase at desktop width:**

   ```bash
   "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1440,4000 \
     --screenshot="$preview/showcase-1440.png" "file://$PWD/assets/logo/brand-showcase.html"
   ```

3. **Showcase at 390 px:** headless Chrome lays out no window narrower than about
   500 px. A `--window-size=390,…` screenshot is 390 px wide but shows a 500 px
   layout cut off on the right. Load the page in a 390 px iframe instead:

   ```bash
   printf '<!doctype html><body style="margin:0;background:#888"><iframe src="file://%s" width="390" height="4000" style="border:0;display:block"></iframe></body>\n' \
     "$PWD/assets/logo/brand-showcase.html" > "$preview/frame-390.html"
   "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=600,4000 \
     --screenshot="$preview/showcase-390.png" "file://$preview/frame-390.html"
   ```

   The grey band right of 390 px is the wrapper page, not the showcase.
4. **Check both screenshots and the PNGs against the ban list:**
   - a glow, blur or halo around any shape
   - a gradient: a color that shifts across a shape, card or background
   - a shadow under a static card or under text
   - a mark that is only the product's initial, unless the brief records its idea or the user's request
   - small, uppercase, letter-spaced section labels
   - a broken image, a PNG link to a missing file, or placeholder text
   - at 390 px: content cut off at the right, a horizontal scrollbar, or a grid that did not collapse to one column
   - any `brief.bans` entry, unless `brief.lifted_bans` names it
5. **A hit:** fix the file and re-run its own checks. For an SVG, that is the
   read-back, `svg-reviewer` and its PNG. For the showcase, that is the grep in
   `references/brand-showcase.md`. Then take the screenshots again and look again.

## When a gate cannot run

| Missing | What still runs | Final status |
|---------|-----------------|--------------|
| No rasterizer | Gates 1 and 2 check geometry only: clearance in units, contrast by the formula, the layer cut by reasoning. Gate 3 has no PNGs. Say the renders did not run | `PARTIAL` (already, for the missing PNGs) |
| `magick` | Every render, viewed unenlarged | Unchanged; `Uncertainty:` names it |
| Chrome | The PNG check of Gate 3; no screenshots | `PARTIAL`; `Decision:` names installing Chrome or Chromium |
| A way to view images | Renders written but not viewed | `PARTIAL`; `Uncertainty:` says the gates rendered but nobody looked |

## Reporting

The Phase 3 step report has one row per gate (`references/step-reports.md`). The Final
Report's `Evidence:` line names each gate that ran, with its sizes and backgrounds,
every finding it fixed, and any layer it cut, and a gate that did not run goes on
`Uncertainty:` (`references/final-report.md`).
