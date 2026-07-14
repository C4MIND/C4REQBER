"""
Tests for src/patterns/library/optimization.py (Linear Programming pattern)

NOTE: This file already has comprehensive tests in test_optimization_lp.py.
This file adds additional coverage for:
- Edge cases with mocked heavy computations
- Resource estimation with complexity calculation
- Additional error handling paths
- Config edge cases
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.optimization import (
    HAS_CVXPY,
    LinearProgrammingPattern,
    OptimizationType,
)


# ═══════════════════════════════════════════════════════════════════
# Complexity and Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestComplexityCalculation:
    def test_complexity_small(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={"num_variables": 3, "num_constraints": 5})
        resources = pattern.estimate_resources(h)
        expected_complexity = (3 + 5) ** 3
        assert resources["memory_gb"] == pytest.approx(0.5 + expected_complexity / 1e6)
        assert resources["estimated_time_seconds"] == pytest.approx(expected_complexity / 1e8)

    def test_complexity_large(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={"num_variables": 100, "num_constraints": 200})
        resources = pattern.estimate_resources(h)
        expected_complexity = (100 + 200) ** 3
        assert resources["memory_gb"] > 0.5
        assert resources["estimated_time_seconds"] > 0

    def test_complexity_zero_variables(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={"num_variables": 0, "num_constraints": 5})
        resources = pattern.estimate_resources(h)
        assert resources["memory_gb"] == pytest.approx(0.5, abs=0.01)
        assert resources["estimated_time_seconds"] >= 0.0


# ═══════════════════════════════════════════════════════════════════
# Mocked Heavy Computation Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestMockedHeavyComputations:
    async def test_solve_linear_mocked(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={})
        config = {"optimization_type": "linear", "num_variables": 3, "num_constraints": 2}

        mock_result = MagicMock()
        mock_result.fun = 42.0
        mock_result.success = True
        mock_result.status = 0
        mock_result.nit = 50
        mock_result.slack = np.array([1.0, 2.0])
        mock_result.x = np.array([1.0, 2.0, 3.0])

        with patch("src.patterns.library.optimization.linprog", return_value=mock_result):
            result = await pattern._solve_linear(h, config)
            assert result["metrics"]["optimal_value"] == 42.0
            assert result["metrics"]["success"] is True

    async def test_solve_nonlinear_mocked(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={})
        config = {"optimization_type": "nonlinear", "num_variables": 100}

        mock_result = MagicMock()
        mock_result.fun = 1.0
        mock_result.success = True
        mock_result.nit = 20
        mock_result.x = np.zeros(100)

        with patch("src.patterns.library.optimization.minimize", return_value=mock_result):
            result = await pattern._solve_nonlinear(h, config)
            assert result["metrics"]["optimal_value"] == 1.0
            assert result["metrics"]["success"] is True

    async def test_solve_quadratic_mocked(self):
        if not HAS_CVXPY:
            pytest.skip("cvxpy not available")
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={})
        config = {"optimization_type": "quadratic", "num_variables": 50}

        mock_x = MagicMock()
        mock_x.value = np.array([0.5] * 50)
        mock_x.__array__ = lambda dtype=None: np.zeros(50)
        mock_x.__ge__ = lambda self, other: MagicMock()
        mock_x.__eq__ = lambda self, other: MagicMock()

        mock_sum_result = MagicMock()
        mock_sum_result.__eq__ = lambda self, other: MagicMock()

        mock_problem = MagicMock()
        mock_problem.solve.return_value = 1.5
        mock_problem.status = "optimal"

        with patch("src.patterns.library.optimization.cp.Variable", return_value=mock_x):
            with patch("src.patterns.library.optimization.cp.Minimize"):
                with patch(
                    "src.patterns.library.optimization.cp.Problem", return_value=mock_problem
                ):
                    with patch("src.patterns.library.optimization.cp.quad_form"):
                        with patch(
                            "src.patterns.library.optimization.cp.sum", return_value=mock_sum_result
                        ):
                            result = await pattern._solve_quadratic(h, config)
                            assert result["metrics"]["optimal_value"] == 1.5


# ═══════════════════════════════════════════════════════════════════
# Additional Error Handling
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestAdditionalErrorHandling:
    async def test_linprog_failure(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={})
        config = {"optimization_type": "linear", "num_variables": 3, "num_constraints": 5}

        mock_result = MagicMock()
        mock_result.fun = 0.0
        mock_result.success = False
        mock_result.status = 2
        mock_result.nit = 100
        mock_result.slack = None
        mock_result.x = None

        with patch("src.patterns.library.optimization.linprog", return_value=mock_result):
            result = await pattern._solve_linear(h, config)
            assert result["metrics"]["success"] is False
            assert "failed" in result["logs"][0].lower()

    async def test_run_with_linprog_error(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={})
        config = {"optimization_type": "linear", "num_variables": 3, "num_constraints": 5}

        with patch(
            "src.patterns.library.optimization.linprog", side_effect=MemoryError("out of memory")
        ):
            result = await pattern.run(h, config)
            assert result.status == SimulationStatus.FAILED
            assert "out of memory" in result.error_message

    async def test_minimize_failure(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={})
        config = {"optimization_type": "nonlinear", "num_variables": 3}

        mock_result = MagicMock()
        mock_result.fun = float("inf")
        mock_result.success = False
        mock_result.nit = 0
        mock_result.x = np.zeros(3)

        with patch("src.patterns.library.optimization.minimize", return_value=mock_result):
            result = await pattern._solve_nonlinear(h, config)
            assert result["metrics"]["success"] is False


# ═══════════════════════════════════════════════════════════════════
# Config Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestConfigEdgeCases:
    def test_estimate_resources_empty_hypothesis(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis()
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert resources["gpu_required"] is False

    def test_estimate_resources_negative_values(self):
        pattern = LinearProgrammingPattern()
        h = Hypothesis(parameters={"num_variables": -5, "num_constraints": -3})
        resources = pattern.estimate_resources(h)
        # Negative values still compute (cube of negative)
        assert resources["estimated_time_seconds"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
