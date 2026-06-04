"""
Model-per-Stage LLM Router — different LLMs for different pipeline phases.

Phase A (C4 Framing)     → Claude 3.5 Sonnet (deep reasoning)
Phase B (Knowledge)       → Qwen 72B (balanced)
Phase C (Gap Analysis)    → Qwen 72B (balanced)
Phase D (Hypotheses)      → Claude 3.5 Sonnet (creative, high temp)
Phase E (Simulation)      → no LLM (compute plugins)
Phase F (Dissertation)    → Claude 3.5 Sonnet (academic writing)
Phase G (Quality)         → GPT-4o-mini (cheap validation)
"""
from __future__ import annotations
from typing import Any

import os


# Default model for each pipeline phase
PHASE_MODEL: dict[str, str] = {
    "A": "anthropic/claude-sonnet-4.5",
    "B": "qwen/qwen-2.5-72b-instruct",
    "C": "qwen/qwen-2.5-72b-instruct",
    "D": "anthropic/claude-sonnet-4.5",
    "E": "",  # no LLM — compute plugins only
    "F": "anthropic/claude-sonnet-4.5",
    "G": "openai/gpt-4o-mini",
}

# Temperature per phase
PHASE_TEMPERATURE: dict[str, float] = {
    "A": 0.3,   # precise reasoning
    "B": 0.1,   # factual search
    "C": 0.3,   # analytical
    "D": 0.7,   # creative hypothesis generation
    "E": 0.0,   # N/A
    "F": 0.5,   # academic writing
    "G": 0.2,   # scoring consistency
}

# Max tokens per phase
PHASE_MAX_TOKENS: dict[str, int] = {
    "A": 500,
    "B": 300,
    "C": 600,
    "D": 800,
    "E": 0,
    "F": 2000,
    "G": 400,
}


def get_model_for_phase(phase: str) -> str:
    """Return the LLM model to use for a given pipeline phase."""
    model = os.environ.get(f"PHASE_{phase}_MODEL", "")
    if model:
        return model
    return PHASE_MODEL.get(phase, "openai/gpt-4o-mini")


def get_temperature_for_phase(phase: str) -> float:
    return PHASE_TEMPERATURE.get(phase, 0.3)


def get_max_tokens_for_phase(phase: str) -> int:
    return PHASE_MAX_TOKENS.get(phase, 500)


def get_cost_estimate(phase: str, prompt_tokens: int = 500) -> dict[str, Any]:
    """Estimate cost per phase."""
    model = get_model_for_phase(phase)
    prices = {
        "anthropic/claude-sonnet-4.5": (3.0, 15.0),   # $/1M input, $/1M output
        "qwen/qwen-2.5-72b-instruct": (0.35, 0.40),
        "openai/gpt-4o-mini": (0.15, 0.60),
    }
    in_price, out_price = prices.get(model, (0.5, 1.0))
    max_tok = get_max_tokens_for_phase(phase)
    cost = (prompt_tokens * in_price + max_tok * out_price) / 1_000_000
    return {"model": model, "prompt_cost": round(prompt_tokens * in_price / 1_000_000, 6),
            "output_cost": round(max_tok * out_price / 1_000_000, 6), "total": round(cost, 6)}


__all__ = ["get_model_for_phase", "get_temperature_for_phase", "get_max_tokens_for_phase",
           "get_cost_estimate", "PHASE_MODEL", "PHASE_TEMPERATURE", "PHASE_MAX_TOKENS"]
