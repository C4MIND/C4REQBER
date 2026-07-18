"""Lateral Thinking plugin — LLM-powered creative ideation."""

from typing import Any

from src.plugins._llm_base import _llm_reason, finalize_plugin_result


TECHNIQUES = [
    "reverse_the_problem",
    "analogy_transfer",
    "random_stimulus",
    "challenge_assumptions",
    "provocation",
]


def generate_ideas(problem: str, count: int = 3) -> tuple[list[dict[str, str]], str]:
    """Generate ideas. Returns (ideas, llm_raw)."""
    prompt = f"""Apply lateral thinking techniques to generate {count} creative, non-obvious ideas for this problem.

PROBLEM: {problem[:1000]}

For each idea:
1. Choose a lateral thinking technique (from: {", ".join(TECHNIQUES)})
2. Apply it concretely to the problem
3. Describe the resulting idea — be specific, not generic

Respond as JSON:
[
  {{"technique": "technique_name", "idea": "concrete, specific idea (1-3 sentences)"}},
  ...
]"""
    system = "You are an expert in lateral thinking and creative problem-solving. Generate genuinely novel, counter-intuitive ideas. Never use generic filler."
    raw = _llm_reason(prompt, system=system, max_tokens=500, temperature=0.8)
    if not raw:
        ideas = [
            {
                "technique": t,
                "idea": f"Technique '{t}' ready — retry when LLM gateway is available for: {problem[:50]}",
            }
            for t in TECHNIQUES[:count]
        ]
        return ideas, raw
    try:
        import json
        import re

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result[:count], raw
    except (json.JSONDecodeError, ValueError):
        pass
    ideas = [
        {"technique": t, "idea": f"LLM output unparseable for: {problem[:50]}"}
        for t in TECHNIQUES[:count]
    ]
    return ideas, raw


def execute(problem: str, **kwargs: Any) -> dict[str, Any]:
    """Execute."""
    result, raw = generate_ideas(problem, **kwargs)
    return finalize_plugin_result({"problem": problem, "ideas": result}, raw)
