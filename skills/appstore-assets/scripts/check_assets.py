#!/usr/bin/env python3
"""Verify an App Store asset set before upload, and optionally build review sheets.

Checks every image under OUT_DIR's class folders against App Store Connect's
upload rules: an accepted pixel size for its display class, RGB with no alpha
channel, at most 10 screenshots per class, the required class present for each
platform, and the same frame names across the iPhone classes. Optional WCAG
contrast checks cover caption color pairs.

Usage:
  python3 check_assets.py OUT_DIR --platforms iphone,ipad,mac
         [--sheet SHEET_DIR] [--pair "#1d5fd6/#e6edf8@3" ...]

Exit 0 = every check passed. Exit 1 = at least one FAIL row (each says why).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed, so images cannot be inspected.\n"
          "Fix: python3 -m pip install pillow", file=sys.stderr)
    sys.exit(1)


def both(*sizes: tuple[int, int]) -> set[tuple[int, int]]:
    """Portrait sizes plus their landscape rotations."""
    return {s for w, h in sizes for s in ((w, h), (h, w))}


# Accepted sizes per folder, from App Store Connect's screenshot specifications.
ACCEPTED = {
    "iphone-6.9": both((1320, 2868), (1290, 2796), (1260, 2736)),
    "iphone-6.3": both((1206, 2622), (1179, 2556)),
    "ipad-13": both((2064, 2752), (2048, 2732)),
    "mac": {(1280, 800), (1440, 900), (2560, 1600), (2880, 1800)},
}
REQUIRED = {"iphone": "iphone-6.3", "ipad": "ipad-13", "mac": "mac"}
CREATIVE = {"header": {(3840, 1646)}, "universal": {(5244, 2950)}}
MAX_PER_CLASS = 10


def search_ok(size: tuple[int, int]) -> bool:
    w, h = size
    return 1920 <= w <= 3840 and w * 2 == h * 3


def contrast(fg: str, bg: str) -> float:
    def lum(hexcolor: str) -> float:
        c = hexcolor.lstrip("#")
        if len(c) != 6:
            raise ValueError(f"'{hexcolor}' is not a #rrggbb color")
        ch = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        ch = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def inspect(path: Path, accepted: set | None, kind: str | None) -> tuple[bool, str]:
    try:
        img = Image.open(path)
    except OSError as e:
        return False, f"unreadable image ({e})"
    fmt, mode, size = img.format, img.mode, img.size
    if fmt not in ("PNG", "JPEG"):
        return False, f"format {fmt}; App Store Connect accepts PNG or JPEG"
    if mode != "RGB" or "transparency" in img.info:
        return False, f"mode {mode}{' with transparency' if 'transparency' in img.info else ''}; re-render or convert to RGB (no alpha)"
    if kind == "search":
        if not search_ok(size):
            return False, f"{size[0]}x{size[1]} is not 3:2 between 1920x1280 and 3840x2560"
    elif kind == "universal" and fmt != "PNG":
        return False, "the 16:9 universal creative must be PNG"
    elif accepted is not None and size not in accepted:
        want = ", ".join(f"{w}x{h}" for w, h in sorted(accepted))
        return False, f"{size[0]}x{size[1]} is not accepted here; use {want}"
    return True, f"{size[0]}x{size[1]} {mode} {fmt}"


def sheet(files: list[Path], out: Path, thumb_w: int = 300) -> None:
    thumbs = []
    for f in files:
        im = Image.open(f).convert("RGB")
        im.thumbnail((thumb_w, thumb_w * 3), Image.LANCZOS)
        thumbs.append(im)
    gap = 12
    canvas = Image.new("RGB", (sum(t.width for t in thumbs) + gap * (len(thumbs) + 1),
                               max(t.height for t in thumbs) + gap * 2), "white")
    x = gap
    for t in thumbs:
        canvas.paste(t, (x, gap))
        x += t.width + gap
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", type=Path, help="asset-set folder holding iphone-6.9/, iphone-6.3/, ipad-13/, mac/, creative/")
    ap.add_argument("--platforms", required=True, help="platforms the app ships, e.g. iphone or iphone,ipad,mac")
    ap.add_argument("--sheet", type=Path, help="write one contact sheet per folder here for visual review")
    ap.add_argument("--pair", action="append", default=[], help='caption color pair "FG/BG[@MIN]", MIN defaults to 4.5')
    a = ap.parse_args()

    if not a.out.is_dir():
        print(f"Error: {a.out} is not a folder.\nFix: pass the asset-set folder that render.py wrote into.", file=sys.stderr)
        sys.exit(1)
    platforms = [p.strip() for p in a.platforms.split(",") if p.strip()]
    bad = [p for p in platforms if p not in REQUIRED]
    if bad:
        print(f"Error: unknown platform(s) {', '.join(bad)}.\nFix: use iphone, ipad and/or mac.", file=sys.stderr)
        sys.exit(1)

    rows, failures = [], 0
    names: dict[str, list[str]] = {}
    for folder in [*ACCEPTED, "creative"]:
        d = a.out / folder
        files = sorted(p for p in d.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")) if d.is_dir() else []
        if not files:
            continue
        names[folder] = [f.stem for f in files]
        for f in files:
            kind = f.stem.split("-")[0] if folder == "creative" else None
            if folder == "creative" and kind not in ("header", "search", "universal"):
                ok, why = False, "creative files must be named header*, search* or universal*"
            else:
                ok, why = inspect(f, CREATIVE.get(kind) if folder == "creative" else ACCEPTED[folder], kind)
            failures += not ok
            rows.append((f"{folder}/{f.name}", "PASS" if ok else "FAIL", why))
        if folder != "creative" and len(files) > MAX_PER_CLASS:
            failures += 1
            rows.append((f"{folder}/", "FAIL", f"{len(files)} screenshots; App Store Connect allows {MAX_PER_CLASS} per class"))
        if a.sheet:
            sheet(files, a.sheet / f"{folder}.png")

    for p in platforms:
        need = REQUIRED[p]
        if need not in names:
            failures += 1
            rows.append((f"{need}/", "FAIL", f"{p} ships but the required {need} class has no screenshots"))
    if "iphone-6.9" in names and "iphone-6.3" in names and names["iphone-6.9"] != names["iphone-6.3"]:
        failures += 1
        rows.append(("iphone-*", "FAIL", "iphone-6.9 and iphone-6.3 hold different frame sets; render both from the same config"))

    for spec in a.pair:
        try:
            colors, _, minimum = spec.partition("@")
            fg, bg = colors.split("/")
            ratio, need = contrast(fg, bg), float(minimum or 4.5)
        except ValueError as e:
            print(f'Error: bad --pair "{spec}": {e}.\nFix: use "#rrggbb/#rrggbb" with an optional "@3" minimum.', file=sys.stderr)
            sys.exit(1)
        ok = ratio >= need
        failures += not ok
        rows.append((f"contrast {fg} on {bg}", "PASS" if ok else "FAIL", f"{ratio:.2f}:1 (needs {need}:1)"))

    if not rows:
        print(f"Error: no images found under {a.out}.\nFix: run render.py first, or pass the folder it wrote into.", file=sys.stderr)
        sys.exit(1)
    width = max(len(r[0]) for r in rows)
    for name, verdict, why in rows:
        print(f"{verdict}  {name.ljust(width)}  {why}")
    if a.sheet:
        print(f"Contact sheets: {a.sheet}")
    print(f"{'FAIL' if failures else 'PASS'}: {len(rows) - failures}/{len(rows)} checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
