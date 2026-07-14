"""Robust Decision Making API Router — /v7/robust"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.robust_decisions.prim import prim_analysis
from src.robust_decisions.xlrm import XLMRModel, explore_scenarios


router = APIRouter(prefix="/api/v7/robust", tags=["robust-decisions"])

@router.post("/explore")
async def explore(request: dict[str, Any]) -> dict[str, Any]:
    """
    Explore scenarios using XLRM framework.

    Body:
    {
        "uncertainties": [{"name": "...", "range": [min, max], "unit": "..."}],
        "levers": [{"name": "...", "options": ["A", "B"]}],
        "relationships": ["Metric = f(...)"],
        "metrics": ["metric_1", ...],
        "n_scenarios": 1000,
        "threshold": 0.5
    }
    """
    uncertainties: list[dict[str, Any]] = request.get("uncertainties", [])
    levers: list[dict[str, Any]] = request.get("levers", [])
    relationships: list[str] = request.get("relationships", [])
    metrics: list[str] = request.get("metrics", [])
    n_scenarios: int = request.get("n_scenarios", 1000)
    threshold: float = request.get("threshold", 0.5)

    if not uncertainties:
        raise HTTPException(status_code=400, detail="uncertainties is required")
    if not levers:
        raise HTTPException(status_code=400, detail="levers is required")

    # Validate uncertainty ranges
    for i, u in enumerate(uncertainties):
        if "name" not in u:
            raise HTTPException(
                status_code=400, detail=f"uncertainty[{i}] missing 'name'"
            )
        if "range" not in u or len(u["range"]) != 2:
            raise HTTPException(
                status_code=400,
                detail=f"uncertainty[{i}] missing 'range' [min, max]",
            )

    model = XLMRModel(
        uncertainties=uncertainties,
        levers=levers,
        relationships=relationships,
        metrics=metrics,
    )

    result = explore_scenarios(
        model, n_scenarios=n_scenarios, threshold=threshold
    )

    return {
        "scenarios_explored": result.scenarios_explored,
        "robust_strategies": result.robust_strategies,
        "vulnerability_map": result.vulnerability_map,
        "regret_analysis": result.regret_analysis,
    }

@router.post("/discover")
async def discover(request: dict[str, Any]) -> dict[str, Any]:
    """
    Discover scenario boxes using PRIM analysis.

    Body:
    {
        "data": [{"x": 0.5, "y": 1.2, "outcome": 1.0}, ...],
        "outcome_key": "outcome",
        "target_coverage": 0.25,
        "target_density": 0.5,
        "max_boxes": 3
    }
    """
    data: list[dict[str, Any]] = request.get("data", [])
    outcome_key: str = request.get("outcome_key", "")
    target_coverage: float = request.get("target_coverage", 0.25)
    target_density: float = request.get("target_density", 0.5)
    max_boxes: int = request.get("max_boxes", 3)

    if not data:
        raise HTTPException(status_code=400, detail="data is required")
    if not outcome_key:
        raise HTTPException(status_code=400, detail="outcome_key is required")

    boxes = prim_analysis(
        data,
        outcome_key=outcome_key,
        target_coverage=target_coverage,
        target_density=target_density,
        max_boxes=max_boxes,
    )

    return {
        "boxes": [
            {
                "dimensions": box.dimensions,
                "coverage": round(box.coverage, 4),
                "density": round(box.density, 4),
                "mean_outcome": round(box.mean_outcome, 4),
            }
            for box in boxes
        ],
        "total_boxes": len(boxes),
    }

@router.get("/methods")
async def list_methods() -> dict[str, Any]:
    """List available RDM methods and their descriptions."""
    return {
        "methods": [
            {
                "name": "XLRM Scenario Exploration",
                "endpoint": "POST /v7/robust/explore",
                "description": (
                    "Explore scenarios using Latin Hypercube Sampling across "
                    "uncertainties and policy levers. Identifies robust strategies "
                    "that perform above a threshold across many futures."
                ),
                "fields": [
                    "uncertainties",
                    "levers",
                    "relationships",
                    "metrics",
                    "n_scenarios",
                    "threshold",
                ],
            },
            {
                "name": "PRIM Scenario Discovery",
                "endpoint": "POST /v7/robust/discover",
                "description": (
                    "Patient Rule Induction Method — discovers interpretable "
                    "rectangular boxes in parameter space where outcomes of "
                    "interest are concentrated. Produces coverage/density metrics."
                ),
                "fields": [
                    "data",
                    "outcome_key",
                    "target_coverage",
                    "target_density",
                    "max_boxes",
                ],
            },
        ],
        "methodology": "XLRM + PRIM — Robust Decision Making (RAND Corporation)",
    }
