from __future__ import annotations


"""Инверсия (Inversion) — Functor Agent ι."""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import FUNCTOR_SYSTEM_PROMPTS, build_user_prompt


class InversionAgent(FunctorAgent):
    """InversionAgent."""
    symbol = "ι"
    name_ru = "Инверсия"
    name_en = "Inversion"
    c4_state: tuple[int, int, int] = (0, 0, 2)
    phase = "сеть"

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        system = FUNCTOR_SYSTEM_PROMPTS["ι_inversion"]
        user = build_user_prompt(problem, context.get("vector", "discover") if context else "discover", context)
        insight = await self._llm_generate(system, user)
        has_contradiction = "opposite" in insight.lower() or "wrong" in insight.lower() or "not" in insight.lower()
        return self._build_result(
            problem,
            insight,
            confidence=0.80,
            contradiction=f"Inversion reveals tension: {problem[:40]}" if has_contradiction else None,
            novel=True,
        )

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        problem = data.get("problem", "")
        context = {"vector": data.get("vector", "discover"), **data}
        result = await self.analyze(problem, context)
        return {**data, "transformed_by": self.symbol, "inversion_insight": result["insight"], "contradiction": result.get("contradiction")}
