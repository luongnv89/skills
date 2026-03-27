---
name: opencode-runner
description: Delegate coding tasks to opencode (opencode.ai) using free models. Checks installation, discovers free models, selects the best available one (preferring minimax > kimi > glm > MiMo, with Big Pickle as last resort), executes the task, and monitors progress. Use when asked to "run this with opencode", "use opencode for this", "opencode this task", "delegate to opencode", "run with a free model", or when the user wants to offload a coding task to opencode without paying for API credits. Also trigger when the user mentions opencode, free coding models, or wants a second AI opinion on a coding task.
effort: medium
license: MIT
metadata:
  version: 1.2.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# OpenCode Runner

Delegate coding tasks to opencode using free models — zero cost, fully automated.

OpenCode (opencode.ai) is a terminal AI coding assistant that supports multiple providers and models. This skill automates the process of selecting the best available free model, launching the task, and reporting progress back to you.

## Critical Rules

1. **Never do the task yourself.** This skill exists solely to delegate work to opencode. If opencode is not installed, fails to run, or no free cloud model is available — report the problem to the user and **stop**. Do not fall back to editing files directly, writing code yourself, or using any other tool to accomplish the user's coding task. The whole point is that opencode does the work.

2. **Only select cloud models.** Never select local models (e.g., `ollama/*`, `lmstudio/*`, or any model running on localhost). Only select models from the `opencode/*` provider namespace, which are cloud-hosted on OpenCode Zen. Local models have unpredictable availability, performance, and may not support the tool-use capabilities opencode needs.

3. **Always clean up after yourself.** opencode spawns background processes (LSP servers, MCP servers, node workers) that persist after the task finishes. Every execution path — success, failure, error, timeout — must end with the cleanup steps in Phase 5. Orphaned opencode processes silently eat CPU and memory, and users won't notice until their machine slows to a crawl.

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

If `origin` is missing or conflicts occur, stop and ask the user before continuing.

## Phase 1: Verify Installation

Check that opencode is installed and at the latest version.

### Step 1: Check if installed

```bash
which opencode && opencode --version
```

If `opencode` is not found, tell the user:

> opencode is not installed. Install it with one of these commands:
>
> ```bash
> curl -fsSL https://opencode.ai/install | bash
> ```
> or
> ```bash
> npm i -g opencode-ai@latest
> ```
> or (macOS)
> ```bash
> brew install opencode
> ```

Then **stop completely** — do not proceed to any other phase, do not attempt the task yourself, do not edit any files. Wait for the user to install opencode and re-invoke this skill.

### Step 2: Check for updates

```bash
opencode upgrade
```

This will upgrade to the latest version if one is available, or confirm already up to date. If the upgrade fails, inform the user of the error and suggest running the command manually. If the upgrade itself breaks opencode, stop and report — do not continue.

## Phase 2: Discover Free Models

Query the available models and identify which free ones are accessible.

```bash
opencode models --verbose 2>/dev/null || opencode models
```

### Free model priority list

Select the **first available** model from this ordered list:

| Priority | Model ID | Name |
|----------|----------|------|
| 1 | `opencode/minimax-m2.5-free` | MiniMax M2.5 Free |
| 2 | `opencode/kimi-k2.5` | Kimi K2.5 (via Zen, check if free tier) |
| 3 | `opencode/glm-5` | GLM 5 (via Zen, check if free tier) |
| 4 | `opencode/mimo-v2-pro-free` | MiMo V2 Pro Free |
| 5 | `opencode/mimo-v2-omni-free` | MiMo V2 Omni Free |
| 6 | `opencode/big-pickle` | Big Pickle (last resort) |
| 7 | `opencode/gpt-5-nano` | GPT 5 Nano (fallback) |
| 8 | `opencode/nemotron-3-super-free` | Nemotron 3 Super Free (fallback) |

The model IDs above are based on OpenCode Zen's free tier. When checking `opencode models` output, look for models with "$0" or "Free" pricing. The exact IDs may change — match by name if the ID format differs.

**Selection logic:**
1. Parse the output of `opencode models` to find available models
2. **Filter out all local models** — ignore anything from `ollama/*`, `lmstudio/*`, or any provider that runs locally. Only consider models from the `opencode/*` provider namespace (cloud-hosted on OpenCode Zen)
3. Cross-reference the remaining cloud models with the priority list above
4. Pick the highest-priority model that appears in the available list
5. If none of the priority models are found, look for any `opencode/*` model listed as free ($0 or "Free")
6. If no free cloud models exist at all, inform the user and **stop** — do not fall back to local models or paid models, and do not attempt the task yourself

Report the selected model to the user before proceeding:

> Selected free model: **[model name]** (`[model-id]`)
> Reason: Highest priority free model available.

**Privacy note:** Free models on OpenCode Zen may use collected data for model improvement. Mention this to the user when selecting a free model so they can make an informed choice.

## Phase 3: Execute the Task

Run the coding task with the selected free model.

```bash
opencode run -m "[selected-model-id]" "[user's task prompt]"
```

### Handling multi-line or complex prompts

For tasks that reference files or need detailed context, use the `--file` flag:

```bash
opencode run -m "[selected-model-id]" --file path/to/relevant-file.py "[task description]"
```

