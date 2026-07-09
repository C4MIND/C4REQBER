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
    dissertation_mode,
    flash_discovery,
    multi_hypothesis_discovery,
    navigate_c4,
    one_click_discovery,
)


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
@router.post("/one-click", operation_id="discoverOneClick")
async def one_click_discovery_route(request: OneClickRequest) -> dict[str, Any]:
    store = get_job_store()
    job = await store.create("one-click", request.model_dump())
    # Audit 2026-06-22 M-5: fire-and-forget tasks can swallow exceptions
    # after the 202 response is sent. Wrap in _supervised_task so any error
    # is logged AND sets the job to 'failed' (not stuck in 'running' forever).
    asyncio.create_task(
        _supervised_task(_run_one_click_job(job.job_id, request), job_id=job.job_id, kind="one-click")
    )
    return {"job_id": job.job_id, "status": job.status.value}


@router.post("/flash", operation_id="discoverFlash")
async def flash_discovery_route(request: FlashRequest) -> dict[str, Any]:
    store = get_job_store()
    job = await store.create("flash", request.model_dump())
    asyncio.create_task(
        _supervised_task(_run_flash_job(job.job_id, request), job_id=job.job_id, kind="flash")
    )
    return {"job_id": job.job_id, "status": job.status.value}


async def _supervised_task(coro, *, job_id: str, kind: str) -> None:
    """Wrap a fire-and-forget coroutine so uncaught exceptions are logged
    and the job is marked failed (instead of silently stuck in 'running')."""
    try:
        await coro
    except Exception as exc:
        logger.exception("fire-and-forget task failed: %s (job_id=%s)", kind, job_id)
        try:
            store = get_job_store()
            await store.set_failed(job_id, [f"{type(exc).__name__}: {exc}"])
        except Exception:
            logger.exception("could not mark job %s as failed", job_id)


@router.post("/multi", operation_id="discoverMulti")
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
@router.get("/status/{job_id}", operation_id="discoverJobStatus")
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
        yield 'event: error\ndata: {"type": "error", "detail": "Job not found"}\n\n'
        return

    last_event_seq = 0
    terminal_sent = False
    while True:
        job = await store.get(job_id)
        if job is None:
            yield 'event: error\ndata: {"type": "error", "detail": "Job disappeared"}\n\n'
            return

        for ev in await store.drain_events(job_id, last_event_seq):
            last_event_seq = ev.seq
            yield f"event: {ev.event_type}\ndata: {json.dumps(ev.data)}\n\n"
            if ev.event_type in ("complete", "failed"):
                terminal_sent = True
                return

        if not terminal_sent and job.status in (JobStatus.COMPLETE, JobStatus.FAILED):
            # Back-compat: emit terminal frame if set_complete/set_failed raced the drain.
            event_type = "complete" if job.status == JobStatus.COMPLETE else "failed"
            payload = {
                "type": event_type,
                "phase": job.phase,
                "status": job.status.value,
                "progress": job.progress,
                "detail": job.phase_detail,
                "result": job.result,
                "errors": job.errors,
            }
            yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
            return

        await asyncio.sleep(0.5)


@router.get("/stream/{job_id}", operation_id="discoverJobStream")
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
