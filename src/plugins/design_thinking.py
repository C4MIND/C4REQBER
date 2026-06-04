"""Design Thinking Plugin — LLM-powered human-centered design."""

from __future__ import annotations

from typing import Any

from src.plugins._llm_base import _llm_reason


def analyze(challenge: str) -> dict[str, Any]:
    """Analyze."""
    prompt = f"""Apply Design Thinking (Empathize-Define-Ideate-Prototype-Test) to this challenge:

CHALLENGE: {challenge[:1500]}

Provide 2-3 concrete, domain-specific points for each phase:
- EMPATHIZE: Who are the users/stakeholders? What are their real needs, pain points, contexts?
- DEFINE: What is the core problem statement? What constraints exist?
- IDEATE: What are radical, feasible solution concepts?
- PROTOTYPE: How would you create a low-fidelity testable version?
- TEST: How would you validate with real users? What metrics?

Respond as JSON:
{{"empathize": ["point 1", "point 2"], "define": [...], "ideate": [...], "prototype": [...], "test": [...]}}"""
    system = "You are a Design Thinking facilitator. Provide human-centered, concrete design insights. Never use generic questions or templates."
    raw = _llm_reason(prompt, system=system, max_tokens=600, temperature=0.5)
    if not raw:
        return {"challenge": challenge, "empathize": [], "define": [], "ideate": [], "prototype": [], "test": []}
    try:
        import json
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            result["challenge"] = challenge
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    return {"challenge": challenge, "empathize": [], "define": [], "ideate": [], "prototype": [], "test": []}


def execute(challenge: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(challenge)
