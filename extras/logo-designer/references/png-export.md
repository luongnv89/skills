# PNG Export (Phase 3b)

Most upload targets (plugin and marketplace avatars, GitHub social previews, app stores,
social profiles) accept only raster images. After the SVGs pass the Phase 3 geometry
read-back and the `svg-reviewer` check, render a PNG of every variant into
`assets/logo/png/`. Render from those final verified SVGs, never from an earlier draft,
so each PNG has the same geometry as its SVG.

## Step 1: Confirm the SVGs need no fonts

A rasterizer substitutes whatever font is installed for a `<text>` element, so the PNG
would not match the SVG. The wordmark must already be outlined `<path>` geometry
(`agents/svg-generator.md`). Check before rendering:

```bash
grep -lE '<(text|tspan)[ >]|@font-face' assets/logo/*.svg
```

No output means every SVG is outlined. For each file it lists, redraw the text as
`<path>` letterforms, or, with Inkscape installed, convert the text in place:

```bash
inkscape FILE.svg --export-text-to-path --export-plain-svg --export-filename=FILE.svg
```

Re-run the Phase 3 read-back on any file you changed, then run the `grep` again.

## Step 2: Detect a rasterizer

Use the first tool found, in this order:

```bash
command -v rsvg-convert || command -v magick || command -v inkscape
```

If none is found, look for a Chrome or Chromium binary: `google-chrome`, `chromium` or
`chromium-browser` on `PATH`, or `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
on macOS.

**No rasterizer found:** skip Steps 3 and 4, keep the SVGs and the showcase, and end with a
`PARTIAL` Final Report whose `Decision:` names the install command:
`brew install librsvg` (macOS) or `sudo apt install librsvg2-bin` (Debian/Ubuntu).

## Step 3: Render every size

| Source | PNG output | Size (px) |
|--------|-----------|-----------|
| `logo-icon.svg` | `png/logo-icon-512.png`, `png/logo-icon-1024.png` | 512×512, 1024×1024 |
| `logo-mark.svg` | `png/logo-mark-512.png` (transparent background) | 512×512 |
| `logo-full.svg` | `png/logo-full.png` | 1280×288 |
| `logo-white.svg` | `png/logo-white.png` | 1280×288 |
| `logo-black.svg` | `png/logo-black.png` | 1280×288 |
| `logo-wordmark.svg` | `png/logo-wordmark.png` | 720×160 |
| `favicon.svg` | `png/favicon-16.png`, `png/favicon-32.png`, `png/favicon-48.png` | 16, 32, 48 square |

Every size is an exact multiple of its viewBox, so always pass both width and height.
Run `mkdir -p assets/logo/png` first. One command per row and size, with `W`×`H` from
the table:

| Tool | Command |
|------|---------|
| `rsvg-convert` | `rsvg-convert -w W -h H IN.svg -o OUT.png` |
| `magick` | `magick -background none -density D IN.svg -resize 'WxH!' -depth 8 PNG32:OUT.png` |
| `inkscape` (1.x) | `inkscape IN.svg --export-type=png --export-filename=OUT.png -w W -h H` |
| Chrome | `"$CHROME" --headless=new --disable-gpu --hide-scrollbars --default-background-color=00000000 --window-size=W,H --screenshot=OUT.png "file://$PWD/IN.svg"` |

- **magick:** `-background none` and `-density` go *before* the input, or the PNG is
  blurred and the transparent background turns opaque. Set `D` to
  `72 × W ÷ viewBox width`, rounded up (for example 576 for the 512 px mark), and keep
  `-depth 8`, or magick writes 16-bit PNGs. The `PNG32:` prefix keeps the output RGBA, since magick may otherwise save a palette PNG.
- **inkscape 0.92** uses `--export-png=OUT.png -w W -h H` instead.
- **Chrome** renders the SVG at the window size; the 8-digit background color keeps it
  transparent.

**Optional `favicon.ico`:** with `magick` installed, bundle the three favicon PNGs:

```bash
magick assets/logo/png/favicon-16.png assets/logo/png/favicon-32.png assets/logo/png/favicon-48.png assets/logo/png/favicon.ico
```

## Step 4: Verify dimensions

Measure each PNG; never copy the size from the table:

```bash
file assets/logo/png/*.png
```

Each line must read `PNG image data, W x H` with the table's size, and
`logo-mark-512.png` must be `RGBA`. `magick identify -format '%f %wx%h\n'
assets/logo/png/*.png` or, on macOS, `sips -g pixelWidth -g pixelHeight` give the same
numbers. Re-render any PNG with the wrong size. Cite the measured sizes in the Final
Report's `Evidence:` line (`references/final-report.md`).
