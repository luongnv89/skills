# Native-app applicability

For native-only iOS/Android/macOS/desktop surfaces, keep all six human aspects. Adapt
responsive to supported sizes/orientation, dynamic text/window resizing; accessibility to
platform APIs, keyboard/VoiceOver/TalkBack; performance to launch, frame pacing, responsiveness,
network and battery using actual traces rather than web vitals. Conversion may mean the
primary user task rather than payment. Screenshots alone cannot prove runtime behavior.

For a native-only scope with no supplied public companion site, mark `robots-sitemap`,
`structured-data`, `markdown-pages`, `llms-txt`, and `crawler-access` **not-applicable**
with rationale: no public web/search surface in scope. Do not prescribe robots files
inside an app bundle or invent a companion site. App-store/distribution metadata is a
separate public surface only if explicitly included.

`ai-actions` remains potentially applicable: copy/share/deep links, export and opt-in AI
handoff can serve native tasks. Assess provided evidence; if inaccessible use not-tested,
if the task has no meaningful share/export/AI handoff record a reasoned not-applicable.
Never penalize a private native app for intentionally not publishing its content.

For hybrid/webview apps, apply web checks only to supplied public web surfaces; separate
authenticated app screens and native shells in scope/evidence. Native security/privacy
policy takes precedence over suggestions to publish Markdown or widen crawler access.
