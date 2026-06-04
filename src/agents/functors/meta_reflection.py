from __future__ import annotations


"""Мета-рефлексия (Meta-Reflection) — Functor Agent ψ."""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import FUNCTOR_SYSTEM_PROMPTS, build_user_prompt


class MetaReflectionAgent(FunctorAgent):
    """MetaReflectionAgent."""
    symbol = "ψ"
    name_ru = "Мета-рефлексия"
    name_en = "Meta-Reflection"
    c4_state: tuple[int, int, int] = (2, 2, 2)
    phase = "интеграция"

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        system = FUNCTOR_SYSTEM_PROMPTS["ψ_meta_reflection"]
        user = build_user_prompt(problem, context.get("vector", "discover") if context else "discover", context)
        insight = await self._llm_generate(system, user)
        return self._build_result(problem, insight, confidence=0.81)

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        problem = data.get("problem", "")
        context = {"vector": data.get("vector", "discover"), **data}
        result = await self.analyze(problem, context)
        return {**data, "transformed_by": self.symbol, "meta_reflection_insight": result["insight"]}
