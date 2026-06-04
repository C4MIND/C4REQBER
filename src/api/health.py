"""
C4REQBER: Health Check Endpoint
Production health monitoring with real dependency checks.
"""
from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src import __version__
from src.compat import UTC


router = APIRouter(prefix="/health", tags=["health"])

_start_time = time.time()


class HealthStatus(BaseModel):
    """HealthStatus."""
    status: str
    version: str
    uptime_seconds: float
    timestamp: str
    checks: dict[str, bool]


class ReadinessStatus(BaseModel):
    """ReadinessStatus."""
    ready: bool
    checks: dict[str, bool]


def _check_database() -> bool:
    """Check SQLite database connectivity."""
    try:
        conn = sqlite3.connect("data/discoveries.db", timeout=2)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except (sqlite3.Error, OSError):
        return False


def _check_cache() -> bool:
    """Check cache backend availability."""
    import os
    cache_backend = os.getenv("CACHE_BACKEND", "memory")
    if cache_backend == "memory":
        return True
    if cache_backend == "redis":
        try:
            import redis
            r = redis.from_url(  # type: ignore[no-untyped-call]
            os.getenv("REDIS_URL", "redis://localhost:6379"))
            r.ping()
            return True
        except (ConnectionError, TimeoutError, OSError):
            return False
    return False


def _check_llm_router() -> bool:
    """Check if at least one LLM provider is available."""
    try:
        from src.llm.router import get_llm_router  # type: ignore[attr-defined]
        router = get_llm_router()  # type: ignore[attr-defined,used-before-def]
        return len(router.providers) > 0
    except (ImportError, RuntimeError, ValueError):
        return False


@router.get("", response_model=HealthStatus)
async def health_check() -> Any:
    """Liveness probe — is the service running?"""
    return HealthStatus(
        status="healthy",
        version=__version__,
        uptime_seconds=time.time() - _start_time,
        timestamp=datetime.now(UTC).isoformat(),
        checks={
            "api": True,
            "memory": True,
        },
    )


@router.get("/ready", response_model=ReadinessStatus)
async def readiness_check() -> Any:
    """Readiness probe — is the service ready to accept traffic?"""
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
        "llm_router": _check_llm_router(),
    }

    return ReadinessStatus(
        ready=all(checks.values()),
        checks=checks,
    )
