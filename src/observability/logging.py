"""
C4REQBER: Structured Logging Configuration
Production-grade logging with OpenTelemetry integration.
"""
from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime

from src.compat import UTC


class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "asctime", "getMessage",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def setup_logging(
    level: str = "INFO",
    format_type: str = "structured",  # "structured" or "simple"
    enable_opentelemetry: bool = False,
) -> logging.Logger:
    """Configure structured logging for C4REQBER."""

    logger = logging.getLogger("c4_cdi_turbo")
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    if format_type == "structured":
        formatter = StructuredLogFormatter()
    else:
        formatter = logging.Formatter(  # type: ignore[assignment]
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # OpenTelemetry integration
    if enable_opentelemetry:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider()
            processor = BatchSpanProcessor(OTLPSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)

            logger.info("OpenTelemetry tracing enabled")
        except ImportError:
            logger.warning("OpenTelemetry not installed. Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the c4_cdi_turbo prefix."""
    return logging.getLogger(f"c4_cdi_turbo.{name}")
