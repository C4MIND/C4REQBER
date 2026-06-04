"""TOPSIS — Technique for Order Preference by Similarity to Ideal Solution"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TOPSISResult:
    """TOPSISResult."""
    ranks: list[tuple[str, float]]
    ideal_best: list[float]
    ideal_worst: list[float]
    distances_to_best: dict[str, float]
    distances_to_worst: dict[str, float]

def topsis(
    matrix: list[list[float]],
    alternatives: list[str],
    weights: list[float],
    benefits: list[bool],
) -> TOPSISResult:
    """Topsis."""
    m, n = len(matrix), len(matrix[0])

    col_norms = [(sum(row[j] ** 2 for row in matrix)) ** 0.5 for j in range(n)]
    norm_matrix = [
        [matrix[i][j] / col_norms[j] if col_norms[j] else 0 for j in range(n)]
        for i in range(m)
    ]

    weighted = [
        [norm_matrix[i][j] * weights[j] for j in range(n)] for i in range(m)
    ]

    ideal_best: list[float] = []
    ideal_worst: list[float] = []
    for j in range(n):
        col = [weighted[i][j] for i in range(m)]
        if benefits[j]:
            ideal_best.append(max(col))
            ideal_worst.append(min(col))
        else:
            ideal_best.append(min(col))
            ideal_worst.append(max(col))

    d_best: dict[str, float] = {}
    d_worst: dict[str, float] = {}
    for i, alt in enumerate(alternatives):
        db = (sum((weighted[i][j] - ideal_best[j]) ** 2 for j in range(n))) ** 0.5
        dw = (sum((weighted[i][j] - ideal_worst[j]) ** 2 for j in range(n))) ** 0.5
        d_best[alt] = db
        d_worst[alt] = dw

    closeness: list[tuple[str, float]] = [
        (
            alt,
            d_worst[alt] / (d_best[alt] + d_worst[alt])
            if (d_best[alt] + d_worst[alt])
            else 0.0,
        )
        for alt in alternatives
    ]
    closeness.sort(key=lambda x: x[1], reverse=True)

    return TOPSISResult(
        ranks=closeness,
        ideal_best=ideal_best,
        ideal_worst=ideal_worst,
        distances_to_best=d_best,
        distances_to_worst=d_worst,
    )
