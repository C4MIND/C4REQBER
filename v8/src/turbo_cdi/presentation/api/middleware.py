"""
FastAPI middleware for TURBO-CDI v8.4 API
Provides request timing, logging, exception handling, and security features.
"""

import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that measures and logs request processing time.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        # Add processing time header
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2)) + "ms"

        # Log slow requests
        if process_time > 1.0:  # More than 1 second
            logger = logging.getLogger("performance")
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
            )

        # TODO: Record metrics for monitoring
        # from turbo_cdi.infrastructure.metrics import record_request_time
        # record_request_time(request.url.path, process_time)

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all API requests and responses.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger = logging.getLogger("api")

        # Log request
        logger.info(
            f"Request: {request.method} {request.url} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Log request body for debugging (in development only)
        if request.app.settings.debug_mode and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    logger.debug(f"Request body: {body.decode()[:500]}...")
            except Exception:
                pass

        response = await call_next(request)

        # Log response
        logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")

        # TODO: Log response body for debugging (development only)
        # TODO: Log user context if authenticated

        return response


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global exception handling middleware.
    Catches and properly formats unexpected exceptions.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)

        except Exception as exc:
            logger = logging.getLogger("error")

            # Log the exception
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}",
                exc_info=True,
            )

            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security-focused middleware.
    Adds security headers and basic protection.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # API-specific headers
        response.headers["X-API-Version"] = "8.4.0"

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting API usage metrics.
    """

    def __init__(self, app: Callable):
        super().__init__(app)
        self.request_count = 0
        self.endpoint_metrics = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        self.request_count += 1

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Track per-endpoint metrics
        endpoint = request.url.path
        if endpoint not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "status_codes": {},
            }

        metrics = self.endpoint_metrics[endpoint]
        metrics["count"] += 1
        metrics["total_time"] += duration
        metrics["avg_time"] = metrics["total_time"] / metrics["count"]

        # Track status codes
        status = str(response.status_code)
        metrics["status_codes"][status] = metrics["status_codes"].get(status, 0) + 1

        return response

    def get_metrics(self) -> dict:
        """Get current metrics for monitoring."""
        return {
            "total_requests": self.request_count,
            "endpoints": self.endpoint_metrics,
        }


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns unique request IDs for tracing.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        import uuid

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Store in request state
        request.state.request_id = request_id

        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


# CORS middleware is in main app, not here
