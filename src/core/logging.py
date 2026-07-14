"""
C4REQBER Structured Logging Module

Provides structured JSON logging with structlog, OpenTelemetry integration,
and Sentry error tracking support.

Usage:
    from src.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("event_happened", key="value", user_id=123)
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "console").lower()  # "json" or "console"
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
ENABLE_OPENTELEMETRY = os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true"

# Context variable for request ID (correlation)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# ═══════════════════════════════════════════════════════════════════
# REQUEST ID MANAGEMENT
# ═══════════════════════════════════════════════════════════════════


def get_request_id() -> str | None:
    """Get current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set request ID in context. If not provided, generates a new UUID."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear request ID from context."""
    request_id_var.set(None)


# ═══════════════════════════════════════════════════════════════════
# SENTRY INTEGRATION
# ═══════════════════════════════════════════════════════════════════


def init_sentry() -> None:
    """Initialize Sentry SDK if DSN is configured."""
    if not SENTRY_DSN:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            integrations=[sentry_logging],
            environment=os.getenv("ENV", "development"),
            release=os.getenv("RELEASE_VERSION", "dev"),
        )
    except ImportError:
        structlog.get_logger().warning("sentry_sdk not installed, skipping Sentry init")


# ═══════════════════════════════════════════════════════════════════
# OPENTELEMETRY INTEGRATION
# ═══════════════════════════════════════════════════════════════════


def init_opentelemetry() -> None:
    """Initialize OpenTelemetry if enabled."""
    if not ENABLE_OPENTELEMETRY:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider()
        processor = BatchSpanProcessor(OTLPSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        # Add trace ID to log context
        old_processors = structlog.get_config().get("processors", [])

        def add_trace_id(logger: Any, method_name: Any, event_dict: Any) -> Any:
            """Add trace id."""
            span = trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                if ctx.is_valid:
                    event_dict["trace_id"] = format(ctx.trace_id, "032x")
                    event_dict["span_id"] = format(ctx.span_id, "016x")
            return event_dict

        structlog.configure(processors=old_processors + [add_trace_id])

    except ImportError:
        structlog.get_logger().warning(
            "opentelemetry not installed, skipping OTel init"
        )


# ═══════════════════════════════════════════════════════════════════
# STRUCTLOG CONFIGURATION
# ═══════════════════════════════════════════════════════════════════


def _add_request_id(logger: Any, method_name: Any, event_dict: Any) -> Any:
    """Add request ID to log context."""
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def _add_environment(logger: Any, method_name: Any, event_dict: Any) -> Any:
    """Add environment info to log context."""
    event_dict["env"] = os.getenv("ENV", "development")
    return event_dict


def configure_logging() -> None:
    """Configure structlog and standard logging."""

    shared_processors = [
        # Add timestamp with ISO format
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # Custom processors
        _add_request_id,
        _add_environment,
    ]

    if LOG_FORMAT == "json":
        # Production: JSON format
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,  # type: ignore[arg-type]
        )
    else:
        # Development: Console format with colors
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,  # type: ignore[arg-type]
        )

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Configure structlog
    structlog.configure(
        processors=shared_processors  # type: ignore[arg-type]
        + [
            # Prepare for stdlib handler
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Initialize optional integrations
    init_sentry()
    init_opentelemetry()


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        A bound logger with structured logging capabilities

    Example:
        >>> from src.core.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("user_action", user_id=123, action="login")
        {"event": "user_action", "user_id": 123, "action": "login", ...}
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


# ═══════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════


def get_request_id_middleware() -> Any:
    """
    Get FastAPI middleware for request ID tracking.

    Usage:
        from fastapi import FastAPI
        from src.core.logging import get_request_id_middleware

        app = FastAPI()
        app.middleware("http")(get_request_id_middleware())
    """
    from fastapi import Request, Response

    async def request_id_middleware(request: Request, call_next: Any) -> Any:
        # Get or generate request ID
        """Request id middleware."""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)

        # Process request
        response: Response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request
        logger = get_logger("api.request")
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            request_id=request_id,
        )

        clear_request_id()
        return response

    return request_id_middleware


# ═══════════════════════════════════════════════════════════════════
# CONTEXT MANAGERS
# ═══════════════════════════════════════════════════════════════════

from contextlib import contextmanager


@contextmanager  # type: ignore[arg-type]
def log_context(**kwargs: Any) -> None:  # type: ignore[misc]
    """
    Context manager for adding fields to log context.

    Example:
        with log_context(user_id=123, session_id="abc"):
            logger.info("action_performed")
    """
    bind = structlog.contextvars.bind_contextvars
    bind(**kwargs)
    try:
        yield
    finally:
        structlog.contextvars.unbind_contextvars(*kwargs.keys())


# ═══════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════

# Auto-configure on import (if not already configured)
if not structlog.is_configured():
    configure_logging()
