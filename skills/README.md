# lstack

lstack is a Claude Code plugin with 43 first-party Agent Skills for everyday
engineering and product work: code review, test generation, documentation,
diagrams, release shipping, repository cleanup, SEO and App Store audits,
product planning, and multi-agent orchestration. Each skill is a plain-text
playbook: a `SKILL.md` with optional references, scripts and templates. The
plugin has no hooks, MCP servers, native agents or bundled binaries, and it
installs no packages when you install it.

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

## Before you run a skill

- **Some skills act with your credentials.** They use your local `git`, `gh`,
  PyPI and npm logins. `ship` commits, tags, pushes, creates a GitHub release
  and publishes to PyPI and npm **without asking by default**; pass `--no-auto`
  to confirm each step. `auto-push` stages everything, commits and pushes once
  its secret and large-file scan passes. `idea-validator` commits and pushes
  its reports to your ideas repo without a further prompt. `github-pages-publish`
  pushes the site to the target repo's default branch and sets its Pages source
  without a further prompt, but asks before creating a repo or making one public. Other skills that
  push, delete branches or open PRs ask first.
- **Agent-fleet skills pass on autonomy.** `herdr-agent` starts worker agents
  with the same permission-bypass flags as the agent that launched them
  (`--dangerously-skip-permissions`, `bypassPermissions`, Codex bypass, pi
  `--approve`). It prints a warning, and `--without bypass` turns this off.
  `issue-work-loop` drops those flags, then switches Claude workers to
  auto-accept edits and OpenCode workers to the full-permission Build agent.
  Neither skill edits your Claude settings files.
- **Some skills install software, but only after you approve each item.**
  `dev-machine-setup` can run remote installers (Homebrew, NodeSource, uv, Oh
  My Zsh, starship, Claude Code) and system package managers with `sudo`.
  `security-setup`, `ollama-optimizer` and `test-coverage` install tools or dev
  dependencies they need.
- **Data leaves your machine only where the table below says.** Model-provider
  traffic depends on your own Claude Code setup and is not listed. Third-party
  services have their own terms; lstack makes no promise about how they handle
  data.
- Some skills need external tools or other skills: authenticated `gh`, Herdr,
  OpenCode, gstack `browse`, the idd skills and `asm`. The plugin bundles none
  of them. See each skill's `SKILL.md` for its prerequisites.

## What each skill runs, sends or fetches

"Your git remote" means `git fetch`/`pull` against the repository you are
working in. That is the only network access many skills make.

