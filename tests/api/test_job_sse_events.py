"""Tests for typed SSE job event queue (TUI v9 contract)."""

from __future__ import annotations

import pytest

from src.api.v8_routers.discovery.jobs import JobStore


@pytest.mark.asyncio
async def test_push_and_drain_phase_progress_event():
    store = JobStore()
    job = await store.create("one-click", {"problem": "test"})
    await store.push_event(
        job.job_id,
        "phase_progress",
        {
            "type": "phase_progress",
            "phase": "A: Framing",
            "progress": 0.0,
            "status": "running",
        },
    )
    events = await store.drain_events(job.job_id, 0)
    assert len(events) == 1
    assert events[0].event_type == "phase_progress"
    assert events[0].data["type"] == "phase_progress"
    assert events[0].data["phase"] == "A: Framing"
    assert events[0].seq == 1


@pytest.mark.asyncio
async def test_drain_events_incremental():
    store = JobStore()
    job = await store.create("flash", {"question": "why?"})
    await store.push_event(job.job_id, "log", {"type": "log", "status": "queued"})
    await store.push_event(
        job.job_id, "phase_progress", {"type": "phase_progress", "phase": "B: Search"}
    )
    first = await store.drain_events(job.job_id, 0)
    assert len(first) == 2
    second = await store.drain_events(job.job_id, first[-1].seq)
    assert second == []


@pytest.mark.asyncio
async def test_set_complete_emits_typed_complete_event():
    store = JobStore()
    job = await store.create("one-click", {"problem": "x"})
    await store.set_complete(job.job_id, {"status": "ok"})
    events = await store.drain_events(job.job_id, 0)
    assert any(e.event_type == "complete" for e in events)
    complete = next(e for e in events if e.event_type == "complete")
    assert complete.data["type"] == "complete"
    assert complete.data["status"] == "complete"


@pytest.mark.asyncio
async def test_set_failed_emits_typed_failed_event():
    store = JobStore()
    job = await store.create("one-click", {"problem": "x"})
    await store.set_failed(job.job_id, ["boom"])
    events = await store.drain_events(job.job_id, 0)
    failed = next(e for e in events if e.event_type == "failed")
    assert failed.data["type"] == "failed"
    assert failed.data["errors"] == ["boom"]
