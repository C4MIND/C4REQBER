from __future__ import annotations


"""Темпоральность (Temporal) — Functor Agent τ."""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import FUNCTOR_SYSTEM_PROMPTS, build_user_prompt


class TemporalAgent(FunctorAgent):
    """TemporalAgent."""
    symbol = "τ"
    name_ru = "Темпоральность"
    name_en = "Temporal"
    c4_state: tuple[int, int, int] = (2, 0, 0)
    phase = "дивергенция"

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        system = FUNCTOR_SYSTEM_PROMPTS["τ_temporal"]
        user = build_user_prompt(problem, context.get("vector", "discover") if context else "discover", context)
        insight = await self._llm_generate(system, user)
        return self._build_result(problem, insight, confidence=0.78)

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        problem = data.get("problem", "")
        context = {"vector": data.get("vector", "discover"), **data}
        result = await self.analyze(problem, context)
        return {**data, "transformed_by": self.symbol, "temporal_insight": result["insight"]}
