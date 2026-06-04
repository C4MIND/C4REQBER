"""OpenTelemetry tracing setup with HTTP OTLP exporter.

Gracefully degrades when opentelemetry is not installed or disabled.
"""
from __future__ import annotations

import os
from typing import Any

logger: Any = None


def _log(msg: str) -> None:
    global logger
    if logger is None:
        try:
            import structlog
            logger = structlog.get_logger()
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
    logger.warning(msg)


try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    _HAS_OTEL = True
except Exception:
    _HAS_OTEL = False


def init_tracing(app: Any | None = None, service_name: str = "c4reqber") -> Any | None:
    """Initialize OpenTelemetry tracing with HTTP OTLP exporter."""
    if os.environ.get("ENABLE_OPENTELEMETRY", "").lower() != "true":
        return None

    if not _HAS_OTEL:
        _log("opentelemetry packages not installed, skipping tracing init")
        return None

    resource = Resource.create({SERVICE_NAME: service_name})

    endpoint = os.environ.get(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4318/v1/traces",
    )
    exporter = OTLPSpanExporter(endpoint=endpoint)

    _tracer_provider = TracerProvider(resource=resource)
    _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(_tracer_provider)

    if app:
        FastAPIInstrumentor.instrument_app(app)

    HTTPXClientInstrumentor().instrument()

    tracer = trace.get_tracer(service_name)

    try:
        from src.di.container import get_container
        get_container().register("tracer_provider", _tracer_provider)
    except Exception:
        pass

    return tracer


def get_tracer_provider() -> Any | None:
    """Get tracer provider."""
    if not _HAS_OTEL:
        return None
    try:
        from src.di.container import get_container
        container = get_container()
        if container.has("tracer_provider"):
            return container.resolve("tracer_provider")
    except Exception:
        pass
    return None
