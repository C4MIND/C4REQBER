"""W4: runner_v2 must not invent completed over stub/unavailable."""

from __future__ import annotations

from src.simulations.runner_v2 import PatternRunnerV2


def test_finalize_does_not_promote_stub():
    out = PatternRunnerV2._finalize_result(
        {
            "pattern_id": "x",
            "status": "completed",  # lying outer
            "result": {"stub": True, "status": "unavailable", "note": "nope"},
        }
    )
    assert out["status"] == "unavailable"
    assert out.get("stub") is True
    assert out.get("executed") is False


def test_finalize_keeps_explicit_unavailable():
    out = PatternRunnerV2._finalize_result(
        {"status": "unavailable", "stub": True, "executed": False}
    )
    assert out["status"] == "unavailable"


def test_finalize_defaults_completed_only_when_clean():
    out = PatternRunnerV2._finalize_result(
        {"pattern_id": "x", "executed": True, "result": {"potential_energy": 1.0}}
    )
    assert out["status"] == "completed"


def test_finalize_refuses_missing_status_without_executed():
    out = PatternRunnerV2._finalize_result({"pattern_id": "x", "energy": 1.0})
    assert out["status"] == "unavailable"
    assert out.get("stub") is True
    assert out.get("accelerated") is False


def test_finalize_partial_not_completed():
    out = PatternRunnerV2._finalize_result(
        {
            "status": "partial",
            "executed": True,
            "backend": "numpy_fallback",
            "engine_truth": "not_newton_physics",
        }
    )
    assert out["status"] == "partial"
    assert out.get("accelerated") is False
