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
3. Replace the `@0.2.4` pin in the SKILL.md command block and the docs/README.md examples.
4. Bump `metadata.version` in SKILL.md and add a CHANGELOG entry under `## Unreleased`.

## Deviations from upstream

Everything outside this list is verbatim upstream content:

- Frontmatter `description` is quoted and gains a negative-trigger clause (repo convention).
- Frontmatter gains `compatibility`, `effort`, `metadata.version`, and an expanded
  `metadata.author` credit (upstream has none of these).
- The three `npx` commands pin `@0.2.4` (upstream floats on `latest`).
- Rule 5 adds that `--ocr hosted` uploads the file to Firecrawl's hosted API and asks the
  agent to confirm first; the upstream text only links to Firecrawl Parse.
- `## When to use`, `## Prerequisites`, `## Instructions`, `## Example`, `## Edge cases`,
  and this `## Attribution` section are additive structure; upstream's six rules and exit
  codes are unchanged.
