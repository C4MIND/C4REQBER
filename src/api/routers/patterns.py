"""
C4REQBER API: Pattern Router
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.dependencies import sanitize_json
from src.patterns.runner import get_runner as get_pattern_runner


router = APIRouter(prefix="/api/v1/patterns", tags=["patterns"])

_PATTERN_CATEGORIES = [
    (
        "physics",
        frozenset(
            [
                "cfd",
                "fdtd",
                "maxwell",
                "n_body",
                "plasma",
                "quantum",
                "wave",
                "thermal",
                "elasticity",
                "acoustic",
                "poisson",
                "rigid_body",
                "dft",
                "qft",
            ]
        ),
    ),
    (
        "biology",
        frozenset(
            [
                "neural",
                "gene",
                "epidemic",
                "enzyme",
                "protein",
                "connectome",
                "evolutionary",
                "synaptic",
                "signal",
                "hodgkin",
                "pharmacokinetics",
                "age_structured",
                "lotka",
            ]
        ),
    ),
    (
        "economics",
        frozenset(
            [
                "dsge",
                "garch",
                "game_theory",
                "portfolio",
                "credit",
                "supply_chain",
                "economic",
                "input_output",
                "gravity_trade",
                "market_microstructure",
                "option_pricing",
                "prospect_theory",
                "overlapping_generations",
                "search_matching",
                "herding",
                "heterogeneous",
            ]
        ),
    ),
    (
        "earth_science",
        frozenset(
            [
                "climate",
                "ocean",
                "seismic",
                "wildfire",
                "air_quality",
                "biogeochemistry",
                "cloud",
                "groundwater",
                "land_surface",
                "land_use",
                "mantle",
                "geomagnetic",
                "sea_ice",
                "surface_water",
            ]
        ),
    ),
    (
        "engineering",
        frozenset(
            [
                "mpc",
                "kalman",
                "slam",
                "path_planning",
                "pid",
                "circuit",
                "composite",
                "crystal",
                "fem",
                "continuum",
                "inverse_kinematics",
                "model_predictive",
                "circuit_simulation",
            ]
        ),
    ),
    (
        "social",
        frozenset(
            [
                "social_network",
                "opinion",
                "cultural",
                "migration",
                "urban",
                "conflict",
                "collaborative",
                "pedestrian",
                "rumor",
                "language",
            ]
        ),
    ),
]


def _categorize_pattern(p: str) -> str:
    for cat, keys in _PATTERN_CATEGORIES:
        if any(k in p for k in keys):
            return cat
    return "other"


pattern_runner = get_pattern_runner()


@router.get("")
async def list_patterns() -> dict[str, Any]:
    """List patterns."""
    patterns = pattern_runner.list_patterns()
    categories: dict[str, list[str]] = {}
    for p in patterns:
        cat = _categorize_pattern(p)
        categories.setdefault(cat, []).append(p)
    return {
        "patterns": patterns,
        "count": len(patterns),
        "total_files": len(patterns),
        "version": "v6.5",
        "categories": categories,
        "load_errors": 0,
    }


@router.get("/{pattern_id}")
async def get_pattern(pattern_id: str) -> dict[str, Any]:
    """Get pattern."""
    meta = pattern_runner.get_metadata(pattern_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    meta["resources"] = pattern_runner.estimate_resources(pattern_id)
    return meta


@router.post("/{pattern_id}/run")
async def run_pattern(
    pattern_id: str, payload: dict[str, Any] | None = None
) -> Any:
    """Run pattern."""
    payload = payload or {}
    if pattern_id not in pattern_runner.list_patterns():
        raise HTTPException(
            status_code=404, detail="Pattern not found or failed to load"
        )
    result = await pattern_runner.run_pattern(
        pattern_id,
        hypothesis=payload.get("hypothesis"),
        params=payload.get("params"),
    )
    return sanitize_json(result)
