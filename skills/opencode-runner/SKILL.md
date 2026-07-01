---
name: opencode-runner
description: "Run coding tasks via opencode using free cloud models. Use when asked to offload work to opencode.ai or run a free model. Don't use for local models (Ollama, LM Studio), Claude/OpenAI calls, or when Claude should do the work itself."
license: MIT
effort: medium
metadata:
  version: 1.4.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# OpenCode Runner

Delegate coding tasks to opencode using free models — zero cost, fully automated.

OpenCode (opencode.ai) is a terminal AI coding assistant that supports multiple providers and models. This skill automates the process of selecting the best available free model, launching the task, and reporting progress back to you.

## Prerequisites

- **opencode installed**: `which opencode` must succeed; install via `npm i -g opencode-ai@latest` or `brew install opencode` if missing
- **Internet access**: required for cloud model selection and task execution via OpenCode Zen
- **Project context**: the current working directory should be the project root for file-context tasks

## Critical Rules

1. **Never do the task yourself.** This skill exists solely to delegate work to opencode. If opencode is not installed, fails to run, or no free cloud model is available — report the problem to the user and **stop**. Do not fall back to editing files directly, writing code yourself, or using any other tool to accomplish the user's coding task. The whole point is that opencode does the work.

2. **Only select cloud models.** Never select local models (e.g., `ollama/*`, `lmstudio/*`, or any model running on localhost). Only select models from the `opencode/*` provider namespace, which are cloud-hosted on OpenCode Zen. Local models have unpredictable availability, performance, and may not support the tool-use capabilities opencode needs.

3. **Always clean up after yourself.** opencode spawns background processes (LSP servers, MCP servers, node workers) that persist after the task finishes. Every execution path — success, failure, error, timeout — must end with the cleanup steps in Phase 6. Orphaned opencode processes silently eat CPU and memory, and users won't notice until their machine slows to a crawl.

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

## Phase 2: Discover Free Models & Let User Pick

Query the available models, present the free ones to the user, and let them choose. If the user doesn't choose, fall back to the priority order.

```bash
opencode models 2>/dev/null
```

### Free model priority list (default order if user defers)

| Priority | Model ID | Notes |
|----------|----------|-------|
| 1 | `opencode/deepseek-v4-flash-free` | Strong recent free coding model — preferred default |
| 2 | `opencode/minimax-m2.5-free` | MiniMax free tier — good general-purpose |
| 3 | `opencode/nemotron-3-super-free` | NVIDIA Nemotron free tier |
| 4 | `opencode/big-pickle` | Free fallback |
| 5 | `opencode/gpt-5-nano` | Small, low-cost fallback (verify pricing) |

Model IDs evolve. When parsing `opencode models` output, treat any `opencode/*` model whose ID ends in `-free` (or is explicitly priced $0) as free-tier eligible. Match by suffix, not by exact ID.

### Selection logic

1. Run `opencode models` and collect all entries.
2. **Filter out all non-`opencode/*` models** — ignore anything from `ollama/*`, `lmstudio/*`, `nvidia/*`, or any other namespace. Only cloud-hosted `opencode/*` models qualify.
3. Among the remaining list, identify the free candidates (suffix `-free` or known-free IDs from the priority list).
4. **Present the free models to the user as numbered options**, in priority order, with priority 1 marked as the default. Use the `<options>` format if possible. Example:

   > I found these free cloud models available via opencode. Pick one, or accept the default.
   >
   > 1. `opencode/deepseek-v4-flash-free` *(default — priority 1)*
   > 2. `opencode/minimax-m2.5-free`
   > 3. `opencode/nemotron-3-super-free`
   > 4. `opencode/big-pickle`

5. If the user names a model, use that one. If the user says "default", "you pick", "any", or doesn't specify, use priority 1 (the highest-priority available free model).
6. If no free cloud models exist at all, inform the user and **stop** — do not fall back to local models, paid models, or doing the task yourself.

**Privacy note** (always show this with the model list): Free models on OpenCode Zen may use collected data for model improvement.

## Phase 3: Confirm Before Executing

Before invoking opencode, show the user a one-screen summary and get explicit confirmation. This catches wrong-model or wrong-prompt mistakes before any tokens are burned.

