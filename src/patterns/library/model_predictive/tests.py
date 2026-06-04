"""Unit tests for Model Predictive Control pattern."""

import unittest

import numpy as np

from .config import MPCConfig
from .core import ModelPredictivePattern
from .solvers import ActiveSetSolver
from .types import SystemType


class TestActiveSetSolver(unittest.TestCase):
    """Unit tests for active set[Any] QP solver"""

    def test_unconstrained_qp(self) -> None:
        """Test unconstrained QP"""
        solver = ActiveSetSolver()

        # min 0.5*x^2 + 2*x + 3 => x* = -2
        H = np.array([[1.0]])
        g = np.array([2.0])
        A_eq = np.zeros((0, 1))
        b_eq = np.zeros(0)
        A_ineq = np.zeros((0, 1))
        b_ineq = np.zeros(0)
        lb = np.array([-np.inf])
        ub = np.array([np.inf])

        x, feasible = solver.solve(H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub)

        self.assertTrue(feasible)
        self.assertAlmostEqual(x[0], -2.0, places=2)

    def test_constrained_qp(self) -> None:
        """Test QP with box constraints"""
        solver = ActiveSetSolver()

        # min 0.5*x^2 subject to x >= 1
        H = np.array([[1.0]])
        g = np.array([0.0])
        lb = np.array([1.0])
        ub = np.array([np.inf])

        x, feasible = solver.solve(
            H, g, np.zeros((0, 1)), np.zeros(0), np.zeros((0, 1)), np.zeros(0), lb, ub
        )

        self.assertTrue(feasible)
        self.assertGreaterEqual(x[0], 1.0 - 1e-4)

    def test_2d_qp(self) -> None:
        """Test 2D QP"""
        solver = ActiveSetSolver()

        # min 0.5*(x1^2 + x2^2) + x1 + 2*x2
        H = np.eye(2)
        g = np.array([1.0, 2.0])
        lb = np.array([-10.0, -10.0])
        ub = np.array([10.0, 10.0])

        x, feasible = solver.solve(
            H, g, np.zeros((0, 2)), np.zeros(0), np.zeros((0, 2)), np.zeros(0), lb, ub
        )

        self.assertTrue(feasible)
        self.assertAlmostEqual(x[0], -1.0, places=2)
        self.assertAlmostEqual(x[1], -2.0, places=2)

class TestModelPredictivePattern(unittest.TestCase):
    """Unit tests for MPC pattern"""

    def test_initialization(self) -> None:
        """Test pattern initialization"""
        pattern = ModelPredictivePattern()
        self.assertIsNotNone(pattern.config)
        self.assertEqual(pattern.config.N, 20)

    def test_qp_build(self) -> None:
        """Test QP matrix construction"""
        config = MPCConfig(system_type=SystemType.DOUBLE_INTEGRATOR, N=10)
        pattern = ModelPredictivePattern(config)

        x0 = np.array([1.0, 0.0])
        x_ref = np.array([0.0, 0.0])

        H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub = pattern._build_qp(x0, x_ref)

        # Check dimensions
        n_vars = config.N * config.B.shape[1]  # type: ignore[union-attr]
        self.assertEqual(H.shape, (n_vars, n_vars))
        self.assertEqual(g.shape, (n_vars,))

    def test_mpc_solve(self) -> None:
        """Test MPC optimization solve"""
        config = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=10,
            u_max=np.array([5.0]),
            u_min=np.array([-5.0]),
        )
        pattern = ModelPredictivePattern(config)
        pattern._initialize_solver()

        x0 = np.array([1.0, 0.0])
        x_ref = np.array([0.0, 0.0])

        u, feasible, t_solve = pattern._solve_mpc(x0, x_ref)

        self.assertEqual(u.shape, (1,))
        self.assertGreaterEqual(u[0], -5.0 - 1e-3)
        self.assertLessEqual(u[0], 5.0 + 1e-3)

    def test_full_simulation(self) -> None:
        """Test complete MPC simulation"""
        config = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=15,
            simulation_steps=200,
            u_max=np.array([2.0]),
            u_min=np.array([-2.0]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        self.assertEqual(result["system_type"], "double_integrator")
        self.assertIn("performance_metrics", result)
        self.assertGreater(result["performance_metrics"]["feasibility_rate"], 0.8)

    def test_constrained_control(self) -> None:
        """Test MPC with control constraints"""
        config = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=20,
            simulation_steps=300,
            u_max=np.array([1.0]),
            u_min=np.array([-1.0]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        # Check that constraints are respected
        controls = np.array(result["history"]["control"])
        self.assertLessEqual(np.max(controls), 1.0 + 1e-3)
        self.assertGreaterEqual(np.min(controls), -1.0 - 1e-3)

    def test_inverted_pendulum(self) -> None:
        """Test MPC on inverted pendulum"""
        config = MPCConfig(
            system_type=SystemType.INVERTED_PENDULUM,
            N=25,
            simulation_steps=300,
            Q=np.array([[10.0, 0.0], [0.0, 1.0]]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        # Should stabilize the pendulum
        final_state = result["performance_metrics"]["final_state"]
        self.assertLess(abs(final_state[0]), 1.0)  # Angle should be small

    def test_mimo_system(self) -> None:
        """Test MPC on MIMO system"""
        config = MPCConfig(
            system_type=SystemType.MIMO_SYSTEM, N=15, simulation_steps=200
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        self.assertEqual(result["system_type"], "mimo_system")
        self.assertEqual(len(result["history"]["state"][0]), 4)
        self.assertEqual(len(result["history"]["control"][0]), 2)

    def test_get_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = ModelPredictivePattern.get_metadata()

        self.assertEqual(metadata["id"], "model_predictive")
        self.assertEqual(metadata["category"], "EXTENDED")
        self.assertIn("parameters", metadata)

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    import logging

    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("Model Predictive Control Pattern[str] Demo")
    print("=" * 60)

    for system in [SystemType.DOUBLE_INTEGRATOR, SystemType.INVERTED_PENDULUM]:
        print(f"\n--- {system.value.upper()} ---")
        config = MPCConfig(
            system_type=system,
            N=20,
            simulation_steps=300,
            u_max=np.array([2.0]),
            u_min=np.array([-2.0]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        print(f"Prediction Horizon: {result['prediction_horizon']}")
        print(
            f"Mean Solve Time: {result['performance_metrics']['mean_solve_time'] * 1000:.2f} ms"
        )
        print(
            f"Feasibility Rate: {result['performance_metrics']['feasibility_rate'] * 100:.1f}%"
        )
        print(
            f"Mean State Error: {result['performance_metrics']['mean_state_error']:.4f}"
        )
        print(f"Final State: {result['performance_metrics']['final_state']}")