| Skill | Network destinations | Data sent | Actions with your credentials | Tools it runs |
|---|---|---|---|---|
| agent-config | your git remote | none | none; writes local files only | git |
| ai-job-scout | web search and fetch: public profiles, employer career sites, ATS boards (Greenhouse, Lever, Ashby, Workable), job aggregators | search queries built from the candidate's skills, roles and location | none; never applies or contacts anyone | web search/fetch, optional browser |
| appstore-assets | your git remote; developer.apple.com (screenshot and creative-asset spec pages); Google Fonts and raw.githubusercontent.com/google/fonts (caption font and its license); the app's landing page when there is no code; GitHub when `asm deps acquire` fetches `emil-design-eng` | the spec and font URLs, the font family name, the landing-page URL | none; never commits, pushes or uploads to App Store Connect | git, python3 (Pillow), headless Chrome/Chromium, asm, web fetch/browse |
| appstore-review-checker | your git remote | none | none; never reads App Store Connect keys | git |
| aso-marketing | your git remote | none | none; store uploads are left to you | git |
| auto-push | your git remote | all working-tree changes and the commit message | `git add`, commit and push, automatic once the safety scan passes | git |
| brand-name-checker | web search/fetch: npm, PyPI, Homebrew, Debian/Ubuntu packages, social sites, domain registrars, WIPO, EUIPO, INPI | the candidate name | none | web search/fetch, git |
| cleanup-project | your git remote, GitHub API via `gh` | branch names; on confirmation, commits, branches and PR text | after one confirmation: delete remote branches, push main or archive branches, `gh pr create` | git, gh |
| cli-builder | your git remote; package registries when adding CLI framework dependencies | dependency names | local branch and commits only | git, pip, npm, go, `npx oclif`, project test runner |
| code-review | your git remote; Context7 MCP (optional) | library doc queries | local commits per cleanup category (cleanup mode); no push | git, knip, madge, ts-prune, vulture, jscpd, pylint and similar linters |
| codebase-modernizer | package registries and advisory databases (npm, PyPI, Go proxy and vuln DB, crates.io and RustSec, RubyGems, Maven, Packagist, NuGet, pub.dev, Hex) unless `--offline`; Context7 (optional); your git remote | dependency names, versions and lockfile trees | none; read-only, never installs or upgrades | `dep_scan.sh` with npm, pip-audit, govulncheck, cargo audit and similar; local `tsc` |
| design-optimizer | the target URL and its robots.txt, sitemap.xml and llms.txt; headless browser via `browse`; isitagentready.com only through `website-agent-readiness` after you approve | HTTP requests for the public pages; the target URL | git fetch/pull in apply mode; no push | curl, python3, asm, git, delegated review skills |
| dev-machine-setup | OS package repositories, npm registry, raw.githubusercontent.com, deb.nodesource.com, astral.sh, starship.rs, github.com plugin clones, claude.ai/install.sh | package and download requests only | each item needs your yes: `sudo` installs, `curl \| sh` and `irm \| iex` installers, `npm install -g`, `chsh`, shell rc edits (with backup), global git config, Windows app removal | brew, apt, dnf, pacman, winget, npm, curl, git, PowerShell |
| devops-pipeline | your git remote; generated hooks and CI fetch pre-commit hook repos, npm packages, GitHub Actions and Codecov when they run | the generated CI uploads coverage to Codecov with your `CODECOV_TOKEN` secret | writes pre-commit and CI config, installs git hooks; no commit or push | git, pre-commit; generated hooks run prettier, eslint, tsc |
| diagram-generator | none | none | none | asm; routes to drawio-generator or excalidraw-generator |
| doc-manager | your git remote; your own health endpoint when the generated check script runs | a GET to your endpoint | creates a feature branch and writes docs; no commit unless asked | git, bash, mmdc (optional) |
| dont-make-me-think | the target URL via `browse` (live-URL path only); your git remote (redesign mode) | page loads; screenshots are processed locally | UI edits after you confirm the diff; no commit | browse, asm, python3 (Pillow, OpenCV), git |
| drawio-generator | your git remote, before writing into a repo | none | none | git |
| excalidraw-generator | your git remote, before writing into a repo | none | none | git |
| frontend-design | your git remote; optional browser for render checks | none | writes UI files after approval; runs your build, lint and test commands | git, project tooling |
| github-pages-publish | your git remote; GitHub via `gh` (the target repo, its Pages settings and Actions runs, release lookups for the `actions/*` deploy actions); the published site (live check) | the site content you publish, which becomes a public website | commits and pushes the site to the target repo's default branch and sets Pages to deploy from Actions without a further prompt; asks before creating a repo or making a private repo public | git, gh, python3, asm (optional, for frontend-design) |
| herdr-agent | local Herdr socket; workers contact their own model providers | task prompts typed to worker agents | starts workers with the launcher's permission-bypass flags by default (see above); types into panes | herdr, python3, claude, codex, pi |
| idea-validator | web search; your ideas repo remote | idea text and search queries; reports committed to your remote | commits and pushes `idea.md` and `validate.md` without a further prompt | git, web search |
| install-script-generator | your git remote; a HEAD request to raw.githubusercontent.com when `install.sh` already exists | repository owner, name and branch | none; no commit or push | git, python3 helpers (dry run), bash, shellcheck, curl |
| issue-work-loop | GitHub API via `gh`, your git remote, worker agents' model providers | issue and PR data, repository source and diffs to workers; commits to the PR branch | workers commit and push (never force) to the PR branch; ISSUE mode opens a PR; never merges | gh, git, herdr, asm, idd skills |
| landing-page-generator | your git remote; the built pages may load web fonts or a pinned Mermaid script in your browser | none | none unless you ask for a commit | git, python3, asm (optional, for frontend-design) |
| logo-designer | your git remote; the generated showcase page loads Google Fonts in your browser | none | none | git, `open` |
| ollama-optimizer | your local Ollama server; the Ollama model registry on `ollama pull` (after approval) | a benchmark prompt to local Ollama; model names to the registry | each change needs approval: shell rc edits, `launchctl setenv`, `sudo` systemd drop-ins, service restarts | ollama, nvidia-smi, rocm-smi, launchctl, systemctl, sudo |
| opencode-runner | OpenCode Zen (opencode.ai) and its free-model providers; your git remote | the task prompt, files passed with `--file`, and repository files OpenCode reads. Free models may use this data for training | OpenCode may edit files in the working directory; the skill does not commit | opencode, git |
| oss-ready | GitHub API via `gh repo view`; your git remote | the repository name (read-only) | creates a local branch; no commit or push | git, gh, python3 |
| prd-generator | your ideas repo remote | `prd.md` and `README.md` commits | commit and push after asking; never force | git |
| product-planner | your git remote; member skills reach their own destinations | none itself | none itself; `idea-validator` pushes without asking, the other members ask first | git, asm, planning skills |
| search-optimizer | the target site's page, robots.txt, sitemap.xml and llms.txt; isitagentready.com only through `website-agent-readiness` after you approve; your git remote | the target URL | git fetch/pull; no push | curl, python3, git, asm, delegated audit skills |
| security-setup | package registries for approved tool installs; Trivy vulnerability DB download; your git remote. Installed hooks then run offline | package names only | writes hook config, scripts and `SECURITY.md` after a dry run and approval; no push | git, pre-commit, gitleaks, trivy, semgrep, bandit, detect-secrets |
| seo-ai-optimizer | web search for current guidance; your deployed site when needed; isitagentready.com only through `website-agent-readiness` after you approve; your git remote | generic search queries, the URL you supply | edits SEO files after plan approval and per-diff confirmation; no push | python3, git, asm |
| ship | your git remote, GitHub API via `gh`, PyPI (`pypi.org` JSON API, `twine upload`), npm registry | release commits, tags, release notes, built packages, package lookups | **automatic by default**: commit, tag, push, `gh release create`, `twine upload`, `npm publish`; `--no-auto` asks first; never force-pushes. Checks that `TWINE_PASSWORD` or `~/.pypirc` exists and runs `npm whoami` | git, gh, curl, python -m build, twine, npm, your project's build |
| tad-generator | web search/fetch for technology research; your git remote | stack research queries; `tad.md` commits | commit, then push only after you approve | git, mmdc (optional) |
| tasks-generator | your git remote | `tasks.md` commits | commit, then push only after you approve | git, python3 |
| test-coverage | npm registry if `npx jest`/`npx vitest` is not installed locally; package registries for coverage tools (pytest-cov, nyc, cargo-tarpaulin); your git remote | package names | creates a feature branch and commits new tests locally; installs missing coverage dev dependencies; no push | your test runner, git |
| tmux-agent-comms | none itself; agent CLIs it launches use their own network | task text typed into local sessions | asks before ending or killing sessions | tmux, python3, bash |
| ux-ax-review | the target site's pages, robots.txt, sitemap, llms.txt and public machine-readable routes; your git remote | the target URL and paths it reads | none; no commit, form submission or publishing | browser/retrieval tools, git, python3 |
| viral-product-evaluator | the landing-page URL via `browse`, after you confirm; competitor pricing research; your git remote | the landing-page URL | writes `viral-evaluation.md` only | browse, asm, git, python3 |
| website-agent-readiness | isitagentready.com (`POST /api/scan`, after approval gate G1; localhost is refused); GitHub API via `gh` | the target URL, which isitagentready.com then fetches; plan tasks become GitHub issues | creates a GitHub epic and issues through `plan-to-issues` after gate G4 | curl, python3, git, gh, asm |

## Support

Report problems at
[github.com/luongnv89/skills/issues](https://github.com/luongnv89/skills/issues).
The full catalog, other install methods and contribution guide are in the
[repository README](https://github.com/luongnv89/skills#readme).
