"""PRIM — Patient Rule Induction Method for scenario discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PRIMBox:
    """PRIMBox."""
    dimensions: dict[str, tuple[float, float]]
    coverage: float
    density: float
    mean_outcome: float

def prim_analysis(
    data: list[dict[str, Any]],
    outcome_key: str,
    target_coverage: float = 0.25,
    target_density: float = 0.5,
    max_boxes: int = 3,
) -> list[PRIMBox]:
    """Discover interpretable scenario boxes that describe regions of interest."""
    boxes: list[PRIMBox] = []
    remaining: list[dict[str, Any]] = data.copy()

    for _ in range(max_boxes):
        if len(remaining) < 2:
            break

        best_box: tuple[str, float, float, list[dict[str, Any]], float] | None = None
        best_density: float = 0.0

        for key in remaining[0]:
            if key == outcome_key or not isinstance(remaining[0][key], (int, float)):
                continue
            values = [d[key] for d in remaining]
            lo: float = sorted(values)[len(values) // 4]
            hi: float = sorted(values)[len(values) * 3 // 4]

            in_box = [d for d in remaining if lo <= d.get(key, 0) <= hi]
            if len(in_box) / len(remaining) >= target_coverage:
                positive = sum(1 for d in in_box if d.get(outcome_key, 0) > 0)
                density = positive / len(in_box) if in_box else 0.0
                if density > best_density:
                    best_density = density
                    best_box = (key, lo, hi, in_box, density)

        if best_box:
            k, lo, hi, in_box_local, den = best_box
            boxes.append(
                PRIMBox(
                    dimensions={k: (lo, hi)},
                    coverage=len(in_box_local) / len(data),
                    density=den,
                    mean_outcome=(
                        sum(d.get(outcome_key, 0) for d in in_box_local) / len(in_box_local)
                        if in_box_local
                        else 0.0
                    ),
                )
            )
            remaining = [d for d in remaining if d not in in_box_local]
        else:
            break

    return boxes
