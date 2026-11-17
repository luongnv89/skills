#!/usr/bin/env python3
"""Download a Google Fonts caption face and its license into an asset set's src/fonts/.

Fonts are fetched at run time instead of being bundled with the skill. The
latin subset is saved as fonts/display.woff2 (the path config.js expects) and
the family's license as fonts/LICENSE.txt, so the repo that stores the asset
set also carries the font's terms.

Usage:
  python3 fetch_font.py "Bricolage Grotesque" SRC_DIR [--weights 200..800]
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def css_for(family: str, weights: str) -> str:
    q = urllib.parse.quote_plus(family)
    tries = [f"{q}:wght@{weights}", f"{q}:wght@400;700", q]  # variable range, then static, then default
    last = None
    for spec in tries:
        try:
            return get(f"https://fonts.googleapis.com/css2?family={spec}&display=block").decode()
        except urllib.error.HTTPError as e:
            last = e
    raise last  # type: ignore[misc]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("family", help='Google Fonts family name, e.g. "Bricolage Grotesque"')
    ap.add_argument("src", type=Path, help="asset-set src/ folder")
    ap.add_argument("--weights", default="200..800", help="weight range for variable families (default 200..800)")
    a = ap.parse_args()

    if not (a.src / "config.js").exists():
        print(f"Error: {a.src} has no config.js.\nFix: pass the asset set's src/ folder (a copy of assets/template/).", file=sys.stderr)
        sys.exit(1)
    try:
        css = css_for(a.family, a.weights)
    except (urllib.error.URLError, OSError) as e:
        print(f"Error: could not reach Google Fonts for '{a.family}' ({e}).\n"
              "Fix: check the family name at fonts.google.com and the network; offline, remove fonts.display "
              "from config.js so captions use the system face.", file=sys.stderr)
        sys.exit(1)
    # Google returns one block per subset; take the latin block's woff2 URL.
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*{(.*?)}", css, re.S)
    latin = [b for name, b in blocks if name == "latin"] or [b for _, b in blocks]
    if not latin:
        print(f"Error: Google Fonts returned no @font-face for '{a.family}'.\nFix: use the exact family name shown on fonts.google.com.", file=sys.stderr)
        sys.exit(1)
    url = re.search(r"url\((https://[^)]+\.woff2)\)", latin[-1])
    weight = re.search(r"font-weight:\s*([\d ]+);", latin[-1])
    if not url:
        print("Error: the latin @font-face has no woff2 URL.\nFix: re-run; if it persists, pick another family.", file=sys.stderr)
        sys.exit(1)
    fonts = a.src / "fonts"
    fonts.mkdir(exist_ok=True)
    (fonts / "display.woff2").write_bytes(get(url.group(1)))

    slug = re.sub(r"[^a-z0-9]", "", a.family.lower())
    license_saved = None
    for path in (f"ofl/{slug}/OFL.txt", f"apache/{slug}/LICENSE.txt", f"ufl/{slug}/UFL.txt"):
        try:
            (fonts / "LICENSE.txt").write_bytes(get(f"https://raw.githubusercontent.com/google/fonts/main/{path}"))
            license_saved = path
            break
        except urllib.error.HTTPError:
            continue
    print(f"ok  {fonts / 'display.woff2'}  weight {weight.group(1).strip() if weight else 'unknown'}")
    if license_saved:
        print(f"ok  {fonts / 'LICENSE.txt'}  (google/fonts {license_saved})")
    else:
        print(f"Warning: no license file found for '{a.family}' in google/fonts. Record the font's license in the report.", file=sys.stderr)
    if weight and " " not in weight.group(1).strip():
        print(f"Note: static family; set fonts.display.weight to \"{weight.group(1).strip()}\" in config.js.")


if __name__ == "__main__":
    main()
