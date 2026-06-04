"""
C4REQBER: TRIZ Bridge Plugin
Direct access to 40 principles and contradiction matrix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrizBridgeResult:
    """Result of TRIZ bridge analysis."""

    problem: str
    principles: list[dict] = field(default_factory=list)  # type: ignore[type-arg]
    contradiction: dict | None = None  # type: ignore[type-arg]
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "principles": self.principles,
            "contradiction": self.contradiction,
            "suggestions": self.suggestions,
        }


def analyze(problem: str, max_principles: int = 5) -> TrizBridgeResult:
    """Apply TRIZ principles to problem."""
    from src.triz.bridge import TRIZ_PRINCIPLES  # type: ignore[attr-defined]
    from src.triz.contradiction_matrix import get_contradiction_matrix

    result = TrizBridgeResult(problem=problem)

    # Try to find contradiction
    matrix = get_contradiction_matrix()
    improve, worsen = matrix.suggest_parameters(problem)

    if improve and worsen:
        cell = matrix.get_principles(improve, worsen)
        if cell:
            result.contradiction = {
                "improve": matrix.get_parameter_name(improve),
                "worsen": matrix.get_parameter_name(worsen),
                "principles": cell.principles,
            }
            for p in cell.principles[:max_principles]:
                if p in TRIZ_PRINCIPLES:
                    result.principles.append(
                        {
                            "id": p,
                            "name": TRIZ_PRINCIPLES[p]["name"],  # type: ignore[index]
                            "description": TRIZ_PRINCIPLES[p]["description"][:100],  # type: ignore[index]
                        }
                    )

    if not result.principles:
        # Fallback: suggest generic principles
        generic = [1, 15, 29, 28, 2]  # Segmentation, Dynamics, Pneumatics, Mechanics, Extraction
        for p in generic[:max_principles]:
            if p in TRIZ_PRINCIPLES:
                result.principles.append(
                    {
                        "id": p,
                        "name": TRIZ_PRINCIPLES[p]["name"],  # type: ignore[index]
                        "description": TRIZ_PRINCIPLES[p]["description"][:100],  # type: ignore[index]
                    }
                )

    result.suggestions = [f"Apply principle {p['id']} ({p['name']})" for p in result.principles]

    return result


def execute(problem: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(problem, **kwargs).to_dict()
