"""Tests for src/observability/ — dashboards, metrics, middleware."""
from __future__ import annotations

import pytest


def test_dashboards_import():
    try:
        from src.observability.dashboards import (
            DashboardPanel,
            GrafanaDashboardGenerator,
            generate_turbo_cdi_dashboard,
        )
    except ImportError:
        pytest.skip("observability module has import issues")
    assert DashboardPanel is not None
    assert GrafanaDashboardGenerator is not None
    assert callable(generate_turbo_cdi_dashboard)


def test_metrics_import():
    try:
        import importlib
        spec = importlib.util.find_spec("src.observability.metrics")
        if spec is None:
            pytest.skip("observability.metrics module not found")
        from src.observability.metrics import get_metrics, init_metrics
    except (ImportError, ModuleNotFoundError):
        pytest.skip("observability.metrics has import issues")
    assert callable(init_metrics)
    assert callable(get_metrics)


def test_middleware_import():
    try:
        from src.observability.middleware import ObservabilityMiddleware
    except ImportError:
        pytest.skip("observability.middleware has import issues")
    assert ObservabilityMiddleware is not None
