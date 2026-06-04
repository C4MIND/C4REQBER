from __future__ import annotations


"""Контекст (Context) — Functor Agent φ."""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import FUNCTOR_SYSTEM_PROMPTS, build_user_prompt


class ContextAgent(FunctorAgent):
    """ContextAgent."""
    symbol = "φ"
    name_ru = "Контекст"
    name_en = "Context"
    c4_state: tuple[int, int, int] = (2, 1, 0)
    phase = "интеграция"

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        system = FUNCTOR_SYSTEM_PROMPTS["φ_context"]
        user = build_user_prompt(problem, context.get("vector", "discover") if context else "discover", context)
        insight = await self._llm_generate(system, user)
        return self._build_result(problem, insight, confidence=0.75)

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        problem = data.get("problem", "")
        context = {"vector": data.get("vector", "discover"), **data}
        result = await self.analyze(problem, context)
        return {**data, "transformed_by": self.symbol, "context_insight": result["insight"]}
