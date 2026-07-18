"""Morphological Analysis plugin — LLM-powered parameter space exploration."""

from typing import Any

from src.plugins._llm_base import _llm_reason, finalize_plugin_result


def analyze(
    parameters: list[str],
    values: list[list[str]],
    *,
    problem: str = "",
) -> tuple[list[dict[str, Any]], str]:
    """Analyze. Returns (ranked_or_enumerated combos, llm_raw). Combinatorics always run."""
    if not parameters or not values:
        return [], ""
    import itertools

    combinations = list(itertools.product(*values))
    enumerated = [
        {"id": i + 1, "combination": dict(zip(parameters, combo, strict=False))}
        for i, combo in enumerate(combinations[:10])
    ]
    combo_strs = [str(dict(zip(parameters, combo, strict=False))) for combo in combinations[:30]]
    problem_line = f"\nPROBLEM CONTEXT: {problem[:800]}\n" if problem else "\n"

    prompt = f"""Analyze these morphological combinations for novelty and feasibility. Rank the top 5-10 most promising ones.
{problem_line}
PARAMETERS: {parameters}
TOTAL COMBINATIONS: {len(combinations)}

Sample combinations:
{chr(10).join(combo_strs[:15])}

For each promising combination, provide:
- Why it's novel or non-obvious relative to the problem
- Feasibility assessment (1-5)
- Potential applications

Respond as JSON:
[
  {{"id": 1, "combination": {{"param1": "value1", "param2": "value2"}}, "assessment": "why promising (1-2 sentences)", "feasibility": 4}},
  ...
]"""
    system = (
        "You are a morphological analysis expert. Evaluate parameter combinations "
        "for novelty and practical feasibility relative to the stated problem. Be specific."
    )
    raw = _llm_reason(prompt, system=system, max_tokens=600)
    if not raw:
        return enumerated, raw
    try:
        import json
        import re

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result[:20], raw
    except (json.JSONDecodeError, ValueError):
        pass
    return enumerated, raw


def execute(
    problem: str = "",
    parameters: list[str] | None = None,
    values: list[list[str]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute morphological analysis for the given problem (not a fixed Metal/Polymer toy)."""
    problem = (problem or kwargs.get("context") or "").strip()
    if parameters is None and values is None:
        # Problem-derived axes — keep real combinatorial work, not a unrelated toy grid.
        seed = problem[:60] if problem else "baseline approach"
        parameters = ["Approach", "Scale", "Constraint"]
        values = [
            [seed, "alternative framing", "hybrid of both"],
            ["local", "systemic", "multi-scale"],
            ["evidence-limited", "time-limited", "resource-limited"],
        ]
    if parameters is None:
        parameters = ["Approach", "Scale", "Constraint"]
    if values is None:
        values = [
            ["baseline", "alternative", "hybrid"],
            ["local", "systemic", "multi-scale"],
            ["evidence", "time", "resource"],
        ]
    result, raw = analyze(parameters, values, problem=problem)
    total = 1
    for axis in values:
        total *= max(len(axis), 1)
    payload = {
        "problem": problem,
        "parameters": parameters,
        "values": values,
        "combinations": result,
        "executed": True,
        "total_combinations": total,
    }
    return finalize_plugin_result(payload, raw)
