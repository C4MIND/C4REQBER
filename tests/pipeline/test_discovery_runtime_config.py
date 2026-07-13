from __future__ import annotations

import asyncio

import pytest

from src.pipeline.discovery_config import (
    minimum_discovery_papers,
    minimum_paradigm_shift_papers,
    simulation_timeout_seconds,
)
from src.pipeline.discovery_phases.phase_5_verification import run_verification_suite


def test_discovery_defaults_are_realistic_and_configurable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("C4_SIMULATION_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("C4_MIN_DISCOVERY_PAPERS", raising=False)
    monkeypatch.delenv("C4_MIN_PARADIGM_SHIFT_PAPERS", raising=False)
    assert simulation_timeout_seconds() == 60.0
    assert minimum_discovery_papers() == 5
    assert minimum_paradigm_shift_papers() == 20

    monkeypatch.setenv("C4_SIMULATION_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("C4_MIN_DISCOVERY_PAPERS", "8")
    monkeypatch.setenv("C4_MIN_PARADIGM_SHIFT_PAPERS", "30")
    assert simulation_timeout_seconds() == 12.5
    assert minimum_discovery_papers() == 8
    assert minimum_paradigm_shift_papers() == 30


@pytest.mark.asyncio
async def test_verification_does_not_fabricate_empirical_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.discovery.pipeline_logic as logic

    async def simulation(*args: object, **kwargs: object) -> dict[str, object]:
        await asyncio.sleep(0)
        return {"status": "completed"}

    async def proof(*args: object, **kwargs: object) -> dict[str, object]:
        return {"generated": True}

    monkeypatch.setattr(logic, "run_relevant_simulation", simulation)
    monkeypatch.setattr(logic, "generate_lean4_proof", proof)
    monkeypatch.setattr(logic, "run_bayesian_model_averaging", lambda *args: {"ok": True})
    monkeypatch.setattr(logic, "run_dempster_shafer", lambda *args: {"ok": True})
    monkeypatch.setattr(logic, "run_bayesian_conjugate_update", lambda *args: {"ok": True})
    monkeypatch.setattr(logic, "run_causal_do_calculus", lambda *args: {"ok": True})
    monkeypatch.setattr(logic, "run_counterfactual", lambda *args: {"ok": True})

    results = await run_verification_suite(
        "problem",
        "physics",
        {"hypothesis": {"text": "claim"}},
        [],
    )

    assert results["simulation"]["status"] == "completed"
    assert results["monte_carlo"] == {
        "status": "skipped",
        "reason": "No empirical hypothesis and baseline metrics were supplied",
    }


def test_bayesian_helpers_skip_without_observed_evidence() -> None:
    from src.discovery.pipeline_logic import (
        run_bayesian_conjugate_update,
        run_bayesian_model_averaging,
    )

    bma = run_bayesian_model_averaging({}, {"status": "skipped"})
    update = run_bayesian_conjugate_update({"status": "skipped"})

    assert bma["status"] == "skipped"
    assert update["status"] == "skipped"
    assert update["posterior_mean"] is None
