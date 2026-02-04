# VRAM Requirements and Model Selection

## VRAM Tiers and Recommended Models

| VRAM | Capability | Recommended Models |
|------|-----------|-------------------|
| 3-4GB | Small models (Q4_K_M) at moderate contexts | Llama 3.2 3B, Qwen 3 4B, Phi-3 Mini |
| 6-8GB | 7-8B models, 40+ tokens/sec | Llama 3.1 8B, Qwen 3 8B, Mistral 7B |
| 10-12GB | 12-14B models with extended contexts | Gemma 3 12B, DeepSeek-R1-Qwen-14B |
| 16-24GB | 27-32B models | Gemma 3 27B, Qwen 3 32B, Mixtral 8x7B |
| 48GB+ | 70B+ workstation inference | Llama 3.3 70B, Qwen 2.5 72B |

## Apple Silicon Unified Memory

Apple Silicon Macs share RAM between CPU and GPU (unified memory). The effective VRAM depends on total system RAM:

| System RAM | Effective GPU Memory | Max Model Size |
|------------|---------------------|----------------|
| 8GB | ~6GB usable | 7B Q4_K_M |
| 16GB | ~12GB usable | 14B Q4_K_M |
| 32GB | ~24GB usable | 32B Q4_K_M |
| 64GB | ~48GB usable | 70B Q4_K_M |
| 128GB | ~100GB usable | 70B Q5+ or multiple models |

## Quantization Guide

| Quantization | Quality | VRAM Usage | Use Case |
|--------------|---------|------------|----------|
| Q2_K | Poor | Minimal | Not recommended |
| Q3_K_S/M | Degraded | Very Low | Extreme memory constraints |
| **Q4_K_M** | **Good** | **Optimal** | **Default recommendation** |
| Q5_K_M | Very Good | +15-20% | Quality-focused tasks |
| Q6_K | Excellent | +30-40% | Near-original quality |
| Q8_0 | Near-perfect | +60-80% | Quality-critical tasks |
| FP16 | Original | Maximum | Research/comparison only |

## Model Size Estimation Formula

Approximate VRAM needed:
```
VRAM (GB) ≈ (Parameters in B × Bits per Weight) / 8 + Context Overhead

Examples:
- 7B Q4 model: (7 × 4) / 8 ≈ 3.5GB base + 1-2GB context = 4.5-5.5GB
- 14B Q4 model: (14 × 4) / 8 ≈ 7GB base + 2-3GB context = 9-10GB
- 70B Q4 model: (70 × 4) / 8 ≈ 35GB base + 4-6GB context = 39-41GB
```

## Context Length Impact

KV cache memory scales linearly with context length:
- 4K context: baseline
- 8K context: +0.2-0.4GB
- 16K context: +0.4-0.8GB
- 32K context: +0.8-1.6GB
- 128K context: +3-6GB (model dependent)

Reduce context length if memory is constrained.
