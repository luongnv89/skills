# Render pipeline and kit API

Read this in Step 4 (building `config.js`) and Step 5 (rendering). The three
scripts live in the skill's `scripts/`; the template lives in `assets/template/`.
Header and search videos: see **Video creatives** below.

## Asset set layout

```
<out>/                      e.g. metadata/screenshots/<version>/ or appstore-assets/<version>/
├── src/                    copy of assets/template/ — index.html, kit.css, kit.js, config.js
│   ├── fonts/              display.woff2 + LICENSE.txt (fetch_font.py)
│   └── captures/           clean real captures, when a frame uses ui.capture(); keep them in git
├── iphone-6.9/ iphone-6.3/ ipad-13/ mac/   screenshots, <frame-id>.png
├── creative/               header.png, search.png, universal.png; header.mp4, search.mp4 when video is on
│   ├── .kit-outputs.json   ownership record: the files render.py wrote here (size and sha256) and the variant folders it created
│   └── <variant>/          the same files per Custom Product Page variant (optional)
├── sheets/                 contact sheets and video-*.png sheets for review (not for upload)
├── PLAN.md                 the approved frame plan with evidence per screen
├── run.json                optional run options for a batch run (see Batch runs and reports)
├── REPORT.md               the final report (Result, Evidence, Uncertainty, Decision)
└── report.json             the same, machine-readable, for an orchestrator
```

## Commands

```bash
SKILL=<this skill's directory>
python3 "$SKILL/scripts/fetch_font.py" "Bricolage Grotesque" <out>/src
python3 "$SKILL/scripts/render.py" <out>/src                 # all frames, all classes, creatives
python3 "$SKILL/scripts/render.py" <out>/src --only 02-siri   # re-render one frame or creative kind
python3 "$SKILL/scripts/check_assets.py" <out> --platforms iphone,ipad --sheet <out>/sheets
python3 "$SKILL/scripts/render.py" --preflight                # tools only: Pillow + Chrome
python3 "$SKILL/scripts/render.py" --preflight --video        # also ffmpeg (libx264) + ffprobe
python3 "$SKILL/scripts/render.py" <out>/src --no-video       # stills only while iterating
python3 "$SKILL/scripts/render.py" <out>/src --only header    # header.png and header.mp4
python3 "$SKILL/scripts/check_assets.py" <out> --platforms iphone --json <out>/.check.json   # facts for report.json
```

For several languages, render one asset set per locale (`<out>/<locale>/src/`);
captions are per set, so one language never overwrites another.

Inside a project with a Python venv, activate it first; both scripts need
Pillow (`python3 -m pip install pillow`). `render.py` needs Chrome or Chromium
(`--chrome PATH` or `$CHROME` to override detection). Videos also need ffmpeg
4.1 or later (for `setparams` color tags) built with libx264, and ffprobe.

## What render.py does and why

