"""Ishikawa (Fishbone) Diagram Plugin — LLM-powered root cause analysis."""

from __future__ import annotations

from typing import Any

from src.plugins._llm_base import _llm_reason


DEFAULT_CATEGORIES = {
    "People": ["Skills", "Training", "Motivation", "Communication"],
    "Process": ["Procedures", "Workflow", "Efficiency", "Bottlenecks"],
    "Materials": ["Quality", "Availability", "Cost", "Specifications"],
    "Equipment": ["Maintenance", "Capacity", "Technology", "Reliability"],
    "Environment": ["Regulations", "Market", "Competition", "Economy"],
    "Measurement": ["Metrics", "Accuracy", "Frequency", "Feedback"],
}


def analyze(problem: str, custom_categories: dict[str, list[str]] | None = None) -> dict[str, Any]:
    """Analyze."""
    cats = custom_categories or DEFAULT_CATEGORIES
    cat_list = "\n".join(f"- {k}: {', '.join(v)}" for k, v in cats.items())
    prompt = f"""Perform an Ishikawa (fishbone) root cause analysis.

PROBLEM: {problem[:1500]}

Analyze across these categories:
{cat_list}

For EACH category, provide 2-3 SPECIFIC potential root causes relevant to this problem. Then identify the 3 most likely ROOT CAUSES overall.

Respond as JSON:
{{"categories": {{"People": ["specific cause 1", "specific cause 2"], "Process": [...], ...}}, "root_causes": ["top cause 1", "top cause 2", "top cause 3"]}}"""
    system = "You are a root cause analyst. Provide specific, domain-grounded causes for each Ishikawa category. Never use generic template strings."
    raw = _llm_reason(prompt, system=system, max_tokens=700, temperature=0.3)
    if not raw:
        return {"problem": problem, "categories": {}, "root_causes": []}
    try:
        import json
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            result["problem"] = problem
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    return {"problem": problem, "categories": {}, "root_causes": []}


def execute(problem: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(problem)
