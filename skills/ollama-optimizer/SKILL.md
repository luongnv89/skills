---
name: ollama-optimizer
description: "Optimize Ollama configuration for the current machine's hardware. Use when asked to speed up Ollama, tune local LLM performance, or pick models that fit available GPU/RAM. Don't use for LM Studio, llama.cpp, vLLM, or hosted-API LLM providers."
license: MIT
effort: medium
metadata:
  version: 1.3.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Ollama Optimizer

Optimize Ollama configuration based on system hardware analysis.

## When to Use

Use this skill when the user asks to optimize Ollama, configure Ollama, speed up Ollama, fix Ollama running slow, set up a local LLM, tune inference speed, reduce memory usage, or select models that fit their GPU/RAM. The skill analyzes hardware (GPU, VRAM, RAM, CPU) and produces tailored recommendations.

Do not use for LM Studio, llama.cpp, vLLM, or hosted-API LLM providers (OpenAI, Anthropic) — those use different runtimes and tuning surfaces.

## Safety Rules

- Phases 1 and 2 are read-only. They run `scripts/detect_system.py`, `ollama --version`, `ollama list`, and `ollama ps`, and they change nothing.
- An **applied change** is any write to the machine: an env-var write, a service or app restart, `ollama pull`, a Modelfile `ollama create`, or any `sudo` command. Before each applied change, show its exact command and wait for the user's yes for that change.
- Saving the guide to the path the user chose is not an applied change.
- If the user asks for recommendations only, apply nothing and deliver the guide. A recommendations-only request is not a decline.
- Back up each config location before the first write to it (*Choose where the env vars go*).
- Never delete a model, and never run `ollama rm`. List oversized models in the guide instead.
- Never set `OLLAMA_HOST=0.0.0.0` unless the user asks for network access. If they ask, warn that it exposes the Ollama API to the network without authentication.

## Workflow

**Fast path (opt-in only):** only skip full hardware analysis if the user explicitly asks to. Otherwise always run Phases 1-4 and follow the tier-based recommendation — do not apply shortcuts by default, and do not let them override a tier decision already made. For the per-platform shortcut commands and env vars, see [Platform-Specific Setup](references/platform_specific.md) and [Environment Variables](references/environment_variables.md).

### Phase 1: System Detection

Run the detection script to gather hardware information:

```bash
python3 scripts/detect_system.py
```

The script prints JSON on stdout and exits 0. On an unexpected failure it prints `Error: ...` on stderr and exits 1. If it exits 1, show that message, follow its fix hint, and run it once more. If the second run also exits 1, stop with `BLOCKED` (*Final Report*).

Parse the JSON output to identify:
- OS and version
- CPU model and core count
- Total RAM / unified memory
- GPU type, VRAM, and driver version
- Current Ollama installation and environment variables
- `hardware_tier` — the script's computed `category`, `max_model_size`, and `recommended_quant`

If `ollama.installed` is `false`, continue to Phase 2. The plan then starts with the install step from [Platform-Specific Setup](references/platform_specific.md). Installing Ollama is an applied change.

### Phase 2: Analyze and Recommend

Use `hardware_tier` from Phase 1 as the tier decision. Do not re-derive it; the table below explains what each tier means and which optimizations it implies. Override the script only with an explicit reason (e.g. VRAM shared with a display), and state that reason in the report.

**Unknown VRAM.** The script tiers a GPU only from `vram_gb`. An AMD ROCm GPU, an NVIDIA GPU whose VRAM reads `[N/A]`, and the Windows WMIC fallback report no `vram_gb`, so the script returns `low_vram`. An Intel Mac with a discrete GPU reports an empty `gpu` list, so the script returns `cpu_only`. In these cases, ask the user for the VRAM size. If they give it, override the tier from the table and state the reason. If they do not, keep the script's tier and list it under `Uncertainty:` as a conservative tier.

**Hardware Tier Classification:**

| Tier (`category`) | Script band | Max Model | Key Optimizations |
|------|----------|-----------|-------------------|
| `cpu_only` | No GPU detected | 3B | num_thread tuning, Q4_K_M quant |
| `low_vram` | <6GB VRAM | 3B | Flash attention, KV cache q4_0 |
| `entry` | 6-10GB VRAM | 8B | Flash attention, KV cache q8_0 |
| `prosumer` | 10-16GB VRAM | 14B | Flash attention, full offload |
| `workstation` | 16-48GB VRAM | 32B | Standard config, Q5_K_M option |
| `high_end` | 48GB+ VRAM | 70B+ | Multiple models, Q5/Q6 quants |

**Apple Silicon Special Case:**
- Unified memory = shared CPU/GPU RAM; the script tiers it directly from total unified memory
- 8GB Mac → `entry`
- 16GB Mac → `prosumer`
- 32GB Mac → `workstation`; 64GB+ Mac → `high_end`

