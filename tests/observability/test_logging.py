"""Tests for src/observability/logging.py — StructuredLogFormatter, setup_logging."""
from __future__ import annotations

import json
import logging

from src.observability.logging import StructuredLogFormatter, setup_logging


class TestStructuredLogFormatter:
    def test_format_basic(self):
        fmt = StructuredLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Hello world", args=(), exc_info=None,
        )
        result = fmt.format(record)
        parsed = json.loads(result)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Hello world"
        assert "timestamp" in parsed

    def test_format_with_exception(self):
        fmt = StructuredLogFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="test.py",
                lineno=1, msg="Error occurred", args=(), exc_info=sys.exc_info(),
            )
            result = fmt.format(record)
            parsed = json.loads(result)
            assert "exception" in parsed

    def test_format_extra_fields(self):
        fmt = StructuredLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Extra", args=(), exc_info=None,
        )
        record.__dict__["request_id"] = "abc123"
        record.__dict__["user_id"] = 42
        result = fmt.format(record)
        parsed = json.loads(result)
        assert parsed["request_id"] == "abc123"
        assert parsed["user_id"] == 42


class TestSetupLogging:
    def test_structured_logging(self):
        logger = setup_logging(level="INFO", format_type="structured")
        assert logger.name == "c4_cdi_turbo"
        assert logger.level == logging.INFO

    def test_simple_logging(self):
        logger = setup_logging(level="DEBUG", format_type="simple")
        assert logger.level == logging.DEBUG
