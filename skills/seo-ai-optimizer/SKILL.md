---
name: seo-ai-optimizer
description: "Audit and optimize websites for technical SEO, content SEO, and AI bot accessibility. Fixes meta tags, sitemaps, robots.txt, structured data, llms.txt, and GPTBot/ClaudeBot directives. Not for App Store ASO, paid search, or blog writing."
license: MIT
effort: high
metadata:
  version: 1.3.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# SEO & AI Bot Optimizer

Audit and optimize website codebases for search engines and AI systems.

## Dependency Preflight (mandatory)

Step 8 invokes `website-agent-readiness`. Verify it is installed **before** the first
step that changes anything:

```bash
test -d "$HOME/.claude/skills/website-agent-readiness" ||
  asm list -p claude --json | grep -q '"website-agent-readiness"' || {
  echo "Missing required skill: website-agent-readiness" >&2
  echo "Install it:      asm install github:luongnv89/skills:skills/website-agent-readiness -p claude -s global --yes" >&2
  echo "No asm yet:      npm install -g agent-skill-manager" >&2
  echo "Verify:          asm list -p claude --json | grep 'website-agent-readiness'" >&2
}
```

The install path is tested **before** `asm list`: this skill ships in the same repo as its
dependency, so a repo-installed `website-agent-readiness` is present without the curated
registry knowing the bare name — an `asm list` check alone would nag on every run, and a
bare-name `asm install` would not resolve.

On a miss, print those commands and **skip Step 8** — Steps 1-7 audit the codebase and
still run. Never invoke a half-installed skill. `website-agent-readiness` enforces its own
prerequisites (`curl`, `python3`, and for issue filing `git`, `gh`, `plan-to-issues`); this
skill does not re-check them.

## Repo Sync Before Edits (mandatory)

Before modifying any project files, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Prerequisites

Before starting the SEO audit, ensure the following:
- **Environment:** The project must be managed by a git repository.
- **Tools:** Python 3.x must be installed and available in the path.
- **Audit Script:** `scripts/audit_seo.py` (shipped with this skill) is invoked against the audited project: `python scripts/audit_seo.py <project-root>`.
- **Access:** You must have write access to the project files and permission to create new files (robots.txt, llms.txt, etc.).

## Quick Reference

Consult these reference files as needed during the workflow:
- `references/workflow-detail.md` — Detailed checklists, templates, and implementation steps
- `references/technical-seo.md` — Full SEO checklist and best practices
- `references/framework-configs.md` — Framework-specific configuration
- `references/ai-bot-guide.md` — AI crawler directives, llms.txt format, JSON-LD templates

## Environment Check

This skill has two modes of operation:

**With Subagent Architecture (Recommended):**
If the Agent tool is available in your environment, the audit runs via a 4-phase subagent workflow for maximum accuracy and depth. See `references/subagent-architecture.md`.

**Without Subagent Tool (Fallback):**
If Agent is not available, the skill runs a complete audit in a single conversation. The end result (SEO audit report) is the same.

## Important

- Audit first, present findings, then propose a plan — never modify files without user approval
- **Safety First:** Always show a diff and get explicit confirmation before writing any file change
- Fetch latest best practices via web search during each audit to supplement embedded knowledge

## Workflow

1. **Detect** -- Identify project framework and scan for relevant files
2. **Audit** -- Run automated scan + manual review across 4 categories
3. **Research** -- Web search for latest SEO/AI bot best practices
4. **Report** -- Present findings grouped by severity
5. **Plan** -- Propose prioritized improvements for user approval
6. **Implement** -- Apply approved changes following the Safety Protocol
7. **Validate** -- Re-check modified files
8. **Agent-readiness handoff** -- Scan the deployed site via `/website-agent-readiness`

---

## Step 1: Detect Project Type

Run the audit script to detect framework and scan files:

```bash
python scripts/audit_seo.py <project-root>
```

If the script reports "No HTML/template files found," inform the user: this skill is designed for web frontends with HTML output.

## Step 2: Audit

The audit script checks **per-file issues** and **project-level issues**. After running the script, perform a manual review for items requiring human judgment (content quality, links, E-E-A-T).

For the full manual review checklist, see `references/workflow-detail.md`.

## Step 3: Research Latest Best Practices

Use web search to check for updates (SEO best practices, AI bot directives, llms.txt spec, algorithm updates). Compare findings with embedded knowledge in `references/`.

## Step 4: Report

Present the audit report grouping findings by severity (Critical, Warning, Info) and project-level findings (robots.txt, sitemap, llms.txt, JSON-LD).

## Step 5: Plan

Present a prioritized improvement plan using the template in `references/workflow-detail.md`.

Ask the user: "Which improvements should I implement? You can approve all, select specific items, or modify the plan."

Do NOT proceed without explicit approval.

## Step 6: Implement

Apply approved changes following the **Safety First** protocol:

1. **Show Diff:** For every file change, generate and show a clear diff or summary.
2. **Confirm:** Request explicit user confirmation before writing each file (or batch).

For detailed implementation instructions per category (Technical SEO, robots.txt, llms.txt, JSON-LD, sitemaps), see `references/workflow-detail.md`.

## Step 7: Validate

After implementing changes, re-run the audit script on modified files to verify critical issues are resolved and check for regressions.

## Step 8: Agent-Readiness Handoff

Steps 1-7 fix the **codebase**. This step scores the **deployed site** as an AI agent sees
it, catching what a static audit cannot: rendered output, live headers, and runtime
robots/llms.txt delivery.

Run it when both hold, else skip and say why:

- The site is deployed at a reachable public URL, and the Step 6 changes are live there
- The user supplies that URL and approves the handoff

```
/website-agent-readiness <live-url>
```

That skill owns its own gated pipeline (scan → triage → `agent-ready-plan.md` → issue
filing) — do not re-run its phases here, and do not re-apply its recommended llms.txt or
metadata fixes inline. Anything it returns that belongs in the codebase comes back through
Steps 5-7 as a normal approved plan item.

**Verify:** the step passes when `agent-ready-plan.md` exists in the working directory and
its reported 0-5 agent-readiness score is recorded in the final summary; a skip passes when
the summary names which of the two conditions above was unmet.

## Step Completion Reports

After each step, emit a `◆` status block. For templates and per-step check lists, see `references/step-reports.md`.

## Acceptance Criteria

See the itemized checklist in `references/workflow-detail.md` (Acceptance Criteria) — a run only passes when every item there is checked.

## Expected Output

After a full run, the agent should produce:
1. **Audit Report:** A structured markdown report grouping findings by severity.
2. **Implementation:** Modified or new files (robots.txt, llms.txt, sitemap.xml, JSON-LD) with confirmed changes.
3. **Validation Report:** A post-fix verification showing critical issues reduced to 0.
4. **Agent-Readiness Handoff:** The live-site score and `agent-ready-plan.md` from Step 8, or a one-line reason it was skipped.

For a concrete example of the audit report output, see `references/workflow-detail.md`.

