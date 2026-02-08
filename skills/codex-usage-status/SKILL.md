---
name: codex-usage-status
description: Check OpenAI Codex (openai-codex) account usage/quota windows using local OpenClaw configuration (OAuth). Report clean, readable usage stats and compute a linear pace projection for end-of-week usage (pace derived from the provider’s Day usage percent with the week anchored to Day resetAt). Use when asked for Codex usage, quota, limits, reset times, remaining percent, or “pace/projection”.
---

# Codex usage status (quota + pace)

## Quick start

Run the bundled CLI script (it reads credentials implicitly via `openclaw status --usage --json`, so no API keys are needed):

```bash
python3 scripts/codex_usage_status.py
# or
./scripts/codex_usage_status.py
```

Common options:

```bash
./scripts/codex_usage_status.py --provider openai-codex
./scripts/codex_usage_status.py --json
```

## What the script reports

- Provider plan name (when available)
- Usage windows (example labels: `5h`, `Day`, `Week`) with:
  - **Used %**
  - **Reset time** (UTC) + time remaining
  - **Pace** projection

## Pace definition

Pace is a simple **end-of-week projection** computed from the provider’s **`Day`** window usage percent.

The week window is anchored to the `Day` window reset time:
- `week_end = Day.resetAt`
- `week_start = week_end - 7 days`

Formula:
- Basis: `Day.usedPercent` (different label, same signal)
- Usage rate: `current_used_percent ÷ time_elapsed_since_week_start`
- Projection: `current% + (rate × time_remaining_in_week)`

If `Day.usedPercent` is missing or 0%, Pace is **0%**.
