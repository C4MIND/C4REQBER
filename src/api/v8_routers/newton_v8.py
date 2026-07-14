from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator


router = APIRouter(prefix="/newton", tags=["v8-newton"])


class NewtonSimulateRequest(BaseModel):
    """NewtonSimulateRequest."""
    initial_conditions: dict[str, Any]
    duration: float
    timestep: float = 0.01

    @field_validator('duration')
    def duration_must_be_non_negative(cls, v) -> float:
        """Duration must be non negative."""
        if v < 0:
            raise ValueError('duration must be non-negative')
        return v


class NewtonBenchmarkRequest(BaseModel):
    """NewtonBenchmarkRequest."""
    pattern_id: str
    legacy_config: dict[str, Any] = {}


@router.get("/supported")
async def list_supported() -> dict[str, Any]:
    """List Newton-supported simulation types."""
    from src.simulations.newton_bridge import NewtonBridge
    bridge = NewtonBridge()
    return {"supported": bridge.get_supported_simulations(), "newton_available": bridge.available}


@router.post("/simulate")
async def simulate_newton(req: NewtonSimulateRequest) -> dict[str, Any]:
    """Run Newton simulation (matches test contract)."""
    from src.simulations.newton_bridge import NewtonBridge
    bridge = NewtonBridge()

    if not bridge.available:
        raise HTTPException(status_code=503, detail="Newton engine unavailable")

    config = {
        "initial_conditions": req.initial_conditions,
        "duration": req.duration,
        "timestep": req.timestep,
    }

    result = bridge.run_simulation(config)

    return {
        "simulation_id": result.data.get("simulation_id", f"sim-{hash(str(req.initial_conditions))}"),
        "status": result.status,
        "results": result.data.get("results"),
    }


@router.post("/benchmark")
async def benchmark_newton(req: NewtonBenchmarkRequest) -> dict[str, Any]:
    """Compare Newton vs Legacy speed."""
    from src.simulations.newton_bridge import NewtonBridge
    bridge = NewtonBridge()

    if not bridge.available:
        raise HTTPException(status_code=501, detail="Newton not installed")

    # benchmark_legacy_vs_newton not implemented in NewtonBridge
    return {"error": "Benchmark not implemented", "pattern_id": req.pattern_id}  # type: ignore[attr-defined]
