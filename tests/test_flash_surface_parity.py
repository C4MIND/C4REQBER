"""Contract tests: FlashResult schema parity CLI/MCP/API + JobStore terminal."""

from __future__ import annotations

import asyncio

import pytest

from src.api.v8_routers.discovery.jobs import JobStatus, JobStore
from src.knowledge.flash_contract import (
    FLASH_RESULT_CORE_KEYS,
    celebration_allowed,
    count_verified_sources,
    derive_terminal,
)


def test_derive_terminal_success_complete() -> None:
    assert derive_terminal("success") == ("complete", "complete")
    assert derive_terminal("complete") == ("complete", "complete")
    assert derive_terminal("ok") == ("complete", "complete")


def test_derive_terminal_partial_fail_closed() -> None:
    assert derive_terminal("partial") == ("partial", "partial")
    assert derive_terminal("") == ("partial", "partial")
    assert derive_terminal(None) == ("partial", "partial")
    assert derive_terminal("failed") == ("failed", "failed")
    assert derive_terminal("error") == ("failed", "failed")


def test_celebration_allowed() -> None:
    assert celebration_allowed("success") is True
    assert celebration_allowed("partial") is False
    assert celebration_allowed("") is False


def test_count_verified_sources() -> None:
    papers = [
        {"title": "a", "verified": True},
        {"title": "b", "verified": False, "verify_verdict": "UNVERIFIED"},
        {"title": "c", "verify_verdict": "PARTIAL"},
    ]
    assert count_verified_sources(papers) == 2


def test_flash_result_core_keys_stable() -> None:
    assert "status" in FLASH_RESULT_CORE_KEYS
    assert "verified_count" in FLASH_RESULT_CORE_KEYS
    assert "sources" in FLASH_RESULT_CORE_KEYS


@pytest.mark.asyncio
async def test_job_store_partial_emits_partial_event() -> None:
    store = JobStore(ttl_seconds=60)
    job = await store.create("flash", {"problem": "x"})
    await store.set_complete(
        job.job_id,
        {"status": "partial", "answer": "maybe", "verified_count": 0},
    )
    got = await store.get(job.job_id)
    assert got is not None
    assert got.status == JobStatus.PARTIAL
    events = await store.drain_events(job.job_id, 0)
    assert events
    assert events[-1].event_type == "partial"
    assert events[-1].data.get("type") == "partial"


@pytest.mark.asyncio
async def test_job_store_success_emits_complete() -> None:
    store = JobStore(ttl_seconds=60)
    job = await store.create("flash", {"problem": "x"})
    await store.set_complete(
        job.job_id,
        {"status": "success", "answer": "yes", "verified_count": 1},
    )
    got = await store.get(job.job_id)
    assert got is not None
    assert got.status == JobStatus.COMPLETE
    events = await store.drain_events(job.job_id, 0)
    assert events[-1].event_type == "complete"


@pytest.mark.asyncio
async def test_job_store_legacy_no_status_still_complete() -> None:
    store = JobStore(ttl_seconds=60)
    job = await store.create("one-click", {"problem": "x"})
    await store.set_complete(job.job_id, {"hypothesis": {"text": "h"}, "papers": []})
    got = await store.get(job.job_id)
    assert got is not None
    assert got.status == JobStatus.COMPLETE
    events = await store.drain_events(job.job_id, 0)
    assert events[-1].event_type == "complete"
