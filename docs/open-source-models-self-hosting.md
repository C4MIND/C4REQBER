# TURBO-CDI v5.3.1 — Open-Source Model Guide for Self-Hosting

> **Date:** May 14, 2026 | **Source:** OpenRouter, HuggingFace, Artificial Analysis, vLLM recipes
> **Platforms:** NVIDIA GPU · AMD GPU · Apple Silicon (M1–M4) · CPU-only

---

## Executive Summary

Self-hosting frontier AI is now practical on consumer hardware — including MacBooks. Apache 2.0 and MIT-licensed models from DeepSeek, Alibaba (Qwen), Google (Gemma), NVIDIA (Nemotron), Mistral, and Moonshot (Kimi) deliver frontier-quality reasoning, coding, and agentic capabilities at zero per-token cost.

**Key takeaway (GPU):** A Qwen 3.6-35B-A3B on a single RTX 4090 achieves 44-196 tok/s with 73.4% SWE-bench.
**Key takeaway (Mac):** A Mac M3 Ultra 192GB runs Qwen 3.5-122B-A10B at 10+ tok/s — cloud-competitive quality on a desk.

---

## Mac Quick Start

```bash
# 1. Install Ollama (1 click!)
brew install ollama              # or download from ollama.com
ollama serve                     # start background service

# 2. Pull models (auto-detects Metal/MLX)
ollama pull qwen3.6:35b-a3b      # 22GB — M1 Max 64GB+, M2/M3 Pro 32GB+
ollama pull qwen3.6:27b          # 16GB — M1 Pro 32GB+, any M2/M3 24GB+
ollama pull gemma4:26b           # 15GB — any M2/M3 24GB+
ollama pull deepseek-r1:32b      # 20GB — M1 Max 64GB+, M2/M3 Pro 32GB+

# 3. OpenAI-compatible on http://localhost:11434/v1
# Use in TURBO-CDI: export API_BASE_URL=http://localhost:11434/v1
```

---

## Apple Silicon: What Makes It Different

| Concept | NVIDIA GPU | Apple Silicon |
|---------|-----------|---------------|
| **Memory type** | Dedicated VRAM (24GB RTX 4090) | Unified memory (CPU+GPU share) |
| **Max memory** | 24GB (consumer) / 48GB (pro) | 192GB (M3 Ultra) |
| **Memory bandwidth** | 1TB/s (RTX 4090) | 800GB/s (M3 Ultra) |
| **Framework** | CUDA (NVIDIA only) | **MLX** (Apple-native, 2x llama.cpp) |
| **Quantization** | GGUF via llama.cpp | MLX-format via mlx-lm |
| **Inference speed** | 100-200 tok/s (consumer) | 20-80 tok/s (same model) |
| **Advantage** | Raw speed | **Fit bigger models** (192GB!) |

> Mac unified memory is the secret weapon: a 192GB M3 Ultra can run Qwen 122B at Q4 that needs 4× RTX 4090s. Slower, but 1/10th the cost and all on one desk.

---

## Mac Hardware Tiers

### Tier 1: MacBook Air / Base M1–M2 (8–16 GB)

| Model | Unified RAM | Best Model | Speed |
|-------|-----------|------------|-------|
| M1/M2 Air 8GB | 8 GB | ✗ too small for LLMs | — |
| M1/M2 Air 16GB | 16 GB | Qwen 3.6-35B-A3B IQ3_XS (15GB) | ~8 tok/s |
| M1 Pro 16GB | 16 GB | Gemma 4 26B MoE Q4 (15GB) | ~15 tok/s |

> **16GB Air warning:** IQ3_XS quantization leaves almost no room for context. Use 8-16K context max. For daily driving, use cloud API or upgrade to 24GB+.

### Tier 2: M2/M3 Pro, M1/M2 Max (24–64 GB)

