# lstack (directory edition)

lstack 0.8.0 for the Claude plugin directory: 22 first-party Agent
Skills for everyday engineering and product work. Every skill here is plain Markdown: a
`SKILL.md` playbook with optional reference files. The plugin has no scripts, hooks, MCP
servers, native agents or binaries, and installing it installs no packages.

The skills use tools and accounts you already have. Some tell Claude to run your local
`git`, `gh`, npm or other command-line tools, to push or publish when you ask for it
(`auto-push`, `ship`), or to look things up on the web (for example the domain, trademark
and package-registry checks in `brand-name-checker`). Read a skill's `SKILL.md` to see
exactly what it does before you run it.

The full lstack (48 skills, including the ones that ship helper scripts) installs
from this project's own marketplace:

```bash
claude plugin marketplace add luongnv89/skills
claude plugin install lstack@lstack --scope user
```

Source: [github.com/luongnv89/skills](https://github.com/luongnv89/skills) · License: MIT

## Skills

- **agent-config**: Create, update, or audit AGENTS.md (default) or CLAUDE.md agent instructions: set up, prune, add a rule, or merge CLAUDE.md or .cursorrules into one file Claude Code, Codex, and Cursor all read.
- **ai-job-scout**: Find open AI engineering jobs that fit a candidate, verify location and apply links, and assess each employer's product.
- **appstore-review-checker**: Audit iOS/macOS apps against App Store Review Guidelines before submission, with evidence-backed verdicts and fixes.
- **aso-marketing**: Optimize App Store and Google Play listings via a 7-phase, plan-approval-gated ASO workflow: keywords and rank tracking, metadata, screenshot captions, localization.
- **auto-push**: Generate a commit message, stage all changes, and push to remote after scanning for secrets, large files, and protected-branch risks.
- **brand-name-checker**: Check product and brand names for conflicts across trademarks, domains, social handles, and package registries.
- **cleanup-project**: Prepare a git repo before new work: review uncommitted changes, fix .gitignore, delete merged branches, end on clean main, or inspect one branch before deciding.
- **cli-builder**: Build production-quality CLIs with language detection and a five-step approval-gated workflow.
- **devops-pipeline**: Configure pre-commit hooks and lean, fast GitHub Actions for shift-left QA.
- **diagram-generator**: Generate a diagram and route to the right engine — draw.io XML (precise, editable, C4, swimlanes) or Excalidraw JSON (hand-drawn, sketch, wireframes).
- **doc-manager**: Generate or update docs to match the code, citing each claim to path:line and asking on ambiguity; runbook docs also get a check-only validation script.
- **drawio-generator**: Generate professional diagrams as valid draw.io XML — flowcharts, architecture, C4 models, ER diagrams, sequence diagrams, mind maps, and swimlanes.
- **excalidraw-generator**: Generate diagrams as valid Excalidraw JSON — flowcharts, architecture, ER diagrams, mind maps, sequence diagrams, wireframes, C4 models, and more.
- **frontend-design**: Build production-grade frontend interfaces with distinctive aesthetics and working code.
- **idea-validator**: Validate app/startup ideas with market, feasibility, commercial, and open-source competitor analysis.
- **landing-page-generator**: Write landing pages (PAS, AIDA, StoryBrand) from a brief or README, as HTML with privacy, terms, changelog, setup pages.
- **logo-designer**: Generate professional SVG logos from project context: 7 brand variants plus a showcase HTML page.
- **opencode-runner**: Run coding tasks via opencode using free cloud models.
- **prd-generator**: Generate Product Requirements Documents from `idea.md` and `validate.md` files.
- **ship**: Run a release end to end, autonomous by default: version bump everywhere, changelog, docs, landing page, tag, push, GitHub release, PyPI/npm.
- **tad-generator**: Generate a Technical Architecture Document (TAD) from a PRD.
- **test-coverage**: Generate unit tests for untested branches and edge cases.

Left out of this edition (they ship files the directory accepts only from verified
organizations, such as scripts, or depend on skills outside this edition): agent-profile, appstore-assets, code-review, codebase-modernizer, design-optimizer, dev-machine-setup, dont-make-me-think, github-pages-publish, hc-agent, herdr-agent, install-script-generator, issue-work-loop, ollama-optimizer, oss-ready, product-launch, product-planner, rex-agent, search-optimizer, security-setup, seo-ai-optimizer, tasks-generator, tmux-agent-comms, user-test, ux-ax-review, viral-product-evaluator, website-agent-readiness.
