"""Redis-backed job store for multi-replica API deployments."""
from __future__ import annotations

import json
import os
import time
from typing import Any

from src.api.v8_routers.discovery.jobs import Job, JobEvent, JobStatus, JobStore, _phase_to_status


def _redis_url() -> str | None:
    url = os.getenv("REDIS_URL", "").strip()
    return url or None


class RedisJobStore(JobStore):
    """JobStore that persists job state to Redis for cross-pod visibility."""

    def __init__(self, redis_url: str, ttl_seconds: float = 300.0) -> None:
        super().__init__(ttl_seconds=ttl_seconds)
        self._redis_url = redis_url
        self._redis: Any = None

    async def _client(self) -> Any:
        if self._redis is None:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _job_key(self, job_id: str) -> str:
        return f"c4reqber:job:{job_id}"

    def _events_key(self, job_id: str) -> str:
        return f"c4reqber:job:{job_id}:events"

    def _serialize_job(self, job: Job) -> str:
        return json.dumps(
            {
                "job_id": job.job_id,
                "job_type": job.job_type,
                "payload": job.payload,
                "status": job.status.value,
                "phase": job.phase,
                "phase_detail": job.phase_detail,
                "progress": job.progress,
                "result": job.result,
                "errors": job.errors,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "completed_at": job.completed_at,
                "event_seq": job._event_seq,
            }
        )

    def _deserialize_job(self, raw: str, events: list[JobEvent]) -> Job:
        data = json.loads(raw)
        job = Job(data["job_type"], data["payload"])
        job.job_id = data["job_id"]
        job.status = JobStatus(data["status"])
        job.phase = data.get("phase", "")
        job.phase_detail = data.get("phase_detail", "")
        job.progress = float(data.get("progress", 0.0))
        job.result = data.get("result")
        job.errors = list(data.get("errors", []))
        job.created_at = float(data.get("created_at", time.time()))
        job.updated_at = float(data.get("updated_at", job.created_at))
        job.completed_at = data.get("completed_at")
        job._event_seq = int(data.get("event_seq", 0))
        job.events = events
        return job

    async def _persist(self, job: Job) -> None:
        r = await self._client()
        pipe = r.pipeline()
        pipe.set(self._job_key(job.job_id), self._serialize_job(job), ex=int(self._ttl * 4))
        await pipe.execute()

    async def _load(self, job_id: str) -> Job | None:
        r = await self._client()
        raw = await r.get(self._job_key(job_id))
        if not raw:
            return None
        event_rows = await r.lrange(self._events_key(job_id), 0, -1)
        events: list[JobEvent] = []
        for row in event_rows:
            item = json.loads(row)
            events.append(
                JobEvent(
                    seq=int(item["seq"]),
                    event_type=item["event_type"],
                    data=item["data"],
                    ts=float(item.get("ts", time.time())),
                )
            )
        return self._deserialize_job(raw, events)

    async def create(self, job_type: str, payload: dict[str, Any]) -> Job:
        job = await super().create(job_type, payload)
        await self._persist(job)
        return job

    async def get(self, job_id: str) -> Job | None:
        local = await super().get(job_id)
        if local is not None:
            return local
        remote = await self._load(job_id)
        if remote is not None:
            async with self._lock:
                self._jobs[job_id] = remote
        return remote

    async def update_phase(
        self,
        job_id: str,
        phase_name: str,
        detail: str = "",
        progress: float | None = None,
    ) -> None:
        await super().update_phase(job_id, phase_name, detail, progress)
        job = await super().get(job_id)
        if job:
            await self._persist(job)

    async def set_running(self, job_id: str) -> None:
        await super().set_running(job_id)
        job = await super().get(job_id)
        if job:
            await self._persist(job)

    async def push_event(self, job_id: str, event_type: str, data: dict[str, Any]) -> None:
        await super().push_event(job_id, event_type, data)
        job = await super().get(job_id)
        if job is None:
            return
        r = await self._client()
        last = job.events[-1]
        await r.rpush(
            self._events_key(job_id),
            json.dumps(
                {
                    "seq": last.seq,
                    "event_type": last.event_type,
                    "data": last.data,
                    "ts": last.ts,
                }
            ),
        )
        await r.expire(self._events_key(job_id), int(self._ttl * 4))
        await self._persist(job)

    async def drain_events(self, job_id: str, after_seq: int) -> list[JobEvent]:
        job = await self.get(job_id)
        if job is None:
            return []
        return [e for e in job.events if e.seq > after_seq]

    async def set_complete(self, job_id: str, result: dict[str, Any]) -> None:
        await super().set_complete(job_id, result)
        job = await super().get(job_id)
        if job:
            await self._persist(job)

    async def set_failed(self, job_id: str, errors: list[str]) -> None:
        await super().set_failed(job_id, errors)
        job = await super().get(job_id)
        if job:
            await self._persist(job)