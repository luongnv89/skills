---
name: context-hub
version: 1.0.0
description: Use Context Hub (`chub`) to fetch up-to-date third-party API/SDK docs before writing or reviewing integration code. Trigger this skill whenever a task mentions external APIs, SDKs, webhooks, auth flows, or library-specific method usage (OpenAI, Stripe, Anthropic, Pinecone, etc.), even if the user does not explicitly ask for documentation.
---

# Context Hub

Use `chub` as the default source of truth for third-party API/SDK behavior.

## Repo Sync Before Edits (mandatory)

When the task will modify files in a git repository, sync first.

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty, stash before syncing, then pop after sync.
If `origin` is missing or rebase conflicts happen, stop and ask the user.

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