| Model | Unified RAM | Models that fit | Best Pick |
|-------|-----------|-----------------|-----------|
| M2/M3 24GB | 24 GB | 27B Q4 (17GB), 35B IQ4_XS (15GB), Gemma 4 26B (16GB) | Gemma 4 26B + context |
| M1/M2 Pro 32GB | 32 GB | 27B Q4 (17GB), 35B Q4 (22GB), R1-32B Q4 (20GB) | Qwen 3.6-35B-A3B Q4 |
| M1/M2 Max 64GB | 64 GB | 35B Q8 (38GB), 122B Q3 (59GB) | Qwen 3.5-122B Q3 |

```bash
# M2 Pro 32GB — sweet spot for Mac users
ollama pull qwen3.6:35b-a3b       # primary workhorse
ollama pull qwen3.6:27b            # reasoning
ollama pull gemma4:26b             # cheap/fast
```

### Tier 3: M2/M3 Ultra, M4 Max (96–256 GB)

| Model | Unified RAM | Models that fit | Speed |
|-------|-----------|-----------------|-------|
| M3 Ultra 96GB | 96 GB | 122B Q4 (74GB) | ~8-12 tok/s |
| M3 Ultra 128GB | 128 GB | 122B Q5 (87GB) | ~8-12 tok/s |
| M3 Ultra 192GB | 192 GB | 122B Q8 (132GB), 397B Q3 (160GB) | ~5-8 tok/s |
| M3 Ultra 256GB | 256 GB | 397B Q4 (220GB) | ~4-6 tok/s |

```bash
# M3 Ultra 192GB — runs models that need 8× H100 in the cloud
ollama pull qwen3.5:122b           # 122B MoE at home
ollama pull qwen3.5:397b           # 397B flagship — yes, really
```

---

## MLX: Apple's Native Framework (2x Faster)

MLX is Apple's machine learning framework designed specifically for Apple Silicon. For LLMs, it's **2x faster** than llama.cpp on the same hardware.

```bash
# Install MLX
pip install mlx-lm mlx-vlm

# Download MLX-format models (HF repos ending with -MLX)
huggingface-cli download mlx-community/Qwen3.6-35B-A3B-4bit \
  --local-dir ~/models/qwen3.6-35b-mlx

# Serve via mlx-lm (OpenAI-compatible API at :8001)
python -m mlx_lm.server --model ~/models/qwen3.6-35b-mlx --port 8001

# TURBO-CDI config: export API_BASE_URL=http://localhost:8001/v1
```

### MLX Speed Comparison (M3 Ultra)

| Model | llama.cpp | MLX | Speedup |
|-------|----------|-----|---------|
| Qwen 3.6-35B Q4 | 22 tok/s | 44 tok/s | **2x** |
| Qwen 3.5-122B Q4 | 6 tok/s | 12 tok/s | **2x** |
| DeepSeek R1-32B Q4 | 18 tok/s | 35 tok/s | **1.9x** |

> Always prefer MLX on Apple Silicon. Only fall back to llama.cpp if MLX model files aren't available.

---

## GPU Tiers (NVIDIA / AMD)

### Tier 1: Consumer GPU (8–24 GB VRAM)

