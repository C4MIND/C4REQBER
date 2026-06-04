"""
c4reqber: Centralized API error handling

Provides a unified error response schema and exception handler
for all v8 (and future) API routers.
"""
from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class C4APIError(Exception):
    """Base exception for API errors with structured response."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: dict[str, Any] | None = None,
        error_code: str = "internal_error",
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        self.error_code = error_code
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail,
            "status_code": self.status_code,
        }


class ValidationError(C4APIError):
    """Request validation failed."""

    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=422, detail=detail, error_code="validation_error")


class NotFoundError(C4APIError):
    """Resource not found."""

    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=404, detail=detail, error_code="not_found")


class ExternalServiceError(C4APIError):
    """Upstream service failed."""

    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=502, detail=detail, error_code="external_service_error")


async def c4_api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for C4APIError and subclasses."""
    if isinstance(exc, C4APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
    # Fallback for unexpected exceptions
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "internal_error",
            "message": "An unexpected error occurred",
            "detail": {"exception_type": type(exc).__name__, "exception": str(exc)},
            "status_code": 500,
        },
    )


def register_error_handlers(app: Any) -> None:
    """Register exception handlers on a FastAPI app."""
    app.add_exception_handler(C4APIError, c4_api_exception_handler)
    app.add_exception_handler(Exception, c4_api_exception_handler)
