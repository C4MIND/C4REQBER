"""
C4REQBER API: Health Router
Production-ready health endpoints with per-service status checks.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from src import __version__
from src.compat import UTC


router = APIRouter(prefix="/api/v1", tags=["health"])

VERSION = os.getenv("APP_VERSION", __version__)
START_TIME = time.time()


async def _check_database() -> tuple[str, str | None]:
    """Check database connectivity."""
    try:
        from src.api.db_manager import get_db

        db = await get_db()
        if await db.ping():
            return "ok", None
        return "error", "ping failed"
    except Exception as e:
        return "error", str(e)


async def _check_cache() -> tuple[str, str | None]:
    """Check cache (Redis or memory) connectivity."""
    try:
        from src.api.cache import CacheManager

        cache = CacheManager()
        await cache.connect()
        if await cache.ping():
            return "ok", None
        return "error", "ping failed"
    except Exception as e:
        return "error", str(e)


async def _check_llm_providers() -> tuple[str, str | None]:
    """Check LLM provider availability."""
    try:
        from src.llm.config import LLMProvider

        # Check if any provider API keys are configured
        providers = []
        for provider in LLMProvider:
            key_env = f"{provider.value.upper()}_API_KEY"
            if os.getenv(key_env):
                providers.append(provider.value)
        if providers:
            return "ok", f"{len(providers)} providers configured"
        return "degraded", "no providers configured"
    except Exception as e:
        return "error", str(e)


@router.get("/health", operation_id="healthCheck")
async def health_check() -> Any:
    """General health status. Returns 200 if process is alive."""
    uptime_seconds = int(time.time() - START_TIME)
    return {
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_seconds": uptime_seconds,
    }


@router.get("/health/ready")
async def readiness_check() -> Any:
    """Readiness probe: checks DB and cache. Returns 503 if any critical service is down."""
    db_status, db_error = await _check_database()
    cache_status, cache_error = await _check_cache()
    llm_status, llm_error = await _check_llm_providers()

    all_ok = all(s == "ok" for s in (db_status, cache_status))
    status_code = 200 if all_ok else 503

    response = {
        "status": "ready" if all_ok else "not_ready",
        "version": VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "services": {
            "database": {"status": db_status, "error": db_error},
            "cache": {"status": cache_status, "error": cache_error},
            "llm": {"status": llm_status, "error": llm_error},
        },
    }

    if status_code == 503:
        raise HTTPException(status_code=503, detail=response)
    return response


@router.get("/health/live")
async def liveness_check() -> Any:
    """Liveness probe: returns 200 if process is alive."""
    return {
        "status": "alive",
        "version": VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/dependencies")
async def dependencies_check() -> Any:
    """Dependency check endpoint."""
    db_status, db_error = await _check_database()
    cache_status, cache_error = await _check_cache()
    llm_status, llm_error = await _check_llm_providers()

    all_ok = all(s == "ok" for s in (db_status, cache_status))

    return {
        "status": "ok" if all_ok else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "dependencies": {
            "database": {"status": db_status, "error": db_error},
            "cache": {"status": cache_status, "error": cache_error},
            "llm": {"status": llm_status, "error": llm_error},
        },
    }
