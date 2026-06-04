"""
c4-cdi-turbo: Observability Module
Re-exports logging, Sentry, and OpenTelemetry.
"""
from __future__ import annotations

try:
    from src.observability.logging import get_logger, setup_logging
    from src.observability.sentry import SentryManager, get_sentry
    from src.observability.telemetry import TelemetryManager, get_telemetry
except Exception:
    get_logger = None  # type: ignore[assignment]
    setup_logging = None  # type: ignore[assignment]
    SentryManager = None  # type: ignore[assignment,misc]
    get_sentry = None  # type: ignore[assignment]
    TelemetryManager = None  # type: ignore[assignment,misc]
    get_telemetry = None  # type: ignore[assignment]


__all__ = [
    "setup_logging",
    "get_logger",
    "SentryManager",
    "get_sentry",
    "TelemetryManager",
    "get_telemetry",
]