**Nothing to change.** `current_env_vars` shows only the environment the script ran in. For `Ollama.app` or the systemd service, also read the values Ollama uses (`launchctl getenv VAR`, `systemctl show ollama -p Environment`). If every recommended env var already has the recommended value there and every installed model fits the tier, the guide says so and the run proposes no applied change.

### Phase 3: Generate Optimization Plan

Read [Report Templates](references/report-template.md), then create the guide with these sections:

#### 1. System Overview
Present detected hardware specs and highlight constraints (e.g., "8GB unified memory limits to 8B models").

#### 2. Dependency Assessment
List what's needed based on the platform:
- macOS: Ollama only (Metal automatic)
- Linux NVIDIA: Ollama + NVIDIA driver 450+
- Linux AMD: Ollama + ROCm 5.0+
- Windows: Ollama + NVIDIA driver 452+

#### 3. Configuration Recommendations

**Essential environment variables:**
```bash
# Always recommended
export OLLAMA_FLASH_ATTENTION=1

# Memory-constrained systems (<12GB)
export OLLAMA_KV_CACHE_TYPE=q8_0  # or q4_0 for severe constraints
```

Set `OLLAMA_KV_CACHE_TYPE` when the GPU has under 12GB of VRAM or unified memory: `q4_0` for `low_vram`, `q8_0` otherwise. `OLLAMA_KV_CACHE_TYPE` requires `OLLAMA_FLASH_ATTENTION=1`.

**Model selection guidance:**
- Recommend specific models from `ollama list` output
- Suggest appropriate quantization (Q4_K_M default, Q5_K_M if headroom exists)
- Warn if current models exceed hardware capacity

**Modelfile tuning (when needed):**
```
PARAMETER num_gpu <layers>    # Partial offload for limited VRAM
PARAMETER num_thread <cores>  # CPU threads (physical cores, not hyperthreads)
PARAMETER num_ctx <size>      # Reduce context for memory savings
```

#### 4. Choose where the env vars go

A shell init file reaches only an `ollama serve` started from that shell. Find how Ollama runs: on macOS, check for a running `Ollama.app` (`pgrep -x Ollama`); on Linux, run `systemctl is-active ollama`; on Windows, use the Windows row; if `docker ps` lists an Ollama container, use the Docker row. If the checks are inconclusive, ask the user. Then use the matching row; the commands are in [Environment Variables](references/environment_variables.md) → *Setting Variables Permanently*.

| How Ollama runs | Where the env vars go | Backup before the write | One-command rollback |
|---|---|---|---|
| `ollama serve` from a terminal (macOS, Linux) | the shell init file that `$SHELL` uses | `cp "$RC" "$RC.ollama-bak"` | `cp "$RC.ollama-bak" "$RC"` |
| `Ollama.app` (macOS) | `launchctl setenv VAR value`, then quit and reopen the app; the value does not survive a reboot, so list that under `Uncertainty:` | record `launchctl getenv VAR` | `launchctl unsetenv VAR` for each var, chained on one line |
| systemd service (Linux) | `Environment=` lines in `sudo systemctl edit ollama` | `systemctl cat ollama > ~/ollama.service.bak` | `sudo systemctl revert ollama && sudo systemctl restart ollama` |
| Windows | user env vars via `SetEnvironmentVariable(..., "User")` | record the current value | set each var to `$null` at `"User"` scope, chained on one line |
| Docker | `-e` flags or the compose `environment:` list | copy the compose file | restore the copy and recreate the container |

#### 5. Execution Checklist
Provide copy-paste commands in order. Run a command only after the user approves it (*Safety Rules*):
1. Back up the config location from step 4 and write the env vars. For the shell init file (`$SHELL` decides: `~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`):
   ```bash
   RC=~/.zshrc  # or ~/.bashrc / ~/.bash_profile, matching $SHELL
   cp "$RC" "$RC.ollama-bak"
   printf '\n# ollama-optimizer start\nexport OLLAMA_FLASH_ATTENTION=1\n<KV cache + other export lines from section 3, per tier>\n# ollama-optimizer end\n' >> "$RC"
   ```
2. Restart Ollama the way the step 4 row runs it: restart `ollama serve`, quit and reopen Ollama.app, run `sudo systemctl restart ollama`, or recreate the container
3. Pull recommended models
4. Test with `ollama run <model> --verbose`
5. Rollback (one command, same location as step 1): for the shell init file, `cp "$RC.ollama-bak" "$RC"` — then restart Ollama. Other locations use the rollback column in step 4.

If an approved command exits non-zero, stop the checklist, show the error, and keep the backup. Offer the rollback command, and run it only after the user approves it.

### Phase 4: Verification

Run Phase 4 only when, at this point, `ollama --version` exits 0 and `ollama list` shows at least one model. Otherwise, skip it and record the reason.

```bash
# Benchmark current performance
python3 scripts/benchmark_ollama.py --model <model>
# Expected output: tokens/s and generation latency — record as the post-tuning baseline.

# Check GPU memory usage (NVIDIA only)
nvidia-smi

# Verify config is applied
ollama run <model> "test" --verbose 2>&1 | head -20
```

