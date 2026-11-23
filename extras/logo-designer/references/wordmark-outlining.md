# Wordmark Outlining

Use this reference in Phase 3, before any wordmark-bearing SVG is written. Every
wordmark is drawn as outlined `<path>` letterforms (`references/svg-deliverables.md`).
This is the method for producing them from a real font file: check the licence,
pick a static weight, outline the glyphs once with fontTools, and paste the same
paths into every wordmark file.

## Step 1: Find the font file

The typeface comes from Phase 2 (`references/design-principles.md`). Outlining needs
the actual `.ttf` or `.otf` file, in this order:

1. A font file the project already ships, or one the user names.
2. An installed font: `fc-list : family style file` lists them (on macOS also look
   in `~/Library/Fonts` and `/Library/Fonts`).
3. A download, only after the user agrees, from the family's own repository or
   Google Fonts. Both ship OFL families with a `static/` folder of single-weight files.

`system-ui` and `sans-serif` are CSS fallbacks, not files. Never outline a platform
UI font (San Francisco, Segoe UI): its licence covers use on that platform, not in a
logo. Agree a named family with the user instead.

## Step 2: Check the licence before outlining

Read the font's own licence fields. Run it with fontTools (see *Running fontTools*):

```python
import sys
from fontTools.ttLib import TTFont

font = TTFont(sys.argv[1])
name = font["name"]
print("family:  ", name.getDebugName(1), name.getDebugName(2))
print("licence: ", name.getDebugName(13))
print("URL:     ", name.getDebugName(14))
print("fsType:  ", hex(font["OS/2"].fsType))
print("variable:", "fvar" in font)
```

- **Proceed** when the licence text or URL (name IDs 13 and 14), or an `OFL.txt` or
  `LICENSE` beside the file, names the SIL Open Font License or Apache 2.0, and
  `fsType` has neither the `0x0002` bit (restricted licence embedding) nor the
  `0x0200` bit (bitmap embedding only).
- **Stop and ask** for anything else: a commercial or unknown licence, an empty
  name ID 13, or either restricted bit. The user either confirms they hold a licence
  that allows logo use, or picks an OFL family. `fsType` only describes embedding
  rights, so a clear `fsType` never replaces the licence text.

Record the family, weight, file name and licence. They go in the design rationale
and the Final Report's `Evidence:` line.

## Step 3: Use a static weight, not a variable font

A variable font (`Family[wght].ttf`, or any file whose `variable:` line above
prints `True`) outlines its **default** instance, whatever weight is wanted. For
JetBrains Mono, the `[wght]` file outlines weight 400 even when Bold was chosen.

- Use the static file for the chosen weight (`Family-Bold.ttf`, often in `static/`).
- With only a variable file, pin the weight first and outline the instance:

  ```bash
  fonttools varLib.instancer "Family[wght].ttf" wght=700 -o family-700.ttf
  ```

  Its contours can overlap, so keep the SVG default `fill-rule` (`nonzero`) and
  never set `evenodd` on the letters.

The outliner below refuses a variable font.

## Step 4: Outline the wordmark once

Write this script to a temporary directory outside the project. It is a tool for
this run, never a deliverable.

```python
# outline_wordmark.py FONT TEXT [CAP] [GAP]
#   CAP: cap height in SVG units (default 24)
#   GAP: ink gap between letters in font units (default: the font's own spacing)
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointInsidePen import PointInsidePen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONT, TEXT = sys.argv[1], sys.argv[2]
CAP = float(sys.argv[3]) if len(sys.argv) > 3 else 24.0
GAP = float(sys.argv[4]) if len(sys.argv) > 4 else None

font = TTFont(FONT)
if "fvar" in font:
    sys.exit("variable font: use a static weight file or instance one (Step 3)")
if font["OS/2"].fsType & 0x0202:
    sys.exit("fsType restricts embedding: stop and ask the user (Step 2)")
gs, cmap = font.getGlyphSet(), font.getBestCmap()
missing = sorted({c for c in TEXT + "nI" if ord(c) not in cmap})
if missing:
    sys.exit(f"font has no glyph for {missing}")

def bounds(g):
    pen = BoundsPen(gs)
    gs[g].draw(pen)
    return pen.bounds  # None for a space

def stem(ch, y):
    """Width in font units of the first stem crossed at height y."""
    g, run = cmap[ord(ch)], 0
    for x in range(int(gs[g].width)):
        pen = PointInsidePen(gs, (x, y))
        gs[g].draw(pen)
        if pen.getResult():
            run += 1
        elif run:
            break
    return run

def fmt(n):
    t = f"{n:.2f}".rstrip("0").rstrip(".")
    return "0" if t == "-0" else t

cap = getattr(font["OS/2"], "sCapHeight", 0) or bounds(cmap[ord("I")])[3]
s = CAP / cap
x, right, paths = 0.0, None, []
for ch in TEXT:
    g = cmap[ord(ch)]
    b = bounds(g)
    if b is None:  # a space advances and draws nothing
        x, right = x + gs[g].width, None
        continue
    if not paths:
        x = -b[0]  # first ink starts at x = 0
    elif GAP is not None and right is not None:
        x = right + GAP - b[0]
    pen = SVGPathPen(gs, ntos=fmt)
    gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x * s, CAP)))  # flip y, baseline at CAP
    paths.append(f'  <path d="{pen.getCommands()}"/>')
    right = x + b[2]
    x += gs[g].width

probe = "I" if TEXT.isupper() else "n"
y = cap / 2 if probe == "I" else (getattr(font["OS/2"], "sxHeight", 0) or cap) / 2
w = stem(probe, y)
print(f"<!-- {font['name'].getDebugName(4)}: cap {fmt(CAP)}, baseline y={fmt(CAP)}, "
      f"right edge x={fmt(right * s)}, stem {fmt(w * s)} ({w} font units) -->")
print("\n".join(paths))
```

