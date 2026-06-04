from __future__ import annotations


"""Связность (Integration) — Functor Agent σ."""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import FUNCTOR_SYSTEM_PROMPTS, build_user_prompt


class IntegrationAgent(FunctorAgent):
    """IntegrationAgent."""
    symbol = "σ"
    name_ru = "Связность"
    name_en = "Integration"
    c4_state: tuple[int, int, int] = (1, 1, 0)
    phase = "дивергенция"

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        system = FUNCTOR_SYSTEM_PROMPTS["σ_integration"]
        user = build_user_prompt(problem, context.get("vector", "discover") if context else "discover", context)
        insight = await self._llm_generate(system, user)
        return self._build_result(problem, insight, confidence=0.76)

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        problem = data.get("problem", "")
        context = {"vector": data.get("vector", "discover"), **data}
        result = await self.analyze(problem, context)
        return {**data, "transformed_by": self.symbol, "integration_insight": result["insight"]}
