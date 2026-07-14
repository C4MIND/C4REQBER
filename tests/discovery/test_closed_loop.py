"""Tests for closed-loop simulation module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.discovery.closed_loop.bayesian_tracker import BayesianHypothesisTracker
from src.discovery.closed_loop.convergence import ConvergenceChecker
from src.discovery.closed_loop.ensemble_runner import EnsembleRunner
from src.discovery.closed_loop.experiment_designer import ExperimentDesigner
from src.discovery.closed_loop.orchestrator import ClosedLoopOrchestrator
from src.discovery.closed_loop.refiner import HypothesisRefiner


class TestBayesianHypothesisTracker:
    def test_prior_default(self) -> None:
        tracker = BayesianHypothesisTracker("H1")
        assert tracker.prior == 0.5
        assert tracker.posterior == 0.5

    def test_update_increases_posterior_on_agreement(self) -> None:
        tracker = BayesianHypothesisTracker("H1")
        tracker.update({"predicted": 10.0, "observed": 10.1, "uncertainty": 1.0}, "sim1")
        assert tracker.posterior > tracker.prior

    def test_update_decreases_posterior_on_disagreement(self) -> None:
        tracker = BayesianHypothesisTracker("H1")
        tracker.update({"predicted": 10.0, "observed": 100.0, "uncertainty": 1.0}, "sim1")
        assert tracker.posterior < tracker.prior

    def test_bayes_factor(self) -> None:
        tracker = BayesianHypothesisTracker("H1", prior=0.9)
        assert tracker.bayes_factor == pytest.approx(9.0, abs=0.1)

    def test_to_dict(self) -> None:
        tracker = BayesianHypothesisTracker("H1")
        tracker.update({"predicted": 1.0, "observed": 1.0, "uncertainty": 0.5}, "sim")
        d = tracker.to_dict()
        assert d["evidence_count"] == 1
        assert "posterior" in d


class TestConvergenceChecker:
    def test_accept(self) -> None:
        checker = ConvergenceChecker()
        tracker = BayesianHypothesisTracker("H1", prior=0.9)
        # After update, posterior ~0.95 -> bayes_factor ~19
        tracker.update({"predicted": 1.0, "observed": 1.0, "uncertainty": 0.1}, "sim")
        assert checker.check(tracker, 0) == "accept"

    def test_reject(self) -> None:
        checker = ConvergenceChecker()
        tracker = BayesianHypothesisTracker("H1", prior=0.1)
        tracker.update({"predicted": 1.0, "observed": 100.0, "uncertainty": 0.1}, "sim")
        assert checker.check(tracker, 0) == "reject"

    def test_continue(self) -> None:
        checker = ConvergenceChecker()
        tracker = BayesianHypothesisTracker("H1")
        assert checker.check(tracker, 0) == "continue"

    def test_inconclusive_at_max_iter(self) -> None:
        checker = ConvergenceChecker(max_iterations=3)
        tracker = BayesianHypothesisTracker("H1")
        assert checker.check(tracker, 2) == "inconclusive"


class TestExperimentDesigner:
    def test_design_returns_valid(self) -> None:
        designer = ExperimentDesigner()
        tracker = BayesianHypothesisTracker("H1")
        design = designer.design(tracker, 0)
        assert design.simulator in designer.DEFAULT_SIMULATORS
        assert design.n_runs > 0
        assert "scale" in design.params

    def test_rotates_simulators(self) -> None:
        designer = ExperimentDesigner()
        tracker = BayesianHypothesisTracker("H1")
        d1 = designer.design(tracker, 0, ["a", "b"])
        d2 = designer.design(tracker, 1, ["a", "b"])
        assert d1.simulator != d2.simulator


class TestEnsembleRunner:
    @pytest.mark.anyio(backend="asyncio")
    async def test_run_ensemble(self) -> None:
        from src.discovery.closed_loop.experiment_designer import ExperimentDesign

        runner = EnsembleRunner()
        design = ExperimentDesign(
            simulator="test",
            params={"scale": 2.0, "seed": 42, "perturbation": 0.5},
            n_runs=10,
            target_uncertainty=0.5,
        )
        result = await runner.run_ensemble(design)
        assert "predicted" in result
        assert "uncertainty" in result
        assert result["n_runs"] == 10


class TestHypothesisRefiner:
    @pytest.mark.anyio(backend="asyncio")
    async def test_no_refinement_without_evidence(self) -> None:
        refiner = HypothesisRefiner()
        tracker = BayesianHypothesisTracker("H1")
        result = await refiner.refine("H1", tracker)
        assert result is None

    @pytest.mark.anyio(backend="asyncio")
    async def test_refinement_with_evidence(self) -> None:
        refiner = HypothesisRefiner()
        tracker = BayesianHypothesisTracker("H1")
        tracker.update({"predicted": 1.0, "observed": 1.0, "uncertainty": 0.1}, "sim")

        mock_response = AsyncMock()
        mock_response.content = "Refined: H1 under condition C"
        with patch.object(refiner._router, "generate_for_stage", return_value=mock_response):
            result = await refiner.refine("H1", tracker)

        assert result == "Refined: H1 under condition C"

    @pytest.mark.anyio(backend="asyncio")
    async def test_no_refinement_needed(self) -> None:
        refiner = HypothesisRefiner()
        tracker = BayesianHypothesisTracker("H1")
        tracker.update({"predicted": 1.0, "observed": 1.0, "uncertainty": 0.1}, "sim")

        mock_response = AsyncMock()
        mock_response.content = "NO_REFINEMENT_NEEDED"
        with patch.object(refiner._router, "generate_for_stage", return_value=mock_response):
            result = await refiner.refine("H1", tracker)

        assert result is None


class TestClosedLoopOrchestrator:
    @pytest.mark.anyio(backend="asyncio")
    async def test_runs_and_converges(self) -> None:
        orch = ClosedLoopOrchestrator(max_iterations=3)
        # Mock refiner to avoid LLM calls
        orch.refiner.refine = AsyncMock(return_value=None)
        result = await orch.run({"text": "H1"}, available_simulators=["test"])
        assert result.action in ("accept", "reject", "inconclusive", "continue")
        assert result.iterations <= 3
        assert result.tracker is not None

    @pytest.mark.anyio(backend="asyncio")
    async def test_respects_max_iterations(self) -> None:
        orch = ClosedLoopOrchestrator(max_iterations=2)
        orch.refiner.refine = AsyncMock(return_value=None)
        result = await orch.run({"text": "H1"})
        assert result.iterations <= 2
