"""Suite 02 — QualityGates.check_simulation demotes engine_truth fallbacks."""

from __future__ import annotations

from src.pipeline.quality import QualityGates


def test_not_newton_engine_truth_not_full_pass() -> None:
    gates = QualityGates()
    # require_simulation_success default may be False — still must not score 1.0 PASS
    out = gates.check_simulation(
        {
            "status": "success",
            "stub": False,
            "heuristic": False,
            "executed": True,
            "engine_truth": "not_newton_physics",
            "metrics": {"execution_time": 1.0},
        }
    )
    assert out.score < 1.0
    assert "PASS" not in out.message or out.score <= 0.25
    assert out.details.get("stub") is True or out.score <= 0.25


def test_rebound_not_amuse_engine_truth_demoted() -> None:
    gates = QualityGates()
    out = gates.check_simulation(
        {
            "status": "completed",
            "stub": False,
            "heuristic": False,
            "executed": True,
            "engine_truth": "rebound_not_amuse",
            "metrics": {},
        }
    )
    assert out.score < 1.0


def test_legacy_fallback_engine_truth_demoted() -> None:
    gates = QualityGates()
    out = gates.check_simulation(
        {
            "status": "success",
            "stub": False,
            "executed": True,
            "engine_truth": "legacy_fallback",
            "metrics": {},
        }
    )
    assert out.score < 1.0
