#!/usr/bin/env python3
"""Verify an App Store asset set before upload, and optionally build review sheets.

Checks every image under OUT_DIR's class folders against App Store Connect's
upload rules: an accepted pixel size for its display class, RGB with no alpha
channel, at most 10 screenshots per class, the required class present for each
platform, and the same frame names across the iPhone classes. Optional WCAG
contrast checks cover caption color pairs.

Header and search videos under creative/ (and creative/<variant>/) are checked
with ffprobe: .mov/.m4v/.mp4, exact size (header 3840x1646, search 3:2 from
1920x1280 to 3840x2560), 30 or 60 fps at a constant rate, 5-30 s, H.264
yuv420p (the level is reported; above 5.2 is a warning), and the audio-track rule. With ffmpeg, a blank frame or a jump at the
loop seam also fails, and --sheet writes one video sheet per file: frames at
most 2 s apart with Apple's art safe area outlined, plus the seam pair.

Usage:
  python3 check_assets.py OUT_DIR --platforms iphone,ipad,mac
         [--sheet SHEET_DIR] [--pair "#1d5fd6/#e6edf8@3" ...]

Exit 0 = every check passed (WARN rows are notes). Exit 1 = at least one FAIL row (each says why).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
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
IMAGE_EXT, VIDEO_EXT = (".png", ".jpg", ".jpeg"), (".mov", ".m4v", ".mp4")
# Apple's "Art Safe Area" layer in its Photoshop creative-asset templates, as
# (x, y, w, h) fractions of the canvas: header 1646x661 and search 2168x1030, centered.
SAFE = {"header": (1097 / 3840, 493 / 1646, 1646 / 3840, 661 / 1646),
        "search": (836 / 3840, 765 / 2560, 2168 / 3840, 1030 / 2560)}
# Assumption: Apple states no file-size limit for creative videos; its app preview cap is 500 MB.
MAX_VIDEO_MB = 500
VIDEO_FIX = "re-render with render.py from creatives.video in config.js"


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


def tool(name: str) -> str | None:
    path = os.environ.get(name.upper()) or shutil.which(name)
    return path if path and os.path.exists(path) else None


def probe(ffprobe: str, path: Path, *args: str) -> dict:
    out = subprocess.run([ffprobe, "-v", "error", "-of", "json", *args, str(path)], capture_output=True, text=True)
    if out.returncode != 0:
        raise ValueError(out.stderr.strip().splitlines()[-1] if out.stderr.strip() else "ffprobe failed")
    return json.loads(out.stdout)


def rate(fraction: str) -> float:
    num, _, den = fraction.partition("/")
    return float(num) / float(den or 1) if float(den or 1) else 0.0


def inspect_video(path: Path, kind: str, ffprobe: str) -> tuple[list[str], list[str], dict]:
    """Return (problems, notes, facts) for one creative video; any problem is a FAIL."""
    problems, notes = [], []
    if path.suffix.lower() not in VIDEO_EXT:
        problems.append(f"extension {path.suffix}; use .mov, .m4v or .mp4")
    if kind not in SAFE:
        return problems + [f"{kind} has no video placement; only header and search take video"], notes, {}
    try:
        info = probe(ffprobe, path, "-show_streams", "-show_format", "-count_packets")
        pts = probe(ffprobe, path, "-select_streams", "v:0", "-show_entries", "packet=pts_time")
    except (ValueError, json.JSONDecodeError) as e:
        return problems + [f"unreadable video ({e})"], notes, {}
    fmt = info.get("format", {})
    video = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if "mov" not in fmt.get("format_name", "") and "mp4" not in fmt.get("format_name", ""):
        problems.append(f"container {fmt.get('format_name')}; use a QuickTime/MPEG-4 file")
    if len(video) != 1:
        return problems + [f"{len(video)} video streams; expected exactly 1"], notes, {}
    v = video[0]
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    if kind == "header" and (w, h) != (3840, 1646):
        problems.append(f"{w}x{h}; the header video must be exactly 3840x1646 ({VIDEO_FIX})")
    if kind == "search" and not search_ok((w, h)):
        problems.append(f"{w}x{h} is not 3:2 between 1920x1280 and 3840x2560 ({VIDEO_FIX})")
    fps, avg = rate(v.get("r_frame_rate", "0/1")), rate(v.get("avg_frame_rate", "0/1"))
    if not any(abs(fps - want) < 0.01 for want in (30, 60)):
        problems.append(f"{fps:.3f} fps; Apple accepts exactly 30 or 60 (re-encode with -r 30 or -r 60)")
    times = sorted(float(p["pts_time"]) for p in pts.get("packets", []) if p.get("pts_time") not in (None, "N/A"))
    steps = [b - a for a, b in zip(times, times[1:])]
    odd = [d for d in steps if fps and abs(d - 1 / fps) > 0.002]
    if fps and (abs(avg - fps) > 0.01 or odd):
        problems.append(f"variable frame rate (avg {avg:.3f} fps, {len(odd)} frame step(s) other than {1 / fps:.4f} s, "
                        f"e.g. {max(odd, key=lambda d: abs(d - 1 / fps), default=0):.4f} s); re-encode at a constant rate (ffmpeg -r 30 or -r 60)")
    duration = float(v.get("duration") or fmt.get("duration") or 0)
    if not 5 - 1e-3 <= duration <= 30 + 1e-3:
        problems.append(f"{duration:.2f} s is outside Apple's 5-30 s (set creatives.video.duration)")
    codec, pix, profile, level = v.get("codec_name"), v.get("pix_fmt"), v.get("profile", ""), v.get("level")
    if codec == "h264":
        if pix != "yuv420p":
            problems.append(f"H.264 with {pix}; use 8-bit 4:2:0 (-pix_fmt yuv420p)")
        if isinstance(level, int) and level > 0:
            profile += f" L{level // 10}.{level % 10}"
            if level > 52:
                notes.append(f"H.264 Level {level // 10}.{level % 10} is above 5.2; Apple states no level for creative videos, "
                             "and the kit has not tested one above 5.2 with App Store Connect")
    elif codec == "prores":
        notes.append("ProRes: accepted for app previews (422 HQ in .mov); Apple states no codec for creative videos")
    elif codec == "hevc":
        notes.append("HEVC: Apple states no codec for creative videos and lists only H.264 and ProRes for app previews; prefer H.264")
    else:
        problems.append(f"codec {codec}; use H.264 ({VIDEO_FIX})")
    if audio and kind == "search":
        notes.append("has an audio track that never plays: search videos can't be unmuted (drop it with ffmpeg -an)")
    elif audio:
        notes.append("has an audio track: the header is muted by default, so the message must work without it")
    size_mb = path.stat().st_size / 1e6
    if size_mb > MAX_VIDEO_MB:
        problems.append(f"{size_mb:.0f} MB; keep under {MAX_VIDEO_MB} MB (assumed cap, App Store Connect's app preview limit)")
    frames = int(v.get("nb_read_packets") or len(times))
    return problems, notes, {"w": w, "h": h, "fps": fps, "duration": duration, "frames": frames,
                             "desc": f"{w}x{h} {codec} {profile} {pix} {fps:g} fps CFR {duration:.2f} s, "
                                     f"{'no audio' if not audio else f'{len(audio)} audio'}, {size_mb:.1f} MB"}


def video_frames(ffmpeg: str, path: Path, indices: list[int], width: int) -> dict[int, Image.Image]:
    """Decode the given frame numbers at a reduced width."""
    wanted = sorted(set(indices))
    expr = "+".join(f"eq(n\\,{i})" for i in wanted)
    with tempfile.TemporaryDirectory() as tmp:
        run = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-vf", f"select={expr},setpts=N/FRAME_RATE/TB,scale={width}:-2",
                              f"{tmp}/%04d.png"], capture_output=True, text=True)
        files = sorted(Path(tmp).glob("*.png"))
        if run.returncode != 0 or len(files) != len(wanted):
            raise ValueError(f"ffmpeg decoded {len(files)} of {len(wanted)} sample frames "
                             f"({(run.stderr.strip().splitlines() or ['no error'])[-1]})")
        return {i: Image.open(f).convert("RGB") for i, f in zip(wanted, files)}


def loop_and_blank(frames: dict[int, Image.Image], last: int) -> tuple[list[str], str]:
    """A blank frame or a loop seam jumping more than twice the neighboring steps fails."""
    gray = {i: im.convert("L").resize((480, round(480 * im.height / im.width))) for i, im in frames.items()}
    diff = lambda a, b: ImageStat.Stat(ImageChops.difference(gray[a], gray[b])).mean[0]
    problems = [f"frame {i} is blank (flat color)" for i, g in gray.items() if ImageStat.Stat(g).stddev[0] < 2]
    seam, near = diff(last, 0), max(diff(0, 1), diff(last - 1, last))
    if seam > 2 * near + 1.0:
        problems.append(f"loop seam jumps (last→first diff {seam:.2f} vs {near:.2f} between neighbors); "
                        "end the video on the state it starts with")
    return problems, f"seam diff {seam:.2f} (neighbors {near:.2f})"


def video_sheet(frames: dict[int, Image.Image], samples: list[int], last: int, fps: float, kind: str, out: Path) -> None:
    try:
        font = ImageFont.load_default(size=26)
    except TypeError:
        font = ImageFont.load_default()
    tw = next(iter(frames.values())).width
    th = next(iter(frames.values())).height
    cols, gap, label = 3, 12, 36
    rows = math.ceil(len(samples) / cols) + 1
    canvas = Image.new("RGB", (cols * tw + (cols + 1) * gap, rows * (th + label) + (rows + 1) * gap), "white")
    draw = ImageDraw.Draw(canvas)
    tiles = [(i, f"frame {i}  t={i / fps:.2f} s", True) for i in samples] + [(None, "", False)] * (-len(samples) % cols)
    tiles += [(last, f"seam: last frame {last}", False), (0, "seam: loops to frame 0 (poster)", False)]
    sx, sy, sw, sh = SAFE[kind]
    for n, (i, text, safe) in enumerate(tiles):
        if i is None:
            continue
        x, y = gap + (n % cols) * (tw + gap), gap + (n // cols) * (th + label + gap)
        canvas.paste(frames[i], (x, y + label))
        draw.text((x, y + 4), text, fill="black", font=font)
        if safe:  # Apple's art safe area; not part of the video
            draw.rectangle([x + sx * tw, y + label + sy * th, x + (sx + sw) * tw, y + label + (sy + sh) * th], outline="#ff2bd6", width=3)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)


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
    ffprobe, ffmpeg = tool("ffprobe"), tool("ffmpeg")
    for folder in [*ACCEPTED, "creative"]:
        d = a.out / folder
        pattern = ["*", "*/*"] if folder == "creative" else ["*"]  # creative/<variant>/ holds Custom Product Page sets
        found = sorted(p for g in pattern for p in d.glob(g) if p.is_file() and not p.name.startswith(".")) if d.is_dir() else []
        files = [p for p in found if p.suffix.lower() in IMAGE_EXT]
        videos = [p for p in found if p.suffix.lower() in VIDEO_EXT] if folder == "creative" else []
        if not files and not videos:
            continue
        names[folder] = [f.stem for f in files + videos]
        for f in files:
            kind = f.stem.split("-")[0] if folder == "creative" else None
            if folder == "creative" and kind not in ("header", "search", "universal"):
                ok, why = False, "creative files must be named header*, search* or universal*"
            else:
                ok, why = inspect(f, CREATIVE.get(kind) if folder == "creative" else ACCEPTED[folder], kind)
            failures += not ok
            rows.append((f"{folder}/{f.relative_to(d)}", "PASS" if ok else "FAIL", why))
        for f in videos:
            name, kind = f"{folder}/{f.relative_to(d)}", f.stem.split("-")[0]
            if not ffprobe:
                failures += 1
                rows.append((name, "FAIL", "ffprobe not found, so the video cannot be checked; install ffmpeg "
                             "(brew install ffmpeg, or sudo apt install ffmpeg) or set FFPROBE"))
                continue
            problems, notes, facts = inspect_video(f, kind, ffprobe)
            if facts and ffmpeg:
                last, fps = facts["frames"] - 1, facts["fps"]
                step = max(1, round(facts["frames"] / math.ceil(facts["duration"] / 2)))
                samples = list(range(0, last + 1, step))
                try:
                    frames = video_frames(ffmpeg, f, [0, 1, last - 1, last, *samples], 960)
                except ValueError as e:
                    frames = None
                    problems.append(f"frames could not be decoded for the seam check: {e}")
                if frames:
                    found_problems, seam = loop_and_blank(frames, last)
                    problems += found_problems
                    facts["desc"] += f", {seam}"
                if frames and a.sheet:
                    variant = f"{f.parent.name}-" if f.parent != d else ""
                    video_sheet(frames, samples, last, fps, kind, a.sheet / f"video-{variant}{f.stem}.png")
            elif facts:
                notes.append("ffmpeg not found: loop-seam and blank-frame checks and the video sheet were skipped")
            failures += bool(problems)
            rows.append((name, "FAIL" if problems else "PASS", "; ".join(problems) if problems else facts["desc"]))
            rows += [(name, "WARN", n) for n in notes]
        if folder != "creative" and len(files) > MAX_PER_CLASS:
            failures += 1
            rows.append((f"{folder}/", "FAIL", f"{len(files)} screenshots; App Store Connect allows {MAX_PER_CLASS} per class"))
        if a.sheet and files:
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
    warns = sum(r[1] == "WARN" for r in rows)
    checks = len(rows) - warns
    print(f"{'FAIL' if failures else 'PASS'}: {checks - failures}/{checks} checks passed" + (f", {warns} warning(s)" if warns else ""))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
