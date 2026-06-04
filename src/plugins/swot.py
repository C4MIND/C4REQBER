"""SWOT Analysis plugin — LLM-powered strategic analysis."""

from typing import Any

from src.plugins._llm_base import _llm_reason


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
    system = "You are a strategic analyst. Provide SWOT analysis with concrete, domain-specific items — never generic templates."
    raw = _llm_reason(prompt, system=system, max_tokens=600)
    if not raw:
        return {"strengths": ["LLM unavailable — unable to analyze"], "weaknesses": [], "opportunities": [], "threats": []}
    try:
        import json
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        pass
    lines = [l.strip("- ") for l in raw.split("\n") if l.strip().startswith("-")]
    return {"strengths": lines[:3] or ["Analysis produced no structured output"], "weaknesses": [], "opportunities": [], "threats": []}


def execute(context: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(context)
