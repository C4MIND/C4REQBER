"""
C4REQBER: Pareto Analysis Plugin
80/20 rule prioritization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParetoResult:
    """Result of Pareto analysis."""

    items: list[dict[str, Any]]
    vital_few: list[dict] = field(default_factory=list)  # type: ignore[type-arg]
    trivial_many: list[dict] = field(default_factory=list)  # type: ignore[type-arg]
    cumulative_percentage: list[float] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": self.items,
            "vital_few": self.vital_few,
            "trivial_many": self.trivial_many,
            "cumulative_percentage": self.cumulative_percentage,
            "recommendation": self.recommendation,
        }


def analyze(items: list[dict[str, Any]], value_key: str = "value") -> ParetoResult:
    """Apply Pareto analysis.

    Args:
        items: List of dicts with at least value_key
        value_key: Key to sort by
    """
    result = ParetoResult(items=items)

    # Sort by value descending
    sorted_items = sorted(items, key=lambda x: x.get(value_key, 0), reverse=True)
    total = sum(x.get(value_key, 0) for x in sorted_items)

    if total == 0:
        return result

    cumulative = 0.0
    for item in sorted_items:
        cumulative += item.get(value_key, 0) / total
        result.cumulative_percentage.append(round(cumulative * 100, 1))

    # Split at 80%
    cutoff = next(
        (i for i, p in enumerate(result.cumulative_percentage) if p >= 80), len(sorted_items)
    )
    result.vital_few = sorted_items[:cutoff]
    result.trivial_many = sorted_items[cutoff:]

    result.recommendation = (
        f"Focus on top {cutoff} items ({cutoff}/{len(sorted_items)} = {cutoff / len(sorted_items):.0%}) "
        f"which deliver {result.cumulative_percentage[cutoff - 1]:.0%} of total value. "
        f"Deprioritize or eliminate the remaining {len(sorted_items) - cutoff}."
    )

    return result


def execute(items: list[dict], **kwargs: Any) -> dict[str, Any]:  # type: ignore[type-arg]
    return analyze(items, **kwargs).to_dict()
