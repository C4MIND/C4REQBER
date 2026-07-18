"""OODA Loop Plugin — LLM-powered rapid decision-making."""

from __future__ import annotations

from typing import Any

from src.plugins._llm_base import _llm_reason, finalize_plugin_result


def analyze(situation: str) -> dict[str, Any]:
    """Analyze."""
    prompt = f"""Apply the OODA (Observe-Orient-Decide-Act) loop to this situation:

SITUATION: {situation[:1500]}

Provide 2-3 concrete, domain-specific points for each phase:
- OBSERVE: What data is available? What's happening? What are the signals?
- ORIENT: What mental models apply? What biases exist? What's the context?
- DECIDE: What are the options? Which has the best risk/reward?
- ACT: What specific actions to take? In what sequence? With what resources?

Respond as JSON:
{{"observe": ["point 1", "point 2"], "orient": [...], "decide": [...], "act": [...], "cycle_time_estimate": "hours/days/weeks"}}"""
    system = "You are a military-strategic OODA loop analyst. Provide specific, actionable analysis. Never use generic templates."
    raw = _llm_reason(prompt, system=system, max_tokens=600, temperature=0.4)
    empty = {
        "situation": situation,
        "observe": [],
        "orient": [],
        "decide": [],
        "act": [],
        "cycle_time_estimate": "unknown",
    }
    if not raw:
        return finalize_plugin_result(empty, raw)
    try:
        import json
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            result["situation"] = situation
            return finalize_plugin_result(result, raw)
    except (json.JSONDecodeError, ValueError):
        pass
    return finalize_plugin_result(empty, raw)


def execute(situation: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(situation)
