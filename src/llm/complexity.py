"""Task complexity classifier for LLM routing."""

from __future__ import annotations

from enum import Enum


class TaskComplexity(Enum):
    """Complexity levels for LLM task routing."""

    SIMPLE = "simple"       # translation, summary, formatting
    MEDIUM = "medium"       # analysis, coding, explanation
    HARD = "hard"           # research, synthesis, multi-step reasoning
    EXTREME = "extreme"     # dissertation, formal verification, novel discovery


# Rule-based keywords
SIMPLE_KEYWORDS = ["translate", "summarize", "format", "rewrite", "shorten", "expand"]
MEDIUM_KEYWORDS = ["analyze", "explain", "code", "implement", "compare", "contrast"]
HARD_KEYWORDS = ["research", "synthesize", "discover", "prove", "verify", "design"]
EXTREME_KEYWORDS = ["dissertation", "thesis", "formal verification", "novel", "breakthrough"]


def classify_complexity(query: str) -> TaskComplexity:
    """Classify task complexity using rule-based keyword matching."""
    q = query.lower()
    if any(k in q for k in EXTREME_KEYWORDS):
        return TaskComplexity.EXTREME
    if any(k in q for k in HARD_KEYWORDS):
        return TaskComplexity.HARD
    if any(k in q for k in MEDIUM_KEYWORDS):
        return TaskComplexity.MEDIUM
    return TaskComplexity.SIMPLE


# Fallback: use local LLM for classification
async def classify_complexity_llm(query: str, client) -> TaskComplexity:
    """Classify task complexity using an LLM client."""
    prompt = f"Classify task complexity [simple|medium|hard|extreme]: {query[:200]}"
    response = await client.complete(prompt, max_tokens=10)
    result = response.strip().lower()
    for c in TaskComplexity:
        if c.value in result:
            return c
    return TaskComplexity.MEDIUM
