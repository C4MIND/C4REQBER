"""Job tracking for async discovery pipelines."""
from __future__ import annotations

import asyncio
import time
import uuid
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Pipeline job lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    PHASE_A = "phase_a"
    PHASE_B = "phase_b"
    PHASE_C = "phase_c"
    PHASE_D = "phase_d"
    PHASE_E = "phase_e"
    PHASE_F = "phase_f"
    PHASE_G = "phase_g"
    COMPLETE = "complete"
    FAILED = "failed"


_PHASE_MAP: dict[str, JobStatus] = {
    "A: Framing": JobStatus.PHASE_A,
    "B: Search": JobStatus.PHASE_B,
    "C: Gaps": JobStatus.PHASE_C,
    "D: Hyps": JobStatus.PHASE_D,
    "E: Sim": JobStatus.PHASE_E,
    "F: Dissertation": JobStatus.PHASE_F,
    "G: Quality": JobStatus.PHASE_G,
}


def _phase_to_status(phase_name: str) -> JobStatus:
    return _PHASE_MAP.get(phase_name, JobStatus.RUNNING)


class Job:
    """Represents a single discovery pipeline job."""

    def __init__(self, job_type: str, payload: dict[str, Any]) -> None:
        self.job_id: str = f"job_{uuid.uuid4().hex[:12]}"
        self.job_type = job_type
        self.payload = payload
        self.status = JobStatus.QUEUED
        self.phase: str = ""
        self.phase_detail: str = ""
        self.progress: float = 0.0
        self.result: dict[str, Any] | None = None
        self.errors: list[str] = []
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "phase": self.phase,
            "phase_detail": self.phase_detail,
            "progress": round(self.progress, 2),
            "result": self.result,
            "errors": self.errors,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }


class JobStore:
    """In-memory job store with optional Redis backend and TTL cleanup."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._jobs: dict[str, Job] = {}
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
        self._cleaner_task: asyncio.Task[Any] | None = None

    async def start_cleaner(self) -> None:
        """Start background TTL cleanup task."""
        if self._cleaner_task is None or self._cleaner_task.done():
            self._cleaner_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleaner(self) -> None:
        if self._cleaner_task and not self._cleaner_task.done():
            self._cleaner_task.cancel()
            try:
                await self._cleaner_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(60.0)
            await self._purge_expired()

    async def _purge_expired(self) -> None:
        now = time.time()
        async with self._lock:
            expired = [
                jid
                for jid, job in self._jobs.items()
                if job.completed_at is not None and now - job.completed_at > self._ttl
            ]
            for jid in expired:
                del self._jobs[jid]

    async def create(self, job_type: str, payload: dict[str, Any]) -> Job:
        job = Job(job_type, payload)
        async with self._lock:
            self._jobs[job.job_id] = job
        return job

    async def get(self, job_id: str) -> Job | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_phase(
        self,
        job_id: str,
        phase_name: str,
        detail: str = "",
        progress: float | None = None,
    ) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.status = _phase_to_status(phase_name)
            job.phase = phase_name
            job.phase_detail = detail
            if progress is not None:
                job.progress = progress
            job.updated_at = time.time()

    async def set_running(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = JobStatus.RUNNING
                job.updated_at = time.time()

    async def set_complete(self, job_id: str, result: dict[str, Any]) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = JobStatus.COMPLETE
                job.result = result
                job.progress = 1.0
                job.completed_at = time.time()
                job.updated_at = job.completed_at

    async def set_failed(self, job_id: str, errors: list[str]) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = JobStatus.FAILED
                job.errors.extend(errors)
                job.completed_at = time.time()
                job.updated_at = job.completed_at

    async def list_all(self) -> list[dict[str, Any]]:
        async with self._lock:
            return [j.to_dict() for j in self._jobs.values()]


# Global job store instance (per-process; scale with Redis later)
_job_store: JobStore | None = None


def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store
