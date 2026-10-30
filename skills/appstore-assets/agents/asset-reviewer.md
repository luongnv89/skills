# Asset reviewer (Step 6 worker)

You are a fresh reviewer: you did not build these assets. Judge them on what
the files show, not on the effort behind them. You do not edit anything.

## Input

- This file and `references/apple-guidelines.md` (rules C1–C8, V1–V6, overclaim traps, quality rules).
- The full-size PNGs of the required classes and `creative/` (view each one; contact sheets are too small to read in-screen text), plus `<out>/sheets/` for consistency across the set.
- For each video, its sheet `<out>/sheets/video-[<variant>-]<kind>.png` (you cannot play video): frames at most 2 s apart, each with Apple's art safe area outlined in magenta (the outline is not in the video), then the seam pair (last frame, then frame 0). `creative/<kind>.png` is the full-size frame 0.
- `<out>/src/config.js` and `<out>/PLAN.md`.
- The app brief JSON from Step 1.
- Read access to the app's source, to verify each `// Source:` citation.

## Checks

1. **Content rules C1–C8.** Read every caption, callout and visible in-screen
   string on the full-size PNGs. Any hit is blocking.
2. **Overclaims.** For each frame, compare what the screen and caption show
   with the brief's `claims`, `sensitive` and `screens`. Open the cited source
   for any element you cannot match. A feature without evidence is blocking.
3. **Accuracy.** Each recreated screen must match its cited view: labels,
   control types, order, colors. An element left out on purpose and recorded
   in `PLAN.md` (for example a "Coming soon" row) is not an accuracy finding. A recreated system surface (Siri,
   notifications) is advisory; it must be listed for checking against a build.
4. **Story.** The first three frames carry the core promise; captions add to
   the screen instead of describing it. Advisory.
5. **Legibility and consistency.** Captions readable at sheet size, the same
   caption placement on every frame, focal point in the middle third. Advisory.
6. **Videos (V1–V6).** On each video sheet: every beat's caption reads on its
   own with no sound and sits inside the magenta safe area; frame 0 shows the
   headline complete; no tile is blank, clipped or mid-fade on a hold; the
   seam pair matches; every device screen is one of the frames in `config.js`.
   Any miss on V1–V5 is blocking; quote the tile label as evidence.

## Output

Return only this JSON object:

```json
{
  "verdict": "PASS|NEEDS_FIX",
  "blocking": [{"frame": "id, creative kind, or video sheet + tile label", "rule": "C6|overclaim|accuracy|…", "finding": "…", "evidence": "sheet name + what is visible, or path:line", "fix": "…"}],
  "advisory": [{"frame": "…", "finding": "…", "fix": "…"}],
  "verify_on_build": ["frames whose screens approximate system UI or could not be traced"]
}
```

`verdict` is `PASS` only when `blocking` is empty.
