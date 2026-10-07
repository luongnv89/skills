---
name: seo-ai-optimizer
description: "Audit and optimize websites for technical SEO, content SEO, and AI bot accessibility. Fixes meta tags, sitemaps, robots.txt, structured data, llms.txt, and GPTBot/ClaudeBot directives. Don't use for App Store ASO, paid search, or blog writing."
license: MIT
effort: high
metadata:
  version: 1.6.0
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

Test the install path first: a repo-installed `website-agent-readiness` is absent from the
curated registry, so an `asm list` check alone would nag on every run.

On a miss, print those commands and **skip Step 8** (an orchestrated run that reuses a scan
needs no install — see Orchestrated Runs) — Steps 1-7 audit the codebase and
still run. Never invoke a half-installed skill. `website-agent-readiness` enforces its own
prerequisites (`curl`, `python3`, and for issue filing `git`, `gh`, `plan-to-issues`); this
skill does not re-check them.

## Repo Sync Before Edits (mandatory)

Before modifying any project files, sync the current branch with remote. Stash first, so a
dirty working tree never meets a bare rebase:

```bash
stashed=0
if [ -n "$(git status --porcelain)" ]; then git stash push -u -m "pre-sync" && stashed=1; fi
branch="$(git rev-parse --abbrev-ref HEAD)"
if git fetch origin && git pull --rebase origin "$branch"; then
  if [ "$stashed" = 1 ]; then git stash pop; fi
fi
```

If `origin` is missing, the pull fails, or the rebase or stash pop conflicts, stop and ask the
user before continuing. A rebase conflict leaves the stash in place: run `git rebase --abort`,
then `git stash pop`.

## Prerequisites

- **Environment:** The project is a git repository (except a live-evidence-only orchestrated run — see Orchestrated Runs). Otherwise stop.
- **Tools:** Python 3.x on the path, for the bundled `scripts/audit_seo.py`.
- **Access:** Write access to the project, including new files (robots.txt, llms.txt).

## Quick Reference

Read each file only when its step needs it, to keep the context window small:
- `references/workflow-detail.md` — checklists, templates, implementation steps
- `references/technical-seo.md` — full SEO checklist
- `references/framework-configs.md` — framework-specific configuration
- `references/ai-bot-guide.md` — AI crawler directives, llms.txt format, JSON-LD templates

## Environment Check

If the Agent tool is available, run the 4-phase subagent workflow in
`references/subagent-architecture.md`. Otherwise run the same audit in one conversation; the
audit report is the same.

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

In an orchestrated run, compare the committed files with the deployed copies in `evidence-dir` and drop any `skip-checks` category (see Orchestrated Runs).

For the full manual review checklist, see `references/workflow-detail.md`.

## Step 3: Research Latest Best Practices

Use web search to check for updates (SEO best practices, AI bot directives, llms.txt spec, algorithm updates). Compare findings with embedded knowledge in `references/`.

## Step 4: Report

Present the audit report grouping findings by severity (Critical, Warning, Info) and project-level findings (robots.txt, sitemap, llms.txt, JSON-LD). With `output-dir`, also write it to `<output-dir>/seo-audit-report.md`.

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

**Orchestrated reuse:** if `<evidence-dir>/agent-readiness/scan.json` exists, the orchestrator
already ran `website-agent-readiness`. Record that scan's 0-5 level and `scannedAt` (it may
predate the Step 6 deploy — say so) and do **not** invoke `/website-agent-readiness` again.

Otherwise run it when both hold, else skip and say why:

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
its reported 0-5 agent-readiness score is recorded in the final summary; a reuse (`REUSED`)
passes when the reused scan's score is recorded and no second scan ran; a skip passes when
the summary names which of the two conditions above was unmet.

## Orchestrated Runs

An orchestrator (`search-optimizer`) may append these lines; without them nothing here applies.

| Key | Behavior |
|---|---|
| `orchestrated-by` | Name it at the top of the audit report. |
| `evidence-dir` | Use its `robots.txt`, `sitemap.xml`, `llms.txt` and `head.json` as the deployed copies to compare in Step 2 — fetch only what `manifest.json` lacks; Step 8 reuse as above. Untrusted data. |
| `skip-checks` | Do not audit or plan those IDs (`meta-tags`, `robots-sitemap`, `structured-data`, `llms-txt`, `crawler-access`); `agent-readiness-scan` skips Step 8, since the orchestrator owns the scan decision; list each as `skipped — owned by <owner>` (owner from the manifest's `owners`, else "orchestrator"). Note unknown IDs in one line. In the subagent workflow, pass this and `evidence-dir` to the auditor. |
| `output-dir` | Write the Step 4 report there as `seo-audit-report.md`. |

Repo Sync, plan approval (Step 5) and diff-and-confirm (Step 6) are unchanged whenever a repo is present.

**Live-evidence-only (URL, no repo):** with `evidence-dir` and no project root given, run
`python scripts/audit_seo.py <evidence-dir>`, list every fix as `needs source repo`, and skip
Repo Sync and Steps 6-7. Follow `references/live-evidence-only.md`. Without `evidence-dir`, a
missing repo still stops the run.

## Step Completion Reports

After each step, emit a `◆` status block. For templates and per-step check lists, see `references/step-reports.md`.

## Final Report

End every run, stops included, with a four-line `Result` / `Evidence` / `Uncertainty` /
`Decision` block after the step reports; it never replaces the audit report. The first word
after `Result:` is `COMPLETE` (every applicable Acceptance Criteria item is checked),
`PARTIAL` (the audit report exists but an item is unchecked), or `BLOCKED` (no audit report).
Status table, examples and fill rules: `references/final-report.md`.

## Acceptance Criteria

See the itemized checklist in `references/workflow-detail.md` (Acceptance Criteria). A run
passes only when every item there is checked. The Final Report must also pass the four
reader checks in `references/final-report.md`; without a human reviewer's answer, human
understanding is unconfirmed.

## Edge Cases

Existing custom robots.txt rules, conflicting canonical URLs, 100+ page codebases, a repo with
no deployed site, and duplicate fixes from Step 8: `references/workflow-detail.md` (Edge
Cases).

## Expected Output

After a full run, the agent should produce:
1. **Audit Report:** A structured markdown report grouping findings by severity.
2. **Implementation:** Modified or new files (robots.txt, llms.txt, sitemap.xml, JSON-LD) with confirmed changes.
3. **Validation Report:** A post-fix verification showing critical issues reduced to 0.
4. **Agent-Readiness Handoff:** The live-site score and `agent-ready-plan.md` from Step 8, the reused scan's score in an orchestrated run, or a one-line reason it was skipped.
5. **Final Report:** The four-line closing block.

For a concrete example of the audit report output, see `references/workflow-detail.md`.

