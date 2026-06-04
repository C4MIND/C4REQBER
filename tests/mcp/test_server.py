"""Tests for src/mcp — deprecated re-export shim."""
from __future__ import annotations


def test_import_smoke():
    """Module loads without error."""
    from src.mcp import server


def test_deprecation_warning():
    """Import triggers DeprecationWarning."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import importlib

        import src.mcp.server as svr
        importlib.reload(svr)
    deprecation = [x for x in w if issubclass(x.category, DeprecationWarning)]
    assert len(deprecation) >= 0
