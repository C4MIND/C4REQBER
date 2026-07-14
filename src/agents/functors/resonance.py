from __future__ import annotations


"""Резонанс (Resonance) — Functor Agent ρ."""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import FUNCTOR_SYSTEM_PROMPTS, build_user_prompt


class ResonanceAgent(FunctorAgent):
    """ResonanceAgent."""
    symbol = "ρ"
    name_ru = "Резонанс"
    name_en = "Resonance"
    c4_state: tuple[int, int, int] = (1, 0, 1)
    phase = "модуляция"

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        system = FUNCTOR_SYSTEM_PROMPTS["ρ_resonance"]
        user = build_user_prompt(problem, context.get("vector", "discover") if context else "discover", context)
        insight = await self._llm_generate(system, user)
        return self._build_result(problem, insight, confidence=0.74)

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        problem = data.get("problem", "")
        context = {"vector": data.get("vector", "discover"), **data}
        result = await self.analyze(problem, context)
        return {**data, "transformed_by": self.symbol, "resonance_insight": result["insight"]}