`python3 -I outline_wordmark.py Family-Bold.ttf sfm` prints one `<path>` per letter,
in SVG units: x offsets are baked in, y is flipped (font units point up, SVG units
point down), the baseline sits at `y = CAP` and the first letter's ink starts at
`x = 0`. The comment line gives the ink's right edge, which is the wordmark width
wherever `references/svg-deliverables.md` sizes a canvas from it, and the stem width
used in Step 6. The script places letters by the font's advance widths only, with no
kerning (`GPOS`) or ligatures, so Step 5 checks the spacing.

## Step 5: Space the letters

Render the wordmark (`references/png-export.md`) and look at it at 720 px wide and at
a small size, then adjust and re-run the script. Never edit one letter's `d` by hand.

- **Monospaced fonts** (every letter has the same advance width, `post.isFixedPitch`
  set) give narrow letters (`i`, `l`, `j`, `t`, `f`, `r`, `1`) the same cell as `m`, so
  the gaps look uneven. Pass `GAP`, the gap from one letter's ink to the next in font
  units. Start at the stem's font units printed by a first run and tighten while the
  render still looks even; a logo wordmark usually lands between half a stem and one
  stem (JetBrains Mono Bold `sfm`: stem 125, gap 90).
- **Proportional fonts:** keep the font's spacing (no `GAP`) and check the pairs
  kerning normally fixes (`AV`, `To`, `Ty`, `LT`, `r.`, `ry`). One loose pair is
  fixed by passing a `GAP` that also suits the other pairs, or by drawing that pair
  as two runs of the script and joining them, never by moving one path.
- Round and diagonal sides (`o`, `c`, `v`) can sit closer than straight stems (`n`,
  `l`, `i`); a gap below half the stem lets letters merge in the small PNGs.

## Step 6: Match the weight to the mark

The wordmark's stems should look as heavy as the mark's strokes. Compare the stem
width from the script, scaled the way the lockup scales the wordmark, with the mark's
`stroke-width` as rendered in the lockup (times any `scale()` on the mark group).
For a filled mark, compare with its thinnest bar. Pick the static weight whose stem
comes within about 15% of the stroke, re-running Steps 4 and 5 for each weight you
try. The stem is measured on `n`, or on `I` for an all-caps wordmark.

## Step 7: Reuse one set of paths in every wordmark file

The script's output is the only copy of the letterforms. Paste its `<path>` lines,
byte for byte, into `logo-wordmark.svg`, `logo-full.svg`, `logo-white.svg` and
`logo-black.svg`. Each file wraps them in its own group, and only the group's
transform and fill differ:

```xml
<g transform="translate(76 22) scale(1.1)" fill="#FAFAFA" aria-label="sfm">
  <path d="…"/>
  …
</g>
```

Hand the paths to `agents/svg-generator.md` as literal `wordmark_paths`, the same way
the mark's `canonical_paths` are handed over. Any change to the font, weight, `CAP`
or `GAP` means re-running the script and replacing the paths in all four files.
After writing them, check that every letter in `logo-wordmark.svg` appears unchanged
in each lockup (no output means they match):

```bash
for f in logo-full logo-white logo-black; do
  comm -23 <(grep -o 'd="[^"]*"' assets/logo/logo-wordmark.svg | sort) \
           <(grep -o 'd="[^"]*"' assets/logo/$f.svg | sort)
done
```

## Running fontTools

Check with `python3 -c "import fontTools"`. When it is missing, ask the user before
installing anything, then use a throwaway virtual environment outside the project,
never the project's own:

```bash
python3 -m venv "${TMPDIR:-/tmp}/logo-fonttools"
"${TMPDIR:-/tmp}/logo-fonttools/bin/pip" install fonttools
"${TMPDIR:-/tmp}/logo-fonttools/bin/python" -I outline_wordmark.py Family-Bold.ttf sfm
```

When fontTools cannot be used (the user declines, or there is no network), Inkscape
can outline a licence-checked font: write a `<text>` draft and convert it with
`--export-text-to-path` (`references/png-export.md`, Step 1), then reuse the
converted paths as in Step 7. With neither, draw the letters by hand as geometric
paths and say so under `Uncertainty:` in the Final Report.
