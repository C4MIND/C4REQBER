"""Delphi Method plugin — LLM-powered expert consensus forecasting."""

from __future__ import annotations

from typing import Any

from src.plugins._llm_base import _llm_reason, plugin_fallback


def analyze(question: str, num_experts: int = 5) -> dict[str, Any]:
    """Analyze."""
    prompt = f"""Simulate a Delphi method expert panel. {num_experts} diverse domain experts independently estimate and provide rationale for:

QUESTION: {question[:1000]}

For each expert, provide:
- A numerical estimate (0.0 to 1.0, or a specific quantity with units)
- Confidence level (0.0 to 1.0)
- A specific, domain-grounded rationale

After individual estimates, provide consensus range and key assumptions.

Respond as JSON:
{{
  "expert_estimates": [
    {{"expert_id": "E1 (domain: ...)", "estimate": 0.72, "confidence": 0.8, "rationale": "concrete domain-specific reason"}}
  ],
  "consensus_range": [0.65, 0.78],
  "confidence": 0.75,
  "rounds_needed": 3,
  "key_assumptions": ["specific assumption 1", "specific assumption 2"]
}}"""
    system = "You are a Delphi method facilitator simulating diverse domain experts. Give realistic, varied estimates with genuine domain reasoning. Never use random values or generic rationales."
    raw = _llm_reason(prompt, system=system, max_tokens=800)
    if not raw:
        return {"question": question, "expert_estimates": [], "consensus_range": [0.0, 0.0], "confidence": 0.0, "rounds_needed": 3, "key_assumptions": [plugin_fallback("LLM unavailable — no analysis performed")]}
    try:
        import json
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            result["question"] = question
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    return {"question": question, "expert_estimates": [], "consensus_range": [0.0, 0.0], "confidence": 0.0, "rounds_needed": 3, "key_assumptions": [plugin_fallback("LLM output unparseable")]}


def execute(question: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(question, **kwargs)
