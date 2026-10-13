# Step 3 detail: staging the content

Read this at Step 3. Stage everything in `<work>/content/`. Never edit the user's originals.

## Text branch (inline text, `.md`, or `.txt`)

Acquire `frontend-design` (see SKILL.md → Dependency Preflight) and give it this brief.
The brief pre-authorizes it ("just build it"), so it states its direction in one line and
asks nothing:

- Output: `<work>/content/index.html`, plus any asset files in that folder.
- Static HTML and CSS only. No build step, no framework, no external JavaScript.
- Purpose and audience: taken from the text. Title: the text's first heading, or the repo name.
- Use every heading, paragraph, list item, and link of the text verbatim. Keep code blocks as `<pre><code>`.
- Add no claims, prices, features, testimonials, images, or links that the text lacks.
- Use relative paths only.
- `<work>/content/` is a staging folder, not a repo to edit: skip your own Repo Sync step.

Fallback when `frontend-design` is unavailable:

1. Copy `<skill>/assets/text-page.html` to `<work>/content/index.html`.
2. Replace `{{TITLE}}` with the first heading. Replace `{{DESCRIPTION}}` with the first sentence. Replace `{{LANG}}` with the text's language code.
3. Convert the text to semantic HTML: headings, paragraphs, lists, links, `<pre><code>`. Put the result in `{{CONTENT}}`.
4. Check that `grep -cE "\{\{(TITLE|DESCRIPTION|LANG|CONTENT)\}\}" <work>/content/index.html` prints `0`. Escape `<`, `>` and `&` in the user's text; leave other braces as they are.
5. Record "page built from the fallback template" under Uncertainty.

## Ready files branch

| Input | Action |
|---|---|
| One `.html` file | Copy it to `<work>/content/index.html`. Copy each local file it links to, keeping the relative paths |
| A folder with `index.html` at its root | Copy the folder to `<work>/content/` |
| A folder without `index.html`, holding one HTML file | Copy the folder, then rename that file to `index.html` |
| A folder without `index.html`, holding several HTML files | Ask which file is the home page. Rename that one |
| A folder whose site is inside a subfolder (`dist/`, `public/`, `_site/`) | Use that subfolder when it holds `index.html`, and log the choice |

Do not run a build. `check-site` returns `needs-build` when the folder holds site-generator
source (`_config.yml`, `hugo.toml`, `mkdocs.yml`, `astro.config.*`, `vite.config.*`, and
similar). If the folder holds only source files, report BLOCKED. The Decision is "build
the site, then publish the output folder".

## Validate the staged copy

Run `P check-site --dir <work>/content`. For a project site, add `--project-site --fix-root-links`.

| Error id | Handling |
|---|---|
| `no-index` | Apply the table above, then re-run the check |
| `broken-link` | Copy the missing file from the user's source when it exists. If it does not exist, ask the user, or remove the link only with the user's yes |
| `root-absolute-link` | Re-run with `--fix-root-links`. The command rewrites `href`, `src`, `srcset`, and CSS `url()` links to relative paths |
| `needs-build` | Report BLOCKED, as described above |
| `file-too-large`, `site-too-large` | Report BLOCKED. Git hosting rejects files over 100 MB, and Pages rejects sites over 1 GB |

Log every `fixed` entry with its `links`, and every warning. Hidden files (names starting with `.`) are not
deployed, so list them under Uncertainty. The bar is `check-site` exiting 0.
