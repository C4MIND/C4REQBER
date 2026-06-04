"""
C4REQBER v8.0: One-Click Discovery API Router
POST /api/v8/discover/one-click — runs the full discovery pipeline:
C4 → TRIZ → UCOS (4-Layer) → QZRF (14 Operators) →
Knowledge Search → Isomorphism → Hypothesis → Simulation → Verification → Paper Generation.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.api.v8_routers.discovery.export import ExportRequest, ExportResponse, export_discovery
from src.api.v8_routers.discovery.jobs import JobStatus, get_job_store
from src.api.v8_routers.discovery.pipeline import (
    DissertationRequest,
    FlashRequest,
    MultiHypothesisRequest,
    OneClickRequest,
    _domain_improving_param,
    _domain_worsening_param,
    build_temporal_kg,
    detect_paradigm_shift,
    dissertation_mode,
    flash_discovery,
    generate_hypothesis,
    generate_lean4_proof,
    generate_paper,
    mine_contradictions,
    multi_hypothesis_discovery,
    navigate_c4,
    one_click_discovery,
    resolve_triz,
    run_abduction,
    run_autoscanner,
    run_bayesian_conjugate_update,
    run_bayesian_model_averaging,
    run_c4_observer,
    run_causal_do_calculus,
    run_cognitive_plugins,
    run_consensus_meter,
    run_counterfactual,
    run_dempster_shafer,
    run_doe_design,
    run_empirical_validation,
    run_falsification_engine,
    run_fra_routing,
    run_matrix_dream,
    run_power_analysis,
    run_relevant_simulation,
    run_reproducibility_check,
    run_strong_inference,
    search_isomorphisms,
)
from src.api.v8_routers.discovery.search import search_knowledge


logger = logging.getLogger("c4_cdi_turbo.api.v8.discovery")

router = APIRouter(prefix="/discover", tags=["v8-discovery"])


# ---------------------------------------------------------------------------
# Async job runner helpers
# ---------------------------------------------------------------------------
async def _run_one_click_job(job_id: str, request: OneClickRequest) -> None:
    store = get_job_store()
    await store.set_running(job_id)
    try:
        result = await one_click_discovery(request, job_id=job_id)
        await store.set_complete(job_id, result)
    except Exception as exc:
        logger.exception("One-click job %s failed", job_id)
        await store.set_failed(job_id, [str(exc)])


async def _run_flash_job(job_id: str, request: FlashRequest) -> None:
    store = get_job_store()
    await store.set_running(job_id)
    try:
        result = await flash_discovery(request, job_id=job_id)
        await store.set_complete(job_id, result)
    except Exception as exc:
        logger.exception("Flash job %s failed", job_id)
        await store.set_failed(job_id, [str(exc)])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/one-click")
async def one_click_discovery_route(request: OneClickRequest) -> dict[str, Any]:
    store = get_job_store()
    job = await store.create("one-click", request.model_dump())
    asyncio.create_task(_run_one_click_job(job.job_id, request))
    return {"job_id": job.job_id, "status": job.status.value}


@router.post("/flash")
async def flash_discovery_route(request: FlashRequest) -> dict[str, Any]:
    store = get_job_store()
    job = await store.create("flash", request.model_dump())
    asyncio.create_task(_run_flash_job(job.job_id, request))
    return {"job_id": job.job_id, "status": job.status.value}


@router.post("/multi")
async def multi_hypothesis_discovery_route(request: MultiHypothesisRequest) -> dict[str, Any]:
    return await multi_hypothesis_discovery(request)


@router.post("/dissertation")
async def dissertation_mode_route(request: DissertationRequest) -> dict[str, Any]:
    return await dissertation_mode(request)


@router.post("/export")
def export_discovery_route(req: ExportRequest) -> ExportResponse:
    return export_discovery(req)


# ---------------------------------------------------------------------------
# C4 Navigation
# ---------------------------------------------------------------------------
class C4NavigateRequest(BaseModel):
    problem: str


@router.post("/navigate-c4")
async def navigate_c4_route(request: C4NavigateRequest) -> dict[str, Any]:
    return navigate_c4(request.problem)


# ---------------------------------------------------------------------------
# Job status polling
# ---------------------------------------------------------------------------
@router.get("/status/{job_id}")
async def job_status_route(job_id: str) -> dict[str, Any]:
    store = get_job_store()
    job = await store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------
async def _sse_stream(job_id: str) -> Any:
    store = get_job_store()
    job = await store.get(job_id)
    if job is None:
        yield "event: error\ndata: {\"detail\": \"Job not found\"}\n\n"
        return

    last_status: str | None = None
    while True:
        job = await store.get(job_id)
        if job is None:
            yield "event: error\ndata: {\"detail\": \"Job disappeared\"}\n\n"
            return

        if job.status.value != last_status:
            last_status = job.status.value
            payload = {
                "phase": job.phase,
                "status": job.status.value,
                "progress": job.progress,
                "detail": job.phase_detail,
            }
            yield f"event: phase\ndata: {json.dumps(payload)}\n\n"

        if job.status in (JobStatus.COMPLETE, JobStatus.FAILED):
            result_payload = {
                "phase": job.phase,
                "status": job.status.value,
                "progress": job.progress,
                "result": job.result,
                "errors": job.errors,
            }
            yield f"event: complete\ndata: {json.dumps(result_payload)}\n\n"
            return

        await asyncio.sleep(0.5)


@router.get("/stream/{job_id}")
async def job_stream_route(job_id: str) -> StreamingResponse:
    return StreamingResponse(
        _sse_stream(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


__all__ = [
    "router",
    "one_click_discovery_route",
    "flash_discovery_route",
    "multi_hypothesis_discovery_route",
    "dissertation_mode_route",
    "export_discovery_route",
    "navigate_c4_route",
    "job_status_route",
    "job_stream_route",
    "OneClickRequest",
    "MultiHypothesisRequest",
    "DissertationRequest",
    "FlashRequest",
    "C4NavigateRequest",
    "ExportRequest",
    "ExportResponse",
]
