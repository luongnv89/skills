---
name: appstore-assets
description: "Generate App Store screenshots, header/search images and looping videos for iPhone, iPad, Mac from code or a landing page, or re-render a set. Use when preparing a submission. Don't use for App Previews, ASO, review audits, icons, Google Play."
license: MIT
effort: high
dependencies:
  - frontend-design
  - "github:emilkowalski/skills:skills/emil-design-eng"
  - browse
metadata:
  version: 1.1.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# App Store Assets

Turn an app's codebase or landing page into an upload-ready App Store **asset
set**: screenshots for each required display class plus optional creative
assets (header and search images, and their looping muted videos), rendered
from HTML by headless Chrome and verified against Apple's specs. Prime directive: show only what the shipped app does. Never invent UI,
features or claims (App Review Guideline 2.3).

Terms used throughout:

- **asset set**: `<out>/` holding `src/`, one folder per display class, `creative/`, `sheets/` and `PLAN.md`.
- **display class**: `iphone-6.9`, `iphone-6.3`, `ipad-13` or `mac`.
- **grounded screen**: a recreated screen whose elements trace to a cited view (`path:line`) or a landing-page image.
- **clean capture**: a real screenshot that passes the checklist in `references/input-discovery.md`.
- **overclaim**: anything a frame shows that the shipped build cannot do.
- **pre-authorized run**: the request fixes the direction, frames and UI source, or delegates them ("just build it", "pick whatever looks good", "don't ask").
- **creative video**: a looping, muted product page header or search results video (`creative/<kind>.mp4`) made from the still creative and grounded frames. An **App Preview** (recorded app footage with audio) is not one.

## When to Use

Use when someone needs App Store screenshots, header/search creative images,
or a product page header or search results video for an iPhone, iPad or Mac
app, from its code or landing page, or wants an existing asset set edited and
re-rendered. Not for App Previews (recorded app footage, 15–30 s, with audio):
say so and offer a header video instead. Also not for listing copy, review
audits, app icons, or Google Play assets.

## Workflow overview

Step 0 branch → 1 discover → 2 refresh specs → 3 plan and approve → 4 build →
5 render and verify → 6 review → 7 hand off. After each step, print a Step
Completion Report: `√`/`×` rows tied to commands, files or counts, then
`Result: PASS | FAIL | PARTIAL`.

## Step 0 — Select the branch

| Condition | Branch |
| --- | --- |
| The input holds an Xcode project, `Package.swift`, Swift sources, or a Flutter/React Native app with an `ios/` or `macos/` target | **Codebase**: Steps 1–7 |
| The input is a landing-page URL or `.html` file, with no codebase | **Landing page**: Steps 1–7; screens come only from page imagery |
| `<out>/src/config.js` exists and the user asks for edits or a re-render | **Update**: refresh the kit files (below), edit `config.js`, then Steps 5–7 |
| Only watchOS, tvOS or visionOS, or no Apple target | **Stop**: report BLOCKED with the reason; write nothing |
| No input named or found | Ask for the codebase path or landing-page URL; write nothing |

Update branch kit refresh: note whether `src/kit.js` predates video (no `__seek` in it), then
copy the template's `kit.js`, `kit.css` and `index.html` into `src/`, first backing up any that
differ as `<name>.bak-<timestamp>` so a hand edit is never lost. List the backups in the report.

```bash
grep -q __seek "<out>/src/kit.js" || echo "kit predates 1.1.0: header/search stills will be re-laid out"
ts=$(date +%Y%m%d-%H%M%S); for f in kit.js kit.css index.html; do
  cmp -s "<skill>/assets/template/$f" "<out>/src/$f" || { [ -e "<out>/src/$f" ] && cp "<out>/src/$f" "<out>/src/$f.bak-$ts" && echo "backup: src/$f.bak-$ts"; }
  cp "<skill>/assets/template/$f" "<out>/src/$f"; done
```

