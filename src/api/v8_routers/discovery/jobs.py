"""Job tracking for async discovery pipelines."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


@dataclass
class JobEvent:
    """One SSE event queued for a job (drained by the stream endpoint)."""

    seq: int
    event_type: str
    data: dict[str, Any]
    ts: float = field(default_factory=time.time)


class JobStatus(StrEnum):
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
    PARTIAL = "partial"
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
        self.events: list[JobEvent] = []
        self._event_seq: int = 0

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

    async def push_event(self, job_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Append a typed SSE event to the job queue."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job._event_seq += 1
            payload = dict(data)
            payload.setdefault("type", event_type)
            payload.setdefault("job_id", job_id)
            payload.setdefault("ts", time.time())
            job.events.append(JobEvent(seq=job._event_seq, event_type=event_type, data=payload))
            job.updated_at = time.time()

    async def drain_events(self, job_id: str, after_seq: int) -> list[JobEvent]:
        """Return events with seq > after_seq (for SSE streaming)."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return []
            return [e for e in job.events if e.seq > after_seq]

    async def set_complete(self, job_id: str, result: dict[str, Any]) -> None:
        from src.knowledge.flash_contract import derive_terminal

        phase = ""
        result_status = ""
        if isinstance(result, dict):
            result_status = str(result.get("status") or "")
        event_type, job_status_value = derive_terminal(result_status)
        # Empty status on legacy payloads that omit status → treat as complete
        # only when result has no honesty status key at all and looks like
        # classic one-click (has papers/hypothesis without status field).
        if not result_status and isinstance(result, dict) and "status" not in result:
            event_type, job_status_value = "complete", "complete"

        async with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                if job_status_value == "failed":
                    job.status = JobStatus.FAILED
                elif job_status_value == "partial":
                    job.status = JobStatus.PARTIAL
                else:
                    job.status = JobStatus.COMPLETE
                job.result = result
                job.progress = 1.0
                job.completed_at = time.time()
                job.updated_at = job.completed_at
                phase = job.phase
                terminal_status = job.status.value
            else:
                terminal_status = job_status_value

        await self.push_event(
            job_id,
            event_type,
            {
                "type": event_type,
                "status": (result_status if result_status else terminal_status),
                "phase": phase,
                "progress": 1.0,
                "result": result,
            },
        )

    async def set_failed(self, job_id: str, errors: list[str]) -> None:
        phase = ""
        progress = 0.0
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = JobStatus.FAILED
                job.errors.extend(errors)
                job.completed_at = time.time()
                job.updated_at = job.completed_at
                phase = job.phase
                progress = job.progress
        await self.push_event(
            job_id,
            "failed",
            {
                "type": "failed",
                "status": JobStatus.FAILED.value,
                "phase": phase,
                "progress": progress,
                "errors": errors,
            },
        )

    async def list_all(self) -> list[dict[str, Any]]:
        async with self._lock:
            return [j.to_dict() for j in self._jobs.values()]


# Global job store: in-memory default; Redis when REDIS_URL is set (multi-replica).
_job_store: JobStore | None = None


def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        import os

        redis_url = os.getenv("REDIS_URL", "").strip()
        if redis_url:
            from src.api.v8_routers.discovery.job_store_redis import RedisJobStore

            _job_store = RedisJobStore(redis_url)
        else:
            _job_store = JobStore()
    return _job_store
