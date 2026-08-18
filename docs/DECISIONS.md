# Documentation decisions

Append-only log of ambiguities resolved while reconciling docs to the code.

## 2026-07-20

- Q: Full doc-manager inventory scope (option C) — include guide, CHANGELOG, historical root MD dumps, and GH Pages HTML?
- A (user): Yes to full inventory including guide + CHANGELOG. Follow-up “fix open items” brought `docs/index.html` into scope; it was reconciled to current catalog counts, versions, tool support, and installable skills.
- Source: user scope replies “C” and “fix open items”

- Q: Root status/checklist files (`APPSTORE_*`, `PHASE_1_SUMMARY.md`, `DEPLOYMENT_CHECKLIST.md`, etc.) — keep, archive, or delete?
- A (user/doc-manager): User asked to fix remaining open items. Preserve the prose by moving drafts into `docs/archive/`, keep root draft filenames ignored to prevent future local dumps, and explicitly unignore the archived copies in `.gitignore`.
- Source: user reply “fix open items”, `.gitignore` (Documentation drafts block), `docs/archive/README.md`

- Q: Should `clean-code` appear in the README skill catalog?
- A (doc-manager): No. `skills/clean-code/` has no `SKILL.md`; CHANGELOG Unreleased states `clean-code` was merged into `code-review` `clean` mode. Catalog lists installable skills only.
- Source: `CHANGELOG.md` (Unreleased / Removed Skills), `skills/clean-code/` listing, `skills/code-review/SKILL.md` frontmatter

- Q: CONTRIBUTING pointed at `python3 skills/skill-creator/scripts/*` — correct path?
- A (doc-manager): Code/config truth is external skill-creator at `~/.claude/skills/skill-creator/scripts/` (`CLAUDE.md:7-9`). There is no `skills/skill-creator` in this repo. CONTRIBUTING updated to match.
- Source: `CLAUDE.md:7-12`, absence of `skills/skill-creator`

- Q: README frontmatter example vs real skills — top-level `version` or `metadata.version`?
- A (doc-manager): Real skills use `metadata.version` (and often `license`, `effort`). README + CONTRIBUTING examples updated to that shape.
- Source: `skills/doc-manager/SKILL.md`, `skills/code-review/SKILL.md`

- Q: Guide line “No README.md inside the skill folder” vs catalog convention of `docs/README.md`?
- A (doc-manager): Repo convention allows human-only `docs/README.md` with AI-skip comment (`CLAUDE.md:20`, CONTRIBUTING). Guide corrected: no root-level skill `README.md`; `docs/README.md` is allowed.
- Source: `CLAUDE.md:20`, existing `skills/*/docs/README.md`

## 2026-08-18

- Q: CHANGELOG.md Unreleased “New Skills” and “Skills Updated” version cells drifted from on-disk `metadata.version` (e.g. code-review listed as 2.0.1 while `SKILL.md` says 2.1.0). Reconcile them?
- A (user): Yes — “update all docs”; scope “Fix CHANGELOG + touch all docs”.
- Source: 42 tracked `skills/**/SKILL.md` files’ `metadata.version` (fork-upstream-sync 1.3.2, issue-work-loop 1.3.1, diagram-generator 1.1.2, codebase-modernizer 1.2.2, doc-manager 2.0.2, landing-page-generator 1.2.1, code-review 2.1.0, cli-builder 1.0.5, frontend-design 1.2.4, install-script-generator 2.2.1, logo-designer 1.2.3, ollama-optimizer 1.1.1, seo-ai-optimizer 1.2.3, tasks-generator 1.3.1, website-cloner 1.2.1)

- Q: README intro line listed six supported tools but omitted Google Antigravity, which `install.sh` installs.
- A (user): Reconcile to code — add Google Antigravity to the intro line and cite `install.sh:23`.
- Source: `install.sh:23` (TOOLS list), `install.sh:309-321` (Antigravity install case)
