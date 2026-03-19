# Auto Push

> Stage all changes, create a conventional commit, and push to remote with comprehensive safety checks.

## Highlights

- Detect secrets, API keys, large files, and build artifacts before pushing
- Generate conventional commit messages (feat, fix, docs, etc.) automatically
- Pre-push confirmation with detailed change summary
- Handle non-fast-forward pushes with fallback strategies

## When to Use

| Say this... | Skill will... |
|---|---|
| "Push everything" | Stage, commit, and push all changes |
| "Commit and push all" | Bulk push with safety checks |
| "Push all my changes" | Analyze, confirm, then push |

## How It Works

```mermaid
graph TD
    A["Analyze Changes"] --> B["Run Safety Checks"]
    B --> C{"Secrets or Issues Found?"}
    C -->|Yes| D["Warn & Abort"]
    C -->|No| E["Show Summary"]
    E --> F["Commit & Push"]
    style A fill:#4CAF50,color:#fff
    style C fill:#FF9800,color:#fff
    style F fill:#2196F3,color:#fff
```

## Installation

Install via [npx (Vercel)](https://www.npmjs.com/package/skills):

```bash
npx skills add https://github.com/luongnv89/skills --skill auto-push
```

Or via [agent-skill-manager (asm)](https://www.npmjs.com/package/agent-skill-manager):

```bash
asm install github:luongnv89/skills --skill auto-push
```

## Usage

```
/auto-push
```

## Output

Committed and pushed changes with a confirmation report showing commit hash, branch info, files changed, and insertions/deletions.
