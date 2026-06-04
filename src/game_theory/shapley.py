from __future__ import annotations

import itertools
from math import factorial


def shapley_value(
    players: list[str],
    coalition_values: dict[tuple[str, ...], float],
) -> dict[str, float]:
    """Compute Shapley values for cooperative game theory"""
    n = len(players)
    values: dict[str, float] = {p: 0.0 for p in players}

    for player in players:
        for r in range(n):
            others = [p for p in players if p != player]
            for subset in itertools.combinations(others, r):
                # v(S U {i}) - v(S)
                with_player = tuple(sorted(list(subset) + [player]))
                without_player = tuple(sorted(subset))
                marginal = coalition_values.get(with_player, 0.0) - coalition_values.get(
                    without_player, 0.0
                )
                weight = factorial(r) * factorial(n - r - 1) / factorial(n)
                values[player] += weight * marginal

    return values
