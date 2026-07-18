"""SCAMPER Plugin — LLM-powered creative innovation."""

from __future__ import annotations

from typing import Any

from src.plugins._llm_base import _llm_reason, finalize_plugin_result


def analyze(original: str) -> dict[str, Any]:
    """Analyze."""
    prompt = f"""Apply the SCAMPER creative technique to this product/process/idea:

{original[:1500]}

For EACH of the 7 SCAMPER dimensions, provide 1-2 concrete, domain-specific ideas:
- SUBSTITUTE: What components/materials/processes can be replaced?
- COMBINE: What can be merged with other concepts?
- ADAPT: What can be borrowed from other domains?
- MODIFY: What can be changed, magnified, or minified?
- PUT TO OTHER USES: What unexpected applications exist?
- ELIMINATE: What can be removed or simplified?
- REVERSE: What if we reversed the order, direction, or assumptions?

Respond as JSON:
{{"substitute": ["idea 1", "idea 2"], "combine": [...], "adapt": [...], "modify": [...], "put_to_other_uses": [...], "eliminate": [...], "reverse": [...]}}"""
    system = "You are a SCAMPER creative facilitator. Generate genuinely non-obvious, domain-specific ideas. Never use generic filler."
    raw = _llm_reason(prompt, system=system, max_tokens=700, temperature=0.7)
    empty = {
        "original": original,
        "substitute": [],
        "combine": [],
        "adapt": [],
        "modify": [],
        "put_to_other_uses": [],
        "eliminate": [],
        "reverse": [],
    }
    if not raw:
        return finalize_plugin_result(empty, raw)
    try:
        import json
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            result["original"] = original
            return finalize_plugin_result(result, raw)
    except (json.JSONDecodeError, ValueError):
        pass
    return finalize_plugin_result(empty, raw)


def execute(original: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(original)
