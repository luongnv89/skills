---
name: context-hub
description: Use Context Hub (`chub`) to fetch up-to-date third-party API/SDK docs before writing or reviewing integration code. Trigger this skill whenever a task mentions external APIs, SDKs, webhooks, auth flows, or library-specific method usage (OpenAI, Stripe, Anthropic, Pinecone, etc.), even if the user does not explicitly ask for documentation.
effort: low
license: MIT
metadata:
  version: 1.0.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Context Hub

Use `chub` as the default source of truth for third-party API/SDK behavior.

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

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

## 1) Ensure `chub` is ready

Run:

```bash
chub help
chub update
```

If `chub` is not installed and installation is allowed, run:

```bash
npm install -g @aisuite/chub
```

If installation is blocked, tell the user and use official docs directly.

## 2) Identify target docs

Run:

```bash
chub search "<library or API name>" --json
```

Choose the best `id` (`<author>/<name>`, for example `openai/chat`, `stripe/api`).
If results are weak, retry with broader keywords.

## 3) Fetch language-specific docs

Run:

```bash
chub get <id> --lang py
```

Use the project language (`py`, `js`, `ts`) when variants exist.
Omit `--lang` when only one variant is available.

Prefer focused fetches when possible:

```bash
chub get <id> --file <reference-file>
```

Use `--full` only when full package context is required.

## 4) Implement from fetched docs only

Write code and explanations from fetched docs.
Do not guess method names, payload fields, endpoint paths, or auth headers.
When uncertain, fetch again instead of inferring.

## 5) Capture durable learnings

If you discover a real gap (gotcha, workaround, version quirk), store it:

```bash
chub annotate <id> "<concise actionable note>"
```

Keep notes short, concrete, and non-duplicative.

## 6) Submit doc feedback only with user approval

Ask the user before sending feedback.

```bash
chub feedback <id> up
chub feedback <id> down --label outdated
```

Common labels:
`outdated`, `inaccurate`, `incomplete`, `wrong-examples`, `wrong-version`, `poorly-structured`, `accurate`, `well-structured`, `helpful`, `good-examples`.

## Quick commands

```bash
chub search "stripe"
chub get stripe/api --lang js
chub annotate stripe/api "Webhook verification requires raw body"
chub annotate --list
```

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Tool Readiness** — checks: `chub availability`, `chub updated`

**Phase: Documentation Fetch** — checks: `Doc identification`, `Doc fetch success`

**Phase: Implementation** — checks: `Implementation accuracy`, `No guessed fields`

**Phase: Learning Capture** — checks: `Annotation saved`, `Note non-duplicative`