Present this block:

> **Ready to delegate to opencode**
>
> - **Model:** `opencode/deepseek-v4-flash-free` (free tier)
> - **Working directory:** `/Users/.../current-project`
> - **Context files:** `path/to/foo.py`, `path/to/bar.py` *(or "none")*
> - **Prompt:** *(quote the prompt verbatim, multi-line OK)*
> - **Estimated duration:** unknown — opencode is non-deterministic; cleanup runs even on timeout
>
> Confirm to proceed, or tell me what to change (model, prompt, files).

Then offer the user two `<options>`: "Proceed" and "Change something". Wait for confirmation. Do **not** invoke `opencode run` until the user confirms.

If the user asks to change anything (different model, edit prompt, add/remove context files), loop back: update the field, re-show the summary, and ask again.

## Phase 4: Execute the Task

Run the coding task with the confirmed model. **Always run in the background with output redirected to a log file** — this is required for the low-token monitoring strategy in Phase 5.

```bash
LOG=/tmp/opencode-$$.log
opencode run -m "[confirmed-model-id]" "[confirmed prompt]" > "$LOG" 2>&1 &
OPENCODE_PID=$!
echo "opencode started: pid=$OPENCODE_PID log=$LOG"
```

### Handling multi-line or complex prompts

For tasks that reference files or need detailed context, use the `--file` flag:

```bash
opencode run -m "[confirmed-model-id]" --file path/to/relevant-file.py "[task description]" > "$LOG" 2>&1 &
OPENCODE_PID=$!
```

Foreground execution is **discouraged** — streaming the full opencode output back into your context wastes tokens. The Phase 5 monitor reads only the log tail.

## Phase 5: Monitor with Minimum Tokens

opencode output is verbose. Streaming the full log back into your context is expensive — a single long run can easily push past 10k tokens of stream chatter. Use the lightweight polling protocol below instead.

### Polling protocol

Run **one** tiny status command per check. It returns at most ~200 bytes — enough to know status, elapsed time, and the latest activity line — without ingesting the whole log.

```bash
LOG=/tmp/opencode-$$.log   # the same log file from Phase 4
status() {
  if kill -0 $OPENCODE_PID 2>/dev/null; then s=running; else s=done; fi
  bytes=$(wc -c < "$LOG" 2>/dev/null || echo 0)
  last=$(tail -n 1 "$LOG" 2>/dev/null | tr -d '\r' | cut -c1-160)
  printf 'status=%s pid=%s bytes=%s last=%q\n' "$s" "$OPENCODE_PID" "$bytes" "$last"
}
status
```

That single line is your full progress sample. Do not `tail -n 50`, do not `cat $LOG`, do not stream stdout — those defeat the purpose.

### Cadence (mandatory)

- Wait **at least 30 seconds between polls** for short tasks, **60–120s** for longer ones.
- Hard cap: **6 polls total** per run. If still running after that, ask the user whether to keep waiting or kill the process. Do not silently loop.
- Detect stalls: if `bytes=` is unchanged for **two consecutive polls** (i.e., ≥60s of no output growth), treat the run as stalled — confirm with the user before killing.
- Detect timeout: if no completion after ~5 minutes with no `bytes` growth, kill and report (then run Phase 6).

### What to report between polls

One short line per check, derived from the `status()` output:

> *Poll 2 (t+60s): running, 4.2 KB written, last: "Editing src/foo.py …"*

Do not paste the raw log. Do not summarize what opencode is "thinking" — you can't tell from a tail line. Stick to: status, elapsed, byte growth, last line.

### On completion

When `status=done`:

1. **Read the tail only**, not the whole log: `tail -n 40 "$LOG"`. That's the summary opencode prints at the end (files changed, tokens used, errors).
2. Report: final status (success/fail), files mentioned in the tail, and token count if opencode printed one.
3. If the user wants the full output, point them to `$LOG` — do not paste it.
4. If the task failed, suggest retrying with the next free model from the Phase 2 list.
5. **Run Phase 6 cleanup** — mandatory, even on success.

### On error, stall, or timeout

