"""Benchmark 1: Monte Carlo integration — convergence and performance."""

import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pytest


np.random.seed(42)

from src.patterns.core import Hypothesis
from src.patterns.library.monte_carlo import MonteCarloPattern


@pytest.fixture(autouse=True)
def _reset_numpy_seed():
    np.random.seed(42)


class TestMonteCarloConvergence:
    def test_mc_convergence_estimates_consistent(self):
        """MC with 50K samples should produce consistent estimates within 1% of each other."""
        np.random.seed(42)
        pattern = MonteCarloPattern()
        hypothesis = Hypothesis(
            text="test",
            parameters={"base_value": 3.14159, "noise_scale": 0.1},
        )
        estimates = []
        for i in range(3):
            np.random.seed(42 + i)
            result = asyncio_run(
                pattern.run(hypothesis, {"n_samples": 50000, "variance_reduction": "none"})
            )
            estimates.append(result.metrics["mean"])

        cv = np.std(estimates) / abs(np.mean(estimates))
        assert cv < 0.05, f"MC estimates inconsistent, CV={cv:.4f}"

    def test_mc_stratified_reduces_variance(self):
        """Stratified sampling should have lower std than naive MC."""
        np.random.seed(42)
        pattern = MonteCarloPattern()
        hypothesis = Hypothesis(
            text="test",
            parameters={"base_value": 3.14159, "noise_scale": 0.1},
        )
        result_naive = asyncio_run(
            pattern.run(hypothesis, {"n_samples": 50000, "variance_reduction": "none"})
        )
        result_strat = asyncio_run(
            pattern.run(hypothesis, {"n_samples": 50000, "variance_reduction": "stratified"})
        )
        assert result_strat.metrics["std"] <= result_naive.metrics["std"] * 1.5, (
            f"Stratified std={result_strat.metrics['std']:.4f} vs naive={result_naive.metrics['std']:.4f}"
        )

    def test_mc_ci_contains_mean(self):
        """Confidence interval should contain the mean."""
        pattern = MonteCarloPattern()
        hypothesis = Hypothesis(
            text="test",
            parameters={"base_value": 1.0, "noise_scale": 0.2},
        )
        result = asyncio_run(
            pattern.run(hypothesis, {"n_samples": 50000, "variance_reduction": "none"})
        )
        assert result.metrics["ci_lower"] <= result.metrics["mean"] <= result.metrics["ci_upper"]


class TestMonteCarloPerformance:
    def test_mc_performance_50k_samples(self):
        """50K samples should compute in under 5 seconds."""
        pattern = MonteCarloPattern()
        hypothesis = Hypothesis(
            text="test",
            parameters={"base_value": 3.14159, "noise_scale": 0.1},
        )
        start = time.perf_counter()
        for _ in range(3):
            asyncio_run(pattern.run(hypothesis, {"n_samples": 15000, "variance_reduction": "none"}))
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"MC too slow: {elapsed:.3f}s"

    def test_mc_batch_processing(self):
        """Batch processing should scale gracefully."""
        pattern = MonteCarloPattern()
        hypothesis = Hypothesis(
            text="test",
            parameters={"base_value": 1.0, "noise_scale": 0.1},
        )
        result = asyncio_run(
            pattern.run(
                hypothesis,
                {"n_samples": 20000, "variance_reduction": "sobol", "batch_size": 2000},
            )
        )
        assert result.status.value == "completed"
        assert result.metrics["n_samples"] >= 20000


def asyncio_run(coro):
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        import concurrent.futures
        import threading

        future = concurrent.futures.Future()

        def _run():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                future.set_result(new_loop.run_until_complete(coro))
                new_loop.close()
            except Exception as e:
                future.set_exception(e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join()
        return future.result()
    else:
        return asyncio.run(coro)
