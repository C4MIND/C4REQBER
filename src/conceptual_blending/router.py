"""
C4REQBER API: Conceptual Blending Router (/v7/conceptual-blending)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from src.auth.dev_mode import dev_mode_dependency
from src.conceptual_blending.blender import ConceptualBlender, InputSpace
from src.conceptual_blending.examples import EXAMPLES


router = APIRouter(prefix="/api/v7/conceptual-blending", tags=["v7-conceptual-blending"])

@router.post("/blend")
async def blend_inputs(
    payload: dict[str, Any] = Body(...),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Blend inputs."""
    input1_data = payload.get("input1")
    input2_data = payload.get("input2")
    blend_name = payload.get("blend_name", "blend")

    if not input1_data or not input2_data:
        raise HTTPException(status_code=400, detail="Both input1 and input2 are required")

    try:
        input1 = InputSpace(
            name=input1_data["name"],
            entities=input1_data["entities"],
            relations=[tuple(r) for r in input1_data["relations"]],
            attributes=input1_data["attributes"],
        )
        input2 = InputSpace(
            name=input2_data["name"],
            entities=input2_data["entities"],
            relations=[tuple(r) for r in input2_data["relations"]],
            attributes=input2_data["attributes"],
        )
    except (KeyError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid input space format: {e}") from e

    blender = ConceptualBlender()
    result = blender.blend(input1, input2, blend_name)

    return {
        "blend_name": result.blend_name,
        "generic_space": result.generic_space,
        "blended_entities": result.blended_entities,
        "emergent_structure": result.emergent_structure,
        "cross_space_mappings": [
            {"from_input1": m[0], "from_input2": m[1]} for m in result.cross_space_mappings
        ],
        "coherence_score": result.coherence_score,
        "input1_name": input1.name,
        "input2_name": input2.name,
    }

@router.get("/examples")
async def list_examples(
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    return {
        "examples": [
            {"key": key, "name1": data[0]["name"], "name2": data[1]["name"]}
            for key, data in EXAMPLES.items()
        ],
        "total": len(EXAMPLES),
    }

@router.get("/examples/{key}")
async def get_example(
    key: str,
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Get example."""
    if key not in EXAMPLES:
        raise HTTPException(
            status_code=404,
            detail=f"Example '{key}' not found. Available: {list(EXAMPLES.keys())}",
        )
    raw = EXAMPLES[key]
    return {"key": key, "input1": raw[0], "input2": raw[1]}

@router.post("/examples/{key}/blend")
async def blend_example(
    key: str,
    payload: dict[str, Any] = Body(default={}),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Blend example."""
    if key not in EXAMPLES:
        raise HTTPException(
            status_code=404,
            detail=f"Example '{key}' not found. Available: {list(EXAMPLES.keys())}",
        )

    data1, data2 = EXAMPLES[key]
    blend_name = payload.get("blend_name", f"{data1['name']}_{data2['name']}")

    input1 = InputSpace(
        name=data1["name"],
        entities=data1["entities"],
        relations=data1["relations"],
        attributes=data1["attributes"],
    )
    input2 = InputSpace(
        name=data2["name"],
        entities=data2["entities"],
        relations=data2["relations"],
        attributes=data2["attributes"],
    )

    blender = ConceptualBlender()
    result = blender.blend(input1, input2, blend_name)

    return {
        "blend_name": result.blend_name,
        "generic_space": result.generic_space,
        "blended_entities": result.blended_entities,
        "emergent_structure": result.emergent_structure,
        "cross_space_mappings": [
            {"from_input1": m[0], "from_input2": m[1]} for m in result.cross_space_mappings
        ],
        "coherence_score": result.coherence_score,
        "input1_name": input1.name,
        "input2_name": input2.name,
    }
