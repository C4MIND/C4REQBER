"""Analytic Hierarchy Process (AHP)"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AHPResult:
    """AHPResult."""
    criteria_weights: dict[str, float]
    alternative_scores: dict[str, dict[str, float]]
    final_ranks: list[tuple[str, float]]
    consistency_ratio: float
    is_consistent: bool

def ahp(
    pairwise_matrix: list[list[float]],
    criteria: list[str],
    alternatives: list[str],
    alt_scores: dict[str, list[float]],
) -> AHPResult:
    """Ahp."""
    n = len(pairwise_matrix)
    col_sums = [sum(row[c] for row in pairwise_matrix) for c in range(n)]
    norm_matrix = [
        [pairwise_matrix[r][c] / col_sums[c] if col_sums[c] else 0 for c in range(n)]
        for r in range(n)
    ]
    weights = [sum(row) / n for row in norm_matrix]

    weighted_sum = [
        sum(pairwise_matrix[i][j] * weights[j] for j in range(n)) for i in range(n)
    ]
    lambda_max = (
        sum(ws / w for ws, w in zip(weighted_sum, weights)) / n  # noqa: B905
        if all(w > 0 for w in weights)
        else 0
    )
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0
    ri_values = {
        1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24,
        7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    }
    ri = ri_values.get(n, n / 10 + 0.5)
    cr = ci / ri if ri else 0

    crit_weights = dict(zip(criteria, weights))  # noqa: B905
    scores: dict[str, dict[str, float]] = {}
    for alt in alternatives:
        sc = alt_scores.get(alt, [0.0] * n)
        scores[alt] = dict(zip(criteria, sc))  # noqa: B905

    final: list[tuple[str, float]] = []
    for alt in alternatives:
        s = sum(scores[alt].get(c, 0.0) * crit_weights.get(c, 0.0) for c in criteria)
        final.append((alt, s))
    final.sort(key=lambda x: x[1], reverse=True)

    return AHPResult(
        criteria_weights=crit_weights,
        alternative_scores=scores,
        final_ranks=final,
        consistency_ratio=cr,
        is_consistent=cr < 0.1,
    )
