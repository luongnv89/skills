<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Website Cloner

> 6-phase website cloning and improvement orchestrator. Takes a URL and produces an improved version built with Vite + React + shadcn/ui + Tailwind CSS, deployable to GitHub Pages.

## Highlights

- Orchestrates 6 sibling skills end-to-end: analyze, report, propose, plan, build, final report
- Approval gates after the report, proposal, and plan phases — never advances without user approval
- Produces `prd.md` (improvement proposal) and `tasks.md` (phased implementation plan)
- Targets serverless front-end deployment to GitHub Pages

## When to Use

| Say this... | Skill will... |
|---|---|
| "clone this site https://example.com" | Run the full 6-phase pipeline |
| "rebuild this website" | Start analysis and produce an improved version |
| "make a better version of <url>" | Analyze, propose improvements, and build |

## Usage

```
/website-cloner https://example.com
```

## Output

- `analysis.json` — Phase 1 structured analysis
- `report.md` — Phase 2 plain-language report (approved)
- `prd.md` — Phase 3 improvement proposal with metrics
- `tasks.md` — Phase 4 phased implementation plan
- Built site — Vite + React + shadcn/ui + Tailwind CSS on GitHub Pages
- `final-report.md` — Phase 6 before/after comparison