Prerequisites: run `python3 <skill>/scripts/render.py --preflight` (add `--video` when a
creative video is requested). It requires Pillow and Chrome or Chromium, plus ffmpeg 4.1 or later with
libx264 and ffprobe for video, and prints the fix for a missing one (use the project's venv
when it has one). If it fails, report BLOCKED; if only the video tools are missing, build
the stills and report PARTIAL. Without the Agent tool, run Steps 1 and 6 inline and say so.
For a landing page, confirm the user publishes the app before building; never make assets
for someone else's app.

## Repo Sync Before Edits (mandatory)

Before the first write of Step 4 (the backup included), sync the repo that will hold `<out>`.
Skip it, and record why, when that folder is not in a git repo or the repo has no `origin`.

```bash
repo="$(git -C "<existing parent of out>" rev-parse --show-toplevel)"; branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"
[ -n "$(git -C "$repo" status --porcelain)" ] && git -C "$repo" stash push -u -m appstore-assets-presync && stashed=1
if git -C "$repo" fetch origin && git -C "$repo" pull --rebase origin "$branch"; then sync=ok
elif [ -d "$repo/.git/rebase-merge" ] || [ -d "$repo/.git/rebase-apply" ]; then git -C "$repo" rebase --abort; sync=conflict
else sync=failed; fi
[ "${stashed:-0}" = 1 ] && git -C "$repo" stash pop
```

`sync=failed` (network, auth, missing branch): record it and continue. `sync=conflict`:
write nothing and ask the user how to continue. This skill never commits, pushes or uploads.

## Dependency Preflight (mandatory)

This skill optionally invokes `frontend-design` (Step 3), `emil-design-eng` (Step 6) and
`browse` (landing-page fetch), declared in frontmatter `dependencies`. Before Step 1:

```bash
command -v asm >/dev/null || echo "asm not installed: npm install -g agent-skill-manager"
asm deps discover "<this skill's directory>" --json
printf 'aa_session=%s\n' "appstore-assets-$(date +%s)-$$"   # record it; reuse it verbatim
```

At a dependency's first use, run `asm deps acquire <reference> --session <aa_session> --json`
with its frontmatter reference, and read the returned `skillMdPath`. Without `asm`, look for
`~/.claude/skills/<name>/SKILL.md` or `~/.agents/skills/<name>/SKILL.md`. Never acquire a
dependency whose step is not reached. At the end, including an early stop, run
`asm deps release --session <aa_session> --json`. All three are fail-soft: without
`frontend-design` or `emil-design-eng`, use `references/design-direction.md` and note it
under Uncertainty; without `browse`, use the host's web-fetch tool.

## Step 1 — Discover (explorer subagent)

Spawn the explorer. Input: `agents/app-explorer.md`, `references/input-discovery.md`, the
input path or URL, and whether `browse` is available. Output: the app brief JSON. Do not
read the source tree yourself in this step; the explorer keeps it out of your context budget.

Bar: every platform carries evidence and every screen has a `source`. If `stop_reason` is set, take the Stop branch.

## Step 2 — Refresh Apple's specs

Fetch the source URLs in `references/apple-specs.md` and compare the required classes,
sizes and, when video is requested, the header/search video rows. The kit's sizes are fixed in `render.py` and `check_assets.py`, so if a class
changed, render only the unchanged classes, report PARTIAL, and list each difference. If
the fetch fails, use the snapshot and record its date under Uncertainty.

Bar: each platform's required display class and pixel size are named.

## Step 3 — Plan and approve

Read `references/apple-guidelines.md` and `references/design-direction.md`. Acquire
`frontend-design` and apply its Design Thinking to the marketing canvas only, with the
app's brand as the explicit brief.

