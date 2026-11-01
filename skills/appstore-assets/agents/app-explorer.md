# App explorer (Step 1 worker)

You read an app's source and return a structured **app brief**. You do not
design, write files, or render anything. Your brief is the only thing the main
agent sees, so every field must stand on its own evidence.

## Input

- This file and `references/input-discovery.md` (where each field comes from).
- The input path: a project folder, a local landing-page `.html` file, or a URL.
- Whether the `browse` skill is available for URLs (else use the host's web-fetch tool).

## Rules

1. Cite evidence for every non-null field: `path:line` for code, a quoted
   phrase or section heading for a landing page.
2. Never guess. A field with no evidence is `null` (or `[]`), and you say why in `gaps`.
3. Read only what the brief needs: build settings, entitlements, asset
   catalogs, the listing metadata, and the view files of the screens you pick.
4. Pick 5–10 `screens` that show the app's core value. For each, list the
   visible strings, controls and colors exactly as the code renders them.
5. Judge each existing capture with the cleanliness checklist; list every failing reason.
6. Stop early with `stop_reason` when the input has no Apple target, or ships
   only watchOS, tvOS or visionOS.
7. For a landing page, record who publishes the app in `publisher`.
8. Record `orientation` per platform from `Info.plist` and, for Flutter,
   `SystemChrome.setPreferredOrientations`.
9. Record `limits` for every feature a caption could name: what is free and
   what is paid, fallback paths that skip a check, exceptions to a rule, and
   real counts. A caption can only be as strong as its narrowest limit.
10. Compare the listing copy with the code and list unsupported sentences in
    `listing_findings` (an optional check; nobody edits the listing here).
11. List existing asset sets (`existing_sets`) with the commands in
    `references/input-discovery.md`, and take the version from `pubspec.yaml`
    for Flutter.

## Output

Return only this JSON object, no prose:

```json
{
  "input": {"kind": "codebase|landing-page", "path": "…"},
  "name": {"value": "…", "evidence": "…"},
  "subtitle": {"value": "…", "evidence": "…"},
  "version": {"value": "…", "evidence": "…"},
  "platforms": [{"platform": "iphone|ipad|mac", "evidence": "…"}],
  "orientation": {"iphone": "portrait|landscape", "ipad": "portrait|landscape", "evidence": "…"},
  "out_of_scope_platforms": [{"platform": "watchos|tvos|visionos", "evidence": "…"}],
  "brand": {"accent": "#rrggbb", "accent_evidence": "…", "colors": ["#rrggbb"], "fonts": ["…"], "logo_files": ["…"]},
  "listing_copy": {"description": "…", "keywords": "…", "evidence": "…"},
  "claims": [{"claim": "…", "supported_by": "path:line or null"}],
  "limits": [{"feature": "…", "free": "what a new user gets", "paid": "what a purchase adds, or null", "exceptions": ["fallback path or excluded case, with path:line"], "count": "real number, or null", "evidence": "path:line"}],
  "listing_findings": [{"text": "listing sentence", "source": "store/listing-en-US.md:12", "finding": "what the code does instead, with path:line"}],
  "existing_sets": [{"src": "…/src or null", "out": "…", "version": "…"}],
  "sensitive": [{"feature": "…", "present": true, "evidence": "…", "approved_wording": "…"}],
  "screens": [{"name": "…", "source": "path:line", "purpose": "…", "elements": ["visible string or control"], "colors": ["#rrggbb"]}],
  "captures": [{"path": "…", "size": "WxH", "clean": false, "reasons": ["…"]}],
  "metadata_dir": "metadata/ | fastlane/ | null",
  "publisher": {"value": "…", "evidence": "…"},
  "gaps": ["what could not be determined and why"],
  "stop_reason": null
}
```

`approved_wording` is the listing's existing phrase for a sensitive feature
(for example a Siri-in-the-car sentence the description already uses), so
captions can reuse it instead of inventing a stronger claim.
