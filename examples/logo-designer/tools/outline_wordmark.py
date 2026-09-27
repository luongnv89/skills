#!/usr/bin/env python3
"""Outline the 'AGENT SKILLS' wordmark for the Agent Skills logo lockup.

Pipeline: instance the Instrument Sans [wdth,wght] variable font at
wght=500 / wdth=100, shape the caps wordmark with harfbuzz (default
features, kerning on), apply +0.16em tracking to every advance except the
last, then emit one combined SVG path d-string (2-decimal coordinates)
with the ink spanning x=76.875..308.875 and caps centered on y=38.25 in
the 320x72 lockup. Also prints the transform for the standalone 180x40
wordmark file.

Dependencies (pinned, install into a venv):
    pip install fonttools==4.65.0 uharfbuzz==0.56.1

Font download (OFL):
    curl -L -o InstrumentSans-VF.ttf \\
      'https://github.com/google/fonts/raw/main/ofl/instrumentsans/InstrumentSans%5Bwdth,wght%5D.ttf'

Usage:
    python3 outline_wordmark.py [--vf InstrumentSans-VF.ttf]
                                [--static InstrumentSans-Medium.ttf]

Prints the metrics and the final d-string to stdout. Re-runnable.
"""
import argparse
import os

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path
from fontTools.misc.transform import Transform

TEXT = "AGENT SKILLS"
TRACKING_EM = 0.16

# Lockup (320x72) placement targets
INK_X0, INK_X1 = 76.875, 308.875
INK_W = INK_X1 - INK_X0            # 232
CAP_CENTER_Y = 38.25


def fmt(v):
    """Number -> string, max 2 decimals, no trailing zeros, no -0."""
    s = f"{v:.2f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def shape(font_path, text):
    data = open(font_path, "rb").read()
    face = hb.Face(data)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {})  # default features, kern on
    return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def glyph_positions(font, shaped):
    """Absolute (x, y) pen origin per glyph with tracking applied."""
    upm = font["head"].unitsPerEm
    track = TRACKING_EM * upm
    out, cursor = [], 0.0
    for n, (gid, adv, xo, yo) in enumerate(shaped):
        out.append((gid, cursor + xo, yo))
        cursor += adv + (track if n < len(shaped) - 1 else 0)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vf", default="InstrumentSans-VF.ttf",
                    help="Instrument Sans [wdth,wght] variable font "
                         "(default: %(default)s)")
    ap.add_argument("--static", default="InstrumentSans-Medium.ttf",
                    help="where to write the wght=500/wdth=100 instance "
                         "(default: %(default)s)")
    args = ap.parse_args()

    # 1. Instance wght=500, wdth=100 -> static TTF
    vf = TTFont(args.vf)
    instantiateVariableFont(vf, {"wght": 500, "wdth": 100}, inplace=True)
    vf.save(args.static)

    font = TTFont(args.static)
    glyphset = font.getGlyphSet()
    upm = font["head"].unitsPerEm
    s_cap = font["OS/2"].sCapHeight
    order = font.getGlyphOrder()

    shaped = shape(args.static, TEXT)
    positions = [(order[gid], gx, gy)
                 for gid, gx, gy in glyph_positions(font, shaped)]

    # 2. Ink bounds in font units (y-up space)
    bp = BoundsPen(glyphset)
    for gname, gx, gy in positions:
        tp = TransformPen(bp, Transform(1, 0, 0, 1, gx, gy))
        glyphset[gname].draw(tp)
    x_min, y_min, x_max, y_max = bp.bounds

    # Confirm sCapHeight against the top of "E"
    ebp = BoundsPen(glyphset)
    glyphset["E"].draw(ebp)
    e_top = ebp.bounds[3]

    # 3. Scale/translate into the 320x72 lockup
    s = INK_W / (x_max - x_min)
    baseline = CAP_CENTER_Y + (s_cap * s) / 2
    tx = INK_X0 - s * x_min

    # 4. Draw to SVG path data (y flipped)
    parts = []
    for gname, gx, gy in positions:
        sp = SVGPathPen(glyphset, ntos=lambda v: fmt(v))
        tp = TransformPen(sp, Transform(s, 0, 0, -s,
                                        tx + s * gx, baseline - s * gy))
        glyphset[gname].draw(tp)
        parts.append(sp.getCommands())
    d = "".join(parts)

    # 5. Post-round ink bounds of the emitted path (sanity)
    rp = RecordingPen()
    parse_path(d, rp)
    chk = BoundsPen(None)
    rp.replay(chk)
    rx0, ry0, rx1, ry1 = chk.bounds

    # 6. Standalone wordmark (180x40): same d, scaled 168/232, caps centered y=20
    r = 168 / 232
    wtx = 6 - rx0 * r
    wty = 20 - ((ry0 + ry1) / 2) * r

    print(f"unitsPerEm        : {upm}")
    print(f"font size (em px) : {s * upm:.4f}  (scale s = {s:.6f})")
    print(f"sCapHeight units  : {s_cap}  -> {s_cap * s:.4f} px")
    print(f"E top units       : {e_top}  (sCapHeight confirmed: {e_top == s_cap})")
    print(f"ink bounds (font) : x {x_min}..{x_max}, y {y_min}..{y_max}")
    print(f"lockup baseline   : {baseline:.4f}")
    print(f"lockup tx         : {tx:.4f}")
    print(f"path ink (rounded): x {rx0}..{rx1}, y {ry0}..{ry1}  w={rx1 - rx0:.2f}")
    print(f"wordmark scale r  : {r:.6f}  translate({wtx:.4f} {wty:.4f})")
    print("D-STRING:")
    print(d)


if __name__ == "__main__":
    main()
