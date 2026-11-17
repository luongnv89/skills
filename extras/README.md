# lstack-extras

lstack-extras is the companion Claude Code plugin to
[lstack](../skills/README.md): 32 first-party Agent Skills for product
planning, marketing and launch, App Store work, design and UX audits, SEO,
agent fleets and machine setup. Many of them ship helper scripts (Python, shell,
HTML/JS templates), so this plugin is offered only from this repository's
marketplace. The plugin has no hooks, MCP servers or native agents, and it
installs no packages when you install it.

## Install

```bash
claude plugin marketplace add luongnv89/skills
claude plugin install lstack-extras@lstack --scope user
```

Call the skills as `/lstack-extras:<skill>`, e.g. `/lstack-extras:idea-validator`.

## Before you run a skill

- **Some skills act with your credentials.** `idea-validator` commits and
  pushes its reports to your ideas repo without a further prompt.
  `github-pages-publish` pushes the site to the target repo's default branch and
  sets its Pages source without a further prompt, but asks before creating a
  repo or making one public. Other skills that push or open PRs ask first.
- **Agent-fleet skills pass on autonomy.** `herdr-agent`, `hc-agent` and `rex-agent` start
  worker agents with the same permission-bypass flags as the agent that
  launched them (`--dangerously-skip-permissions`, `bypassPermissions`, Codex
  bypass, pi `--approve`). They print a warning, and `--without bypass` turns
  this off. `issue-work-loop` drops those flags, then switches Claude workers
  to auto-accept edits and OpenCode workers to the full-permission Build agent.
  None of these skills edits your Claude settings files.
- **Some skills install software, but only after you approve each item.**
  `dev-machine-setup` can run remote installers (Homebrew, NodeSource, uv, Oh
  My Zsh, starship, Claude Code) and system package managers with `sudo`.
  `security-setup` and `ollama-optimizer` install tools they need. `user-test`
  installs a project's dependencies only from its lockfile and Playwright only
  into its own run folder.
- **Data leaves your machine only where the table below says.** Model-provider
  traffic depends on your own Claude Code setup and is not listed.
- Some skills need external tools or other skills: authenticated `gh`, Herdr,
  Rex, gstack `browse`, the idd skills and `asm`. The plugin bundles none of
  them. See each skill's `SKILL.md` for its prerequisites.

## What each skill runs, sends or fetches

"Your git remote" means `git fetch`/`pull` against the repository you are
working in. That is the only network access many skills make.

