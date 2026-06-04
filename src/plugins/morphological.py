"""Morphological Analysis plugin — LLM-powered parameter space exploration."""

from typing import Any

from src.plugins._llm_base import _llm_reason


def analyze(parameters: list[str], values: list[list[str]]) -> list[dict[str, Any]]:
    """Analyze."""
    if not parameters or not values:
        return []
    import itertools
    combinations = list(itertools.product(*values))
    combo_strs = [str(dict(zip(parameters, combo, strict=False))) for combo in combinations[:30]]

    prompt = f"""Analyze these morphological combinations for novelty and feasibility. Rank the top 5-10 most promising ones.

PARAMETERS: {parameters}
TOTAL COMBINATIONS: {len(combinations)}

Sample combinations:
{chr(10).join(combo_strs[:15])}

For each promising combination, provide:
- Why it's novel or non-obvious
- Feasibility assessment (1-5)
- Potential applications

Respond as JSON:
[
  {{"id": 1, "combination": {{"param1": "value1", "param2": "value2"}}, "assessment": "why promising (1-2 sentences)", "feasibility": 4}},
  ...
]"""
    system = "You are a morphological analysis expert. Evaluate parameter combinations for novelty and practical feasibility. Be specific."
    raw = _llm_reason(prompt, system=system, max_tokens=600)
    if not raw:
        return [{"id": i + 1, "combination": dict(zip(parameters, combo, strict=False))} for i, combo in enumerate(combinations[:10])]
    try:
        import json
        import re
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result[:20]
    except (json.JSONDecodeError, ValueError):
        pass
    return [{"id": i + 1, "combination": dict(zip(parameters, combo, strict=False))} for i, combo in enumerate(combinations[:10])]


def execute(parameters: list[str] | None = None, values: list[list[str]] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Execute."""
    if parameters is None:
        parameters = ["Material", "Shape", "Process"]
    if values is None:
        values = [["Metal", "Polymer", "Composite"], ["Sphere", "Cube", "Tube"], ["Cast", "Print", "Machine"]]
    result = analyze(parameters, values)
    return {"parameters": parameters, "values": values, "combinations": result}
