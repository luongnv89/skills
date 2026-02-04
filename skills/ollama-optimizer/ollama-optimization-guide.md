# Ollama Optimization Guide

**Generated:** 2026-02-04
**System:** macOS Darwin 25.2.0 | Apple M1 Max | 32GB Unified Memory | Metal GPU
**Target Model:** gpt-oss:20b (13GB)

## System Overview

Your **Apple M1 Max with 32GB unified memory** is a **workstation-tier** system capable of running models up to 32B parameters efficiently.

| Spec | Value | Impact |
|------|-------|--------|
| CPU | Apple M1 Max (8P + 2E cores) | Excellent single-threaded performance |
| Memory | 32GB Unified | ~24GB effective GPU memory |
| GPU | Metal (integrated) | 100% GPU offload possible |
| Storage | 49GB available | Adequate for multiple models |

**gpt-oss:20b Analysis:**
- Model size: 13GB on disk, ~14GB loaded
- Current status: 100% GPU offload ✓
- Context window: 32K tokens (using ~1-2GB additional)
- **Verdict:** Your hardware can comfortably run this model

## Current Configuration

Your current environment variables:
```bash
OLLAMA_KEEP_ALIVE=5m        # Model stays loaded 5 minutes
OLLAMA_NUM_PARALLEL=2       # 2 concurrent requests
OLLAMA_FLASH_ATTENTION=1    # ✓ Already enabled
```

**What's working well:**
- Flash attention is enabled (good for memory efficiency)
- Model is fully GPU-offloaded (100% GPU)

**What can be improved:**
- Keep-alive is short for a 20B model (cold starts cost ~7.7s)
- No KV cache quantization (could reduce memory further)
- Parallel requests may limit throughput with large models

## Recommendations

### 1. Environment Variables

Create or update your shell configuration (`~/.zshrc` or `~/.bashrc`):

```bash
# Essential optimizations
export OLLAMA_FLASH_ATTENTION=1

# Increase keep-alive to avoid cold starts (model takes ~8s to load)
export OLLAMA_KEEP_ALIVE=30m

# KV cache quantization - saves memory, minimal quality loss
export OLLAMA_KV_CACHE_TYPE=q8_0

# Reduce parallel requests for large models (prevents memory pressure)
export OLLAMA_NUM_PARALLEL=1

# Reserve memory for system overhead
export OLLAMA_GPU_OVERHEAD=512m
```

For the Ollama desktop app (launchd), also run:
```bash
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_KEEP_ALIVE 30m
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
launchctl setenv OLLAMA_NUM_PARALLEL 1
launchctl setenv OLLAMA_GPU_OVERHEAD 512m
```

### 2. Model Configuration (Modelfile)

Create an optimized Modelfile for gpt-oss:20b:

```bash
cat > ~/gpt-oss-optimized.Modelfile << 'EOF'
FROM gpt-oss:20b

# Context window - 32K is fine for your RAM, reduce if needed
PARAMETER num_ctx 32768

# Temperature and sampling (adjust to taste)
PARAMETER temperature 0.7
PARAMETER top_p 0.9

# Ensure full GPU offload (automatic on Apple Silicon, but explicit is safer)
PARAMETER num_gpu 99
EOF
```

Create the optimized model:
```bash
ollama create gpt-oss-optimized -f ~/gpt-oss-optimized.Modelfile
```

### 3. Context Window Tuning

Your 32K context uses ~1.5-2GB memory. If you need to run other apps alongside:

| Context | Memory Saved | Use Case |
|---------|--------------|----------|
| 32768 (current) | Baseline | Full document analysis |
| 16384 | ~0.8GB | Most conversations |
| 8192 | ~1.2GB | Short interactions |
| 4096 | ~1.5GB | Quick Q&A |

To reduce context temporarily:
```bash
ollama run gpt-oss:20b --num-ctx 8192
```

## Execution Checklist

- [ ] **Step 1:** Add environment variables to `~/.zshrc`:
  ```bash
  echo 'export OLLAMA_FLASH_ATTENTION=1' >> ~/.zshrc
  echo 'export OLLAMA_KEEP_ALIVE=30m' >> ~/.zshrc
  echo 'export OLLAMA_KV_CACHE_TYPE=q8_0' >> ~/.zshrc
  echo 'export OLLAMA_NUM_PARALLEL=1' >> ~/.zshrc
  ```

- [ ] **Step 2:** Reload shell configuration:
  ```bash
  source ~/.zshrc
  ```

- [ ] **Step 3:** Set launchd variables (for Ollama.app):
  ```bash
  launchctl setenv OLLAMA_FLASH_ATTENTION 1
  launchctl setenv OLLAMA_KEEP_ALIVE 30m
  launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
  ```

- [ ] **Step 4:** Restart Ollama:
  ```bash
  # If using Ollama.app, quit and reopen it
  # Or if using CLI:
  pkill ollama && ollama serve &
  ```

- [ ] **Step 5:** Verify model loads with new settings:
  ```bash
  ollama run gpt-oss:20b "Hello" --verbose 2>&1 | head -30
  ```

- [ ] **Step 6:** Run benchmark to compare:
  ```bash
  python3 scripts/benchmark_ollama.py --model gpt-oss:20b --runs 3
  ```

## Verification

After applying optimizations, verify with:

```bash
# Check environment variables are set
echo $OLLAMA_FLASH_ATTENTION
echo $OLLAMA_KV_CACHE_TYPE
echo $OLLAMA_KEEP_ALIVE

# Check model is using GPU
ollama ps

# Run verbose test
ollama run gpt-oss:20b "Explain quantum computing briefly" --verbose

# Full benchmark
python3 scripts/benchmark_ollama.py --model gpt-oss:20b
```

**Expected improvements:**
- Cold start: Should remain ~7-8s (hardware limited)
- Warm inference: ~2500-2800 tokens/sec (already good)
- Memory pressure: Reduced with KV cache q8_0
- Stability: Fewer OOM issues with GPU overhead reservation

## Memory Budget

With optimizations applied:

| Component | Memory Usage |
|-----------|--------------|
| System/OS | ~4GB |
| Ollama + gpt-oss:20b | ~14GB |
| KV Cache (32K ctx, q8_0) | ~1.5GB |
| GPU Overhead Reserve | 0.5GB |
| **Available for other apps** | **~12GB** |

## Rollback

If you experience issues, revert to defaults:

```bash
# Remove from ~/.zshrc (manual edit) or:
unset OLLAMA_KV_CACHE_TYPE
unset OLLAMA_GPU_OVERHEAD

# Reset launchd
launchctl unsetenv OLLAMA_KV_CACHE_TYPE
launchctl unsetenv OLLAMA_GPU_OVERHEAD

# Restart Ollama
pkill ollama && ollama serve &
```

## Additional Tips for gpt-oss:20b

1. **Warm-up strategy:** Run a quick prompt after loading to ensure the model is fully cached
2. **Batch processing:** If processing many prompts, keep the model loaded with `OLLAMA_KEEP_ALIVE=-1` (forever)
3. **Multi-model usage:** With 32GB, you could theoretically run gpt-oss:20b alongside a smaller model like llama3.1:8b, but monitor memory closely
