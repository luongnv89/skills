# Attribution and supply-chain notes

## Source

- Repository: <https://github.com/firecrawl/anydoc>
- Skill path: `skills/convert-documents-to-markdown/SKILL.md`
- Mirrored at upstream commit: `1c737ec8216777cd382fcd3fc2e0a47637a8fa30` (2026-08-27)
- License: MIT, © Sideguide Technologies Inc. — full text in `../LICENSE`

## npm pin

Upstream invokes the CLI as `npx -y @firecrawl/anydoc <file>` with no version, so every run
would resolve `latest`. This mirror pins the newest release that was at least 7 days old at
mirror time:

- Pinned: `@firecrawl/anydoc@0.2.4`, published 2026-08-27
- Chosen on 2026-09-26

### How to bump

1. `npm view @firecrawl/anydoc time --json` — list every version's publish date.
2. Pick the newest version published at least 7 days ago.
3. Replace the `@0.2.4` pin everywhere it appears:
   - `../SKILL.md` — the `## Instructions` command block, the `## Example` command, and the `## Attribution` mention
   - `../docs/README.md` — the "When to Use" table row and the `## Supply-chain pin` section
   - `evals/evals.json` needs no edit — its expectation is version-agnostic on purpose
   - The root `README.md` catalog row carries no pin; `CHANGELOG.md` entries are history — do not rewrite the `@0.2.4` mention there, add a new `## Unreleased` entry instead
4. Bump `metadata.version` in SKILL.md alongside that CHANGELOG entry.

## Deviations from upstream

Everything outside this list is verbatim upstream content:

- Frontmatter `description` is quoted, gains a negative-trigger clause (repo convention), and is trimmed to ≤250 chars: upstream's parenthetical extension lists (e.g. `(.doc, .docx)`) are dropped — rule 1 still carries the full list — and "Use when a task needs the contents of an office document, spreadsheet, presentation, ebook, or PDF you cannot read directly" becomes "when you cannot read the document directly".
- Frontmatter gains `compatibility`, `effort`, `metadata.version`, and an expanded
  `metadata.author` credit (upstream has none of these).
- The `npx` invocations pin `@0.2.4` (upstream floats on `latest`).
- Upstream's intro line "Run the anydoc CLI. It needs Node 20+ and no install:" became "Run the anydoc CLI:" under `## Instructions`; the Node 20+ / no-install requirement moved to `## Prerequisites`.
- Rule 5 adds that `--ocr hosted` uploads the file to Firecrawl's hosted API and asks the
  agent to confirm first; the upstream text only links to Firecrawl Parse.
- `## When to use`, `## Prerequisites`, `## Instructions`, `## Example`, `## Edge cases`,
  and this `## Attribution` section are additive structure; upstream's six rules and exit
  codes are unchanged.
