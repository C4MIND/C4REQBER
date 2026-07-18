"""SWOT Analysis plugin — LLM-powered strategic analysis."""

from typing import Any

from src.plugins._llm_base import _llm_reason, finalize_plugin_result


def analyze(context: str) -> dict[str, Any]:
    """Analyze."""
    prompt = f"""Perform a rigorous SWOT analysis on the following context. Be specific and evidence-based.

CONTEXT: {context[:1500]}

Output format (JSON):
{{
  "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
  "weaknesses": ["specific weakness 1", "specific weakness 2", "specific weakness 3"],
  "opportunities": ["specific opportunity 1", "specific opportunity 2"],
  "threats": ["specific threat 1", "specific threat 2"]
}}"""
    system = (
        "You are a strategic analyst. Provide SWOT analysis with concrete, "
        "domain-specific items — never generic templates."
    )
    raw = _llm_reason(prompt, system=system, max_tokens=600)
    if not raw:
        payload = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "note": "LLM unavailable — empty SWOT fields retained for retry",
        }
        return finalize_plugin_result(payload, raw)
    try:
        import json
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return finalize_plugin_result(json.loads(match.group()), raw)
    except (json.JSONDecodeError, ValueError):
        pass
    lines = [line.strip("- ") for line in raw.split("\n") if line.strip().startswith("-")]
    payload = {
        "strengths": lines[:3] or [raw[:200]],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
    }
    return finalize_plugin_result(payload, raw)


def execute(context: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(context)