| Skill | Network destinations | Data sent | Actions with your credentials | Tools it runs |
|---|---|---|---|---|
| agent-profile | your git remote (repo sync before a run in a git repo); the harness CLI you pick contacts its own model provider | the task prompt and the repository files the delegated agent reads, sent by that harness to its provider | runs the harness under your own login only after you say go to the command it shows; a `full` permissions run needs a separate yes every time; creates a git worktree and branch only if you choose one; never commits, merges or pushes | python3, git, mcc (optional), the harness CLI: claude, pi, opencode, codex, droid, devin, grok or gemini |
| ai-job-scout | web search and fetch: public profiles, employer career sites, ATS boards (Greenhouse, Lever, Ashby, Workable), job aggregators | search queries built from the candidate's skills, roles and location | none; never applies or contacts anyone | web search/fetch, optional browser |
| appstore-assets | your git remote; developer.apple.com (screenshot and creative-asset spec pages); Google Fonts and raw.githubusercontent.com/google/fonts (caption font and its license); the app's landing page when there is no code; GitHub when `asm deps acquire` fetches `emil-design-eng` | the spec and font URLs, the font family name, the landing-page URL | none; never commits, pushes or uploads to App Store Connect | git, python3 (Pillow), headless Chrome/Chromium, asm, web fetch/browse |
| appstore-review-checker | your git remote | none | none; never reads App Store Connect keys | git |
| aso-marketing | your git remote | none | none; store uploads are left to you | git |
| brand-name-checker | web search/fetch: npm, PyPI, Homebrew, Debian/Ubuntu packages, social sites, domain registrars, WIPO, EUIPO, INPI | the candidate name | none | web search/fetch, git |
| codebase-modernizer | package registries and advisory databases (npm, PyPI, Go proxy and vuln DB, crates.io and RustSec, RubyGems, Maven, Packagist, NuGet, pub.dev, Hex) unless `--offline`; Context7 (optional); your git remote | dependency names, versions and lockfile trees | none; read-only, never installs or upgrades | `dep_scan.sh` with npm, pip-audit, govulncheck, cargo audit and similar; local `tsc` |
| design-optimizer | the target URL and its robots.txt, sitemap.xml and llms.txt; headless browser via `browse`; isitagentready.com only through `website-agent-readiness` after you approve | HTTP requests for the public pages; the target URL | git fetch/pull in apply mode; no push | curl, python3, asm, git, delegated review skills |
| dev-machine-setup | OS package repositories, npm registry, raw.githubusercontent.com, deb.nodesource.com, astral.sh, starship.rs, github.com plugin clones, claude.ai/install.sh | package and download requests only | each item needs your yes: `sudo` installs, `curl \| sh` and `irm \| iex` installers, `npm install -g`, `chsh`, shell rc edits (with backup), global git config, Windows app removal | brew, apt, dnf, pacman, winget, npm, curl, git, PowerShell |
| dont-make-me-think | the target URL via `browse` (live-URL path only); your git remote (redesign mode) | page loads; screenshots are processed locally | UI edits after you confirm the diff; no commit | browse, asm, python3 (Pillow, OpenCV), git |
| github-pages-publish | your git remote; GitHub via `gh` (the target repo, its Pages settings and Actions runs, release lookups for the `actions/*` deploy actions); the published site (live check) | the site content you publish, which becomes a public website | commits and pushes the site to the target repo's default branch and sets Pages to deploy from Actions without a further prompt; asks before creating a repo or making a private repo public | git, gh, python3, asm (optional, for frontend-design) |
| hc-agent | the local Herdr desktop app via `hc` and `herdr-app`; workers contact their own model providers | task prompts typed to worker agents | starts workers with the launcher's permission-bypass flags by default (see above); types into worker terminals; closes worker panes only after confirmation | hc, herdr-app, python3, claude, codex, pi |
| herdr-agent | local Herdr socket; workers contact their own model providers | task prompts typed to worker agents | starts workers with the launcher's permission-bypass flags by default (see above); types into panes | herdr, python3, claude, codex, pi |
| idea-validator | web search; your ideas repo remote | idea text and search queries; reports committed to your remote | commits and pushes `idea.md` and `validate.md` without a further prompt | git, web search |
| install-script-generator | your git remote; a HEAD request to raw.githubusercontent.com when `install.sh` already exists | repository owner, name and branch | none; no commit or push | git, python3 helpers (dry run), bash, shellcheck, curl |
| issue-work-loop | GitHub API via `gh`, your git remote, worker agents' model providers | issue and PR data, repository source and diffs to workers; commits to the PR branch | workers commit and push (never force) to the PR branch; ISSUE mode opens a PR; never merges | gh, git, herdr (TUI) or hc and herdr-app (desktop app), asm, idd skills |
| landing-page-generator | your git remote; the built pages may load web fonts or a pinned Mermaid script in your browser | none | none unless you ask for a commit | git, python3, asm (optional, for frontend-design) |
| logo-designer | your git remote; the generated showcase page loads Google Fonts in your browser | none | none | git, `open` |
| ollama-optimizer | your local Ollama server; the Ollama model registry on `ollama pull` (after approval) | a benchmark prompt to local Ollama; model names to the registry | each change needs approval: shell rc edits, `launchctl setenv`, `sudo` systemd drop-ins, service restarts | ollama, nvidia-smi, rocm-smi, launchctl, systemctl, sudo |
| prd-generator | your ideas repo remote | `prd.md` and `README.md` commits | commit and push after asking; never force | git |
| product-launch | the landing page you give; the public submit, pricing and rules pages of shortlisted launch sites (read-only); GitHub API via `gh` only for an opted-in metadata edit; your git remote | the landing-page URL; repo description, homepage and topics only if you confirm the `gh repo edit` command | `gh repo edit` after two confirmations; never signs up, submits, votes, pays or posts on any launch site; never commits | curl, python3, gh (optional), asm (optional), git |
| product-planner | your git remote; member skills reach their own destinations | none itself | none itself; `idea-validator` pushes without asking, the other members ask first | git, asm, planning skills |
| rex-agent | local Rex server socket; workers contact their own model providers | task prompts typed to worker agents | starts workers with the launcher's permission-bypass flags by default (see above); types into worker blocks; closes blocks only after confirmation | rex, python3, claude, codex, pi, gemini |
| search-optimizer | the target site's page, robots.txt, sitemap.xml and llms.txt; isitagentready.com only through `website-agent-readiness` after you approve; your git remote | the target URL | git fetch/pull; no push | curl, python3, git, asm, delegated audit skills |
| security-setup | package registries for approved tool installs; Trivy vulnerability DB download; your git remote. Installed hooks then run offline | package names only | writes hook config, scripts and `SECURITY.md` after a dry run and approval; no push | git, pre-commit, gitleaks, trivy, semgrep, bandit, detect-secrets |
| seo-ai-optimizer | web search for current guidance; your deployed site when needed; isitagentready.com only through `website-agent-readiness` after you approve; your git remote | generic search queries, the URL you supply | edits SEO files after plan approval and per-diff confirmation; no push | python3, git, asm |
| tasks-generator | your git remote | `tasks.md` commits | commit, then push only after you approve | git, python3 |
| tmux-agent-comms | none itself; agent CLIs it launches use their own network | task text typed into local sessions | asks before ending or killing sessions | tmux, python3, bash |
| user-test | your git remote; the app under test (localhost, or the URL you give); npm registry when it installs Playwright into its run dir; Ubuntu or npm mirrors only if you approve browser system packages | test inputs typed into the app, named `ut-<run>` | none by default: fixes stay uncommitted; asks before any payment, email or post to real people; commits only on request; never pushes | your app's start, build and test commands, python3, git, curl, Playwright or browser tools, tmux, `docker compose up/stop` for services it starts |
| ux-ax-review | the target site's pages, robots.txt, sitemap, llms.txt and public machine-readable routes; your git remote | the target URL and paths it reads | none; no commit, form submission or publishing | browser/retrieval tools, git, python3 |
| viral-product-evaluator | the landing-page URL via `browse`, after you confirm; competitor pricing research; your git remote | the landing-page URL | writes `viral-evaluation.md` only | browse, asm, git, python3 |
| website-agent-readiness | isitagentready.com (`POST /api/scan`, after approval gate G1; localhost is refused); GitHub API via `gh` | the target URL, which isitagentready.com then fetches; plan tasks become GitHub issues | creates a GitHub epic and issues through `plan-to-issues` after gate G4 | curl, python3, git, gh, asm |

## Support

Report problems at
[github.com/luongnv89/skills/issues](https://github.com/luongnv89/skills/issues).
The full catalog, other install methods and contribution guide are in the
[repository README](https://github.com/luongnv89/skills#readme).
