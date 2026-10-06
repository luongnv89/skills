<p align="center">
  <img src="assets/logo/logo-icon.svg" alt="Agent Skills" width="120">
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
  <a href="https://github.com/luongnv89/skills/releases"><img src="https://img.shields.io/github/v/release/luongnv89/skills?label=version" alt="Latest Release"></a>
  <a href="https://github.com/luongnv89/skills"><img src="https://img.shields.io/github/stars/luongnv89/skills?style=social" alt="GitHub Stars"></a>
</p>

# Install expert workflows for AI coding agents

One command drops a tested, versioned skill into your agent. No more ad-hoc prompts. The same rigorous steps run every time.

Skills are independent files. Works with Claude Code, Cursor, Windsurf, GitHub Copilot, OpenAI Codex, OpenCode, Google Antigravity (`install.sh:23`).

[**Browse catalog**](#skill-catalog) | [**Install**](#install)

---

## Install

> Validate this runbook: `./scripts/validate-install.sh --check`

Pick one:

```bash
npx skills add https://github.com/luongnv89/skills --skill code-review
```

Pick several:

```bash
npx skills add https://github.com/luongnv89/skills --skill code-review --skill auto-push --skill test-coverage
```

All of them:

```bash
npx skills add https://github.com/luongnv89/skills
```

### agent-skill-manager

Use [agent-skill-manager](https://github.com/luongnv89/agent-skill-manager) (`asm`) for a single TUI/CLI across agents:

```bash
npm install -g agent-skill-manager
asm install github:luongnv89/skills
```

```bash
asm search   # find by name or description
asm list     # show installed skills
```

<details>
<summary>Other install methods</summary>

**Remote (no clone)**

```bash
curl -sSL https://raw.githubusercontent.com/luongnv89/skills/main/remote-install.sh | bash
```

Non-interactive:

```bash
curl -sSL https://raw.githubusercontent.com/luongnv89/skills/main/remote-install.sh | bash -s -- \
  --skills "code-review,auto-push" --tools "Claude Code" --scope global
```

**Clone + local**

```bash
git clone https://github.com/luongnv89/skills.git
cd skills && bash install.sh
```

</details>

---

## How It Works

```mermaid
graph TD
    A[User request or trigger phrase] --> B[Agent matches skill name]
    B --> C[Loads SKILL.md + references/]
    C --> D[Follows exact steps + templates]
    D --> E[Quality gates + artifacts]
    E --> F[Report / plan / files / PR links]
```

A skill is a self-contained playbook: frontmatter metadata, instructions, optional scripts, and reference docs. The installer copies it to the right path for your agent.

---

## Key Features

| Feature | What you get |
|---|---|
| Standalone | Any mix installs cleanly; zero shared runtime |
| Versioned | Semver + per-skill changelogs |
| Structured | Steps, templates, checklists, self-validation |
| Tool-agnostic | Same skill works in Claude Code, Cursor, Windsurf, Codex, Copilot |
| Scannable | Tables, diagrams, short outputs |
| Suite support | Multi-phase products (e.g. diagram-generator) with independent phases |

---

## Quick Start

```bash
npx skills add https://github.com/luongnv89/skills --skill landing-page-generator
```

```bash
npx skills add https://github.com/luongnv89/skills --skill code-review --skill auto-push
```

After install, call skills by name in your agent prompts (see catalog for each skill's trigger guidance).

See [skills/](skills/) for full SKILL.md files.

---

## Skill Catalog

Every skill is standalone. Install one or many.

Use:

```bash
npx skills add https://github.com/luongnv89/skills --skill <name>
```

### Find by Task

One skill to invoke per task. The task skills call the related skills for you. In the two
web task skills, evidence is captured once, the live scan runs at most once, overlapping checks
are skipped where the member supports skip-checks, and remaining overlaps are merged into one
row per defect.

| Task | Invoke | It runs |
|---|---|---|
| Optimize a website/app design | [**design-optimizer**](skills/design-optimizer/) | dont-make-me-think · ux-ax-review · viral-product-evaluator · website-agent-readiness, then frontend-design only if you opt in to apply fixes |
| Optimize for SEO, AI-bot or app-store search | [**search-optimizer**](skills/search-optimizer/) | Web: seo-ai-optimizer · website-agent-readiness · viral-product-evaluator. App store: aso-marketing · viral-product-evaluator |
| Take an idea to a build plan | [**product-planner**](skills/product-planner/) | idea-validator → prd-generator → (brand-name-checker) → tad-generator → tasks-generator, resuming from the furthest existing artifact |
| Review or improve code | [**code-review**](skills/code-review/) | One skill, four modes: review, perf, clean, cleanup |
| Draw a diagram | [**diagram-generator**](skills/diagram-generator/) | Routes to drawio-generator or excalidraw-generator |

These other task areas don't have a task skill. Each skill in them stands alone, so invoke them in this order:

| Task | Skills, in order |
|---|---|
| Prepare an app store submission | aso-marketing → appstore-review-checker |
| Harden and ship a repo | security-setup → devops-pipeline → release-manager (auto-push and cleanup-project for day-to-day work) |
| Open-source a project | oss-ready → doc-manager → landing-page-generator |
| Brand and launch | brand-name-checker → logo-designer → landing-page-generator |
| Run an agent fleet | herdr-agent *or* tmux-agent-comms (alternative backends) · issue-work-loop (Herdr) · opencode-runner |

### Find by Category

| Category | What it covers |
|---|---|
| [Code Quality](#code-quality) | Reviews, cleanup, testing, optimization, usability |
| [Shipping](#shipping) | Auto push, repo cleanup, pipelines, releases, security hardening |
| [Product Planning](#product-planning) | Validation, PRDs, architecture, tasks, naming |
| [Career Research](#career-research) | Tailored job discovery with employer/product due diligence |
| [Frontend & Design](#frontend--design) | UIs, logos, diagrams, site clones |
| [Documentation](#documentation) | Docs gen, READMEs, SEO, OSS prep, agent config |
| [App Store](#app-store) | ASO, review compliance |
| [Tooling](#tooling) | CLIs, installers, local models, agent comms |

### Code Quality

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**code-review**](skills/code-review/) | 2.2.0 | high | Review or improve code — 4 modes: bugs/security, performance, clean-code audit, slop cleanup |
| [**codebase-modernizer**](skills/codebase-modernizer/) | 1.3.3 | max | Whole-repo audit + phased, testable plan to modernize a stale or messy codebase |
| [**test-coverage**](skills/test-coverage/) | 1.4.0 | low | Target untested branches and edge cases |
| [**dont-make-me-think**](skills/dont-make-me-think/) | 1.5.0 | medium | Usability review using Krug's principles |
| [**ux-ax-review**](skills/ux-ax-review/) | 1.1.0 | high | Evidence-backed human UX + AI/search AX audit and approval-gated improvement plan |

**`code-review` has four modes** — pick by intent or pass `mode:<name>`:

| I want to... | Mode | It... |
|---|---|---|
| Find bugs, security, or quality issues in a diff | `review` (default) | reads + reports prioritized findings |
| Make code faster / fix perf bottlenecks | `perf` | reads + reports performance fixes |
| Audit readability/standards vs the Clean Code cheat sheet | `clean` | writes an audit report (`CLEAN_CODE_AUDIT.md`) |
| Actually apply cleanup / refactor out AI slop & cruft | `cleanup` | **writes code** (8-subagent refactor) |

**`code-review` or `codebase-modernizer`?** Scope decides. `code-review` inspects a diff, a PR, or a
file set and reports findings. `codebase-modernizer` audits the *whole repo* across all ten
dimensions — including dependency and runtime currency, which nothing else here covers — and converts
the findings into a phased sprint plan with milestones. It is read-only: dependency upgrades become
planned tasks with migration steps, never a bulk `npm update`. Reach for it when returning to a
neglected project or untangling one that has drifted.

Adjacent skills: **test-coverage** (generate tests for untested branches) · **dont-make-me-think** (usability/UX review).

### Shipping

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**auto-push**](skills/auto-push/) | 1.1.0 | low | Commit message + stage + push with secret and size checks |
| [**cleanup-project**](skills/cleanup-project/) | 1.0.1 | high | Review uncommitted changes, update ignore files, delete merged branches locally and on origin, end on clean main |
| [**devops-pipeline**](skills/devops-pipeline/) | 2.2.2 | medium | Pre-commit + GitHub Actions quality gates |
| [**security-setup**](skills/security-setup/) | 1.4.2 | high | Local pre-commit secret scans, dep checks, static analysis, gated CI |
| [**release-manager**](skills/release-manager/) | 2.6.4 | max | Bump, changelog, tag, GitHub release, publish |

### Product Planning

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**product-planner**](skills/product-planner/) | 1.0.0 | high | One run from idea to sprint tasks: idea-validator → prd-generator → tad-generator → tasks-generator, resuming from existing files |
| [**idea-validator**](skills/idea-validator/) | 1.5.1 | max | Market, feasibility, competitor checks for ideas |
| [**viral-product-evaluator**](skills/viral-product-evaluator/) | 1.6.0 | high | Score codebase + landing page vs 32 viral principles |
| [**brand-name-checker**](skills/brand-name-checker/) | 1.4.2 | max | Trademark, domain, social, registry conflicts |
| [**prd-generator**](skills/prd-generator/) | 1.4.3 | max | Structured PRD from idea or validate notes |
| [**tad-generator**](skills/tad-generator/) | 1.5.1 | max | Technical architecture document from PRD |
| [**tasks-generator**](skills/tasks-generator/) | 1.4.1 | max | Sprint tasks and plan from PRD |

> **`plan-to-issues` moved to [luongnv89/idd](https://github.com/luongnv89/idd)** (idd#502), next to the `issue-creator` it depends on: `asm install https://github.com/luongnv89/idd --skill plan-to-issues`, or the idd Claude Code plugin.

### Career Research

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**ai-job-scout**](skills/ai-job-scout/) | 1.1.0 | high | Rank open AI roles for a candidate; verify location and application links; assess each company's product, project, and technical interest with cited evidence; filterable HTML report for larger searches |

### Frontend & Design

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**frontend-design**](skills/frontend-design/) | 1.3.0 | high | Production UIs with usability-first approach |
| [**logo-designer**](skills/logo-designer/) | 1.3.0 | medium | 7 SVG logo variants from project context |
| [**diagram-generator**](skills/diagram-generator/) | 1.3.0 | high | One entry point for diagrams — routes to draw.io XML or Excalidraw JSON |
| [**design-optimizer**](skills/design-optimizer/) | 1.0.0 | high | One run to optimize a website/app design: usability, UX/AX, virality, agent readiness, opt-in fixes |

**Diagram generator engines** (install the umbrella or a single engine):

| Engine | Version | What it does |
|---|---|---|
| drawio-generator | 1.3.0 | draw.io XML — precise, editable, C4, swimlanes |
| excalidraw-generator | 1.4.0 | Excalidraw JSON — hand-drawn, sketch, wireframes |

### Documentation

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**doc-manager**](skills/doc-manager/) | 2.0.4 | medium | Generate/update docs to match code, cited to path:line, never invented |
| [**landing-page-generator**](skills/landing-page-generator/) | 1.4.0 | high | Landing pages: marketing copy from a brief, or a README-to-landing rewrite |
| [**search-optimizer**](skills/search-optimizer/) | 1.0.1 | high | One run to optimize SEO, AI-bot and app-store search: web or store branch, one merged report |
| [**seo-ai-optimizer**](skills/seo-ai-optimizer/) | 1.5.0 | high | Technical SEO + AI-bot directives |
| [**website-agent-readiness**](skills/website-agent-readiness/) | 1.3.0 | high | Scan a live site for agent readiness, plan the gaps, file them as issues |
| [**oss-ready**](skills/oss-ready/) | 1.3.1 | low | Add OSS files and templates |
| [**agent-config**](skills/agent-config/) | 2.0.2 | medium | AGENTS.md by default (CLAUDE.md on request), shadow-checked and evidence-pruned |

### App Store

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**aso-marketing**](skills/aso-marketing/) | 1.3.1 | max | App Store + Google Play keyword and metadata optimization |
| [**appstore-review-checker**](skills/appstore-review-checker/) | 1.3.0 | high | Pre-submission audit vs Apple guidelines |

### Tooling

| Skill | Version | Effort | What it does |
|---|---|---|---|
| [**cli-builder**](skills/cli-builder/) | 1.1.0 | high | 5-step CLI tool builder with approval gates |
| [**ollama-optimizer**](skills/ollama-optimizer/) | 1.2.1 | medium | Hardware-aware Ollama tuning |
| [**install-script-generator**](skills/install-script-generator/) | 2.2.4 | high | Cross-platform install.sh with env detection |
| [**opencode-runner**](skills/opencode-runner/) | 1.5.1 | medium | Delegate work to opencode free cloud models |
| [**herdr-agent**](skills/herdr-agent/) | 3.1.4 | medium | Manage Herdr agent fleets: tile panes, message/wait/read, steer, `help` |
| [**issue-work-loop**](skills/issue-work-loop/) | 1.5.3 | max | Resolve one GitHub issue via a Herdr implementer→reviewer loop until CLEAN |
| [**tmux-agent-comms**](skills/tmux-agent-comms/) | 2.3.2 | medium | Spawn, message, read CLI agents in tmux |
| [**dev-machine-setup**](skills/dev-machine-setup/) | 0.9.3 | high | Gap-driven dev machine setup/tune-up across macOS, Linux, Windows |

---

## Suite Folders

Most skills are `skills/<name>/`. Multi-phase products live under a suite folder: umbrella at `skills/<umbrella>/` + phases at `skills/<umbrella>/<phase>/`.

Current suite: [diagram-generator](skills/diagram-generator/) (draw.io + Excalidraw engines behind one router). Install the umbrella or any child. Installers discover both levels.

Task orchestrators ([design-optimizer](skills/design-optimizer/), [search-optimizer](skills/search-optimizer/), [product-planner](skills/product-planner/)) stay flat at `skills/<name>/`. Their members are ordinary top-level skills, and a member can belong to more than one task: viral-product-evaluator and website-agent-readiness serve both design and search. Each orchestrator checks for its members in a Dependency Preflight and tells you how to install any that are missing.

Mirror the layout for your own multi-skill products.

---

## Project docs

| Doc | Purpose |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribute skills; structure and versioning |
| [docs/guide-building-agent-skills.md](docs/guide-building-agent-skills.md) | Authoring guide (plan → write → validate → distribute) |
| [docs/brand_kit.md](docs/brand_kit.md) | Logo files, colors, typography |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Doc ambiguity resolutions |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Install/setup validation fixes |
| [docs/archive/](docs/archive/) | Historical work notes (not current product docs) |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |

## FAQ

**Do I need every skill?**  
No. Pick only what you need. All are independent.

**Which agents work?**  
Any that load external skill files. Installer tools (`install.sh:23`): Claude Code, Cursor, Windsurf, GitHub Copilot, OpenAI Codex, OpenCode, Google Antigravity.

**How do I make my own?**  
Follow [CONTRIBUTING.md](CONTRIBUTING.md), [docs/guide-building-agent-skills.md](docs/guide-building-agent-skills.md), or patterns from existing skills.

**Do skills change my runtime code?**  
No. They only guide the agent during development.

---

## Get Started

```bash
npx skills add https://github.com/luongnv89/skills --skill code-review
```

[**All skills**](./skills) · [**Contribute**](CONTRIBUTING.md) · MIT

---

<details>
<summary><b>Supported Tool Paths</b> (`install.sh:218-321`)</summary>

| Tool | Global | Project |
|---|---|---|
| Claude Code | `~/.claude/skills/<skill>/` | `.claude/skills/<skill>/` |
| Cursor | `~/.agents/skills/<skill>/` + `.cursor/rules/<skill>.mdc` | same |
| Windsurf | `~/.agents/skills/<skill>/` + `.windsurf/rules/<skill>.md` | same |
| GitHub Copilot | `~/.agents/skills/<skill>/` + `.github/instructions/<skill>.instructions.md` | same |
| OpenAI Codex | `~/.agents/skills/<skill>/` + `~/.codex/AGENTS.md` | same |
| OpenCode | `~/.agents/skills/<skill>/` | same |
| Google Antigravity | `~/.agents/skills/<skill>/` | same |

</details>

<details>
<summary><b>Project Structure</b></summary>

```
.
├── skills/
│   └── <name>/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── docs/
└── install.sh / remote-install.sh

# Suite umbrellas also hold child skills:
# skills/<umbrella>/<child>/SKILL.md  (install.sh:44-46)
```
</details>

<details>
<summary><b>Creating Skills</b></summary>

See [CONTRIBUTING.md](CONTRIBUTING.md).

Minimal:

```yaml
---
name: my-skill
description: "When to use and what it produces. Don't use for X."
license: MIT
effort: medium
metadata:
  version: 1.0.0
  author: "Your Name"
---
# Agent instructions here. Keep SKILL.md under 500 lines.
```

</details>

<details>
<summary><b>Contributing</b></summary>

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
</details>

<details>
<summary><b>Security</b></summary>

See [SECURITY.md](SECURITY.md).
</details>

<details>
<summary><b>Acknowledgements</b></summary>

- frontend-design draws from Anthropic's patterns.
- Many skills follow the conventions established in the skill-creator lineage.
</details>

---

<p align="center">
  <a href="https://luongnv.com">Website</a> ·
  <a href="https://github.com/luongnv89/claude-howto">Claude How-To</a> ·
  <a href="https://medium.com/@luongnv89">Blog</a>
</p>
