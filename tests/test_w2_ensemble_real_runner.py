"""W2: EnsembleRunner must call PatternRunner — not invent noise by default."""

from __future__ import annotations

import pytest

from src.discovery.closed_loop.ensemble_runner import EnsembleRunner, _extract_scalar
from src.discovery.closed_loop.experiment_designer import ExperimentDesign


class _FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict | None]] = []

    def run(self, pattern_id, hypothesis=None, engine=None, force_cpu=False):
        self.calls.append((pattern_id, dict(hypothesis or {})))
        idx = hypothesis.get("ensemble_index", 0) if hypothesis else 0
        return {
            "status": "completed",
            "executed": True,
            "potential_energy": 10.0 + float(idx),
            "engine": "legacy",
        }


class _FailRunner:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, pattern_id, hypothesis=None, engine=None, force_cpu=False):
        self.calls += 1
        return {"status": "unavailable", "stub": True, "note": "nope"}


@pytest.mark.asyncio
async def test_ensemble_calls_runner_n_times():
    fake = _FakeRunner()
    runner = EnsembleRunner(runner=fake, allow_heuristic_fallback=False)
    design = ExperimentDesign(
        simulator="monte_carlo",
        params={"seed": 1, "scale": 1.0, "perturbation": 0.0},
        n_runs=5,
        target_uncertainty=0.1,
    )
    out = await runner.run_ensemble(design, hypothesis={"text": "H"})
    assert len(fake.calls) == 5
    assert all(c[0] == "monte_carlo" for c in fake.calls)
    assert out["heuristic"] is False
    assert out["n_successful"] == 5
    assert "PatternRunner" in out["note"] or "numeric" in out["note"]
    assert out["predicted"] != out["observed"] or out["n_successful"] == 5
    # Anti-fraud: must not be the old placeholder note
    assert "Placeholder ensemble" not in out["note"]


@pytest.mark.asyncio
async def test_ensemble_no_noise_when_fallback_disabled():
    fake = _FailRunner()
    runner = EnsembleRunner(runner=fake, allow_heuristic_fallback=False)
    design = ExperimentDesign(
        simulator="physics",
        params={"seed": 2, "scale": 1.0, "perturbation": 0.0},
        n_runs=3,
        target_uncertainty=0.2,
    )
    out = await runner.run_ensemble(design)
    assert fake.calls == 3
    assert out.get("status") == "unavailable"
    assert out["heuristic"] is False
    assert out["predicted"] is None


def test_extract_scalar_ignores_stub():
    assert _extract_scalar({"status": "unavailable", "stub": True, "potential_energy": 1.0}) is None
    assert (
        _extract_scalar({"status": "completed", "executed": True, "potential_energy": 3.5}) == 3.5
    )


def test_extract_scalar_no_hash_theater():
    assert (
        _extract_scalar({"status": "completed", "executed": True, "note": "hello world output"})
        is None
    )


@pytest.mark.asyncio
async def test_ensemble_default_disallows_noise():
    fake = _FailRunner()
    runner = EnsembleRunner(runner=fake)  # default allow_heuristic_fallback=False
    design = ExperimentDesign(
        simulator="physics",
        params={"seed": 2, "scale": 1.0, "perturbation": 0.0},
        n_runs=2,
        target_uncertainty=0.2,
    )
    out = await runner.run_ensemble(design)
    assert out.get("status") == "unavailable"
    assert out["predicted"] is None
