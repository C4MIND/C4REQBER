"""C4REQBER Model Catalog v5.4.0 — May 2026.

Comprehensive model selection for every pipeline stage, budget, and use case.
Based on: OpenRouter rankings, Artificial Analysis, BenchLM, HuggingFace,
CodeSOTA, SWE-bench Verified, GPQA Diamond, LiveCodeBench.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# Tier definitions
# ═══════════════════════════════════════════════════════════════════════════════

class Tier:
    """Tier."""
    FRONTIER = "frontier"         # Top 3 globally — $15-30/1M out
    PREMIUM = "premium"            # Top 10 — $3-15/1M out
    BALANCED = "balanced"          # Strong general-purpose — $1-3/1M out
    BUDGET = "budget"              # Good quality, low cost — $0.3-1/1M out
    ULTRA_BUDGET = "ultra_budget"  # Cheapest — <$0.3/1M out
    FREE = "free"                  # Free on OpenRouter
    LOCAL = "local"                # Open-weight, self-hosted


@dataclass
class ModelEntry:
    """ModelEntry."""
    id: str
    provider: str
    tier: str
    cost_in: float       # $/1M tokens
    cost_out: float      # $/1M tokens
    context: int         # context window
    strengths: list[str] = field(default_factory=list)
    benchmarks: dict[str, float] = field(default_factory=dict)
    open_weight: bool = False
    license_: str = ""
    notes: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Model Catalog — May 2026
# ═══════════════════════════════════════════════════════════════════════════════

CATALOG: dict[str, ModelEntry] = {
    # ── FRONTIER (Top 3 globally) ──────────────────────────────────────────
    "claude-sonnet-4.6": ModelEntry(
        id="anthropic/claude-sonnet-4.6",
        provider="Anthropic",
        tier=Tier.PREMIUM,
        cost_in=3.0, cost_out=15.0, context=1_000_000,
        strengths=["reasoning", "coding", "agent-planning", "academic-writing", "safety"],
        benchmarks={"SWE-bench": 79.6, "MMLU-Pro": 89.7, "GPQA": 89.9, "LiveCodeBench": 80.0},
        notes="Best all-rounder. 1M context. Strongest for academic writing + hypothesis generation.",
    ),
    "claude-opus-4.6": ModelEntry(
        id="anthropic/claude-opus-4.6",
        provider="Anthropic",
        tier=Tier.FRONTIER,
        cost_in=5.0, cost_out=25.0, context=1_000_000,
        strengths=["deep-reasoning", "complex-coding", "safety", "multi-step-planning"],
        benchmarks={"SWE-bench": 80.8, "MMLU-Pro": 92.1, "GPQA": 91.3, "AIME": 80.0},
        notes="Anthropic flagship. Best for complex multi-step reasoning. Higher cost justified for dissertation quality.",
    ),
    "gemini-3.1-pro": ModelEntry(
        id="google/gemini-3.1-pro",
        provider="Google",
        tier=Tier.FRONTIER,
        cost_in=2.0, cost_out=12.0, context=1_000_000,
        strengths=["multimodal", "reasoning", "coding", "speed", "multilingual"],
        benchmarks={"SWE-bench": 80.6, "MMLU-Pro": 89.8, "GPQA": 91.9, "LiveCodeBench": 91.7},
        notes="Best value frontier. 1M context. Beats Claude on GPQA. Strong multimodal.",
    ),

    # ── PREMIUM (Top 10) ───────────────────────────────────────────────────
    "gpt-5.4": ModelEntry(
        id="openai/gpt-5.4",
        provider="OpenAI",
        tier=Tier.PREMIUM,
        cost_in=2.5, cost_out=15.0, context=200_000,
        strengths=["coding", "reasoning", "tool-use", "json-mode"],
        benchmarks={"SWE-bench": 78.2, "MMLU-Pro": 91.8, "GPQA": 72.8},
        notes="OpenAI workhorse. Strong coding + tool use. 200K context (less than Claude).",
    ),
    "qwen-3.6-plus": ModelEntry(
        id="qwen/qwen-3.6-plus",
        provider="Alibaba (Qwen)",
        tier=Tier.BALANCED,
        cost_in=0.33, cost_out=1.95, context=256_000,
        strengths=["multilingual", "reasoning", "coding", "efficiency"],
        benchmarks={"SWE-bench": 78.8, "LiveCodeBench": 80.4, "AIME": 92.7},
        notes="#5 on OpenRouter. Best performance-per-dollar. 28 apps use it as #1 model. Free preview period.",
    ),

    # ── BALANCED (Best value) ──────────────────────────────────────────────
    "deepseek-v3.2": ModelEntry(
        id="deepseek/deepseek-v3.2",
        provider="DeepSeek",
        tier=Tier.BUDGET,
        cost_in=0.25, cost_out=0.38, context=128_000,
        strengths=["reasoning", "coding", "math", "cost-efficiency"],
        benchmarks={"SWE-bench": 48.3, "MMLU-Pro": 87.2, "GPQA": 71.6, "AIME": 73.3},
        notes="90% GPT-5.4 quality at 1/50th cost. MIT license open weights. DeepSeek API.",
    ),
    "deepseek-v4-pro": ModelEntry(
        id="deepseek/deepseek-v4-pro",
        provider="DeepSeek",
        tier=Tier.PREMIUM,
        cost_in=0.435, cost_out=0.87, context=1_000_000,
        strengths=["coding", "reasoning", "agentic", "math", "long-context", "open-weight"],
        benchmarks={"SWE-bench": 80.6, "LiveCodeBench": 93.5, "GPQA": 90.1, "MMLU-Pro": 87.5, "Codeforces": 3206},
        open_weight=True, license_="MIT",
        notes="Frontier coding (80.6 SWE-bench). Promo $0.435/$0.87 till May 31 (list $1.74/$3.48). 1.6T/49B MoE. MIT.",
    ),
    "deepseek-v4-flash": ModelEntry(
        id="deepseek/deepseek-v4-flash",
        provider="DeepSeek",
        tier=Tier.ULTRA_BUDGET,
        cost_in=0.14, cost_out=0.28, context=1_000_000,
        strengths=["coding", "cost", "long-context", "reasoning", "open-weight"],
        benchmarks={"SWE-bench": 79.0, "LiveCodeBench": 91.6},
        open_weight=True, license_="MIT",
        notes="Cheapest frontier-adjacent. 284B/13B MoE. $0.14/$0.28. 1M ctx. MIT. #1 value pick.",
    ),
    "kimi-k2.6": ModelEntry(
        id="moonshotai/kimi-k2.6",
        provider="Moonshot AI",
        tier=Tier.PREMIUM,
        cost_in=0.75, cost_out=3.50, context=256_000,
        strengths=["agentic", "coding", "swarm", "long-horizon", "multimodal", "open-weight"],
        benchmarks={"SWE-bench-Pro": 58.6, "SWE-bench": 80.2, "HLE-tools": 54.0, "GPQA": 90.5, "AIME": 96.4, "LiveCodeBench": 89.6},
        open_weight=True, license_="Modified MIT",
        notes="#1 open-weight agentic. 300-agent swarms. 12h autonomous runs. 1T/32B MoE. OpenRouter: $0.75/$3.50.",
    ),
    "glm-5.1": ModelEntry(
        id="z-ai/glm-5.1",
        provider="Zhipu AI (Z.ai)",
        tier=Tier.PREMIUM,
        cost_in=1.05, cost_out=3.50, context=200_000,
        strengths=["agentic", "coding", "long-horizon", "reasoning", "open-weight"],
        benchmarks={"SWE-bench-Pro": 58.4, "GPQA": 86.2, "AIME": 95.3, "HLE-tools": 52.3},
        open_weight=True, license_="MIT",
        notes="#1 SWE-bench Pro at launch. 754B/40B MoE. 8h autonomous. MIT. Trained on Huawei Ascend.",
    ),
    "nemotron-3-super": ModelEntry(
        id="nvidia/nemotron-3-super-120b-a12b",
        provider="NVIDIA",
        tier=Tier.BUDGET,
        cost_in=0.09, cost_out=0.45, context=262_000,
        strengths=["agentic", "efficiency", "coding", "open-weight", "throughput"],
        benchmarks={"GPQA": 80.0},
        open_weight=True, license_="NVIDIA Open",
        notes="120B/12B MoE. Mamba-Transformer hybrid. 5x throughput. 1M ctx. GPU-optimized.",
    ),
    "nemotron-3-nano": ModelEntry(
        id="nvidia/nemotron-3-nano-30b-a3b",
        provider="NVIDIA",
        tier=Tier.ULTRA_BUDGET,
        cost_in=0.05, cost_out=0.20, context=262_000,
        strengths=["efficiency", "edge", "open-weight", "cost"],
        benchmarks={"GPQA": 75.7},
        open_weight=True, license_="NVIDIA Open",
        notes="30B/3B MoE. Cheapest capable model. Edge deployment. 1M ctx.",
    ),
    "mistral-small-4": ModelEntry(
        id="mistralai/mistral-small-2603",
        provider="Mistral AI",
        tier=Tier.ULTRA_BUDGET,
        cost_in=0.15, cost_out=0.60, context=262_000,
        strengths=["multimodal", "coding", "agentic", "efficiency", "open-weight"],
        open_weight=True, license_="Apache 2.0",
        notes="119B/6.5B MoE. Unifies Magistral+Pixtral+Devstral. Apache 2.0. Multimodal.",
    ),
    "mistral-large-3": ModelEntry(
        id="mistralai/mistral-large-2512",
        provider="Mistral AI",
        tier=Tier.BALANCED,
        cost_in=0.50, cost_out=1.50, context=262_000,
        strengths=["reasoning", "multimodal", "multilingual", "open-weight"],
        open_weight=True, license_="Apache 2.0",
        notes="675B/41B MoE. Apache 2.0. Best Mistral model. Multilingual + multimodal.",
    ),
    "gemma-4-31b": ModelEntry(
        id="google/gemma-4-31b-it",
        provider="Google DeepMind",
        tier=Tier.BUDGET,
        cost_in=0.14, cost_out=0.40, context=262_000,
        strengths=["reasoning", "math", "coding", "multimodal", "open-weight", "local"],
        benchmarks={"AIME": 89.2, "GPQA": 84.3, "MMLU-Pro": 85.2, "LiveCodeBench": 80.0},
        open_weight=True, license_="Apache 2.0",
        notes="31B dense. GPQA 84.3% beats R1 (81%). AIME 89.2%. Apache 2.0. Runs on 24GB GPU.",
    ),
    "gemma-4-26b-moe": ModelEntry(
        id="google/gemma-4-26b-a4b-it",
        provider="Google DeepMind",
        tier=Tier.ULTRA_BUDGET,
        cost_in=0.06, cost_out=0.33, context=262_000,
        strengths=["efficiency", "cost", "open-weight", "local", "reasoning"],
        benchmarks={"AIME": 88.3, "GPQA": 82.3, "MMLU-Pro": 82.6, "LiveCodeBench": 77.1},
        open_weight=True, license_="Apache 2.0",
        notes="26B/3.8B MoE. Near-31B quality at 4B speed. Cheapest on OpenRouter ($0.06). Runs on single GPU.",
    ),
    "qwen-2.5-72b": ModelEntry(
        id="qwen/qwen-2.5-72b-instruct",
        provider="Alibaba (Qwen)",
        tier=Tier.BALANCED,
        cost_in=0.35, cost_out=0.40, context=128_000,
        strengths=["multilingual", "instruction-following", "balanced"],
        benchmarks={"MMLU-Pro": 83.6, "GPQA": 61.2},
        notes="Dense 72B. Excellent for search result parsing and gap analysis. Apache 2.0 open weights.",
    ),
    "gemini-3-flash": ModelEntry(
        id="google/gemini-3-flash",
        provider="Google",
        tier=Tier.BUDGET,
        cost_in=0.50, cost_out=3.00, context=1_000_000,
        strengths=["speed", "multimodal", "long-context", "reasoning"],
        benchmarks={"GPQA": 90.4, "MMLU-Pro": 89.0, "LiveCodeBench": 90.8},
        notes="Fastest frontier-tier model. 1M context. Excellent for quick validation.",
    ),

    # ── BUDGET / ULTRA-BUDGET ──────────────────────────────────────────────
    "gpt-4o-mini": ModelEntry(
        id="openai/gpt-4o-mini",
        provider="OpenAI",
        tier=Tier.ULTRA_BUDGET,
        cost_in=0.15, cost_out=0.60, context=128_000,
        strengths=["speed", "cost", "json-mode", "tool-use"],
        benchmarks={},
        notes="Cheapest reliable model. Perfect for Phase G quality validation. 128K context.",
    ),

    "mimo-v2-pro": ModelEntry(
        id="xiaomi/mimo-v2-pro",
        provider="Xiaomi",
        tier=Tier.BUDGET,
        cost_in=1.0, cost_out=3.0, context=1_000_000,
        strengths=["coding", "volume", "cost"],
        benchmarks={"SWE-bench": 78.0},
        notes="#1 on OpenRouter by volume (4.65T tokens/week). Trillion-parameter model.",
    ),
    "minimax-m2.5": ModelEntry(
        id="minimax/minimax-m2.5",
        provider="MiniMax",
        tier=Tier.BUDGET,
        cost_in=0.30, cost_out=1.20, context=1_000_000,
        strengths=["creative", "multimodal", "coding"],
        benchmarks={"SWE-bench": 80.2},
        notes="Strong creative writing. Good for dissertation drafts. 1M context.",
    ),

    # ── FREE ───────────────────────────────────────────────────────────────
    "mistral-nemo": ModelEntry(
        id="mistralai/mistral-nemo",
        provider="Mistral",
        tier=Tier.FREE,
        cost_in=0.02, cost_out=0.04, context=128_000,
        strengths=["multilingual", "agentic", "tool-use"],
        notes="Nearly free. Strong function calling. Apache 2.0 open weights.",
    ),

    # ── LOCAL (Open-weight, self-hosted) ───────────────────────────────────
    "qwen3-32b": ModelEntry(
        id="qwen/qwen3-32b",
        provider="Alibaba (Qwen)",
        tier=Tier.LOCAL,
        cost_in=0, cost_out=0, context=128_000,
        strengths=["best-under-40B", "coding", "multilingual"],
        open_weight=True, license_="Apache 2.0",
        notes="Best open-weight model under 40B. Runs on single 24GB GPU. Apache 2.0.",
    ),

    "deepseek-r1-32b": ModelEntry(
        id="deepseek/deepseek-r1-distill-qwen-32b",
        provider="DeepSeek",
        tier=Tier.LOCAL,
        cost_in=0, cost_out=0, context=128_000,
        strengths=["reasoning", "math", "local"],
        open_weight=True, license_="Apache 2.0",
        notes="Best local reasoning model. R1 distilled to 32B. Apache 2.0.",
    ),
    "phi-4": ModelEntry(
        id="microsoft/phi-4",
        provider="Microsoft",
        tier=Tier.LOCAL,
        cost_in=0, cost_out=0, context=32_000,
        strengths=["reasoning", "math", "edge", "small"],
        open_weight=True, license_="MIT",
        notes="Best small reasoning model (14B). MIT license. Fits 8GB VRAM.",
    ),
    "llama-4-scout": ModelEntry(
        id="meta/llama-4-scout",
        provider="Meta",
        tier=Tier.LOCAL,
        cost_in=0, cost_out=0, context=10_000_000,
        strengths=["long-context", "multimodal", "ecosystem"],
        open_weight=True, license_="Llama 4 Community",
        notes="10M context — processes entire repos. 17B active params. Llama ecosystem.",
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# Phase-to-Model Mapping (v5.3.1)
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_MODEL_MAP = {
    "A": ["claude-sonnet-4.6", "gemini-3.1-pro", "deepseek-v4-pro", "qwen-3.6-max"],     # C4 Framing
    "B": ["qwen-3.6-plus", "deepseek-v4-flash", "gemini-3-flash", "seed-2.0-lite"],      # Knowledge
    "C": ["deepseek-v3.2", "qwen-2.5-72b", "gemini-3-flash", "kimi-k2.6"],               # Gap Analysis
    "D": ["claude-sonnet-4.6", "claude-opus-4.6", "kimi-k2.6", "gemini-3.1-pro"],        # Hypothesis
    "E": [],                                                                               # Simulation
    "F": ["claude-sonnet-4.6", "kimi-k2.6", "minimax-m2.7", "gemini-3.1-pro"],           # Dissertation
    "G": ["deepseek-v4-flash", "gpt-4o-mini", "gemma-4-26b-moe", "nemotron-3-nano"],     # Quality
}

COST_TIER_MAP = {
    "budget":     ["deepseek-v4-flash", "gemma-4-26b-moe", "nemotron-3-nano", "seed-2.0-mini"],
    "balanced":   ["qwen-3.6-plus", "deepseek-v3.2", "gemma-4-31b", "mistral-small-4", "minimax-m2.5"],
    "premium":    ["claude-sonnet-4.6", "gemini-3.1-pro", "kimi-k2.6", "glm-5.1", "seed-2.0-lite"],
    "frontier":   ["claude-opus-4.6", "gemini-3.1-pro", "deepseek-v4-pro", "qwen-3.6-max", "grok-4.20"],
}

# ═══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════════════

def get_model(phase: str = "D", cost_tier: str = "balanced") -> str:
    """Get best model for phase + cost tier."""
    import os
    override = os.environ.get(f"PHASE_{phase}_MODEL", "")
    if override:
        return override
    models = PHASE_MODEL_MAP.get(phase, ["gpt-4o-mini"])
    if not models:
        return ""
    cost_models = COST_TIER_MAP.get(cost_tier, models)
    for m in cost_models:
        if m in models:
            return CATALOG[m].id
    return CATALOG[models[0]].id


def estimate_pipeline_cost(prompt_tokens_per_phase: int = 1000) -> dict[str, float]:
    """Estimate total pipeline cost."""
    total = 0.0
    phases = {}
    for phase in "ABCDEFG":
        model_key = next((m for m in PHASE_MODEL_MAP[phase] if m in CATALOG), None)
        if not model_key:
            phases[phase] = 0.0
            continue
        m = CATALOG[model_key]
        max_tok = 500 if phase in "ABCG" else 800 if phase == "D" else 2000
        cost = (prompt_tokens_per_phase * m.cost_in + max_tok * m.cost_out) / 1_000_000
        phases[phase] = round(cost, 6)
        total += cost
    phases["total"] = round(total, 6)
    return phases


def list_models(filter_tier: str | None = None) -> list[dict[str, Any]]:
    """List all models, optionally filtered by tier."""
    result = []
    for key, m in CATALOG.items():
        if filter_tier and m.tier != filter_tier:
            continue
        result.append({
            "key": key, "id": m.id, "provider": m.provider, "tier": m.tier,
            "cost_in": m.cost_in, "cost_out": m.cost_out, "context": m.context,
            "strengths": m.strengths, "open_weight": m.open_weight, "license": m.license_,
        })
    return result


__all__ = ["CATALOG", "ModelEntry", "PHASE_MODEL_MAP", "COST_TIER_MAP",
           "get_model", "estimate_pipeline_cost", "list_models", "Tier"]