### Running in the background

For long-running tasks, run in the background and monitor:

```bash
opencode run -m "[selected-model-id]" "[task]" --format json > /tmp/opencode-output.json 2>&1 &
OPENCODE_PID=$!
```

## Phase 4: Monitor and Report

While the task is running, provide periodic updates to the user.

### For foreground execution

The output streams directly. Summarize key milestones as they appear:
- When opencode starts processing
- When it reads/analyzes files
- When it begins generating code
- When it writes output files
- When it completes or errors

### For background execution

Check progress periodically:

```bash
# Check if still running
kill -0 $OPENCODE_PID 2>/dev/null && echo "Still running..." || echo "Completed"

# Check partial output
tail -20 /tmp/opencode-output.json
```

### Progress report format

Provide updates in this format:

> **OpenCode Progress Report**
> - Model: [model name]
> - Status: [Running / Completed / Error]
> - Duration: [time elapsed]
> - Current activity: [what opencode is doing]

### On completion

When the task finishes:

1. Report the final status (success or failure)
2. Show a summary of what opencode produced (files modified, code generated, etc.)
3. Report token usage if available via `opencode stats`
4. If the task failed, suggest the user try with a different free model from the priority list
5. **Run Phase 5 cleanup** — this is mandatory, even on success

### On error or timeout

If opencode errors or takes too long (>5 minutes with no output):

1. Report the error to the user
2. Suggest retrying with the next free cloud model in the priority list
3. If all free cloud models have been tried, inform the user that no free option worked and suggest checking their opencode configuration
4. **Never** attempt the task yourself as a fallback — the user invoked this skill because they want opencode to do the work, not you
5. **Run Phase 5 cleanup** — even on error or timeout, always clean up

## Phase 5: Cleanup (mandatory)

Every execution — success, failure, error, or timeout — must end with cleanup. opencode spawns child processes (LSP servers, MCP servers, node workers) that persist after the main process exits. Without cleanup, these orphaned processes accumulate and drain system resources.

### Step 1: Kill the opencode process tree

If you launched opencode in the background with a tracked PID:

```bash
# Kill the main process and its children
kill $OPENCODE_PID 2>/dev/null
# Wait briefly for graceful shutdown
sleep 2
# Force kill if still running
kill -9 $OPENCODE_PID 2>/dev/null
```

### Step 2: Find and kill orphaned opencode processes

After the task completes, scan for any lingering opencode processes from this session:

```bash
# List any remaining opencode processes
ps aux | grep '[o]pencode' | grep -v grep
```

If orphaned processes are found, kill them:

```bash
# Kill all opencode run processes (be specific to avoid killing the user's TUI)
pkill -f "opencode run" 2>/dev/null
```

Be careful to only kill `opencode run` processes, not the user's interactive TUI session (`opencode` without subcommand). If the user has an interactive opencode session open, leave it alone.

### Step 3: Clean up temp files

```bash
rm -f /tmp/opencode-output.json 2>/dev/null
```

### Step 4: Confirm cleanup

Report to the user:

> **Cleanup complete** — all opencode processes from this task have been terminated.

If you couldn't kill some processes (permission denied, etc.), warn the user:

> **Warning:** Some opencode processes may still be running. Run `pkill -f "opencode run"` manually to clean up.

## Step Completion Reports

After completing each major phase, output a status report in this format:

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

### Installation (phase 1 of 5)

```
◆ Installation (phase 1 of 5 — opencode readiness)
··································································
  opencode found:         √ pass — /usr/local/bin/opencode
  Version current:        √ pass — already at latest
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

### Model Discovery (phase 2 of 5)

```
◆ Model Discovery (phase 2 of 5 — free model selection)
··································································
  Models queried:         √ pass — 12 models available
  Free model selected:    √ pass — opencode/minimax-m2.5-free
  Tier ranking applied:   √ pass — priority 1 model chosen
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Execution (phase 3 of 5)

```
◆ Execution (phase 3 of 5 — task delegation)
··································································
  Task submitted:         √ pass
  Progress monitored:     √ pass — streaming output observed
  Output captured:        × fail — timeout after 5 min with no output
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

### Monitor and Report (phase 4 of 5)

```
◆ Monitor and Report (phase 4 of 5 — progress tracking)
··································································
  Progress observed:        √ pass — streaming output detected
  Status reported:          √ pass — completion summary delivered
  Token usage logged:       × fail — stats unavailable
  [Criteria]:               √ 2/3 met
  ____________________________
  Result:                   PARTIAL
```

### Cleanup (phase 5 of 5)

```
◆ Cleanup (phase 5 of 5 — process termination)
··································································
  Processes killed:       √ pass — OPENCODE_PID terminated
  Temp files cleaned:     √ pass — /tmp/opencode-output.json removed
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `opencode --version` | Check installed version |
| `opencode upgrade` | Update to latest |
| `opencode models` | List available models |
| `opencode run -m MODEL "prompt"` | Run task with specific model |
| `opencode stats` | View usage statistics |
| `opencode auth list` | Check authenticated providers |
| `pkill -f "opencode run"` | Kill orphaned run processes |
| `ps aux \| grep opencode` | Find running opencode processes |