1. Report the error or stall to the user (one line, derived from the last poll).
2. Suggest retrying with the next free cloud model.
3. If all free models have been tried, suggest the user run `opencode auth list` to check provider auth.
4. **Never** attempt the task yourself as a fallback.
5. **Run Phase 6 cleanup** — always.

## Phase 6: Cleanup (mandatory)

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
rm -f "$LOG" 2>/dev/null
```

### Step 4: Confirm cleanup

Report to the user:

> **Cleanup complete** — all opencode processes from this task have been terminated.

If you couldn't kill some processes (permission denied, etc.), warn the user:

> **Warning:** Some opencode processes may still be running. Run `pkill -f "opencode run"` manually to clean up.

## Expected Output

See `references/expected-output.md` for the full set of example blocks the user should see at each phase (model picker, confirmation summary, low-token progress polls, cleanup confirmation). On error or timeout, the cleanup confirmation still runs.

---

## Edge Cases

- **opencode not installed** — see Phase 1, Step 1 (install instructions, then stop).
- **opencode upgrade fails** — see Phase 1, Step 2 (report and stop, don't continue on a broken binary).
- **No free cloud models available** — see Phase 2, Selection logic step 6 (inform user, stop; no fallback to local/paid models).
- **All priority free models tried and all fail** — see Phase 5, "On error, stall, or timeout" (suggest `opencode auth list`, stop).
- **Task timeout (>5 minutes with no output growth)** — see Phase 5, Cadence and "On error, stall, or timeout" (confirm, kill, retry suggestion, Phase 6 cleanup).
- **User rejects the Phase 3 confirmation** — see Phase 3, final paragraph (loop back to Phase 2 or 3; never invoke `opencode run` unconfirmed).
- **User has an interactive opencode TUI session open** — see Phase 6, Step 2 (kill only `opencode run` children, leave the TUI alone).
- **Task prompt contains multi-line content or file references** — see Phase 4, "Handling multi-line or complex prompts" (use `--file`).
- **opencode produces output but exits non-zero** — Report the exit code and last lines of output to the user, run cleanup, and suggest verifying the task result manually before relying on it.

---

## Acceptance Criteria

The skill run is considered successful when all of the following are verifiable:

- [ ] **Installation verified** — Phase 1 confirms `opencode` is on PATH and reports its version before any other action.
- [ ] **Only cloud `opencode/*` models considered** — Filter step rejects `ollama/*`, `lmstudio/*`, `nvidia/*`, and any other namespace. No local model is ever selected.
- [ ] **Free models presented to the user** — Phase 2 lists every available free `opencode/*` model with priority 1 as default, plus the privacy note. The user may pick one; if they defer, priority 1 is used.
- [ ] **Confirmation captured before execution** — Phase 3 shows model + cwd + context files + prompt, and waits for explicit user confirmation before invoking `opencode run`.
- [ ] **Task delegated to opencode** — The coding task is executed via `opencode run`, not by the skill editing files directly or writing code itself.
- [ ] **Low-token monitoring used** — Phase 5 polls via the single-line `status()` helper. The raw log is never streamed back; only the last line, byte count, and status are reported per poll. Max 6 polls per run.
- [ ] **Stall/timeout handled** — No byte growth across two consecutive polls or no completion after ~5 min triggers a confirmation with the user and (if approved) a kill + cleanup.
- [ ] **Completion summary delivered** — On `status=done`, the skill reads only `tail -n 40 "$LOG"` and summarizes files changed and token usage.
- [ ] **Cleanup runs on every exit path** — Phase 6 runs whether the task succeeded, failed, errored, stalled, or timed out. No orphaned `opencode run` processes remain.
- [ ] **Temp files removed** — `$LOG` (and any other temp files created) are deleted during cleanup.
- [ ] **No fallback to self** — If opencode is unavailable, the user rejects the confirmation, or all free models fail, the skill stops. It never falls back to editing files or writing code itself.

---

## Step Completion Reports

After each phase, emit a compact status block so pass/fail is scannable:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Use `√` for pass, `×` for fail, and `—` to add brief context. Per-phase example blocks (Installation, Model Discovery, Confirmation, Execution, Monitor, Cleanup) are in `references/expected-output.md`.

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
