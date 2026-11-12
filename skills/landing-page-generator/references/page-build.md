# Page Build

The last workflow step in both modes (Mode A Step 7, Mode B Step 8): `frontend-design` builds
the final landing page and the companion pages from the copy this run delivered. The copy
decides every word on the page; `frontend-design` decides only the look. `SKILL.md` →
*Dependency Preflight* says how to load `frontend-design`; this file holds the build
decision, the output folder, the brief, the fallback, and the page checks.

Contents: [Build decision](#build-decision) · [Output folder](#output-folder) ·
[Brief for frontend-design](#brief-for-frontend-design) · [Fallback: copy only](#fallback-copy-only) ·
[Page checks](#page-checks)

## Build decision

Apply the first row that matches. Record the result as the run's `page:` entry; every run
has one, so a page is never skipped silently. If a later item fails (the acquire, Repo Sync,
or `frontend-design` itself), replace the entry with `page: not built — <reason>`.

| Condition | Action | Record |
|---|---|---|
| The user says copy only, text only, no HTML, no page, or that they will build or design the page themselves | Build nothing; do not acquire `frontend-design` | `page: skipped — copy only requested` |
| The run delivered a single section, or companion pages without landing copy, and the user did not ask for HTML, a website file, or a built page by name | Build nothing; do not acquire `frontend-design` | `page: skipped — <single section \| companion pages only>` |
| The host cannot write files | Follow *Fallback: copy only* | `page: not built — host cannot write files` |
| Otherwise | Build each page below | `page: built (<folder>: <files>)` |

Pages to build, each only when the run delivered, wrote, or linked it:

| Source | File | Footer order |
|---|---|---|
| Mode A landing copy, or the rewritten `README.md` (Mode B) | `index.html` | — |
| Privacy Policy | `privacy.html` | 1 |
| Terms of Use | `terms.html` | 2 |
| Changelog | `changelog.html` | 3 |
| Docs | `docs.html` | 4 |
| A page the user added by name | `<kebab-case-name>.html` | After Docs |

A Mode B page recorded as `linked` is the user's existing file: build its page from that
file's text verbatim and leave the file unchanged. A page outside the output folder would
break once the folder is published.

## Output folder

- Use `landing-page/` in the current directory (Mode A) or the project root (Mode B), or the folder the user names.
- If `landing-page/` exists and is not empty, use `landing-page-<YYYYMMDD-HHMMSS>/`. If a folder the user named holds a file this step would write, ask before replacing it.
- Write nothing outside the output folder.
- Repo Sync: Mode B already ran it. In Mode A a new folder holds only new files, so record `sync: skipped (new folder)`. When Mode A writes into a user-named folder that already exists, run the `SKILL.md` Repo Sync with `git -C <that folder>` first. If it stops, record `page: not built — repo sync stopped: <reason>`.

## Brief for frontend-design

Read the `skillMdPath` from *Dependency Preflight* and follow that skill with this brief. Put
each item in the brief, with the copy of each page to build attached in full. Where an item
conflicts with a `frontend-design` rule, the item wins.

- **Pre-authorized.** "Just build it": state the aesthetic direction in one line and ask nothing. Build every page and section in one pass, not in phases. If the user asked to review the design first, leave this item out so `frontend-design` asks for approval.
- **Purpose and audience.** Taken from Mode A Step 1, or Mode B Step 2.
- **Style.** The user's brand, palette, fonts, or style notes are the explicit brief. With none, `frontend-design`'s Default Style Guide applies.
- **Standalone static site.** HTML and CSS in the output folder, one file per page from the *Build decision* table, plus shared assets. Do not read, reuse, or change the project's own frontend code. `<meta charset="utf-8">`; write text as characters, not entities, except `&`, `<`, and `>`.
- **Links.** Links between built pages and to their assets are relative, and no local link or image leaves the output folder. A link in the copy to a page built this run points to its `.html` file. Copy each project image or asset the copy uses into `assets/` in the output folder and link it there. Point any other project file link (`examples/`, `LICENSE`, a doc not built this run) at `https://github.com/<owner>/<repo>/blob/HEAD/<path>` (`tree` for a folder) when `git remote get-url origin` names a GitHub repo; otherwise use `#` and a `[proof needed — link to <path>]` (Mode A) or `[placeholder — link to <path>]` (Mode B) marker beside the link text. A `#id` link stays, and the page has an element with that id. Absolute URLs in the copy, web fonts, and a pinned Mermaid script may stay absolute.
- **Sections.** Every section of the copy, in the copy's order. Framework section names (PROBLEM, AGITATE, ATTENTION) are structure, not page text: use the section's own first line as its heading, or a plain heading such as How it works, FAQ, or Pricing. In landing copy, render the text after a slot label (`Headline:`, `CTA Button:`, `Trust Bar:`), never the label, and render an `[Icon concept]` as an icon, not as text. Companion pages keep their section names and field labels (`Effective date:`, `Install:`, New, Fixed).
- **Text verbatim.** Use each headline, subheadline, body line, list item, FAQ entry, and CTA text exactly as written; do not shorten copy to meet a word-count rule. Mode B: keep each `<details>` block as `<details>`, code blocks as `<pre><code>`, and each mermaid diagram's source in `<pre class="mermaid">`.
- **Gap markers verbatim.** Keep each `[proof needed — …]` (Mode A) or `[placeholder — …]` (Mode B) marker as written, visibly highlighted, in its slot. These markers override your no-placeholder quality check: removing or filling one hides a missing fact from the user.
- **Nothing added.** No claim, metric, price, customer, testimonial, tagline, logo, image of a real product, link, or form that the copy lacks. A text wordmark of the product name, in-page anchor navigation, stock imagery, and decorative illustration are allowed.
- **Notes excluded.** The copy's header lines (`LANDING PAGE COPY`, `Product/Service:`, `Framework:`), OPTIMIZATION NOTES, A/B test ideas, conversion tips, and the COMPANION PAGES block are for the user, not the page.
- **CTAs.** Each CTA is a link or button that keeps its text. Use the target the copy or project gives; otherwise `#` and a `[proof needed — CTA link]` (Mode A) or `[placeholder — CTA link]` (Mode B) marker beside it.
- **Footer.** Every page links each built companion page in the footer order above. Each companion page links back to `index.html` when this run built it.
- **Legal draft notice.** `privacy.html` and `terms.html` open with `<!-- Draft for legal review: confirm every statement before publishing. -->`.
- **Checks.** Record `build: not run (static pages)`; do not run the project's build or tests. Skip your own Repo Sync: this run synced or recorded `sync:`.
- **Report.** Return your verification results (responsive, contrast, quality and usability) and your Final Report's Evidence, Uncertainty, and Decision to this run. This run prints the only Final Report.

## Fallback: copy only

When `frontend-design` cannot be loaded, the host cannot write files, Repo Sync stops, or
`frontend-design` ends without writing a page, the run still delivers the copy:

1. Keep every copy deliverable as written: Mode A copy in chat, Mode B `README.md` and companion files.
2. Write no HTML yourself. A page without `frontend-design` would skip its verification checks.
3. Record `page: not built — <reason>` in the step report and on the Final Report's `Result:` and `Evidence:` lines.
4. The Final Report status is `PARTIAL`, even when the user ended the run without answering a design-approval question: the copy exists. Its `Decision:` line names the fix for the reason:

| Reason | Decision |
|---|---|
| `frontend-design unavailable` (no `asm` acquire and no installed `SKILL.md`) | Install `frontend-design`, then ask for the page build on this copy; or use the copy as is |
| `host cannot write files` | Re-run the page build where files can be written; or use the copy as is |
| `repo sync stopped: <reason>` | Resolve the sync, or name a new output folder |
| `frontend-design BLOCKED: <reason>` | Answer its question (for example approve the direction, or say "just build it") |

## Page checks

Run these after `frontend-design` returns, on each file it wrote. Fix each failure, by editing
the page or by re-running `frontend-design` with the failure named, then re-run the check. After
the second fix cycle, list each remaining failure; the run is `PARTIAL`.

Extract a page's visible text before the text checks (replace the path):

```bash
python3 -c 'import html,re,sys; t=open(sys.argv[1],encoding="utf-8").read(); t=re.sub(r"(?is)<!--.*?-->|<(script|style|template)\b.*?</\1>","",t); t=re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|td|th|dt|dd|section|header|footer|nav|blockquote|pre|button|a)>"," ",t); print(re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",t))))' <folder>/index.html
```

| Check | Pass when |
|---|---|
| Pages built | `test -e` passes for each file the *Build decision* listed |
| Sections carried | Each copy line, without its slot label, is found in the page text (`grep -F`); framework section names and *Notes excluded* lines are exempt |
| CTAs carried | Each CTA text is found in the page text, as the text of a link or button |
| Markers carried | The count of `[proof needed` (Mode A) or `[placeholder` (Mode B) in the page text equals the count in that page's copy plus the CTA and link markers this step added |
| Nothing added | The page states no claim, number, price, name, quote, or link that its copy lacks |
| Notes excluded | No *Notes excluded* line appears on a page |
| Links resolve | Each local link and image, with `#…` and `?…` removed, passes `test -e` from the page's folder and its `realpath` is inside the output folder; each `#id` matches an element id on its target page; absolute URLs are not checked |
| Design checks | No `frontend-design` check failed. A failed check makes the run `PARTIAL`, and its Decision moves to this run's `Decision:` line; an untested check goes on the `Uncertainty:` line |
