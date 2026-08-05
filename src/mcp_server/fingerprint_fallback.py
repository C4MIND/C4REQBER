"""Heuristic / FRA fingerprint fallback for MCP c4_fingerprint."""

from __future__ import annotations

from typing import Any


def fra_or_heuristic_fingerprint(problem: str, space: Any) -> dict[str, Any]:
    """Classify via FRARouter, else C4Space heuristic."""
    try:
        from src.c4.routing import FRARouter

        router = FRARouter()
        state = router.classify_c4_state(problem)
    except (ImportError, AttributeError):
        state = space._heuristic_classify(problem)
        return {
            "problem": problem,
            "state": list(state.to_tuple()),
            "fingerprint": str(state),
            "backend": "heuristic",
            "heuristic": True,
        }
    return {
        "problem": problem,
        "state": list(state.to_tuple()),
        "fingerprint": str(state),
        "backend": "fra_router",
        "heuristic": False,
    }
