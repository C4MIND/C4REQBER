"""
Tests for src/patterns/library/model_predictive.py

Covers: MPCConfig, ActiveSetSolver, ModelPredictivePattern
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.patterns.library.model_predictive import (

    ActiveSetSolver,
    MPCConfig,
    ModelPredictivePattern,
    QPSolver,
    SystemType,
)


# ═══════════════════════════════════════════════════════════════════
# MPCConfig
# ═══════════════════════════════════════════════════════════════════


class TestMPCConfig:
    def test_default_double_integrator(self):
        cfg = MPCConfig()
        assert cfg.system_type == SystemType.DOUBLE_INTEGRATOR
        assert cfg.A.shape == (2, 2)
        assert cfg.B.shape == (2, 1)
        assert cfg.N == 20

    def test_inverted_pendulum(self):
        cfg = MPCConfig(system_type=SystemType.INVERTED_PENDULUM)
        assert cfg.A.shape == (2, 2)
        assert cfg.B.shape == (2, 1)

    def test_mimo_system(self):
        cfg = MPCConfig(system_type=SystemType.MIMO_SYSTEM)
        assert cfg.A.shape == (4, 4)
        assert cfg.B.shape == (4, 2)
        assert cfg.Q.shape == (4, 4)
        assert cfg.R.shape == (2, 2)

    def test_quadrotor(self):
        cfg = MPCConfig(system_type=SystemType.QUADROTOR)
        assert cfg.A.shape == (2, 2)
        assert cfg.B.shape == (2, 1)

    def test_custom_system(self):
        A = np.array([[1.0, 0.1], [0.0, 1.0]])
        B = np.array([[0.0], [1.0]])
        cfg = MPCConfig(system_type=SystemType.CUSTOM, A=A, B=B)
        np.testing.assert_array_equal(cfg.A, A)
        np.testing.assert_array_equal(cfg.B, B)

    def test_default_cost_matrices(self):
        cfg = MPCConfig()
        assert cfg.Q is not None
        assert cfg.R is not None
        assert cfg.Qf is not None

    def test_default_constraints(self):
        cfg = MPCConfig()
        assert cfg.u_min is not None
        assert cfg.u_max is not None
        assert cfg.x_min is not None
        assert cfg.x_max is not None

    def test_default_initial_state(self):
        cfg = MPCConfig()
        np.testing.assert_array_equal(cfg.initial_state, np.zeros(2))

    def test_default_reference(self):
        cfg = MPCConfig()
        np.testing.assert_array_equal(cfg.reference_value, np.ones(2))

    def test_solve_dare(self):
        cfg = MPCConfig(system_type=SystemType.DOUBLE_INTEGRATOR)
        assert cfg.Qf.shape == (2, 2)

    def test_solve_dare_fallback(self):
        # Use an invalid system that will cause solve_discrete_are to fail
        A = np.array([[0.0, 0.0], [0.0, 0.0]])
        B = np.array([[0.0], [0.0]])
        cfg = MPCConfig(system_type=SystemType.CUSTOM, A=A, B=B)
        # Should fallback to Q.copy()
        np.testing.assert_array_equal(cfg.Qf, cfg.Q)


# ═══════════════════════════════════════════════════════════════════
# ActiveSetSolver
# ═══════════════════════════════════════════════════════════════════


class TestActiveSetSolver:
    def test_unconstrained_qp(self):
        solver = ActiveSetSolver()
        H = np.array([[1.0]])
        g = np.array([2.0])
        lb = np.array([-np.inf])
        ub = np.array([np.inf])
        x, feasible = solver.solve(
            H, g,
            np.zeros((0, 1)), np.zeros(0),
            np.zeros((0, 1)), np.zeros(0),
            lb, ub
        )
        assert bool(feasible) is True
        assert x[0] == pytest.approx(-2.0, abs=1e-2)

    def test_box_constrained_qp(self):
        solver = ActiveSetSolver()
        H = np.array([[1.0]])
        g = np.array([0.0])
        lb = np.array([1.0])
        ub = np.array([np.inf])
        x, feasible = solver.solve(
            H, g,
            np.zeros((0, 1)), np.zeros(0),
            np.zeros((0, 1)), np.zeros(0),
            lb, ub
        )
        assert bool(feasible) is True
        assert x[0] >= 1.0 - 1e-4

    def test_2d_qp(self):
        solver = ActiveSetSolver()
        H = np.eye(2)
        g = np.array([1.0, 2.0])
        lb = np.array([-10.0, -10.0])
        ub = np.array([10.0, 10.0])
        x, feasible = solver.solve(
            H, g,
            np.zeros((0, 2)), np.zeros(0),
            np.zeros((0, 2)), np.zeros(0),
            lb, ub
        )
        assert bool(feasible) is True
        assert x[0] == pytest.approx(-1.0, abs=1e-2)
        assert x[1] == pytest.approx(-2.0, abs=1e-2)

    def test_with_inequality_constraints(self):
        solver = ActiveSetSolver()
        H = np.eye(2)
        g = np.array([0.0, 0.0])
        A_ineq = np.array([[1.0, 1.0]])
        b_ineq = np.array([1.0])
        lb = np.array([-10.0, -10.0])
        ub = np.array([10.0, 10.0])
        x, feasible = solver.solve(
            H, g,
            np.zeros((0, 2)), np.zeros(0),
            A_ineq, b_ineq,
            lb, ub
        )
        assert bool(feasible) is True
        assert x[0] + x[1] <= 1.0 + 1e-4

    def test_solver_params(self):
        solver = ActiveSetSolver(max_iters=50, tol=1e-4)
        assert solver.max_iters == 50
        assert solver.tol == 1e-4


# ═══════════════════════════════════════════════════════════════════
# ModelPredictivePattern
# ═══════════════════════════════════════════════════════════════════


class TestModelPredictivePattern:
    def test_init(self):
        pattern = ModelPredictivePattern()
        assert pattern.config.N == 20
        assert pattern.solver is None

    def test_initialize_solver(self):
        pattern = ModelPredictivePattern()
        pattern._initialize_solver()
        assert pattern.solver is not None

    def test_build_qp_dimensions(self):
        cfg = MPCConfig(system_type=SystemType.DOUBLE_INTEGRATOR, N=10)
        pattern = ModelPredictivePattern(cfg)
        pattern._initialize_solver()
        x0 = np.array([1.0, 0.0])
        x_ref = np.array([0.0, 0.0])
        H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub = pattern._build_qp(x0, x_ref)
        n_vars = cfg.N * cfg.B.shape[1]
        assert H.shape == (n_vars, n_vars)
        assert g.shape == (n_vars,)
        assert lb.shape == (n_vars,)
        assert ub.shape == (n_vars,)

    def test_solve_mpc(self):
        cfg = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=10,
            u_max=np.array([5.0]),
            u_min=np.array([-5.0]),
        )
        pattern = ModelPredictivePattern(cfg)
        pattern._initialize_solver()
        x0 = np.array([1.0, 0.0])
        x_ref = np.array([0.0, 0.0])
        u, feasible, t_solve = pattern._solve_mpc(x0, x_ref)
        assert u.shape == (1,)
        assert u[0] >= -5.0 - 1e-3
        assert u[0] <= 5.0 + 1e-3
        assert t_solve >= 0.0

    def test_get_reference_constant(self):
        cfg = MPCConfig(reference_type="constant", reference_value=np.array([1.0, 0.0]))
        pattern = ModelPredictivePattern(cfg)
        ref = pattern._get_reference(0.0)
        np.testing.assert_array_equal(ref, np.array([1.0, 0.0]))

    def test_get_reference_sinusoid(self):
        cfg = MPCConfig(reference_type="sinusoid", reference_value=np.array([1.0, 0.0]))
        pattern = ModelPredictivePattern(cfg)
        ref = pattern._get_reference(0.0)
        assert ref[0] == pytest.approx(0.0, abs=1e-5)

    def test_get_reference_ramp(self):
        cfg = MPCConfig(
            reference_type="ramp",
            reference_value=np.array([1.0, 0.0]),
            simulation_steps=100,
            dt=0.05,
        )
        pattern = ModelPredictivePattern(cfg)
        ref = pattern._get_reference(0.0)
        assert ref[0] == pytest.approx(0.0, abs=1e-5)
        ref2 = pattern._get_reference(100 * 0.05)
        assert ref2[0] == pytest.approx(1.0, abs=1e-5)

    def test_run_double_integrator(self):
        cfg = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=15,
            simulation_steps=50,
            u_max=np.array([2.0]),
            u_min=np.array([-2.0]),
        )
        pattern = ModelPredictivePattern(cfg)
        result = pattern.run()
        assert result["system_type"] == "double_integrator"
        assert "performance_metrics" in result
        assert "history" in result
        assert "system_matrices" in result
        assert "cost_matrices" in result
        assert "constraints" in result

    def test_run_inverted_pendulum(self):
        cfg = MPCConfig(
            system_type=SystemType.INVERTED_PENDULUM,
            N=15,
            simulation_steps=50,
            Q=np.array([[10.0, 0.0], [0.0, 1.0]]),
        )
        pattern = ModelPredictivePattern(cfg)
        result = pattern.run()
        assert result["system_type"] == "inverted_pendulum"
        # Inverted pendulum is unstable; just verify it runs and returns metrics
        assert "performance_metrics" in result
        assert "final_state" in result["performance_metrics"]

    def test_run_mimo(self):
        cfg = MPCConfig(
            system_type=SystemType.MIMO_SYSTEM,
            N=10,
            simulation_steps=30,
        )
        pattern = ModelPredictivePattern(cfg)
        result = pattern.run()
        assert result["system_type"] == "mimo_system"
        assert len(result["history"]["state"][0]) == 4
        assert len(result["history"]["control"][0]) == 2

    def test_run_constrained_control(self):
        cfg = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=10,
            simulation_steps=50,
            u_max=np.array([1.0]),
            u_min=np.array([-1.0]),
        )
        pattern = ModelPredictivePattern(cfg)
        result = pattern.run()
        controls = np.array(result["history"]["control"])
        assert np.max(controls) <= 1.0 + 1e-3
        assert np.min(controls) >= -1.0 - 1e-3

    def test_run_feasibility_rate(self):
        cfg = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=10,
            simulation_steps=50,
        )
        pattern = ModelPredictivePattern(cfg)
        result = pattern.run()
        assert result["performance_metrics"]["feasibility_rate"] > 0.5

    def test_performance_metrics(self):
        cfg = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=10,
            simulation_steps=30,
        )
        pattern = ModelPredictivePattern(cfg)
        result = pattern.run()
        metrics = result["performance_metrics"]
        assert "mean_state_error" in metrics
        assert "max_state_error" in metrics
        assert "control_effort" in metrics
        assert "mean_solve_time" in metrics
        assert "feasibility_rate" in metrics
        assert "final_state" in metrics
        assert "constraint_violations" in metrics

    def test_metadata(self):
        meta = ModelPredictivePattern.get_metadata()
        assert meta["id"] == "model_predictive"
        assert meta["category"] == "EXTENDED"
        assert "parameters" in meta

    def test_history_structure(self):
        cfg = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=10,
            simulation_steps=20,
            output_interval=1,
        )
        pattern = ModelPredictivePattern(cfg)
        result = pattern.run()
        hist = result["history"]
        assert "time" in hist
        assert "state" in hist
        assert "control" in hist
        assert "reference" in hist
        assert "solve_time" in hist
        assert "feasible" in hist
        assert len(hist["time"]) > 0
