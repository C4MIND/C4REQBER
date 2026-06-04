"""OpenTelemetry metrics with HTTP OTLP exporter"""
from __future__ import annotations

import os
from typing import Any

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from src.di.container import get_container


def init_metrics(service_name: str = "c4reqber") -> dict[str, Any] | None:
    """Initialize OpenTelemetry metrics with HTTP OTLP exporter.

    Returns a dict[str, Any] of metric instruments or None if disabled/unavailable.
    """
    if os.environ.get("ENABLE_OPENTELEMETRY", "").lower() != "true":
        return None

    try:
        resource = Resource.create({SERVICE_NAME: service_name})

        endpoint = os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://localhost:4318/v1/metrics",
        )
        exporter = OTLPMetricExporter(endpoint=endpoint)
        reader = PeriodicExportingMetricReader(exporter)

        _meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[reader],
        )
        metrics.set_meter_provider(_meter_provider)

        meter = metrics.get_meter(service_name)

        _METRICS_CACHE = {
            "request_counter": meter.create_counter(
                "api_requests_total",
                description="Total API requests",
                unit="1",
            ),
            "request_duration": meter.create_histogram(
                "api_request_duration_seconds",
                description="API request duration",
                unit="s",
            ),
            "cache_hits": meter.create_counter(
                "cache_hits_total",
                description="Total cache hits",
                unit="1",
            ),
        }

        container = get_container()
        container.register("meter_provider", _meter_provider)
        container.register("metrics_cache", _METRICS_CACHE)

        return _METRICS_CACHE

    except ImportError:
        import structlog
        structlog.get_logger().warning(
            "opentelemetry packages not installed, skipping metrics init"
        )
        return None

def get_metrics() -> dict[str, Any] | None:
    """Get the cached metric instruments dict[str, Any]."""
    container = get_container()
    if container.has("metrics_cache"):
        return container.resolve("metrics_cache")
    return None

def get_meter_provider() -> MeterProvider | None:
    """Get meter provider."""
    container = get_container()
    if container.has("meter_provider"):
        return container.resolve("meter_provider")
    return None
