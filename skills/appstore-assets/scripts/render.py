#!/usr/bin/env python3
"""Render App Store screenshots and creative assets from an asset-set src/ folder.

The src/ folder is a copy of the skill's assets/template/ with config.js
rewritten for one app. One headless Chrome launch renders one asset at an
exact CSS viewport and device scale factor; Pillow flattens it to RGB (App
Store Connect rejects alpha) and the exact pixel size is verified.

Usage:
  python3 render.py --preflight [--video] [--chrome PATH]   # check Pillow + Chrome (+ ffmpeg, ffprobe)
  python3 render.py SRC_DIR [--out OUT_DIR] [--only ID ...] [--classes CLASS,...]
                    [--chrome PATH] [--no-video] [--allow-placeholders]

A full render (no --only) also deletes PNGs and videos in the class and
creative folders that the manifest no longer lists, so a dropped frame cannot
ship by accident. Caption color pairs from config.js brand tokens must reach
3:1 (headline) and 4.5:1 (supporting line) on every canvas stop, or the run fails.

Videos (creatives.video.kinds in config.js) need ffmpeg and ffprobe; a config
without video never calls them. One Chrome, driven over --remote-debugging-pipe,
seeks the page to each frame time and captures it; ffmpeg encodes H.264 High,
yuv420p, BT.709, constant frame rate, no audio, +faststart MP4.

Outputs (OUT_DIR defaults to SRC_DIR's parent):
  iphone-6.9/<id>.png  1320 x 2868   iPhone with Dynamic Island, large display
  iphone-6.3/<id>.png  1206 x 2622   iPhone with Dynamic Island, medium display
  ipad-13/<id>.png     2064 x 2752   iPad 13-inch display
  mac/<id>.png         2880 x 1800   Mac, 16:10
  creative/header.png 3840 x 1646 · search.png 3840 x 2560 · universal.png 5244 x 2950
  creative/header.mp4 3840 x 1646 · search.mp4 3744 x 2496 (30 or 60 fps, 5-30 s, looping)
  creative/<variant>/... the same files per Custom Product Page variant
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
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
# Videos: the header as above; search at 3744 x 2496, the largest 3:2 size whose
# H.264 stream stays within Level 5.2 (3840 x 2560 needs Level 6.0, beyond many decoders).
VIDEO_SPECS = {"header": CREATIVES["header"], "search": {"w": 1920, "h": 1280, "scale": 1.95, "px": (3744, 2496)}}
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


def find_ffmpeg() -> tuple[str, str]:
    found = {t: os.environ.get(t.upper()) or shutil.which(t) for t in ("ffmpeg", "ffprobe")}
    missing = [t for t, p in found.items() if not p or not os.path.exists(p)]
    if missing:
        fail(f"{' and '.join(missing)} not found; header and search videos (creatives.video.kinds) need them.",
             "install ffmpeg (macOS: brew install ffmpeg; Debian/Ubuntu: sudo apt install ffmpeg), set FFMPEG and "
             "FFPROBE to the binaries, or pass --no-video to render the stills only.")
    return found["ffmpeg"], found["ffprobe"]


class Browser:
    """One headless Chrome driven over --remote-debugging-pipe (CDP: fd 3 in, fd 4 out, NUL-delimited JSON)."""

    def __init__(self, binary: str):
        import fcntl  # POSIX only, like the pipe transport itself
        to_r, self.to_w = os.pipe()
        self.from_r, from_w = os.pipe()

        def plumb() -> None:  # runs in the child: move the pipe ends to fds 3 and 4
            r, w = fcntl.fcntl(to_r, fcntl.F_DUPFD, 10), fcntl.fcntl(from_w, fcntl.F_DUPFD, 10)
            os.dup2(r, 3)
            os.dup2(w, 4)
            os.set_inheritable(3, True)
            os.set_inheritable(4, True)

        self.profile = tempfile.mkdtemp(prefix="aa-chrome-")
        self.proc = subprocess.Popen(
            [binary, "--headless=new", "--remote-debugging-pipe", "--disable-gpu", "--hide-scrollbars",
             "--allow-file-access-from-files", "--force-color-profile=srgb", "--no-first-run",
             "--no-default-browser-check", "--disable-background-timer-throttling",
             "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
             f"--user-data-dir={self.profile}", "about:blank"],
            preexec_fn=plumb, close_fds=False, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(to_r)
        os.close(from_w)
        self.buf, self.next_id, self.session = b"", 0, None

    def send(self, method: str, params: dict | None = None, timeout: float = 60) -> dict:
        self.next_id += 1
        msg = {"id": self.next_id, "method": method, "params": params or {}}
        if self.session and not method.startswith(("Target.", "Browser.")):
            msg["sessionId"] = self.session
        try:
            os.write(self.to_w, json.dumps(msg).encode() + b"\0")
        except OSError:
            fail(f"Chrome exited before {method}.", "pass --chrome with a working binary.")
        deadline = time.monotonic() + timeout
        while True:
            while b"\0" not in self.buf:
                left = deadline - time.monotonic()
                if left <= 0 or self.proc.poll() is not None or not select.select([self.from_r], [], [], left)[0]:
                    fail(f"Chrome stopped answering during {method}.",
                         "pass --chrome with a current Chrome or Chromium (the pipe transport needs version 75 or later).")
                chunk = os.read(self.from_r, 1 << 20)
                if not chunk:
                    fail(f"Chrome closed the debugging pipe during {method}.", "pass --chrome with a working binary.")
                self.buf += chunk
            raw, self.buf = self.buf.split(b"\0", 1)
            reply = json.loads(raw)
            if reply.get("id") == self.next_id:
                if "error" in reply:
                    fail(f"Chrome rejected {method}: {reply['error'].get('message')}", "pass --chrome with a current Chrome or Chromium.")
                return reply.get("result", {})

    def open(self, url: str, w: int, h: int, scale: int) -> None:
        target = self.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        self.session = self.send("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
        self.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": scale, "mobile": False})
        self.send("Page.navigate", {"url": url})
        for _ in range(600):  # the page sets __ready once fonts and images have loaded
            if self.eval("window.__ready === true"):
                return
            time.sleep(0.05)
        fail(f"the page never became ready: {url}", "open the same URL in Chrome and check the console for errors.")

    def eval(self, expression: str):
        res = self.send("Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True})
        if "exceptionDetails" in res:
            fail(f"page script failed: {res['exceptionDetails'].get('text')} ({expression})", "fix config.js and re-run.")
        return res.get("result", {}).get("value")

    def capture(self) -> bytes:
        return base64.b64decode(self.send("Page.captureScreenshot", {"format": "png", "optimizeForSpeed": True})["data"])

    def close(self) -> None:
        """Quietly stop Chrome and remove its profile, whatever state it is in."""
        try:
            if self.proc.poll() is None:  # ask politely; no reply needed
                os.write(self.to_w, json.dumps({"id": 0, "method": "Browser.close"}).encode() + b"\0")
                self.proc.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            self.proc.kill()
            self.proc.wait()
        finally:
            for fd in (self.to_w, self.from_r):
                try:
                    os.close(fd)
                except OSError:
                    pass
            shutil.rmtree(self.profile, ignore_errors=True)


def render_video(binary: str, tools: tuple[str, str], url: str, spec: dict, video: dict, out: Path) -> None:
    """Seek the page to each frame time, capture it, and pipe the PNGs to ffmpeg."""
    ffmpeg, ffprobe = tools
    fps, frames, (pw, ph) = video["fps"], video["frames"], spec["px"]
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.stem}.partial.mp4")
    enc = subprocess.Popen(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv", "-c:v", "libx264", "-profile:v", "high",
         "-preset", "veryfast", "-crf", "18", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-color_range", "tv", "-r", str(fps), "-an", "-map_metadata", "-1",
         "-fflags", "+bitexact", "-flags:v", "+bitexact", "-movflags", "+faststart", str(tmp)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    started, browser, done = time.monotonic(), Browser(binary), False
    try:
        browser.open(url, spec["w"], spec["h"], spec["scale"])
        for i in range(frames):
            browser.eval(f"window.__seek({i / fps!r})")
            png = browser.capture()
            if i == 0:
                size = Image.open(io.BytesIO(png)).size
                if size != (pw, ph):
                    fail(f"{out} frames render at {size[0]}x{size[1]}, expected {pw}x{ph}.",
                         "do not change the creative stage sizes in kit.js; pass --chrome with a current build.")
            try:
                enc.stdin.write(png)
            except BrokenPipeError:
                break
        done = True
    finally:
        browser.close()
        if not done:  # a failed capture leaves no encoder or partial file behind
            enc.kill()
            enc.wait()
            tmp.unlink(missing_ok=True)
    enc.stdin.close()
    err = enc.stderr.read().decode(errors="replace").strip()
    if enc.wait() != 0:
        tmp.unlink(missing_ok=True)
        fail(f"ffmpeg failed to encode {out.name}:\n{err[-800:]}",
             "use an ffmpeg build with libx264 (ffmpeg -encoders | grep libx264), or set FFMPEG to one.")
    probe = json.loads(subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                                       "stream=width,height,nb_read_packets", "-of", "json", str(tmp)],
                                      capture_output=True, text=True, check=True).stdout)["streams"][0]
    if (probe["width"], probe["height"], int(probe["nb_read_packets"])) != (pw, ph, frames):
        tmp.unlink(missing_ok=True)
        fail(f"{out.name} encoded as {probe['width']}x{probe['height']} with {probe['nb_read_packets']} frames, "
             f"expected {pw}x{ph} with {frames}.", "re-run; if it repeats, pass --chrome with a current build.")
    tmp.replace(out)
    print(f"ok  {out}  {pw}x{ph}  {fps} fps  {video['duration']} s  {frames} frames  "
          f"{video['beats']} beat(s)  rendered in {time.monotonic() - started:.1f} s")


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


def prune_stale(out: Path, expected: set[Path], videos: bool) -> None:
    patterns = ["*.png", "*/*.png"] + (["*.mp4", "*/*.mp4"] if videos else [])
    for folder in [*CLASSES, "creative"]:
        d = out / folder
        if not d.is_dir():
            continue
        for f in [f for p in patterns for f in d.glob(p)] if folder == "creative" else d.glob("*.png"):
            if f.resolve() not in expected:
                f.unlink()
                print(f"removed stale {f} (not in the current config)")
                if f.parent != d and not any(f.parent.iterdir()):
                    f.parent.rmdir()


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
    ap.add_argument("--video", action="store_true", help="with --preflight: also check ffmpeg and ffprobe (needed for videos)")
    ap.add_argument("--no-video", action="store_true", help="skip creatives.video kinds (stills only; ffmpeg not needed)")
    ap.add_argument("--out", type=Path, help="output folder (default: the src folder's parent)")
    ap.add_argument("--only", nargs="+", default=[], help="render only these frame ids or creative kinds")
    ap.add_argument("--classes", default=",".join(CLASSES), help="comma-separated device classes to render")
    ap.add_argument("--chrome", help="path to a Chrome or Chromium binary (or set $CHROME)")
    ap.add_argument("--allow-placeholders", action="store_true", help="render even if config.js has TODO: markers (template testing only)")
    a = ap.parse_args()

    if a.preflight:
        print(f"ok  Pillow available\nok  Chrome: {find_chrome(a.chrome)}")
        if a.video:
            ffmpeg, ffprobe = find_ffmpeg()
            if "libx264" not in subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout:
                fail(f"{ffmpeg} has no libx264 encoder.", "install an ffmpeg build with libx264 (Homebrew's and Debian's have it).")
            print(f"ok  ffmpeg: {ffmpeg} (libx264)\nok  ffprobe: {ffprobe}")
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
    if any(isinstance(c, str) for c in manifest.get("creatives", [])):
        fail("src/kit.js is older than this render.py (its manifest lists creatives as plain names).",
             "copy kit.js, kit.css and index.html from the skill's assets/template/ into src/ (config.js stays), then re-run.")
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
    videos = [] if a.no_video else [v for v in manifest.get("video", []) if not a.only or v["kind"] in a.only]
    tools = find_ffmpeg() if videos else None
    for still in manifest.get("creatives", []):  # {kind, variant}; a variant renders into creative/<variant>/
        kind, variant = still["kind"], still["variant"]
        if a.only and kind not in a.only:
            continue
        c = CREATIVES[kind]
        target = out / "creative" / (variant or "") / f"{kind}.png"
        shoot(binary, f"{index.as_uri()}?creative={kind}" + (f"&variant={variant}" if variant else ""),
              c["w"], c["h"], c["scale"], target, c["px"])
        written.add(target.resolve())
        count += 1
    for video in videos:
        kind, variant = video["kind"], video["variant"]
        target = out / "creative" / (variant or "") / f"{kind}.mp4"
        render_video(binary, tools, f"{index.as_uri()}?creative={kind}" + (f"&variant={variant}" if variant else ""),
                     VIDEO_SPECS[kind], video, target)
        written.add(target.resolve())
        count += 1
    if count == 0:
        fail("nothing was rendered: no frame matched the platforms, --classes and --only filters.",
             "check platforms[] in config.js and the ids passed to --only.")
    if not a.only and a.classes == ",".join(CLASSES):
        prune_stale(out, written, videos=not a.no_video)
    print(f"Rendered {count} asset(s) into {out}")


if __name__ == "__main__":
    main()
