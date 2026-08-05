"""Compatibility shim — health SSOT lives in ``src.api.routers.health``.

Do not add endpoints here. Compose / k8s / clients must use ``/api/v1/health*``.
"""

from __future__ import annotations

from src.api.routers.health import (  # noqa: F401
    dependencies_check,
    health_check,
    liveness_check,
    readiness_check,
    router,
)


__all__ = [
    "router",
    "health_check",
    "readiness_check",
    "liveness_check",
    "dependencies_check",
]
