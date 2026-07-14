"""Tests for PatternResult — audit 2026-06-22 P2-D PoC.

PatternResult is the structured, JSON-serializable result type for
all BasePattern subclasses. Old dict-returning subclasses are still
supported via from_dict() for backward compatibility.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def test_pattern_result_basic_construction():
    from src.patterns.library.base import PatternResult

    r = PatternResult(pattern_id="test.foo", status="ok", data={"x": 42})
    assert r.pattern_id == "test.foo"
    assert r.status == "ok"
    assert r.data == {"x": 42}
    assert r.metrics == {}
    assert r.error_message == ""
    assert r.elapsed_seconds == 0.0


def test_pattern_result_to_dict_is_serializable():
    """to_dict() output must be JSON-serializable (crosses RPC boundary)."""
    from src.patterns.library.base import PatternResult

    r = PatternResult(
        pattern_id="acoustic.wave",
        status="ok",
        data={"frequency_hz": 440.0, "amplitude": 0.5},
        metrics={"duration_ms": 12.3},
        metadata={"domain": "physics"},
    )
    d = r.to_dict()
    # Must round-trip through JSON
    s = json.dumps(d)
    parsed = json.loads(s)
    assert parsed == d


def test_from_dict_handles_legacy_fields():
    """Legacy subclasses may use 'error' instead of 'error_message', 'duration' instead of 'elapsed_seconds'."""
    from src.patterns.library.base import PatternResult

    legacy = {"error": "boom", "duration": 1.5, "data": {"x": 1}}
    r = PatternResult.from_dict(legacy)
    assert r.error_message == "boom"
    assert r.elapsed_seconds == 1.5
    assert r.data == {"x": 1}


def test_from_dict_handles_missing_keys():
    """from_dict must not crash when keys are absent."""
    from src.patterns.library.base import PatternResult

    r = PatternResult.from_dict({})
    assert r.pattern_id == "unknown"
    assert r.status == "ok"
    assert r.data == {}
    assert r.error_message == ""


def test_from_dict_preserves_non_dict_data():
    """If 'data' is not a dict (legacy scalar/list), wrap it."""
    from src.patterns.library.base import PatternResult

    r = PatternResult.from_dict({"data": [1, 2, 3]})
    assert r.data == {"result": [1, 2, 3]}


def test_from_dict_returns_pattern_result():
    """from_dict return type is PatternResult (not bare dict)."""
    from src.patterns.library.base import PatternResult

    r = PatternResult.from_dict({"data": {}, "status": "ok"})
    assert isinstance(r, PatternResult)
    assert hasattr(r, "to_dict")
    assert callable(r.to_dict)
