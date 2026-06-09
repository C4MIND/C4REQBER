"""
C4REQBER API: System Dynamics Router (/v7/system-dynamics)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from src.api.dev_mode import dev_mode_dependency
from src.system_dynamics.archetypes import ARCHETYPE_BY_NAME, simulate_archetype
from src.system_dynamics.dsl import dsl_to_string, parse_dsl
from src.system_dynamics.simulator import simulate_euler, simulate_rk4
from src.system_dynamics.visualizer import detect_loops, render_ascii, render_dot


router = APIRouter(prefix="/api/v7/system-dynamics", tags=["v7-system-dynamics"])

@router.post("/dsl/parse")
async def dsl_parse(
    payload: dict[str, Any] = Body(...),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Dsl parse."""
    dsl_text = payload.get("dsl", "")
    if not dsl_text:
        raise HTTPException(status_code=400, detail="DSL text is required")

    try:
        model = parse_dsl(dsl_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    errors = model.validate()
    return {
        "model": {
            "name": model.name,
            "stocks": [{"name": s.name, "initial": s.initial, "unit": s.unit} for s in model.stocks],
            "flows": [{"name": f.name, "source": f.source, "target": f.target,
                       "expression": f.expression} for f in model.flows],
            "variables": [{"name": v.name, "expression": v.expression} for v in model.variables],
            "links": [{"source": l.source, "target": l.target, "polarity": l.polarity} for l in model.links],
            "start_time": model.start_time,
            "end_time": model.end_time,
            "dt": model.dt,
        },
        "dsl": dsl_to_string(parse_dsl(dsl_text)),
        "errors": errors,
        "valid": len(errors) == 0,
    }

@router.post("/simulate")
async def simulate_model(
    payload: dict[str, Any] = Body(...),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Simulate model."""
    dsl_text = payload.get("dsl", "")
    method = payload.get("method", "rk4")
    n_steps = payload.get("n_steps", 200)

    if not dsl_text:
        raise HTTPException(status_code=400, detail="DSL text is required")

    try:
        model = parse_dsl(dsl_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    errors = model.validate()
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    if method == "euler":
        t, y_dict = simulate_euler(model, n_steps=n_steps)
    else:
        t, y_dict = simulate_rk4(model, n_steps=n_steps)

    series: list[dict[str, Any]] = []
    for i in range(len(t)):
        point: dict[str, Any] = {"t": float(t[i])}
        for name, arr in y_dict.items():
            point[name] = float(arr[i])
        series.append(point)

    return {
        "model_name": model.name,
        "method": method,
        "t_span": [model.start_time, model.end_time],
        "n_steps": len(t) - 1,
        "stocks": [s.name for s in model.stocks],
        "series": series,
    }

@router.get("/archetypes")
async def list_archetypes(
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """List archetypes."""
    archetypes = []
    for name, arch in ARCHETYPE_BY_NAME.items():
        archetypes.append({
            "name": name,
            "description": arch.description,
            "nodes": arch.signature_nodes,
            "link_count": len(arch.signature_links),
        })
    return {"archetypes": archetypes, "total": len(archetypes)}

@router.get("/archetypes/{name}")
async def get_archetype(
    name: str,
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Get archetype."""
    if name not in ARCHETYPE_BY_NAME:
        raise HTTPException(status_code=404, detail=f"Archetype '{name}' not found")
    arch = ARCHETYPE_BY_NAME[name]
    return {
        "name": name,
        "description": arch.description,
        "nodes": arch.signature_nodes,
        "links": [{"source": s, "target": t, "polarity": p.value} for s, t, p in arch.signature_links],
    }

@router.post("/archetypes/{name}/simulate")
async def run_archetype(
    name: str,
    payload: dict[str, Any] = Body(default={}),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Run archetype."""
    if name not in ARCHETYPE_BY_NAME:
        raise HTTPException(status_code=404, detail=f"Archetype '{name}' not found")

    t_span = (
        float(payload.get("start", 0.0)),
        float(payload.get("end", 100.0)),
    )
    n_steps = int(payload.get("n_steps", 2000))

    try:
        t, y, spec = simulate_archetype(name, t_span=t_span, n_steps=n_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}") from e

    series: list[dict[str, Any]] = []
    stock_names = list(spec.stocks.keys())
    for i in range(len(t)):
        point: dict[str, Any] = {"t": float(t[i])}
        for j, sn in enumerate(stock_names):
            if j < y.shape[1]:
                point[sn] = float(y[i, j])
        series.append(point)

    return {
        "archetype": name,
        "t_span": list(t_span),
        "n_steps": len(t) - 1,
        "stocks": stock_names,
        "series": series,
    }

@router.post("/visualize/ascii")
async def visualize_ascii(
    payload: dict[str, Any] = Body(...),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Visualize ascii."""
    dsl_text = payload.get("dsl", "")
    if not dsl_text:
        raise HTTPException(status_code=400, detail="DSL text is required")

    try:
        model = parse_dsl(dsl_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {"ascii": render_ascii(model)}

@router.post("/visualize/dot")
async def visualize_dot(
    payload: dict[str, Any] = Body(...),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Visualize dot."""
    dsl_text = payload.get("dsl", "")
    horizontal = payload.get("horizontal", False)
    if not dsl_text:
        raise HTTPException(status_code=400, detail="DSL text is required")

    try:
        model = parse_dsl(dsl_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {"dot": render_dot(model, horizontal=horizontal)}

@router.post("/loops")
async def find_loops(
    payload: dict[str, Any] = Body(...),
    user: Any=Depends(dev_mode_dependency),
) -> dict[str, Any]:
    """Find loops."""
    dsl_text = payload.get("dsl", "")
    if not dsl_text:
        raise HTTPException(status_code=400, detail="DSL text is required")

    try:
        model = parse_dsl(dsl_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    raw_loops = detect_loops(model)
    loops = []
    for path, is_balancing in raw_loops:
        loops.append({
            "path": path,
            "type": "balancing" if is_balancing else "reinforcing",
        })

    return {
        "model_name": model.name,
        "loops": loops,
        "total": len(loops),
    }
