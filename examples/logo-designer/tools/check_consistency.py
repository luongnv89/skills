#!/usr/bin/env python3
"""Consistency checks for the Agent Skills logo suite.

Usage: python3 check_consistency.py [LOGO_DIR] [--docs-copy DOCS_DIR]

LOGO_DIR defaults to assets/logo relative to the working directory.
--docs-copy points at a directory holding copies that must be
byte-identical to the LOGO_DIR files of the same name
(e.g. docs/assets/logo).
"""
import argparse
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"

EXPECTED_VIEWBOX = {
    "logo-mark.svg": "0 0 64 64",
    "logo-full.svg": "0 0 320 72",
    "logo-wordmark.svg": "0 0 180 40",
    "logo-icon.svg": "0 0 512 512",
    "favicon.svg": "0 0 16 16",
    "logo-white.svg": "0 0 320 72",
    "logo-black.svg": "0 0 320 72",
}
RING = "M42.75 13.72A1 1 0 0 1 44.24 12.85A24.875 24.875 0 1 1 19.76 12.85A1 1 0 0 1 21.25 13.72V18.16A1 1 0 0 1 20.83 18.97A19.125 19.125 0 1 0 43.17 18.97A1 1 0 0 1 42.75 18.16Z"
CARD_PREFIX = "M26.75 4.5H33.69"
MARK_FILES = ["logo-mark.svg", "logo-full.svg", "logo-icon.svg",
              "logo-white.svg", "logo-black.svg"]
WORDMARK_FILES = ["logo-full.svg", "logo-white.svg", "logo-black.svg",
                  "logo-wordmark.svg"]
DOCS_COPIES = ["favicon.svg", "logo-full.svg", "logo-icon.svg"]

results = []

def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

def paths_of(tree):
    return [e.get("d") for e in tree.iter() if e.tag == NS + "path"]

def normalize_fills(text):
    return re.sub(r'(fill|stroke)="#[0-9A-Fa-f]{6}"', r'\1="X"', text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logo_dir", nargs="?", default="assets/logo")
    ap.add_argument("--docs-copy", default=None)
    args = ap.parse_args()
    d = pathlib.Path(args.logo_dir)

    trees, texts = {}, {}
    for name in EXPECTED_VIEWBOX:
        p = d / name
        texts[name] = p.read_text()
        trees[name] = ET.parse(p)

    # RING + CARD byte-identical across mark-bearing files
    for name in MARK_FILES:
        ds = paths_of(trees[name])
        check(f"{name}: RING d verbatim", RING in ds)
        card = [x for x in ds if x and x.startswith(CARD_PREFIX)]
        check(f"{name}: CARD d verbatim",
              len(card) == 1 and card[0] == CARD_CANON)
        check(f"{name}: card carries fill-rule=evenodd",
              any(e.get("fill-rule") == "evenodd"
                  for e in trees[name].iter() if e.tag == NS + "path"
                  and (e.get("d") or "").startswith(CARD_PREFIX)))

    # WORDMARK identical across the four wordmark files
    wm = {}
    for name in WORDMARK_FILES:
        ds = [x for x in paths_of(trees[name])
              if x and not x.startswith("M42.75") and not x.startswith(CARD_PREFIX)]
        check(f"{name}: single wordmark path", len(ds) == 1,
              f"{len(ds)} candidate(s)")
        if ds:
            wm[name] = ds[0]
    if wm:
        ref = wm["logo-full.svg"]
        for name in WORDMARK_FILES[1:]:
            check(f"{name}: wordmark d identical to logo-full",
                  wm.get(name) == ref)

    # viewBoxes
    for name, vb in EXPECTED_VIEWBOX.items():
        root = trees[name].getroot()
        check(f"{name}: viewBox={vb}", root.get("viewBox") == vb,
              f"got {root.get('viewBox')}")
        check(f"{name}: no root width/height",
              root.get("width") is None and root.get("height") is None)
        check(f"{name}: role+aria-label+title",
              root.get("role") == "img"
              and root.get("aria-label") == "Agent Skills"
              and any(e.tag == NS + "title" for e in root))

    # no rasters / text elements
    for name in EXPECTED_VIEWBOX:
        t = texts[name]
        check(f"{name}: no <image>/data:/<text>",
              "<image" not in t and "data:" not in t and "<text" not in t)

    # white/black differ from full only in fills
    for name in ("logo-white.svg", "logo-black.svg"):
        check(f"{name}: identical to logo-full except fills",
              normalize_fills(texts[name]) == normalize_fills(texts["logo-full.svg"]))

    # docs copies byte-identical
    if args.docs_copy:
        dd = pathlib.Path(args.docs_copy)
        for name in DOCS_COPIES:
            a, b = (d / name).read_bytes(), (dd / name).read_bytes()
            check(f"docs copy {name} byte-identical", a == b)

    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


CARD_CANON = "M26.75 4.5H33.69A0.75 0.75 0 0 1 34.22 4.72L39.28 9.78A0.75 0.75 0 0 1 39.5 10.31V33.75A2.25 2.25 0 0 1 37.25 36H26.75A2.25 2.25 0 0 1 24.5 33.75V6.75A2.25 2.25 0 0 1 26.75 4.5ZM26.75 28.75A0.75 0.75 0 0 1 28.25 28.75V31.75A0.75 0.75 0 0 1 26.75 31.75ZM29.75 28.75A0.75 0.75 0 0 1 31.25 28.75V31.75A0.75 0.75 0 0 1 29.75 31.75ZM32.75 28.75A0.75 0.75 0 0 1 34.25 28.75V31.75A0.75 0.75 0 0 1 32.75 31.75ZM35.75 28.75A0.75 0.75 0 0 1 37.25 28.75V31.75A0.75 0.75 0 0 1 35.75 31.75Z"

if __name__ == "__main__":
    main()