#### Best Overall: Qwen 3.6-35B-A3B (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | MoE — 35B total / 3B active per token |
| SWE-bench Verified | 73.4% (#1 open-weight under 40B) |
| Context | 262K native, 1M via YaRN |
| Q4_K_M Size | 21.2 GB |
| Speed (RTX 4090) | 44 tok/s |
| License | Apache 2.0 |

```bash
ollama pull qwen3.6:35b-a3b
```

#### Best Reasoning: Qwen 3.6-27B Dense (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | Dense 27B |
| Q4 Size | 16.5 GB |
| License | Apache 2.0 |

#### Best Small: Gemma 4 26B MoE (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | MoE — 25.2B total / 3.8B active |
| AIME 2026 | 88.3% |
| GPQA Diamond | 82.3% |
| Q4 Size | ~15 GB |
| Cost (OpenRouter) | $0.06/1M input — cheapest frontier-adjacent |

```bash
ollama pull gemma4:26b
```

#### Best Coding: DeepSeek R1-Distill-Qwen-32B (MIT)

| Spec | Value |
|------|-------|
| Architecture | Dense 32B |
| GPQA Diamond | ~81% |
| Q4 Size | ~20 GB |
| License | MIT |

---

### Tier 2: Prosumer / Multi-GPU (24–80 GB VRAM)

#### Qwen 3.6-122B-A10B MoE (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | MoE — 122B total / 10B active |
| SWE-bench | 72.0% |
| Q4 Size | 74.4 GB |
| Hardware | Mac 96GB+ or 4× RTX 4090 |

#### DeepSeek V4-Flash (MIT) ★

| Spec | Value |
|------|-------|
| Architecture | MoE — 284B total / 13B active |
| SWE-bench Verified | 79.0% |
| Context | 1,000,000 tokens |
| FP4 Size | 158 GB |
| Hardware | 1× H200 or 2× A100 80GB or 4× RTX 4090 (INT4) |
| Inference | vLLM 0.20+, SGLang, llama.cpp (experimental) |

```bash
ollama pull deepseek-v4-flash:cloud          # cloud-hosted via Ollama
vllm serve deepseek-ai/DeepSeek-V4-Flash --tensor-parallel-size 4
```

#### GLM-5.1 (MIT)

| Spec | Value |
|------|-------|
| Architecture | MoE — 754B total / 40B active |
| SWE-bench Pro | 58.4% (#1 globally at launch) |
| Hardware | 4–8× A100/H100 |
| License | MIT |

#### Mistral Small 4 (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | MoE — 119B total / 6.5B active |
| Multimodal | Native text + image |
| Q4 Size | ~48 GB |
| License | Apache 2.0 |

---

### Tier 3: Datacenter / Cluster (160 GB+ VRAM)

#### DeepSeek V4-Pro (MIT) ★

| Spec | Value |
|------|-------|
| Architecture | MoE — 1.6T total / 49B active |
| SWE-bench Verified | 80.6% |
| LiveCodeBench | 93.5% |
| GPQA Diamond | 90.1% |
| Context | 1,000,000 tokens |
| Hardware | 8× B200 or 8× H200 |
| Pricing (API) | $0.435/$0.87 (promo), $1.74/$3.48 (list) |

```bash
vllm serve deepseek-ai/DeepSeek-V4-Pro -dp 8 --enable-expert-parallel
```

#### Qwen 3.5-397B-A17B (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | MoE — 397B total / 17B active |
| Q4 Size | 220 GB |
| Hardware | 8× H100/H200 |

#### Meta Llama 4 Scout (Llama 4 Community License)

| Spec | Value |
|------|-------|
| Architecture | 17B active, 10M context |
| Q4 Size | 48–80 GB |
| License | Llama 4 Community (restricted — no >700M MAU) |

#### Qwen 3.6 Max Preview (API-only)

| Spec | Value |
|------|-------|
| Architecture | MoE ≈1T total |
| SWE-bench Pro | 57.3% |
| Pricing | $1.04/$6.24 per 1M tokens |
| License | Closed-weight (API only) |

---

## Deployment Frameworks

| Framework | Best For | GPU | Apple Silicon | Notes |
|-----------|----------|-----|---------------|-------|
| **Ollama** | Quick dev | ✅ CUDA | ✅ Metal/MLX | 1 command. OpenAI-compat. Ships with Mac app |
| **MLX** (mlx-lm) | **Mac only** | ❌ | ✅ **Native** | 2x llama.cpp. Apple's framework |
| **LM Studio** | GUI | ✅ CUDA | ✅ MLX | Drag-drop GGUF. Built-in model browser |
| **vLLM** | Production serving | ✅ NVIDIA/AMD/Intel | ❌ | Expert parallelism. 200+ architectures |
| **SGLang** | Structured gen | ✅ NVIDIA | ❌ | Advanced prompt control, MoE |
| **llama.cpp** | Max control | ✅ All GPUs | ✅ Metal | GGUF quants. CPU fallback |
| **Graviton** | **Mac 500B+** | ❌ | ✅ **Streaming quant** | 144 GB→36 GB. Apache 2.0 |
| **KTransformers** | CPU-GPU hybrid | ✅ mixed | ❌ | Offloads experts to RAM |
| **LocalAI** | All-in-one | ✅ All | ✅ All | 35+ backends, MCP agents. MIT |
| **MoE Sovereign** | Distributed | ✅ 8GB+ | ✅ | Federated knowledge, Apache 2.0 |

---

## VRAM / Memory Requirements: Quick Reference

| Model | Q4_K_M | Q8 | GPU Minimum | Mac Minimum |
|-------|--------|----|-----------|-----------|
| Qwen 3.6-35B-A3B | 22 GB | 38 GB | RTX 4090 24GB | M1 Max 64GB |
| Qwen 3.6-27B | 17 GB | 28 GB | RTX 4060 Ti 16GB | M1 Pro 32GB |
| Gemma 4 31B | 20 GB | 31 GB | RTX 4090 24GB | M1 Max 64GB |
| Gemma 4 26B MoE | 16 GB | 24 GB | RTX 4060 Ti 16GB | M2/M3 24GB |
| DeepSeek R1-Distill-32B | 20 GB | 35 GB | RTX 4090 24GB | M1 Max 64GB |
| Mistral Small 4 | 48 GB | 90 GB | A6000 / 2× 4090 | M2 Ultra 64GB |
| Qwen 3.5-122B-A10B | 74 GB | 128 GB | 4× RTX 4090 | M3 Ultra 96GB |
| DeepSeek V4-Flash | 158 GB* | — | 2× A100 80GB | ❌ |
| DeepSeek V4-Pro | FP4 only | — | 8× B200/H200 | ❌ |
| GLM-5.1 | 320 GB+ | — | 4–8× A100/H100 | ❌ |

*FP4+FP8 mixed precision. ❌ = not practical on that platform.

---

## License Guide (Self-Hosting)

| License | Models | Restrictions |
|---------|--------|-------------|
| **Apache 2.0** | Qwen 3.5/3.6, Gemma 4, Mistral Small 4/Large 3, Nemotron | Patent grant. Commercial OK |
| **MIT** | DeepSeek V3.2/V4/R1, GLM-5.1, R1-Distill | Most permissive |
| **Modified MIT** | Kimi K2.6 | Near-MIT with modifications |
| **NVIDIA Open** | Nemotron 3 Super/Nano | Permissive, full recipes |
| **Llama 4 Community** | Llama 4 Scout/Maverick | >700M MAU blocked |

---

## Recommended Setup for TURBO-CDI

### Mac Setup (M2 Pro 32GB — Sweet Spot)

```bash
# Install models
ollama pull qwen3.6:35b-a3b       # primary workhorse — 22GB fits
ollama pull qwen3.6:27b            # reasoning — 17GB
ollama pull gemma4:26b             # cheap/fast — 15GB

# TURBO-CDI config
export PHASE_A_MODEL=qwen3.6:27b
export PHASE_B_MODEL=gemma4:26b
export PHASE_D_MODEL=qwen3.6:35b-a3b
export PHASE_G_MODEL=gemma4:26b
export API_BASE_URL=http://localhost:11434/v1
```

### Mac Setup (M3 Ultra 192GB — Max Power)

```bash
ollama pull qwen3.5:122b           # 122B MoE — at home!
ollama pull qwen3.6:35b-a3b        # primary workhorse (fast)
ollama pull deepseek-r1:32b        # reasoning

export PHASE_A_MODEL=qwen3.6:35b-a3b
export PHASE_D_MODEL=qwen3.5:122b
export PHASE_F_MODEL=qwen3.5:122b
export PHASE_G_MODEL=gemma4:26b
```

### GPU Setup (RTX 4090 24GB)

```bash
ollama pull qwen3.6:35b-a3b       # General workhorse
ollama pull qwen3.6:27b            # Reasoning
ollama pull gemma4:26b             # Cheap validation
ollama pull deepseek-r1:32b        # Reasoning backup

export PHASE_A_MODEL=qwen3.6:27b
export PHASE_B_MODEL=gemma4:26b
export PHASE_D_MODEL=qwen3.6:35b-a3b
export PHASE_G_MODEL=gemma4:26b
export API_BASE_URL=http://localhost:11434/v1
```

### Phase Analysis — Per Platform

| Phase | GPU (RTX 4090) | Mac (M2 Pro 32GB) | Mac (M3 Ultra 192GB) |
|-------|----------------|-------------------|---------------------|
| A (C4) | Qwen 3.6-27B | Qwen 3.6-27B | Qwen 3.6-35B-A3B |
| B (Search) | Gemma 4 26B | Gemma 4 26B | Gemma 4 26B |
| C (Gaps) | Qwen 3.6-35B | Qwen 3.6-35B Q4 | Qwen 3.5-122B |
| D (Hyp) | Qwen 3.6-27B | Qwen 3.6-35B | Qwen 3.5-122B |
| E (Sim) | compute | compute | compute |
| F (Dissert) | Qwen 3.6-35B | Qwen 3.6-35B | Qwen 3.5-122B |
| G (Quality) | Gemma 4 26B | Gemma 4 26B | Gemma 4 26B |

### Cloud Fallback (when local can't handle it)

```bash
export PHASE_D_MODEL=deepseek/deepseek-v4-pro      # $0.44/M — frontier
export PHASE_F_MODEL=deepseek/deepseek-v4-pro
export PHASE_G_MODEL=deepseek/deepseek-v4-flash    # $0.14/M — cheapest frontier
export OPENROUTER_API_KEY=sk-or-...
```

---

## Mac Tips

### Memory Pressure

```bash
# Check memory pressure before loading a big model
memory_pressure          # green=OK, yellow=warning, red=will throttle

# For 192GB M3 Ultra loading 122B Q4 (74GB):
#   Used: ~74GB model + ~4GB context + ~6GB OS = ~84GB
#   Free: ~108GB. Green zone.
```

### Power & Throttling

| Mac | Thermal Throttling | Mitigation |
|-----|-------------------|------------|
| MacBook Air | Yes — no fan | Limit to 4K context, use IQ3 | 
| MacBook Pro 14" | Light at 15+ min | External monitor raises GPU clock 20% |
| MacBook Pro 16" | Rare | Better thermals than 14" |
| Mac Studio / Mini | None | Desktop thermals — full speed sustained |

### Disk Space

```bash
# Q4 models in ~/.ollama/models/
# All 4 recommended models: ~65GB total
du -sh ~/.ollama/models/
# Cleanup old models: ollama rm model-name
```

### Performance

```bash
# LM Studio MLX mode (fastest Mac GUI)
# 1. Download LM Studio from lmstudio.ai
# 2. Search for "qwen3.6 35b mlx" in model browser
# 3. Load → Toggle MLX in right sidebar
# 4. Start server → http://localhost:1234/v1
```

### Best Overall: Qwen 3.6-35B-A3B (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | MoE — 35B total / 3B active per token |
| SWE-bench Verified | 73.4% (#1 open-weight under 40B) |
| Context | 262K native, 1M via YaRN |
| Q4_K_M Size | 21.2 GB |
| Speed (RTX 4090) | 44 tok/s |
| License | Apache 2.0 |

```bash
ollama pull qwen3.6:35b-a3b
```

### Best Reasoning: Qwen 3.6-27B Dense (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | Dense 27B |
| Q4 Size | 16.5 GB |
| License | Apache 2.0 |

### Best Small: Gemma 4 26B MoE (Apache 2.0)

| Spec | Value |
|------|-------|
| Architecture | MoE — 25.2B total / 3.8B active |
| AIME 2026 | 88.3% |
| GPQA Diamond | 82.3% |
| Q4 Size | ~15 GB |
| Cost (OpenRouter) | $0.06/1M input — cheapest frontier-adjacent |

```bash
ollama pull gemma4:26b
```

### Best Coding: DeepSeek R1-Distill-Qwen-32B (MIT)

| Spec | Value |
|------|-------|
| Architecture | Dense 32B |
| GPQA Diamond | ~81% |
| Q4 Size | ~20 GB |
| License | MIT |

---

