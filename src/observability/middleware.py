"""FastAPI observability middleware"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware that records request count and duration via OTel metrics."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Dispatch."""
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        try:
            from src.observability.metrics import get_metrics

            meter = get_metrics()
            if meter:
                meter["request_counter"].add(
                    1,
                    {"method": request.method, "path": request.url.path},
                )
                meter["request_duration"].record(
                    duration,
                    {"method": request.method},
                )
        except (ImportError, RuntimeError):
            pass

        return response
