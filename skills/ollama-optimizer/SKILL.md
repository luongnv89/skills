---
name: ollama-optimizer
description: Optimize Ollama configuration for maximum performance on the current machine. Use when asked to "optimize Ollama", "configure Ollama", "speed up Ollama", "tune LLM performance", "setup local LLM", "fix Ollama performance", "Ollama running slow", or when users want to maximize inference speed, reduce memory usage, or select appropriate models for their hardware. Analyzes system hardware (GPU, RAM, CPU) and provides tailored recommendations.
effort: medium
license: MIT
metadata:
  version: 1.0.2
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Ollama Optimizer

Optimize Ollama configuration based on system hardware analysis.

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

## Workflow

### Phase 1: System Detection

Run the detection script to gather hardware information:

```bash
python3 scripts/detect_system.py
```

Parse the JSON output to identify:
- OS and version
- CPU model and core count
- Total RAM / unified memory
- GPU type, VRAM, and driver version
- Current Ollama installation and environment variables

### Phase 2: Analyze and Recommend

Based on detected hardware, determine the optimization profile:

**Hardware Tier Classification:**

| Tier | Criteria | Max Model | Key Optimizations |
|------|----------|-----------|-------------------|
| CPU-only | No GPU detected | 3B | num_thread tuning, Q4_K_M quant |
| Low VRAM | <6GB VRAM | 3B | Flash attention, KV cache q4_0 |
| Entry | 6-8GB VRAM | 8B | Flash attention, KV cache q8_0 |
| Prosumer | 10-12GB VRAM | 14B | Flash attention, full offload |
| Workstation | 16-24GB VRAM | 32B | Standard config, Q5_K_M option |
| High-end | 48GB+ VRAM | 70B+ | Multiple models, Q5/Q6 quants |

**Apple Silicon Special Case:**
- Unified memory = shared CPU/GPU RAM
- 8GB Mac → treat as 6GB VRAM tier
- 16GB Mac → treat as 12GB VRAM tier
- 32GB+ Mac → treat as workstation tier

### Phase 3: Generate Optimization Plan

Create a structured optimization guide with these sections:

#### 1. System Overview
Present detected hardware specs and highlight constraints (e.g., "8GB unified memory limits to 7B models").

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

#### 4. Execution Checklist
Provide copy-paste commands in order:
1. Set environment variables
2. Restart Ollama service
3. Pull recommended models
4. Test with `ollama run <model> --verbose`

#### 5. Verification Commands

```bash
# Benchmark current performance
python3 scripts/benchmark_ollama.py --model <model>
# Expected output: tokens/s and generation latency. Compare against tier baseline from Phase 2.

# Check GPU memory usage (NVIDIA)
nvidia-smi

# Verify config is applied
ollama run <model> "test" --verbose 2>&1 | head -20
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

### Detection (step 1 of 4)

```
◆ Detection (step 1 of 4 — hardware profiling)
··································································
  Hardware detected:      √ pass — macOS 14, Apple M2
  GPU identified:         √ pass — Apple Metal (unified memory)
  RAM measured:           √ pass — 16GB unified memory
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Analysis (step 2 of 4)

```
◆ Analysis (step 2 of 4 — profile selection)
··································································
  Tier classified:        √ pass — Prosumer (16GB unified)
  Profile selected:       √ pass — Flash attention, full offload
  Bottlenecks identified: √ pass — memory bandwidth primary constraint
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Plan (step 3 of 4)

```
◆ Plan (step 3 of 4 — optimization guide)
··································································
  Guide generated:        √ pass — ollama-optimization-guide.md written
  Parameters tuned:       √ pass — OLLAMA_FLASH_ATTENTION=1, KV_CACHE_TYPE=q8_0
  Model recommendations ready: √ pass — llama3.1:14b-instruct-q4_K_M suggested
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Verification (step 4 of 4)

```
◆ Verification (step 4 of 4 — config validation)
··································································
  Benchmark commands listed: √ pass — python3 scripts/benchmark_ollama.py
  Config verified:        √ pass — ollama run --verbose output checked
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

## Reference Files

- [VRAM Requirements](references/vram_requirements.md) - Model sizing and quantization guide
- [Environment Variables](references/environment_variables.md) - Complete env var reference
- [Platform-Specific Setup](references/platform_specific.md) - OS-specific installation and configuration

## Output Format

Generate an `ollama-optimization-guide.md` file. Ask the user where to save it (suggest `~/.config/ollama/optimization-guide.md` or current directory). Contents:

```markdown
# Ollama Optimization Guide

**Generated:** <timestamp>
**System:** <OS> | <CPU> | <RAM>GB RAM | <GPU>

## System Overview
<hardware summary and constraints>

## Current Configuration
<existing Ollama setup and env vars>

## Recommendations

### Environment Variables
<shell commands to set vars>

### Model Selection
<recommended models with rationale>

### Performance Tuning
<Modelfile adjustments if needed>

## Execution Checklist
- [ ] <step 1>
- [ ] <step 2>
...

## Verification
<benchmark commands and expected results>

## Rollback
<commands to revert changes if needed>
```

## Quick Optimization Commands

For users who want immediate results without full analysis:

**macOS (Apple Silicon):**
```bash
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
ollama pull llama3.2:3b  # Safe for 8GB, fast
```

**Linux/Windows with 8GB NVIDIA GPU:**
```bash
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
ollama pull llama3.1:8b-instruct-q4_K_M
```

**CPU-only systems:**
```bash
export CUDA_VISIBLE_DEVICES=-1
ollama pull llama3.2:3b
# Create Modelfile with: PARAMETER num_thread 4
```