1. Choose 3–10 frames. The first three carry the core promise.
2. Give each frame a two-line headline, an optional supporting line, and one screen.
3. Choose each screen's UI source: a clean capture first, then a grounded screen. If neither exists, drop the frame.
4. Remove every overclaim. For sensitive features, reuse the brief's `approved_wording`.
5. Ask one combined question: direction (2–3 options), frame list, UI source, extras (creative images, header/search videos with their beats and length, Custom Product Page variants, preview page).
6. If the run is pre-authorized, state the plan in one line and continue. Extras stay off unless requested.
7. For a video, plan beats: beat 0 is the still creative; each extra beat is one caption plus one grounded frame. Default 12 s at 30 fps; it must read with the sound off (`references/design-direction.md` → Motion).
8. If the brief has no screens (no readable views and no page UI), ask for simulator captures instead.

Bar: the plan is approved or pre-authorized, and nothing was written before that. If the run
ends unanswered, report BLOCKED with the pending question as the Decision.

## Step 4 — Build the asset set

1. Set `<out>`: the user's path; else `metadata/screenshots/<version>/` when the repo has `metadata/`; else `appstore-assets/<version>/` at the repo root (the working directory in landing-page mode). Without a version, use today's date. For several languages, add a `<locale>/` level per set.
2. Run the repo sync. If `<out>` exists outside the Update branch, move it to `<out>.bak-<timestamp>` and record the move.
3. Copy `assets/template/` to `<out>/src/`, then run `scripts/fetch_font.py "<caption face>" <out>/src`. Offline, delete `fonts.display` from `config.js` and record it.
4. Copy clean captures to `<out>/src/captures/` and any logo the UI shows to `<out>/src/`.
5. Open each selected screen's cited view, then rewrite `config.js` with `references/render-pipeline.md`. Put `// Source: path:line` above every screen builder.
6. Write `<out>/PLAN.md`: per frame, the id, headline, UI source, evidence, and any element left out on purpose (for example a "Coming soon" row).

Bar: `grep -c "TODO:" <out>/src/config.js` prints `0`, every screen builder cites a source, and
every video beat's hero and sides name existing frames (`references/render-pipeline.md` → Video creatives).

## Step 5 — Render and verify

```bash
python3 "<skill>/scripts/render.py" <out>/src
python3 "<skill>/scripts/check_assets.py" <out> --platforms <list> --sheet <out>/sheets
```

`render.py` also fails on unknown icons, missing images, caption contrast below 3:1
(headline) or 4.5:1 (supporting line), and a video beat held shorter than its caption needs;
it removes the PNGs and videos it wrote that the config dropped, and warns about (but keeps) other files in `creative/`. Videos render last and are slow (about a
second per 4K frame), so iterate with `--no-video`. `check_assets.py` probes each video (size,
30/60 fps constant, 5–30 s, H.264 yuv420p, audio) and fails a blank frame or a loop-seam jump;
with `--sheet` it writes `sheets/video-<kind>.png`. If a script fails, apply the fix it prints
and re-run it. Bar: both commands exit 0.

## Step 6 — Review and polish

1. View every sheet in `<out>/sheets/`, video sheets included. Fix text overlapping a device, clipped strings, blank screens, and a caption outside the magenta safe area.
2. Acquire `emil-design-eng` and spawn a polish worker with the slice and task in `references/design-direction.md`. Apply its accepted rows to `config.js` only (`css` and brand tokens), then re-run Step 5.
3. Spawn a fresh reviewer, never the builder. Input: `agents/asset-reviewer.md`, `references/apple-guidelines.md`, the full-size PNGs, the video sheets, `config.js`, `PLAN.md`, the brief, and source access.
4. If the verdict is `NEEDS_FIX`, fix each blocking finding, re-run Step 5, and spawn a new reviewer. Stop after two fix cycles.

Bar: the latest verdict is `PASS` on the latest render, or two cycles ran and the report is PARTIAL.

## Step 7 — Hand off

