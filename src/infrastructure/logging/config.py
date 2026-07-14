"""
C4REQBER: Structured Logging Configuration
Production-ready logging with structlog: JSON for prod, colored console for dev.
Trace ID propagation via contextvars.
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog


# Context variable for trace ID propagation
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    """Get current trace ID or generate a new one."""
    tid = _trace_id.get()
    if tid is None:
        tid = str(uuid.uuid4())
        _trace_id.set(tid)
    return tid


def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context."""
    _trace_id.set(trace_id)


def _add_trace_id(logger: Any, method_name: Any, event_dict: Any) -> Any:
    """Processor: inject trace_id into every log entry."""
    event_dict["trace_id"] = get_trace_id()
    return event_dict


def _add_env_info(logger: Any, method_name: Any, event_dict: Any) -> Any:
    """Processor: add environment info."""
    event_dict["env"] = os.getenv("ENV", "development")
    event_dict["service"] = "c4reqber"
    return event_dict


def configure_logging() -> None:
    """Configure structlog for the application."""
    env = os.getenv("ENV", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_trace_id,
        _add_env_info,
        structlog.stdlib.ExtraAdder(),
    ]

    if env == "production":
        # JSON format for production
        structlog.configure(
            processors=shared_processors  # type: ignore[arg-type]
            + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level, logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        # Also configure stdlib logging to JSON
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level, logging.INFO),
        )
    else:
        # Colored console for development
        structlog.configure(
            processors=shared_processors  # type: ignore[arg-type]
            + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level, logging.DEBUG)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level, logging.DEBUG),
        )

    # Wrap stdlib loggers through structlog
    structlog.stdlib.recreate_defaults()


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
