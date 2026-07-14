"""Game Theory API Router — /v7/game-theory"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.game_theory.nash import NashEquilibrium, find_pure_nash
from src.game_theory.shapley import shapley_value


router = APIRouter(prefix="/api/v7/game-theory", tags=["game-theory"])

@router.post("/nash", response_model=list[NashEquilibrium])
async def nash_equilibria(request: dict[str, Any]) -> list[NashEquilibrium]:
    """
    Find pure Nash equilibria in a normal-form game.

    Body:
    {
        "payoff_matrix": [[[3, 3], [0, 5]], [[5, 0], [1, 1]]]
    }
    """
    payoff = request.get("payoff_matrix")
    if not payoff:
        raise HTTPException(status_code=400, detail="payoff_matrix is required")

    return find_pure_nash(payoff)

@router.post("/shapley", response_model=dict[str, float])
async def shapley(request: dict[str, Any]) -> dict[str, float]:
    """
    Compute Shapley values for cooperative game theory.

    Body:
    {
        "players": ["A", "B", "C"],
        "coalition_values": {"A": 0, "B": 0, "C": 0, "AB": 100, "AC": 80, "BC": 60, "ABC": 120}
    }
    """
    players = request.get("players", [])
    raw_values = request.get("coalition_values", {})

    if not players:
        raise HTTPException(status_code=400, detail="players is required")
    if not raw_values:
        raise HTTPException(status_code=400, detail="coalition_values is required")

    coalition_values: dict[tuple[str, ...], float] = {}
    for key, val in raw_values.items():
        coalition_values[tuple(sorted(key))] = float(val)

    return shapley_value(players, coalition_values)

@router.get("/methods")
async def list_methods() -> dict[str, Any]:
    """List available game theory methods and their descriptions."""
    return {
        "methods": [
            {
                "name": "Pure Nash Equilibrium",
                "endpoint": "POST /v7/game-theory/nash",
                "description": "Find all pure-strategy Nash equilibria in a normal-form game. "
                "Payoff matrix format: [[[p1_s1_p2_s1, p1_s1_p2_s2], ...], ...]",
                "fields": ["payoff_matrix"],
            },
            {
                "name": "Shapley Value",
                "endpoint": "POST /v7/game-theory/shapley",
                "description": "Compute Shapley values for fair contribution distribution "
                "in cooperative games. Players keyed by coalition tuple[Any, ...].",
                "fields": ["players", "coalition_values"],
            },
        ],
        "philosophy": "Non-cooperative (Nash) + Cooperative (Shapley) game theory",
    }