| Behavior | Reason |
| --- | --- |
| Refuses to run while `config.js` contains `TODO:` | Template text must never reach a PNG |
| Builds a manifest first (`index.html?manifest=1` via `--dump-dom`), rendering every screen once | A broken builder, an unknown icon name or a missing image fails with its frame id instead of shipping a blank PNG |
| Checks caption contrast from the brand tokens (3:1 headline, 4.5:1 supporting line, light and dark) | A dark frame with dark text cannot pass |
| After a full render, deletes outputs no longer in `config.js`: `<frame>.png` in the class folders, and in `creative/` only files `.kit-outputs.json` lists (videos only without `--no-video`) whose size and sha256 still match the record, then a variant folder it lists once that folder is empty or holds only `.DS_Store` (removed with it). A listed file changed since gets `WARN: … changed since the kit wrote it, left in place` and leaves the record; a listed variant folder holding anything else is kept with a WARN. Each write records the file's fingerprint atomically right after it lands (`--only` adds to it), so a failed render never adds a file; a file deleted by hand stays listed until the next full render clears it. With no record (a 1.0.0 set), only root `header`/`search`/`universal.png` go, as in 1.0.0. Hidden files are skipped silently; symlinks and anything else in `creative/` get `WARN: … not produced by the kit, left in place`. A file the config still produces is re-rendered over whatever is there, as in 1.0.0: to keep a hand-made asset, remove that kind from the config first; the kit will then leave it in place | A dropped frame, video or variant cannot ship by accident, and a file the kit did not write or that changed since (an App Preview recording, raw art, a hand-replaced `search.png`, `old/header.png`, an empty folder, a symlinked folder) is never deleted |
| Retries a Chrome crash, timeout (120 s per screenshot, 240 s on a retry) or silent pipe up to 4 attempts with backoff (about 4, 8, 16 s); a video resumes at the frame it lost, into the same encoder, so the file is byte-identical. After the second failure it switches to `chrome-headless-shell` when one is installed (PATH, Puppeteer or Playwright cache; macOS and Linux) for the rest of the run. `APPSTORE_ASSETS_ATTEMPTS` changes the count | Batch runs on a loaded machine crashed Chrome; a retry or the headless shell finished them. A config error, size mismatch or page script error still fails at once |
| Takes a machine-wide lock (`~/.cache/appstore-assets/video.lock`, `flock`) for the video step only, printing `waiting for the video lock … (held by pid N, <out>)` while another render holds it. `APPSTORE_ASSETS_VIDEO_LOCK=0` skips it; `APPSTORE_ASSETS_LOCK_DIR` moves it | Four parallel 4K video renders pushed the load average near 500; stills still render in parallel, and the lock dies with its process |
| Renders `orientation: "landscape"` classes rotated (iPhone 956 × 440 design zoomed to 874 for 6.3"; iPad 1376 × 1032) | Landscape-only games need landscape screenshots; one kit serves both |
| Prints `fit headline <id>: 41 -> 37 px` when kit.js shrank a headline that wrapped past two lines (down to 75 %), and a WARN when it still does not fit | A wide face (a monospace) no longer needs per-frame overrides; a config `css` rule that pins `font-size` turns the fit off for that headline, and `fitHeadlines: false` turns it off everywhere |
| Prints `note: header: device slot(s) hero, side0 sit outside Apple's art safe area` | Decoration outside the safe area is cropped on narrow displays; the note says so once instead of a reviewer flagging it per run |
| Passes the stage height explicitly (`&h=`) | Headless Chrome's viewport is about 87 px shorter than `--window-size`; a `100vh` stage gets clipped |
| Renders `iphone-6.3` by zooming the 440 px design to 402 px | One layout serves both iPhone classes with identical proportions |
| Flattens to RGB with Pillow | Chrome writes RGBA; App Store Connect rejects alpha |
| Fails unless the pixel size is exact | A 1 px error is an upload rejection |

Device scale factors: iPhone ×3 (440 × 956 → 1320 × 2868), iPad ×2 (1032 × 1376
→ 2064 × 2752), Mac ×2 (1440 × 900 → 2880 × 1800), creatives ×2.

## Rendering environment

- On macOS, `-apple-system` resolves to SF Pro, so recreated iOS/macOS UI matches
  the system look. On Linux it falls back to another sans-serif: record
  "UI font not SF Pro" under Uncertainty.
- Keep every asset local (fonts, captures, logos). Remote URLs make renders
  slow and nondeterministic.
- Copy app logos and provider marks the UI really shows from the app's asset
  catalog into `src/` and pass them to `sym('<img src="…">')`.

## config.js shape

```js
window.APP_CONFIG = {
  app, version, platforms: ["iphone", "ipad", "mac"],      // only what the app ships
  orientation: "portrait",                                  // or "landscape", or { iphone, ipad }
  brand: { brand, brandInk, ink, muted, canvas1, canvas2, glow,
           darkCanvas1, darkCanvas2, darkInk, darkMuted, darkAccent },   // dark* style frames with dark: true
  uiTint: "#3b86f7",                                        // the app's accent inside screens
  css: ".my-card{…}",                                       // optional styles for custom screen HTML
  fonts: { display: { file: "fonts/display.woff2", weight: "200 800" } },
  frames: [{ id, headline, sub, dark?, callout?: { icon, title, text, platforms? },
             screens: { iphone: () => html, ipad: () => html, mac: () => html } }],
  creatives: { enabled /* only when requested */, kinds: ["header", "search", "universal"],
               headline, sub, searchHeadline, searchSub,
               hero: { platform, frame }, sides: [{ platform, frame }], layout?: "safe",
               video: { kinds: ["header", "search"], duration? /* fitted */, fps: 30, transition: 0.8, searchSize?: "max",
                        beats: [{ headline, sub, searchHeadline?, searchSub?, hero?, sides? }] },
               variants: [{ id: "tiktok-trails", kinds?, headline?, hero?, video?: { … } }] },
};
```

Frame ids sort in upload order (`01-…`, `02-…`). Put a `// Source: path:line`
comment above every screen builder: Step 6's reviewer checks it against the code.

**Landscape.** Set `orientation` from the brief. Screens are then 874 × 402
(iPhone) and 1376 × 1032 (iPad): build them with `ui.screen(body, { platform: "ipad" })`
(the default size follows the orientation) or `ui.capture()` of a landscape
capture. The Dynamic Island moves to the left edge, and the caption sits in a
band above a wide device. A set that forked `kit.js` for landscape (a
`render_landscape.py` wrapper) moves to the template kit plus `orientation`;
the hadal-relay set rendered pixel-identical that way.

## Video creatives

Header and search videos are the still creative in motion: `header.png` is
frame 0 of `header.mp4`, so the poster frame is the approved still.

**How it renders.** `kit.js` computes every frame as a pure function of `t`
(no CSS animation, no clock), so re-rendering a config gives the same frames
and, with the same ffmpeg build, the same bytes. `render.py` starts one
headless Chrome with `--remote-debugging-pipe` (CDP over fds 3/4, standard
library only), seeks with `window.__seek(i / fps)`, captures each frame with
`Page.captureScreenshot`, and pipes the PNGs to ffmpeg: libx264 High, CRF 18,
yuv420p, BT.709 (tagged), constant frame rate, no audio, `+faststart`. The
search video is 3744 × 2496 at 30 fps (the stage at ×1.95) and 3600 × 2400
at 60 fps (×1.875), the largest 3:2 sizes within H.264 Level 5.2 at each
rate; `render.py` passes the level to x264 explicitly (5.1 for the header at
30 fps, 5.2 otherwise, 6.0 for `searchSize: "max"`). `searchSize: "max"` in `creatives.video` renders
3840 × 2560 instead, which needs Level 6.0 and is untested with App Store
Connect. The search still stays 3840 × 2560. Open
`src/index.html?creative=header&t=3.2` in Chrome to see any moment.

Alternatives rejected: one `--screenshot` Chrome launch per frame (about a
second of startup per frame), and an ffmpeg pan/zoom/crossfade over stills
(cannot crossfade the screen inside a floating device, and a zoom that
returns to its start is a visible yo-yo).

**Timeline.** Beat 0 is the still (headline, sub, hero, sides; search uses
`searchHeadline`). Each entry in `video.beats` adds a beat built only from
existing frames. The header shows the hero and one side device, search the
hero and two. A beat holds, then crossfades (`transition`, default 0.8 s:
the caption fades out, then the next fades in; each device crossfades its
screen). The last crossfade returns to beat 0 half a second before the end,
so the loop seam falls inside beat 0's hold. Devices drift ±8 px and the arcs
breathe 2 % on one sine period over the whole video, so the last frame flows
into the first.

| Rule | Bar |
| --- | --- |
| First impression | Frame 0 shows beat 0 complete: no fade-in, the headline is readable from 0 s |
| Dwell | Each beat holds at least max(2.5 s, 1 s + words / 4) of its caption (beat 0 before the first crossfade); `render.py` fails with the needed time otherwise |
| Safe area | Caption, and for search the hero device, sit inside Apple's art safe area (`references/apple-specs.md`) |
| Timing | `duration` 5–30 s, `fps` 30 or 60, `duration × fps` a whole number. Without `duration` the kit fits it: the shortest half-second that holds every beat, at least 12 s, at most 30 s. A set `duration` is kept as is |
| Loop | `check_assets.py` fails when the last→first difference exceeds twice the neighboring frame steps |

Fitted lengths from eight game sets: two beats 12 s, three beats 12–16 s.
Leave `duration` out unless the user asked for a length. Render cost is about
0.7 s per 3840 × 1646 frame and 1.1 s per 3744 × 2496 frame on a 2-core Linux
VM (faster on Apple silicon), so render stills with `--no-video` while
iterating and render the videos last.

**Custom Product Page variants.** Each `variants[]` entry has an `id`
(lowercase, digits, hyphens) and overrides any `creatives` key; `video` merges
key by key, except `beats`, which a variant never inherits. A variant
`headline` or `sub` also replaces the base search wording unless the variant
sets `searchHeadline` or `searchSub`. It renders to `creative/<id>/` (for example one header per ad
creative). Upload each variant to its custom product page in App Store Connect.

## Batch runs and reports

**Run options.** A batch run passes its decisions once, instead of in every
prompt: a `run.json` file (a path the prompt names, or `<out>/run.json`), or a
fenced block tagged `appstore-assets-run` in the prompt holding the same JSON.
A short prompt is then enough: "Run appstore-assets on <repo> with
<path>/run.json". Unknown keys are an error to report, not to guess.

```json
{
  "preauthorized": true,
  "out": "appstore-assets/1.0.0",
  "platforms": ["iphone", "ipad"],
  "orientation": "auto",
  "creatives": ["header", "search"],
  "video": {"kinds": ["header", "search"], "duration": "auto", "fps": 30},
  "variants": [],
  "captures": "flutter-test",
  "upload": "none",
  "notes": "free text the run must respect"
}
```

`preauthorized: true` makes it a pre-authorized run (Step 3.6). `out`,
`platforms`, `orientation` (`auto` = from the brief) and `video.duration`
(`auto` = fitted) override discovery; leave a key out to use the default.
`captures` is `flutter-test`, `simulator`, `existing` or `none` (grounded
screens only). The run copies the file to `<out>/run.json`, so an Update run
reuses it.

**Reports.** Each step's checklist ends with `Step N: PASS | FAIL | PARTIAL`,
never `Result:`; the one `Result:` line is the final report's first line, so a
watcher can wait for it. On COMPLETE or PARTIAL the run writes the final report
to `<out>/REPORT.md` and `<out>/report.json`, then prints it. A BLOCKED or Stop
run writes nothing into the repo, unless it was given a `run.json`: then it
writes `report.json` next to that file so the orchestrator still gets an answer.

```json
{
  "result": "COMPLETE|PARTIAL|BLOCKED",
  "out": "appstore-assets/1.0.0",
  "frames": {"iphone-6.9": 6, "iphone-6.3": 6, "ipad-13": 6},
  "creatives": ["header.png", "search.png"],
  "videos": [{"file": "creative/header.mp4", "w": 3840, "h": 1646, "fps": 30, "duration": 14.5, "seam": "0.19 (neighbors 0.08)", "verdict": "PASS"}],
  "checks": {"render": "exit 0", "check_assets": "PASS 22/22"},
  "reviewer": {"verdict": "PASS", "cycles": 1, "blocking": 0, "advisory": 3},
  "decisions": {"preauthorized": true, "platforms": ["iphone", "ipad"], "orientation": "landscape", "video_duration": "auto", "extras": ["header", "search"]},
  "assumptions_differing": [],
  "uncertainty": ["03-boss recreated from lib/ui/game_screen.dart:544; verify on a build"],
  "listing_findings": [],
  "decision": "No approval needed"
}
```

`frames`, `videos` and `checks.check_assets` come from `check_assets.py --json`
(written outside the upload folders, then deleted). `assumptions_differing`
lists only departures from `apple-specs.md` → Known kit assumptions.

## Kit API (kit.js)

| Helper | Renders |
| --- | --- |
| `ui.screen(body, {bg: "white"\|"grouped", dark, platform, w, h})` | The screen root, sized for `platform` (default `iphone`) in the config's orientation |
| `ui.statusBar({onDark, pad})`, `ui.homeIndicator()` | 9:41 status bar (pad = iPad style), home indicator |
| `ui.navBar({title, left, right})`, `ui.largeTitle(t)` | Inline and large navigation titles |
| `ui.section(t)`, `ui.footnote(t)` | Grouped-list header and footer text |
| `ui.list(rows, {icons})`, `ui.row({icon, iconBg, title, sub, value, accessory})` | Inset grouped list; accessory `chevron`, `check`, `toggle-on`, `toggle-off`, `none` or HTML |
| `ui.search(placeholder)`, `ui.chips(items, active)` | Search field, filter chips |
| `ui.button(label, "filled"\|"tinted"\|"plain")`, `ui.badge(text, fg, bg)` | Buttons and badges |
| `ui.messages([ui.bubble("user"\|"other", html, meta)])`, `ui.composer(placeholder)` | Chat transcript and input bar |
| `ui.tabBar([{icon, label}], active)` | Floating tab bar |
| `ui.card(html)`, `ui.stat(value, label)`, `ui.grid2(cards)` | Cards and stat tiles |
| `ui.split(sidebar, detail)`, `ui.sideItem(label, icon, on)` | iPad split view |
| `ui.capture("captures/x.png")` | A real capture filling the screen (it carries its own status bar) |
| `macui.window({title, tools, sidebar, content, dark})`, `macui.group`, `macui.item`, `macui.table` | Mac window with traffic lights, sidebar, toolbar, table |
| `sym("name")` or `sym('<img src="…">')` | Icon from the built-in set (`I` in kit.js) or raw logo markup |

For screens the primitives do not cover, write plain HTML in the builder and
put its styles in the `css:` string of `config.js`; `kit.js` injects it after
`kit.css`. Leave the marketing-canvas rules in `kit.css` untouched so every
frame keeps the same caption and device placement.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `screen builders threw errors` | The named frame calls a missing helper or has no screen for a platform listed in `creatives` |
| Captions in a system font | `fetch_font.py` was not run, or `fonts.display.file` points elsewhere |
| A blank or black device screen | The builder returned nothing, or a capture path is wrong (paths are relative to `src/`) |
| Text overlaps the device | Shorten the headline to two lines; do not move `LAYOUT` offsets per frame |
| `ffmpeg and ffprobe not found` | Install ffmpeg 4.1 or later with libx264, set `FFMPEG`/`FFPROBE`, or pass `--no-video` |
| `header video: 2 beats in 5 s hold beat 0 for 1.27 s, its caption needs 3.25 s (9 s fits every beat …)` | Remove `video.duration` so the kit fits the beats, set the length the error names, shorten that beat's caption, or drop a beat |
| `WARN: <path> not produced by the kit, left in place` or `… changed since the kit wrote it, left in place` | `render.py` keeps any file `creative/.kit-outputs.json` does not list, or lists with a different size or sha256. A file that is not a kit name gets a `check_assets.py` WARN row saying not to upload it. A `header*`/`search*`/`universal*` file is checked as an upload asset, even if hand-made; if it FAILs and the record does not list it, or lists it as changed (the row ends "(not written by the kit)"), never move, rename or delete it yourself: report BLOCKED and ask the user to fix, rename or move it |
| `check_assets.py` checks or FAILs `old/header.png` | With no `.kit-outputs.json` (a set not yet rendered by 1.1.0), every lowercase id folder counts as a variant folder. The next render writes the record, and from then on only recorded variant folders are checked |
| A file the kit rendered earlier is no longer pruned | It changed since the kit wrote it (the render printed `changed since the kit wrote it`), or `.kit-outputs.json` was deleted, edited by hand or unreadable (`WARN: … is unreadable`); delete the stale file yourself if it is not wanted, and the next render rebuilds the record |
| `WARN: Chrome … retry 1/3 in 5 s` | Machine load; the render continues. If every attempt fails, render fewer sets at once, or install `chrome-headless-shell` (`npx @puppeteer/browsers install chrome-headless-shell@stable`) so the fallback has a binary, or pass `--chrome` |
| `waiting for the video lock …` | Another render is encoding videos; this one waits its turn. Not a hang. A watcher reads the holder's pid and `<out>` from the message |
| A capture harness's PNG is 500 px wide (×scale) or clipped on the right | Chrome 156+ clamps headless `--window-size` to a 500 px minimum width. Size small viewports with CDP `Emulation.setDeviceMetricsOverride` instead (`input-discovery.md` → Capture recipes). `render.py`'s 440 and 402 px stills rendered at exact size on Chrome 156 in testing, and it fails on any size mismatch rather than writing a clipped PNG |
| Landscape screenshots come out portrait | `orientation` is missing from `config.js`, or `src/kit.js` predates 1.2.0 (no `setOrientation` in it): refresh the kit files |
