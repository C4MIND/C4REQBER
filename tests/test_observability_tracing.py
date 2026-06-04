"""Tests for src/observability/tracing.py"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestTracing:
    def _import_tracing(self):
        try:
            from src.observability import tracing
            return tracing
        except ImportError:
            pytest.skip("opentelemetry not installed")

    def test_init_tracing_disabled_by_default(self):
        tracing = self._import_tracing()
        with patch.object(tracing, "_tracer_provider", None):
            result = tracing.init_tracing()
            assert result is None

    def test_init_tracing_with_enable_flag(self):
        tracing = self._import_tracing()
        with patch.dict(os.environ, {"ENABLE_OPENTELEMETRY": "true"}):
            with patch.object(tracing, "_tracer_provider", None):
                mock_tracer = MagicMock()
                with patch("src.observability.tracing.trace.get_tracer", return_value=mock_tracer):
                    with patch("src.observability.tracing.TracerProvider") as mock_tp:
                        with patch("src.observability.tracing.OTLPSpanExporter"):
                            with patch("src.observability.tracing.BatchSpanProcessor"):
                                with patch("src.observability.tracing.trace.set_tracer_provider"):
                                    with patch("src.observability.tracing.HTTPXClientInstrumentor"):
                                        with patch("src.observability.tracing.FastAPIInstrumentor"):
                                            result = tracing.init_tracing()
                                            assert result is mock_tracer

    def test_init_tracing_import_error(self):
        tracing = self._import_tracing()
        with patch.dict(os.environ, {"ENABLE_OPENTELEMETRY": "true"}):
            with patch("src.observability.tracing.trace.set_tracer_provider", side_effect=ImportError):
                result = tracing.init_tracing()
                assert result is None

    def test_get_tracer_provider(self):
        tracing = self._import_tracing()
        with patch.object(tracing, "_tracer_provider", None):
            provider = tracing.get_tracer_provider()
            assert provider is None
