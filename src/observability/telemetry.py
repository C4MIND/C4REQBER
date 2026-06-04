"""
C4REQBER: OpenTelemetry Configuration
Distributed tracing and metrics.
"""
from __future__ import annotations

import os
from typing import Any


class TelemetryManager:
    """Manages OpenTelemetry tracing and metrics."""

    def __init__(
        self,
        service_name: str = "c4reqber",
        otlp_endpoint: str | None = None,
    ) -> None:
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        self._tracer = None
        self._meter = None
        self._initialized = False

    def init(self) -> bool:
        """Initialize OpenTelemetry."""
        try:
            from opentelemetry import metrics, trace
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({SERVICE_NAME: self.service_name})

            # Traces
            trace_provider = TracerProvider(resource=resource)
            trace_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint, insecure=True)
            trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
            trace.set_tracer_provider(trace_provider)
            self._tracer = trace.get_tracer(self.service_name)  # type: ignore[assignment]

            # Metrics
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=self.otlp_endpoint, insecure=True)
            )
            metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            metrics.set_meter_provider(metrics_provider)
            self._meter = metrics.get_meter(self.service_name)  # type: ignore[assignment]

            # Auto-instrumentation
            FastAPIInstrumentor().instrument()
            RedisInstrumentor().instrument()
            SQLite3Instrumentor().instrument()

            self._initialized = True
            print(f"✅ OpenTelemetry initialized ({self.service_name} → {self.otlp_endpoint})")
            return True

        except ImportError as e:
            print(f"⚠️  OpenTelemetry not fully installed: {e}")
            print("   Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-redis opentelemetry-instrumentation-sqlite3")
            return False

    def start_span(self, name: str, **attributes: Any) -> Any:
        """Start a traced span."""
        if not self._tracer:
            return None
        return self._tracer.start_as_current_span(name, attributes=attributes)  # type: ignore[unreachable]

    def record_metric(self, name: str, value: float, **attributes: Any) -> None:
        """Record a metric value."""
        if not self._meter:
            return

        counter = self._meter.create_counter(name)  # type: ignore[unreachable]
        counter.add(value, attributes)


def get_telemetry() -> TelemetryManager:
    """Get singleton telemetry manager (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("telemetry", TelemetryManager)
