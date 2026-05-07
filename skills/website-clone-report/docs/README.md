<!--
  DO NOT READ THIS FILE — This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Website Clone Report

> Converts website analysis JSON into a comprehensive plain-language report for non-technical users. Approval gate: saves only after explicit user validation.

## Highlights

- Translates technical metrics (LCP, CLS, SEO scores) into plain language
- Non-technical audience: jargon-free with relatable comparisons
- Approval gate: never persists report without explicit user approval
- Edit loop: incorporates user changes and re-prompts until approved

## When to Use

| Say this... | Skill will... |
|---|---|
| "create a report from the analysis" | Translate JSON analysis into plain-language report |
| "summarize the website scan for a non-technical audience" | Produce accessible report with relatable comparisons |

## Usage

```
/website-clone-report <path-to-analysis.json>
```

## Output

Plain-language `report.md` — written only after explicit user approval.
