from __future__ import annotations


"""Дифференциация (Distinction) — Functor Agent δ."""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import FUNCTOR_SYSTEM_PROMPTS, build_user_prompt


class DistinctionAgent(FunctorAgent):
    """DistinctionAgent."""
    symbol = "δ"
    name_ru = "Дифференциация"
    name_en = "Distinction"
    c4_state: tuple[int, int, int] = (0, 1, 0)
    phase = "модуляция"

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        system = FUNCTOR_SYSTEM_PROMPTS["δ_distinction"]
        user = build_user_prompt(problem, context.get("vector", "discover") if context else "discover", context)
        insight = await self._llm_generate(system, user)
        # Distinction often surfaces contradictions
        has_contradiction = "false" in insight.lower() or "dichotomy" in insight.lower()
        return self._build_result(
            problem,
            insight,
            confidence=0.82,
            contradiction=f"Detected boundary tension in: {problem[:40]}" if has_contradiction else None,
        )

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        problem = data.get("problem", "")
        context = {"vector": data.get("vector", "discover"), **data}
        result = await self.analyze(problem, context)
        return {**data, "transformed_by": self.symbol, "distinction_insight": result["insight"], "contradiction": result.get("contradiction")}
