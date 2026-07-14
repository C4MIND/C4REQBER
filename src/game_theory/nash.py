from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NashEquilibrium:
    """NashEquilibrium."""
    strategies: list[int]
    payoffs: list[float]
    is_pure: bool

def find_pure_nash(payoff_matrix: list[list[list[float]]]) -> list[NashEquilibrium]:
    """Find pure Nash equilibria in a normal-form game"""
    n_players = len(payoff_matrix)
    if n_players == 0:
        return []

    equilibria: list[NashEquilibrium] = []

    n_rows = len(payoff_matrix[0])
    n_cols = len(payoff_matrix[0][0])

    for s1 in range(n_rows):
        for s2 in range(n_cols):
            profile = [s1, s2]
            is_nash = True

            # Check player 1 deviations
            p1_current = payoff_matrix[0][s1][s2]
            for alt_s1 in range(n_rows):
                if alt_s1 != s1 and payoff_matrix[0][alt_s1][s2] > p1_current:
                    is_nash = False
                    break
            if not is_nash:
                continue

            # Check player 2 deviations
            p2_current = payoff_matrix[1][s1][s2]
            for alt_s2 in range(n_cols):
                if alt_s2 != s2 and payoff_matrix[1][s1][alt_s2] > p2_current:
                    is_nash = False
                    break

            if is_nash:
                equilibria.append(
                    NashEquilibrium(
                        strategies=list(profile),
                        payoffs=[payoff_matrix[0][s1][s2], payoff_matrix[1][s1][s2]],
                        is_pure=True,
                    )
                )

    return equilibria
