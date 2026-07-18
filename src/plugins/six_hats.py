"""Six Thinking Hats Plugin — LLM-powered parallel thinking."""

from __future__ import annotations

from typing import Any

from src.plugins._llm_base import _llm_reason, finalize_plugin_result


def analyze(problem: str) -> dict[str, Any]:
    """Analyze."""
    prompt = f"""Apply Edward de Bono's Six Thinking Hats to this problem:

PROBLEM: {problem[:1500]}

Provide 2-3 specific, domain-grounded points for EACH hat:
- WHITE HAT (Facts): What data/facts are relevant? What do we know? What's missing?
- RED HAT (Emotions): What are the gut feelings, intuitions, emotional reactions?
- BLACK HAT (Cautions): What are the risks, weaknesses, potential failures?
- YELLOW HAT (Benefits): What are the opportunities, positive outcomes, value?
- GREEN HAT (Creativity): What novel alternatives, possibilities exist?
- BLUE HAT (Process): What's the thinking process? Next steps? Meta-reflection?

Respond as JSON:
{{"white_hat": ["fact 1", "fact 2"], "red_hat": [...], "black_hat": [...], "yellow_hat": [...], "green_hat": [...], "blue_hat": [...]}}"""
    system = "You are a Six Thinking Hats facilitator. Provide concrete, domain-specific perspectives for each hat. Never use generic questions."
    raw = _llm_reason(prompt, system=system, max_tokens=700)
    empty = {
        "problem": problem,
        "white_hat": [],
        "red_hat": [],
        "black_hat": [],
        "yellow_hat": [],
        "green_hat": [],
        "blue_hat": [],
    }
    if not raw:
        return finalize_plugin_result(empty, raw)
    try:
        import json
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            result["problem"] = problem
            return finalize_plugin_result(result, raw)
    except (json.JSONDecodeError, ValueError):
        pass
    return finalize_plugin_result(empty, raw)


def execute(problem: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(problem)