`benchmark_ollama.py` exits 1 with a JSON `error` on stderr when Ollama is missing or not running, when no model is installed, or when the requested model is absent; it exits 2 on an invalid argument. If every run reports `"success": false`, the model has no `averages`, the script prints a `Warning:` line on stderr, and verification failed. If no change was applied, the numbers are the current baseline, not a post-tuning result; say so under `Uncertainty:`.

## Edge Cases

When several rows match, the first-match status rules in *Final Report* decide.

| Case | Handling | Status |
|---|---|---|
| Ollama not installed (`ollama.installed: false`), and not installed during the run | Plan with the install step first; skip Phase 4 | PARTIAL |
| No model in `ollama list`, and none pulled during the run | Recommend models for the tier; skip Phase 4 | PARTIAL |
| GPU with unknown VRAM | Ask for VRAM; otherwise keep the conservative tier | per the status rules; an Uncertainty line when the tier stays conservative |
| User wants recommendations only | Apply nothing; deliver the guide | COMPLETE |
| User declines an applied change | Mark it not applied in the guide; continue with the rest | PARTIAL |
| Approved command fails, or verification fails | Stop the checklist; offer rollback | PARTIAL |
| Nothing to change | Say so in the guide; benchmark the current setup | COMPLETE |
| `detect_system.py` exits 1 twice | Stop before any recommendation | BLOCKED |

## Final Report

End every run, early stops included, with this summary. Fill rules: [Report Templates](references/report-template.md) → *Final summary fill rules*.

```
Result: COMPLETE | PARTIAL | BLOCKED — <tier>; <what changed>
Evidence: <checks that ran, with observed values>
Uncertainty: <untested or assumed items, or "none">
Decision: <approval needed, or "No approval needed.">
Remaining action: <one user action per line; omit when none>
Guide: <saved path, or "printed inline">
```

Choose the status with the first rule that matches:

1. **BLOCKED** — no guide was delivered: `detect_system.py` exited 1 twice, or the user stopped the run before the guide was delivered.
2. **PARTIAL** — the guide was delivered, and at least one of these holds: Phase 4 was skipped because Ollama or a model was missing, a recommended change was not applied because the user declined it or stopped the run, an approved command failed, or Phase 4 ran and failed.
3. **COMPLETE** — the guide was delivered, and every applied change the user approved succeeded and was verified in Phase 4. A recommendations-only run and a nothing-to-change run are COMPLETE.

A user declining a change never produces BLOCKED.

## Example

An 8GB Apple Silicon Mac running `Ollama.app`, where the user approved both env vars:

```
Result: COMPLETE — entry; OLLAMA_FLASH_ATTENTION=1 and OLLAMA_KV_CACHE_TYPE=q8_0 applied
Evidence: detect_system.py exit 0 (entry, 8GB unified); launchctl setenv exit 0 for both vars; benchmark_ollama.py llama3.1:8b avg 21.7 tokens/s after reopening Ollama.app
Uncertainty: launchctl values reset at reboot; not re-checked after a reboot
Decision: No approval needed.
Remaining action: after a reboot, re-run the two launchctl setenv commands from the guide
Guide: ~/.config/ollama/optimization-guide.md
```

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] Hardware tier (CPU-only / Low-VRAM / Entry / Prosumer / Workstation / High-end) is identified explicitly in the report.
- [ ] Recommended model size fits within detected VRAM/unified-memory budget (no recommending a 14B model on an 8GB Mac).
- [ ] Each applied env var is written to the location the running Ollama reads (*Choose where the env vars go*), after a backup and the user's approval. A recommendations-only run lists these commands without running them.
- [ ] Apple Silicon special case is applied when detected — unified memory is not double-counted as separate VRAM + RAM.
- [ ] Verification step runs `ollama run <model>` with `--verbose` and captures the actual offload/cache numbers, or the report states why Phase 4 was skipped.
- [ ] Rollback instructions are included so the user can revert all env changes with one command.
- [ ] The final summary passes the four reader checks in [Report Templates](references/report-template.md) → *Reader checks*: the status is on the first line, facts and assumptions are separated, each claim is traceable to a check that ran, and the next decision is explicit. Without responsive human feedback, human understanding stays unconfirmed.

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

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict. One example per phase (Detection, Analysis, Plan, Verification): [Report Templates](references/report-template.md) → *Step Completion Report examples*.

## Reference Files

- [VRAM Requirements](references/vram_requirements.md) - Model sizing and quantization guide
- [Environment Variables](references/environment_variables.md) - Complete env var reference
- [Platform-Specific Setup](references/platform_specific.md) - OS-specific installation and configuration
- [Report Templates](references/report-template.md) - Step report examples, guide template, final summary fill rules, reader checks

## Expected Output

Generate an `ollama-optimization-guide.md` file from the guide template in [Report Templates](references/report-template.md). Ask the user where to save it (suggest `~/.config/ollama/optimization-guide.md` or current directory). If the user declines a file, print the guide in the reply. Then print the final summary (*Final Report*).
