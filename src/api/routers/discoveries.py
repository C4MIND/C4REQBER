"""
C4REQBER API: Discovery Router
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from src.agents.orchestrator import AgentOrchestrator
from src.api.cache import CacheManager
from src.api.db_manager import get_db
from src.api.dependencies import check_rate_limit_ip, get_current_user_optional
from src.api.models import (
    DiscoveryRequest,
    DiscoveryResponse,
    HypothesisResponse,
    User,
)
from src.compat import UTC


cache = CacheManager()
router = APIRouter(prefix="/api/v1/discover", tags=["discoveries"])


@router.post("", response_model=DiscoveryResponse)
async def create_discovery(
    request: DiscoveryRequest,
    user: User | None = Depends(get_current_user_optional),
    _rate_limit: bool = Depends(check_rate_limit_ip),
) -> DiscoveryResponse:
    """Create discovery."""
    user_key = user.id if user else "anon"
    cache_key = (
        f"v1:discovery:{user_key}:"
        f"{hashlib.sha256(f'{request.problem}:{request.max_hypotheses}'.encode()).hexdigest()}"
    )
    cached = await cache.get(cache_key)
    if cached:
        return DiscoveryResponse(**cached)

    from src.solver.one_shot import get_one_shot_solver

    solver = get_one_shot_solver()
    result = await solver.solve(
        problem=request.problem, max_hypotheses=request.max_hypotheses or 5
    )

    db = await get_db()
    discovery_id = await db.save_discovery(  # type: ignore[union-attr]
        result, user_id=(user.id if user else None)
    )

    response = DiscoveryResponse(
        id=discovery_id,
        problem=result.problem,
        hypotheses=[
            HypothesisResponse(
                id=h["id"],
                hypothesis=h["hypothesis"],
                confidence=h["confidence"],
                method=h["method"],
                c4_path=h.get("c4_path", []),
                triz_principles=h.get("triz_principles", []),
                simulation=h.get("simulation"),
            )
            for h in result.hypotheses
        ],
        top_hypothesis=result.hypotheses[0]["hypothesis"]
        if result.hypotheses
        else None,
        duration_seconds=result.duration_seconds,
        estimated_cost=result.estimated_cost_usd,
        created_at=datetime.now(UTC),
    )

    await cache.set(cache_key, response.model_dump(), ttl=3600)
    return response


@router.post("/multi-agent")
async def create_discovery_multi_agent(
    request: DiscoveryRequest,
    user: User | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """Create discovery multi agent."""
    orchestrator = AgentOrchestrator()
    result = await orchestrator.solve(problem=request.problem)

    db = await get_db()
    discovery_id = await db.save_discovery(  # type: ignore[union-attr]
        type(
            "Result",
            (),
            {
                "problem": result.problem,
                "hypotheses": [result.final_solution] if result.final_solution else [],
                "duration_seconds": result.total_duration_ms / 1000.0,
                "estimated_cost_usd": 0.0,
            },
        )(),
        user_id=(user.id if user else None),
    )

    return {
        "id": discovery_id,
        "problem": result.problem,
        "session_id": result.session_id,
        "mode": result.mode,
        "final_solution": result.final_solution,
        "confidence": result.confidence,
        "c4_path": result.c4_path,
    }
