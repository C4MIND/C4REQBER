"""
C4REQBER API: C4-TRIZ Bridge Router
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.dependencies import sanitize_json
from src.triz.bridge import (
    generate_c4_triz_path as _triz_generate_c4_triz_path,
)
from src.triz.bridge import (
    get_c4_triz_bridge_obj,
    recommend_for_contradiction,
)
from src.triz.bridge import get_c4_triz_mapping as build_triz_mapping


router = APIRouter(prefix="/api/v1/bridge", tags=["bridge"])


@router.get("/principles")
async def get_triz_principles() -> list[dict[str, Any]]:
    """Get triz principles."""
    principles = get_c4_triz_bridge_obj().get_all_principles()
    return [
        {
            "number": p.number,
            "name": p.name,
            "description": p.description,
            "examples": p.examples,
            "sub_principles": [sp.name for sp in p.sub_principles],
        }
        for p in principles
    ]


@router.get("/mapping")
async def get_c4_triz_mapping() -> dict[str, Any]:
    """Get c4 triz mapping."""
    bridge = get_c4_triz_bridge_obj()
    mapping = build_triz_mapping()
    return {
        "c4_to_triz": mapping,
        "triz_to_c4": {"note": "principles_to_operators"},
        "principle_count": len(bridge.get_all_principles()),
    }


@router.post("/contradiction")
async def solve_contradiction(payload: dict[str, Any]) -> dict[str, Any]:
    """Solve contradiction."""
    improving = payload.get("improving", "")
    worsening = payload.get("worsening", "")

    if not improving or not worsening:
        raise HTTPException(
            status_code=400,
            detail="Both 'improving' and 'worsening' parameters required",
        )

    result = recommend_for_contradiction(improving, worsening)
    return {
        "triz_principles": result["triz_principles"],
        "c4_operators": result["c4_operators"],
        "principle_details": [
            {
                "number": p.number,
                "name": p.name,
                "description": p.description,
                "examples": p.examples,
            }
            for p in result["principle_details"]  # type: ignore[attr-defined]
            if p
        ],
    }


@router.post("/path")
async def generate_c4_triz_path(payload: dict[str, Any]) -> Any:
    """Generate c4 triz path."""
    problem = payload.get("problem", "")
    contradiction = payload.get("contradiction", ["", ""])

    if len(contradiction) != 2:
        raise HTTPException(
            status_code=400, detail="Contradiction must be [improve, worsen]"
        )

    result = _triz_generate_c4_triz_path(problem, tuple(contradiction))
    return sanitize_json(result)
