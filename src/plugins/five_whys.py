"""5 Whys root cause analysis plugin — LLM-powered."""

from typing import Any

from src.plugins._llm_base import _llm_reason, finalize_plugin_result


def analyze(problem: str, depth: int = 5) -> tuple[list[dict[str, Any]], str]:
    """Analyze. Returns (chain, llm_raw)."""
    prompt = f"""Perform a rigorous 5 Whys root cause analysis.

PROBLEM: {problem[:1000]}

For each level (1 through {depth}), ask "Why?" and provide a concrete, domain-specific answer that drills deeper into the root cause. Do NOT use generic template answers.

Respond as a JSON array:
[
  {{"level": 1, "question": "Why did X happen?", "answer": "Because... (concrete, specific)"}},
  {{"level": 2, "...": "..."}},
  ...
]"""
    system = "You are a root cause analyst. Drill deeper at each level. Never say 'root cause level N' — give real answers."
    raw = _llm_reason(prompt, system=system, max_tokens=600, temperature=0.3)
    if not raw:
        chain = [
            {
                "level": i + 1,
                "question": f"Why? (level {i + 1})",
                "answer": "pending — retry when LLM gateway is available",
            }
            for i in range(depth)
        ]
        return chain, raw
    try:
        import json
        import re

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result[:depth], raw
    except (json.JSONDecodeError, ValueError):
        pass
    chain = [
        {
            "level": i + 1,
            "question": f"Why? (level {i + 1})",
            "answer": "LLM output unparseable — see raw_excerpt on execute",
        }
        for i in range(depth)
    ]
    return chain, raw


def execute(problem: str, **kwargs: Any) -> dict[str, Any]:
    """Execute."""
    result, raw = analyze(problem, **kwargs)
    return finalize_plugin_result({"problem": problem, "chain": result}, raw)
