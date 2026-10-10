#!/usr/bin/env python3
"""Render App Store screenshots and creative assets from an asset-set src/ folder.

The src/ folder is a copy of the skill's assets/template/ with config.js
rewritten for one app. One headless Chrome launch renders one asset at an
exact CSS viewport and device scale factor; Pillow flattens it to RGB (App
Store Connect rejects alpha) and the exact pixel size is verified.

Usage:
  python3 render.py --preflight [--chrome PATH]      # check Pillow + Chrome only
  python3 render.py SRC_DIR [--out OUT_DIR] [--only ID ...] [--classes CLASS,...]
                    [--chrome PATH] [--allow-placeholders]

A full render (no --only) also deletes PNGs in the class and creative folders
that the manifest no longer lists, so a dropped frame cannot ship by accident.
Caption color pairs from config.js brand tokens must reach 3:1 (headline)
and 4.5:1 (supporting line) on every canvas stop, or the run fails.

Outputs (OUT_DIR defaults to SRC_DIR's parent):
  iphone-6.9/<id>.png  1320 x 2868   iPhone with Dynamic Island, large display
  iphone-6.3/<id>.png  1206 x 2622   iPhone with Dynamic Island, medium display
  ipad-13/<id>.png     2064 x 2752   iPad 13-inch display
  mac/<id>.png         2880 x 1800   Mac, 16:10
  creative/header.png 3840 x 1646 · search.png 3840 x 2560 · universal.png 5244 x 2950
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed, so rendered PNGs cannot be flattened to RGB.\n"
          "Fix: python3 -m pip install pillow   (inside the project's venv if it has one)", file=sys.stderr)
    sys.exit(1)

# CSS viewport, device scale factor, html zoom, expected pixels. The stage is
# designed at one width per platform; smaller classes zoom it down.
CLASSES = {
    "iphone-6.9": {"platform": "iphone", "w": 440, "h": 956, "scale": 3, "zoom": None, "px": (1320, 2868)},
    "iphone-6.3": {"platform": "iphone", "w": 402, "h": 874, "scale": 3, "zoom": 402 / 440, "px": (1206, 2622)},
    "ipad-13": {"platform": "ipad", "w": 1032, "h": 1376, "scale": 2, "zoom": None, "px": (2064, 2752)},
    "mac": {"platform": "mac", "w": 1440, "h": 900, "scale": 2, "zoom": None, "px": (2880, 1800)},
}
CREATIVES = {
    "header": {"w": 1920, "h": 823, "scale": 2, "px": (3840, 1646)},
    "search": {"w": 1920, "h": 1280, "scale": 2, "px": (3840, 2560)},
    "universal": {"w": 2622, "h": 1475, "scale": 2, "px": (5244, 2950)},
}
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
]


def fail(msg: str, fix: str) -> None:
    print(f"Error: {msg}\nFix: {fix}", file=sys.stderr)
    sys.exit(1)


def find_chrome(explicit: str | None) -> str:
    for cand in [explicit, os.environ.get("CHROME"), *CHROME_CANDIDATES]:
        if not cand:
            continue
        path = cand if os.path.isabs(cand) else shutil.which(cand)
        if path and os.path.exists(path):
            return path
    fail("no Chrome or Chromium binary found (checked --chrome, $CHROME and the standard install paths).",
         "install Google Chrome or Chromium, or pass --chrome /path/to/chrome (or set CHROME=/path).")
    return ""


def chrome(binary: str, args: list[str], what: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([binary, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                               "--allow-file-access-from-files", "--force-color-profile=srgb",
                               "--virtual-time-budget=5000", *args],
                              check=True, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        fail(f"Chrome timed out after 120 s while rendering {what}.",
             "check config.js for an infinite loop or a remote asset that never loads; keep every asset local.")
    except subprocess.CalledProcessError as e:
        tail = "\n".join((e.stderr or "").strip().splitlines()[-8:])
        fail(f"Chrome exited with code {e.returncode} while rendering {what}.\n{tail}",
             "run the same URL in a normal Chrome window to see the error, or pass --chrome with a working binary.")
    raise AssertionError("unreachable")


def check_placeholders(config: Path) -> None:
    hits = [f"  line {n}: {line.strip()[:100]}" for n, line in
            enumerate(config.read_text(encoding="utf-8").splitlines(), 1) if "TODO:" in line]
    if hits:
        fail(f"{config} still contains {len(hits)} template placeholder(s):\n" + "\n".join(hits),
             "replace every TODO: value with the app's real content, then re-run.")


def contrast(fg: str, bg: str) -> float:
    def lum(c: str) -> float:
        c = c.lstrip("#")
        ch = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        ch = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def check_contrast(pairs: list[dict]) -> list[str]:
    lines, bad = [], []
    for pr in pairs:
        fg, bg, need = pr.get("fg"), pr.get("bg"), pr["min"]
        if not (isinstance(fg, str) and isinstance(bg, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", fg) and re.fullmatch(r"#[0-9a-fA-F]{6}", bg)):
            bad.append(f"  {fg} on {bg}: not a #rrggbb pair (set every brand token in config.js, including dark* when a frame is dark)")
            continue
        r = contrast(fg, bg)
        (lines if r >= need else bad).append(f"  {fg} on {bg}: {r:.2f}:1 (needs {need}:1)")
    if bad:
        fail("caption colors fail the contrast check:\n" + "\n".join(bad),
             "darken or lighten the brand tokens in config.js (ink, brandInk, muted, and dark* for dark frames).")
    return lines


def prune_stale(out: Path, expected: set[Path]) -> None:
    for folder in [*CLASSES, "creative"]:
        d = out / folder
        if not d.is_dir():
            continue
        for f in d.glob("*.png"):
            if f.resolve() not in expected:
                f.unlink()
                print(f"removed stale {f} (not in the current config)")


def read_manifest(binary: str, index: Path) -> dict:
    out = chrome(binary, ["--dump-dom", f"{index.as_uri()}?manifest=1"], "the manifest").stdout
    err = re.search(r'id="render-error"[^>]*>(.*?)</div>', out, re.S)
    if err:
        fail(f"config.js failed to load: {html.unescape(err.group(1)).strip()}",
             "fix the JavaScript error in config.js (open index.html in Chrome and check the console).")
    m = re.search(r'id="manifest"[^>]*>(.*?)</div>', out, re.S)
    if not m:
        fail("index.html produced no manifest; kit.js or config.js did not run.",
             "confirm index.html, kit.js, kit.css and config.js are all in the src folder.")
    data = json.loads(html.unescape(m.group(1)))
    if data.get("errors"):
        fail("the config has errors:\n  " + "\n  ".join(data["errors"]),
             "fix each named frame in config.js (a missing helper, unknown icon, wrong image path or creatives frame id).")
    return data


def shoot(binary: str, url: str, w: int, h: int, scale: int, out: Path, expected: tuple[int, int]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.png"
        chrome(binary, [f"--force-device-scale-factor={scale}", f"--window-size={w},{h}", f"--screenshot={raw}", url], out.name)
        if not raw.exists():
            fail(f"Chrome reported success but wrote no screenshot for {out.name}.",
                 "upgrade Chrome; --screenshot needs a version with --headless=new support.")
        img = Image.open(raw).convert("RGB")  # drops the alpha channel
    if img.size != expected:
        fail(f"{out} rendered at {img.size[0]}x{img.size[1]}, expected {expected[0]}x{expected[1]}.",
             "do not change the stage sizes in kit.js; if Chrome ignores --window-size, pass --chrome with a current build.")
    img.save(out, optimize=True)
    print(f"ok  {out}  {img.size[0]}x{img.size[1]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path, nargs="?", help="asset-set src/ folder holding index.html and config.js")
    ap.add_argument("--preflight", action="store_true", help="only check that Pillow and Chrome are available, then exit")
    ap.add_argument("--out", type=Path, help="output folder (default: the src folder's parent)")
    ap.add_argument("--only", nargs="+", default=[], help="render only these frame ids or creative kinds")
    ap.add_argument("--classes", default=",".join(CLASSES), help="comma-separated device classes to render")
    ap.add_argument("--chrome", help="path to a Chrome or Chromium binary (or set $CHROME)")
    ap.add_argument("--allow-placeholders", action="store_true", help="render even if config.js has TODO: markers (template testing only)")
    a = ap.parse_args()

    if a.preflight:
        print(f"ok  Pillow available\nok  Chrome: {find_chrome(a.chrome)}")
        return
    if a.src is None:
        fail("no src folder given.", "pass the asset set's src/ folder, or --preflight to check tools only.")
    index = (a.src / "index.html").resolve()
    config = a.src / "config.js"
    for need in (index, config, a.src / "kit.js", a.src / "kit.css"):
        if not need.exists():
            fail(f"{need} is missing.", "copy the skill's assets/template/ folder to the asset set's src/ and edit config.js there.")
    unknown = [c for c in a.classes.split(",") if c and c not in CLASSES]
    if unknown:
        fail(f"unknown device class(es): {', '.join(unknown)}.", f"use any of: {', '.join(CLASSES)}.")
    if not a.allow_placeholders:
        check_placeholders(config)

    binary = find_chrome(a.chrome)
    out = (a.out or a.src.resolve().parent).resolve()
    manifest = read_manifest(binary, index)
    for line in check_contrast(manifest.get("contrast", [])):
        print(f"ok {line.strip()}")
    if not manifest.get("fontOk", True):
        print("Warning: the display font did not load; captions fell back to the system face. "
              "Run fetch_font.py or remove fonts.display from config.js.", file=sys.stderr)

    count, written = 0, set()
    for cls in [c for c in a.classes.split(",") if c]:
        spec = CLASSES[cls]
        if spec["platform"] not in manifest["platforms"]:
            continue
        for frame in manifest["frames"]:
            if spec["platform"] not in frame["platforms"] or (a.only and frame["id"] not in a.only):
                continue
            q = f"frame={frame['id']}&cls={cls}&h={spec['h']}" + (f"&zoom={spec['zoom']:.6f}" if spec["zoom"] else "")
            target = out / cls / f"{frame['id']}.png"
            shoot(binary, f"{index.as_uri()}?{q}", spec["w"], spec["h"], spec["scale"], target, spec["px"])
            written.add(target.resolve())
            count += 1
    for kind in manifest.get("creatives", []):
        if a.only and kind not in a.only:
            continue
        c = CREATIVES[kind]
        target = out / "creative" / f"{kind}.png"
        shoot(binary, f"{index.as_uri()}?creative={kind}", c["w"], c["h"], c["scale"], target, c["px"])
        written.add(target.resolve())
        count += 1
    if count == 0:
        fail("nothing was rendered: no frame matched the platforms, --classes and --only filters.",
             "check platforms[] in config.js and the ids passed to --only.")
    if not a.only and a.classes == ",".join(CLASSES):
        prune_stale(out, written)
    print(f"Rendered {count} asset(s) into {out}")


if __name__ == "__main__":
    main()
