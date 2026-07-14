"""Six Thinking Hats Plugin — LLM-powered parallel thinking."""

from __future__ import annotations

from typing import Any

from src.plugins._llm_base import _llm_reason


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
    if not raw:
        return {"problem": problem, "white_hat": [], "red_hat": [], "black_hat": [], "yellow_hat": [], "green_hat": [], "blue_hat": []}
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
    return {"problem": problem, "white_hat": [], "red_hat": [], "black_hat": [], "yellow_hat": [], "green_hat": [], "blue_hat": []}


def execute(problem: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(problem)
