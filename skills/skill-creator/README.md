# Skill Creator

> Create, evaluate, benchmark, and iteratively improve skills.

## What’s New (synced with upstream improvements)

- Iterative skill loop: draft → test prompts → evaluate → refine
- Quantitative + qualitative eval workflow
- Baseline comparison support (with-skill vs without/old-skill)
- Benchmark aggregation and report tooling
- Description optimization flow to improve triggering quality
- Dedicated eval viewer (`eval-viewer/`) and grading agents (`agents/`)

## When to Use

Use this skill when you need to:
- Create a new skill from scratch
- Improve an existing skill
- Run evals for a skill and inspect results
- Compare performance variance across iterations
- Tune a skill description for better trigger behavior

## Key Resources

| Path | Purpose |
|---|---|
| `SKILL.md` | Main workflow and operating instructions |
| `scripts/` | Eval loop, benchmarking, packaging, validation utilities |
| `references/schemas.md` | Evals schema reference |
| `eval-viewer/` | Generate/view review pages for eval results |
| `agents/` | Analyzer/comparator/grader agent prompts |
| `assets/` | Viewer template assets |

## Upstream Reference

Based on Anthropic’s official skill-creator:
- https://github.com/anthropics/skills/tree/main/skills/skill-creator
