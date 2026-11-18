# lstack

lstack is a Claude Code plugin with 16 first-party Agent Skills for everyday
engineering work: code review, test generation, documentation, diagrams,
CI pipelines, release shipping, repository cleanup, open-source readiness,
architecture documents and agent instruction files. Each skill is a plain-text
playbook: a `SKILL.md` with optional Markdown references and templates. The
plugin has no scripts, hooks, MCP servers, native agents or bundled binaries,
and it installs no packages when you install it.

Source: [github.com/luongnv89/skills](https://github.com/luongnv89/skills) ·
Homepage: [luongnv.com/skills](https://luongnv.com/skills/) · License: MIT

## Install

```bash
claude plugin marketplace add luongnv89/skills
claude plugin install lstack@lstack --scope user
```

Skills are namespaced, so call them as `/lstack:code-review`,
`/lstack:drawio-generator`, and so on. Claude also loads a skill on its own
when your request matches the skill's description. There is no `/lstack` entry
point. To update, run `claude plugin marketplace update lstack`, then
`claude plugin update lstack@lstack --scope user`.

The same marketplace offers **lstack-extras**, 32 more skills for product,
marketing, App Store, design/UX, agent fleets and machine setup, many with
helper scripts: `claude plugin install lstack-extras@lstack --scope user`.

## Before you run a skill

- **Some skills act with your credentials.** They use your local `git`, `gh`,
  PyPI and npm logins. `ship` commits, tags, pushes, creates a GitHub release
  and publishes to PyPI and npm **without asking by default**; pass `--no-auto`
  to confirm each step. `auto-push` stages everything, commits and pushes once
  its secret and large-file scan passes. Other skills that push, delete
  branches or open PRs ask first.
- **Some skills install dev dependencies.** `test-coverage` installs missing
  coverage tools, and `cli-builder` adds CLI framework dependencies to the
  project it builds.
- **Data leaves your machine only where the table below says.** Model-provider
  traffic depends on your own Claude Code setup and is not listed. Third-party
  services have their own terms; lstack makes no promise about how they handle
  data. `opencode-runner` sends the task to OpenCode's free cloud models, which
  may use it for training.
- Some skills need external tools: authenticated `gh`, OpenCode or `asm`. The
  plugin bundles none of them. See each skill's `SKILL.md` for its
  prerequisites.

## What each skill runs, sends or fetches

"Your git remote" means `git fetch`/`pull` against the repository you are
working in. That is the only network access many skills make.

| Skill | Network destinations | Data sent | Actions with your credentials | Tools it runs |
|---|---|---|---|---|
| agent-config | your git remote | none | none; writes local files only | git |
| auto-push | your git remote | all working-tree changes and the commit message | `git add`, commit and push, automatic once the safety scan passes | git |
| cleanup-project | your git remote, GitHub API via `gh` | branch names; on confirmation, commits, branches and PR text | after one confirmation: delete remote branches, push main or archive branches, `gh pr create` | git, gh |
| cli-builder | your git remote; package registries when adding CLI framework dependencies | dependency names | local branch and commits only | git, pip, npm, go, `npx oclif`, project test runner |
| code-review | your git remote; Context7 MCP (optional) | library doc queries | local commits per cleanup category (cleanup mode); no push | git, knip, madge, ts-prune, vulture, jscpd, pylint and similar linters |
| devops-pipeline | your git remote; generated hooks and CI fetch pre-commit hook repos, npm packages, GitHub Actions and Codecov when they run | the generated CI uploads coverage to Codecov through GitHub OIDC; no token is stored or read | writes pre-commit and CI config, installs git hooks; no commit or push | git, pre-commit; generated hooks run prettier, eslint, tsc |
| diagram-generator | none | none | none | asm; routes to drawio-generator or excalidraw-generator |
| doc-manager | your git remote; your own health endpoint when the generated check script runs | a GET to your endpoint | creates a feature branch and writes docs; no commit unless asked | git, bash, mmdc (optional) |
| drawio-generator | your git remote, before writing into a repo | none | none | git |
| excalidraw-generator | your git remote, before writing into a repo | none | none | git |
| frontend-design | your git remote; optional browser for render checks | none | writes UI files after approval; runs your build, lint and test commands | git, project tooling |
| opencode-runner | OpenCode Zen (opencode.ai) and its free-model providers; your git remote | the task prompt, files passed with `--file`, and repository files OpenCode reads. Free models may use this data for training | OpenCode may edit files in the working directory; the skill does not commit | opencode, git |
| oss-ready | GitHub API via `gh repo view`; your git remote | the repository name (read-only) | creates a local branch; no commit or push | git, gh, python3 |
| ship | your git remote, GitHub API via `gh`, PyPI (`pypi.org` JSON API, `twine upload`), npm registry | release commits, tags, release notes, built packages, package lookups | **automatic by default**: commit, tag, push, `gh release create`, `twine upload`, `npm publish`; `--no-auto` asks first; never force-pushes. Never reads upload credentials: `twine` and `npm` use their own login, and an auth failure skips that registry | git, gh, curl, python -m build, twine, npm, your project's build |
| tad-generator | web search/fetch for technology research; your git remote | stack research queries; `tad.md` commits | commit, then push only after you approve | git, mmdc (optional) |
| test-coverage | npm registry if `npx jest`/`npx vitest` is not installed locally; package registries for coverage tools (pytest-cov, nyc, cargo-tarpaulin); your git remote | package names | creates a feature branch and commits new tests locally; installs missing coverage dev dependencies; no push | your test runner, git |

## Support

Report problems at
[github.com/luongnv89/skills/issues](https://github.com/luongnv89/skills/issues).
The full catalog, other install methods and contribution guide are in the
[repository README](https://github.com/luongnv89/skills#readme).
