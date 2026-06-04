"""DoE API Router — /v7/doe"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.experiment_design.doe import (
    DesignType,
    DoEConfig,
    Factor,
    fractional_factorial_design,
    full_factorial_design,
    generate_design,
    latin_hypercube_sampling,
)
from src.experiment_design.power import ttest_sample_size


router = APIRouter(prefix="/api/v7/doe", tags=["v7-doe"])

class FactorSpec(BaseModel):
    """FactorSpec."""
    name: str
    low: float
    high: float
    levels: int = 2

class DoERequest(BaseModel):
    """DoERequest."""
    factors: list[FactorSpec]
    design_type: str = "full_factorial"
    replicates: int = 1
    random_seed: int | None = None
    samples: int = 10
    alpha: str = "rotatable"
    center_points: int = 4
    resolution: int | None = None
    blocks: int | None = None

class FullFactorialRequest(BaseModel):
    """FullFactorialRequest."""
    factors: dict[str, list[Any]]

class FractionalFactorialRequest(BaseModel):
    """FractionalFactorialRequest."""
    factors: dict[str, list[Any]]
    fraction: int = 2

class LHSRequest(BaseModel):
    """LHSRequest."""
    n_factors: int
    n_samples: int
    bounds: list[tuple[float, float]]
    seed: int | None = None

class PowerAnalysisRequest(BaseModel):
    """PowerAnalysisRequest."""
    effect_size: float
    alpha: float = 0.05
    power: float = 0.8
    design: str = "two_sample"

@router.post("/generate")
async def api_generate_design(request: DoERequest) -> dict[str, Any]:
    """Api generate design."""
    try:
        dt = DesignType[request.design_type.upper()]
    except KeyError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown design_type: {request.design_type}. "
            f"Available: {[d.name for d in DesignType]}",
        ) from err

    factors = [
        Factor(name=f.name, low=f.low, high=f.high, levels=f.levels)
        for f in request.factors
    ]
    config = DoEConfig(
        factors=factors,
        design_type=dt,
        replicates=request.replicates,
        random_seed=request.random_seed,
        samples=request.samples,
        alpha=request.alpha,
        center_points=request.center_points,
        resolution=request.resolution,
        blocks=request.blocks,
    )

    try:
        result = generate_design(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return result.to_dict()

@router.post("/full-factorial")
async def api_full_factorial(request: FullFactorialRequest) -> dict[str, Any]:
    """Api full factorial."""
    factors = [
        Factor(name=k, low=min(v), high=max(v), levels=len(v))
        for k, v in request.factors.items()
    ]
    config = DoEConfig(factors=factors, design_type=DesignType.FULL_FACTORIAL)
    result = full_factorial_design(config)
    return result.to_dict()

@router.post("/fractional-factorial")
async def api_fractional_factorial(
    request: FractionalFactorialRequest,
) -> dict[str, Any]:
    """Api fractional factorial."""
    factors = [
        Factor(name=k, low=min(v), high=max(v), levels=len(v))
        for k, v in request.factors.items()
    ]
    resolution = max(3, len(factors) - request.fraction + 1)
    config = DoEConfig(
        factors=factors,
        design_type=DesignType.FRACTIONAL_FACTORIAL,
        resolution=resolution,
    )
    result = fractional_factorial_design(config)
    return result.to_dict()

@router.post("/latin-hypercube")
async def api_latin_hypercube(request: LHSRequest) -> dict[str, Any]:
    """Api latin hypercube."""
    if len(request.bounds) != request.n_factors:
        raise HTTPException(
            status_code=400,
            detail=f"bounds length ({len(request.bounds)}) != n_factors ({request.n_factors})",
        )
    factors = [
        Factor(name=f"x{i}", low=lo, high=hi)
        for i, (lo, hi) in enumerate(request.bounds)
    ]
    config = DoEConfig(
        factors=factors,
        design_type=DesignType.LATIN_HYPERCUBE,
        samples=request.n_samples,
        random_seed=request.seed,
    )
    result = latin_hypercube_sampling(config)
    return {
        "n_factors": request.n_factors,
        "n_samples": request.n_samples,
        "samples": result.design_matrix.tolist(),
    }

@router.post("/power-analysis")
async def api_power_analysis(request: PowerAnalysisRequest) -> dict[str, Any]:
    """Api power analysis."""
    if request.effect_size <= 0:
        raise HTTPException(status_code=400, detail="effect_size must be > 0")
    result = ttest_sample_size(
        effect_size=request.effect_size,
        alpha=request.alpha,
        power=request.power,
    )
    return result.to_dict()

@router.get("/design-types")
async def list_design_types() -> dict[str, Any]:
    return {
        "design_types": [
            {
                "name": d.name,
                "value": d.value,
                "description": _describe_design_type(d),
            }
            for d in DesignType
        ],
    }

def _describe_design_type(dt: DesignType) -> str:
    descriptions = {
        DesignType.FULL_FACTORIAL: "All combinations of factor levels",
        DesignType.FRACTIONAL_FACTORIAL: "Subset of full factorial runs",
        DesignType.LATIN_HYPERCUBE: "Space-filling design with uniform coverage",
        DesignType.CENTRAL_COMPOSITE: "Response surface methodology design",
        DesignType.RANDOMIZED_BLOCK: "Factorial design within randomized blocks",
    }
    return descriptions.get(dt, "No description available")