If the user asked for a preview, publish a gallery of the sheets with the host's page tool,
or point to `<out>/src/index.html` opened without a query string. Never upload: offer
`asc`, `fastlane deliver` or a manual App Store Connect upload as a next step that needs
approval; creative images and videos go through App Store Connect "either alongside a new app version, or in your Asset Library" (Apple's asset best practices). Release the dependency session.

## Edge Cases

- Captures with QA data, an open keyboard or old UI are not clean: use grounded screens and say why.
- A feature gated by an entitlement the project lacks (CarPlay, HealthKit, Watch) is never drawn.
- "Coming soon" and roadmap features stay out of frames and captions; record the omission in `PLAN.md`.
- An iPhone-only app needs no iPad set, even though it runs on iPad.
- Rendering on Linux replaces SF Pro in the UI: record it under Uncertainty.
- An "App Store video" request is ambiguous: an App Preview (recorded footage) is out of scope; offer a header or search video, and build one only once it is chosen or pre-authorized.
- Voice-over, music or "sound on" requests: videos ship silent (muted by default); put every message in captions and record the decision.
- A video beat that needs a screen no frame shows needs a grounded frame first, or the beat is dropped.
- Custom Product Pages: one `variants[]` entry per page or ad creative, only when asked; renders to `creative/<id>/`.

## Acceptance Criteria

A run is COMPLETE only when you verify every item:

- [ ] `render.py` and `check_assets.py` exit 0 on the final state: exact sizes, RGB without alpha, at most 10 per class, the required class per platform, caption contrast, no dropped-frame leftovers.
- [ ] `iphone-6.9/` and `iphone-6.3/` hold the same frame names.
- [ ] Each requested video passes `check_assets.py` (exact size, 30/60 fps CFR, 5–30 s, H.264 yuv420p, no blank frame or seam jump), and its sheet shows every caption inside the safe area.
- [ ] `config.js` holds no `TODO:` and every screen builder cites `// Source:`.
- [ ] The latest reviewer verdict is `PASS`, with no blocking finding.
- [ ] Nothing was committed, pushed or uploaded.

## Final report

Expected output: open with the result and keep the four labels.

```
Result: COMPLETE | PARTIAL | BLOCKED — <what was produced, where, frames per class>
Evidence: <checks that ran: render.py and check_assets.py summaries, video size/fps/duration/seam rows, lowest contrast, reviewer verdict, spec refresh, sync>
Uncertainty: <recreated or approximated screens to verify on a build, classes not rendered, fallbacks, assumptions (video codec, search video size, file-size cap, safe area applied to video)>
Decision: <the approval needed next (upload, commit, a dropped frame), or "No approval needed">
```

On the Update branch, list each `src/*.bak-<timestamp>` backup under Evidence. If the old kit
predated 1.1.0, say under Decision that `header.png` and `search.png` changed composition (the
caption, and the search hero, now sit in Apple's art safe area), so the user reviews them before upload.

PARTIAL means assets exist but a check or blocking finding remains; BLOCKED means no assets
were written. State that nothing was committed or uploaded, and name the recreated frames.
When grading runs, also check that a reader finds the result first, can tell verified facts
from assumptions, can trace each claim to evidence, and sees the next decision. Without a
human review, mark that understanding as unconfirmed.

## Reference files

- `references/apple-specs.md`: sizes, required classes, creative image and video specs, safe areas, encoding decisions, source URLs (Steps 2, 5).
- `references/apple-guidelines.md`: content rules, overclaim traps, story and captions (Steps 3, 6).
- `references/input-discovery.md`: where each brief field comes from (explorer slice, Step 1).
- `references/design-direction.md`: frontend-design and emil-design-eng mapping, polish checklist (Steps 3, 6).
- `references/render-pipeline.md`: asset set layout, commands, config shape, video timeline and variants, kit API, troubleshooting (Steps 4, 5).
- `agents/app-explorer.md` and `agents/asset-reviewer.md`: worker contracts (Steps 1, 6).
