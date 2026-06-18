"""
C4REQBER: FastAPI Logging Middleware
Automatic request logging with trace IDs, duration, and structured output.
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.config import get_logger, set_trace_id


logger = get_logger("c4_cdi_turbo.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests with structured fields."""

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        # Extract or generate trace ID
        """Dispatch."""
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID")
        if trace_id:
            set_trace_id(trace_id)
        else:
            trace_id = set_trace_id.__module__  # fallback, get_trace_id generates one
            from src.infrastructure.logging.config import get_trace_id

            trace_id = get_trace_id()

        start_time = time.time()
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            logger.error(
                "request_failed",
                method=method,
                path=path,
                status=status_code,
                error=str(exc),
                trace_id=trace_id,
            )
            raise

        duration_ms = (time.time() - start_time) * 1000

        # Inject trace ID into response headers
        response.headers["X-Trace-ID"] = trace_id

        logger.info(
            "request",
            method=method,
            path=path,
            query=query,
            status=status_code,
            duration_ms=round(duration_ms, 3),
            trace_id=trace_id,
            user_agent=request.headers.get("user-agent", ""),
            client_ip=request.client.host if request.client else None,
        )

        return response
