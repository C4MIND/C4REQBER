"""Decision Engine API Router — /v7/decisions"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.decisions.ahp import ahp
from src.decisions.topsis import topsis


router = APIRouter(prefix="/api/v7/decisions", tags=["decisions"])

@router.post("/ahp", response_model=dict[str, Any])
async def ahp_endpoint(request: dict[str, Any]) -> dict[str, Any]:
    """
    Run Analytic Hierarchy Process (AHP).

    Body:
    {
        "pairwise_matrix": [[1, 3, 5], [0.333, 1, 3], [0.2, 0.333, 1]],
        "criteria": ["Cost", "Speed", "Quality"],
        "alternatives": ["A", "B", "C"],
        "alt_scores": {"A": [0.5, 0.7, 0.9], "B": [0.3, 0.8, 0.6], "C": [0.9, 0.4, 0.5]}
    }
    """
    pairwise_matrix: list[list[float]] = request.get("pairwise_matrix", [])
    criteria: list[str] = request.get("criteria", [])
    alternatives: list[str] = request.get("alternatives", [])
    alt_scores: dict[str, list[float]] = request.get("alt_scores", {})

    if not pairwise_matrix:
        raise HTTPException(status_code=400, detail="pairwise_matrix is required")
    if not criteria:
        raise HTTPException(status_code=400, detail="criteria is required")
    if not alternatives:
        raise HTTPException(status_code=400, detail="alternatives is required")

    result = ahp(pairwise_matrix, criteria, alternatives, alt_scores)
    return {
        "criteria_weights": result.criteria_weights,
        "alternative_scores": {k: dict(v) for k, v in result.alternative_scores.items()},
        "final_ranks": [{"alternative": alt, "score": score} for alt, score in result.final_ranks],
        "consistency_ratio": result.consistency_ratio,
        "is_consistent": result.is_consistent,
    }

@router.post("/topsis", response_model=dict[str, Any])
async def topsis_endpoint(request: dict[str, Any]) -> dict[str, Any]:
    """
    Run TOPSIS multi-criteria decision making.

    Body:
    {
        "matrix": [[250, 16, 12], [200, 20, 10], [300, 14, 15]],
        "alternatives": ["Laptop A", "Laptop B", "Laptop C"],
        "weights": [0.4, 0.35, 0.25],
        "benefits": [false, true, true]
    }
    """
    matrix: list[list[float]] = request.get("matrix", [])
    alternatives: list[str] = request.get("alternatives", [])
    weights: list[float] = request.get("weights", [])
    benefits: list[bool] = request.get("benefits", [])

    if not matrix:
        raise HTTPException(status_code=400, detail="matrix is required")
    if not alternatives:
        raise HTTPException(status_code=400, detail="alternatives is required")
    if not weights:
        raise HTTPException(status_code=400, detail="weights is required")
    if not benefits:
        raise HTTPException(status_code=400, detail="benefits is required")

    result = topsis(matrix, alternatives, weights, benefits)
    return {
        "ranks": [{"alternative": alt, "closeness": score} for alt, score in result.ranks],
        "ideal_best": result.ideal_best,
        "ideal_worst": result.ideal_worst,
        "distances_to_best": dict(result.distances_to_best),
        "distances_to_worst": dict(result.distances_to_worst),
    }

@router.get("/methods")
async def list_methods() -> dict[str, Any]:
    """List available decision methods and their descriptions."""
    return {
        "methods": [
            {
                "name": "Analytic Hierarchy Process (AHP)",
                "endpoint": "POST /v7/decisions/ahp",
                "description": "Multi-criteria decision making via pairwise comparisons. "
                "Derives criteria weights from comparison matrix, scores alternatives, "
                "and checks consistency ratio.",
                "fields": ["pairwise_matrix", "criteria", "alternatives", "alt_scores"],
            },
            {
                "name": "TOPSIS",
                "endpoint": "POST /v7/decisions/topsis",
                "description": "Technique for Order Preference by Similarity to Ideal Solution. "
                "Ranks alternatives by closeness to ideal best and distance from ideal worst.",
                "fields": ["matrix", "alternatives", "weights", "benefits"],
            },
        ],
        "philosophy": "Multi-Criteria Decision Making (MCDM): AHP + TOPSIS",
    }
