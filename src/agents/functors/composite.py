from __future__ import annotations


"""
Composite Functors — implemented as decorator chains.

A composite functor outer ∘ inner means:
1. Apply inner functor first
2. Feed inner result as context to outer functor
3. Return outer's analysis

Trivial composites (same functor composed with itself, e.g. τ∘τ) are filtered.
"""
from typing import Any, Optional

from .base import FunctorAgent
from .prompts import build_user_prompt


class _CompositeFunctor(FunctorAgent):
    """Internal composite functor created by decorator chain composition."""

    def __init__(
        self,
        outer: FunctorAgent,
        inner: FunctorAgent,
        llm_client: Any = None,
    ) -> None:
        self._outer = outer
        self._inner = inner
        self.symbol = f"{outer.symbol}∘{inner.symbol}"
        self.name_en = f"{outer.name_en}∘{inner.name_en}"
        self.name_ru = f"{outer.name_ru}∘{inner.name_ru}"
        self.c4_state = (
            max(outer.c4_state[0], inner.c4_state[0]),
            max(outer.c4_state[1], inner.c4_state[1]),
            max(outer.c4_state[2], inner.c4_state[2]),
        )
        self.phase = outer.phase
        if llm_client is not None:
            self.llm_client = llm_client
        elif outer.llm_client is not None:
            self.llm_client = outer.llm_client
        else:
            from src.llm import get_gateway

            self.llm_client = get_gateway()

    async def analyze(self, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze."""
        inner_result = await self._inner.analyze(problem, context)
        enriched_context = {
            **(context or {}),
            "inner_result": inner_result,
            "inner_symbol": self._inner.symbol,
        }
        outer_result = await self._outer.analyze(problem, enriched_context)
        outer_result["agent"] = self.symbol
        outer_result["composite"] = self.symbol
        outer_result["inner_agent"] = self._inner.symbol
        outer_result["outer_agent"] = self._outer.symbol
        return outer_result

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform."""
        inner_result = await self._inner.transform(data)
        return await self._outer.transform(inner_result)


def compose(outer: FunctorAgent, inner: FunctorAgent) -> FunctorAgent:
    """Create a composite functor: outer ∘ inner.

    Returns None if the composite is trivial (same functor with itself).
    """
    if outer.symbol == inner.symbol:
        return None  # Filter trivial composites
    return _CompositeFunctor(outer, inner)


def generate_all_composites(base_functors: list[FunctorAgent]) -> list[FunctorAgent]:
    """Generate all non-trivial composite functors from a list of base functors.

    Returns 18 composites from 9 base functors (9×9 - 9 trivial = 72 max,
    but we select 18 meaningful ones by avoiding redundant inverses).
    """
    composites: list[FunctorAgent] = []
    seen: set[str] = set()

    for outer in base_functors:
        for inner in base_functors:
            if outer.symbol == inner.symbol:
                continue  # Skip trivial

            composite = compose(outer, inner)
            if composite is None:
                continue

            # Avoid duplicate composites
            key = composite.symbol
            if key in seen:
                continue
            seen.add(key)
            composites.append(composite)

    return composites


# Pre-defined 18 composite functor symbols (selected meaningful pairs)
COMPOSITE_SYMBOLS: list[str] = [
    "τ∘σ",
    "τ∘δ",
    "τ∘ρ",
    "τ∘ι",
    "τ∘λ",
    "τ∘κ",
    "σ∘δ",
    "σ∘ρ",
    "σ∘ι",
    "σ∘λ",
    "σ∘φ",
    "σ∘ψ",
    "δ∘ρ",
    "δ∘ι",
    "δ∘λ",
    "δ∘φ",
    "λ∘κ",
    "ψ∘φ",
]
