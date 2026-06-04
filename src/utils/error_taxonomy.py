"""Unified error taxonomy for C4REQBER.

Provides structured error classification with severity, retryability,
and user-facing messages.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any


class ErrorSeverity(enum.StrEnum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RetryPolicy(enum.StrEnum):
    """Whether an error is retryable."""
    NO_RETRY = "no_retry"
    IMMEDIATE = "immediate"
    BACKOFF = "backoff"
    CIRCUIT_BREAK = "circuit_break"


@dataclass(frozen=True, slots=True)
class C4Error:
    """Structured error with taxonomy metadata."""
    code: str
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    retry_policy: RetryPolicy = RetryPolicy.NO_RETRY
    user_message: str = ""
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.code}: {self.message}"


# --- Common error templates ---

ERR_TIMEOUT = C4Error(
    code="TIMEOUT",
    message="Operation timed out",
    severity=ErrorSeverity.WARNING,
    retry_policy=RetryPolicy.BACKOFF,
    user_message="The operation is taking longer than expected. Please try again.",
)

ERR_NETWORK = C4Error(
    code="NETWORK",
    message="Network request failed",
    severity=ErrorSeverity.WARNING,
    retry_policy=RetryPolicy.BACKOFF,
    user_message="Connection issue. Retrying...",
)

ERR_VALIDATION = C4Error(
    code="VALIDATION",
    message="Input validation failed",
    severity=ErrorSeverity.WARNING,
    retry_policy=RetryPolicy.NO_RETRY,
    user_message="Please check your input and try again.",
)

ERR_SECURITY = C4Error(
    code="SECURITY",
    message="Security check failed",
    severity=ErrorSeverity.ERROR,
    retry_policy=RetryPolicy.NO_RETRY,
    user_message="This request could not be processed for security reasons.",
)

ERR_INTERNAL = C4Error(
    code="INTERNAL",
    message="Internal error",
    severity=ErrorSeverity.ERROR,
    retry_policy=RetryPolicy.NO_RETRY,
    user_message="Something went wrong. Please try again later.",
)

ERR_RATE_LIMIT = C4Error(
    code="RATE_LIMIT",
    message="Rate limit exceeded",
    severity=ErrorSeverity.WARNING,
    retry_policy=RetryPolicy.BACKOFF,
    user_message="Too many requests. Please wait a moment.",
)


def classify_exception(exc: Exception) -> C4Error:
    """Classify a raw exception into a structured C4Error."""
    import asyncio
    import httpx
    import subprocess

    if isinstance(exc, asyncio.TimeoutError):
        return ERR_TIMEOUT
    if isinstance(exc, httpx.TimeoutException):
        return ERR_TIMEOUT
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 429:
            return ERR_RATE_LIMIT
        if exc.response.status_code >= 500:
            return C4Error(
                code="SERVER_ERROR",
                message=f"Server error {exc.response.status_code}",
                severity=ErrorSeverity.ERROR,
                retry_policy=RetryPolicy.BACKOFF,
                user_message="The server encountered an error. Retrying...",
            )
        return C4Error(
            code="CLIENT_ERROR",
            message=f"Client error {exc.response.status_code}",
            severity=ErrorSeverity.WARNING,
            retry_policy=RetryPolicy.NO_RETRY,
            user_message="The request could not be completed.",
        )
    if isinstance(exc, httpx.HTTPError):
        return ERR_NETWORK
    if isinstance(exc, subprocess.TimeoutExpired):
        return ERR_TIMEOUT
    if isinstance(exc, subprocess.CalledProcessError):
        return C4Error(
            code="PROCESS_ERROR",
            message=f"Process exited with code {exc.returncode}",
            severity=ErrorSeverity.ERROR,
            retry_policy=RetryPolicy.NO_RETRY,
            user_message="The verification process failed.",
        )
    if isinstance(exc, ValueError):
        return ERR_VALIDATION
    if isinstance(exc, PermissionError):
        return ERR_SECURITY
    return ERR_INTERNAL
