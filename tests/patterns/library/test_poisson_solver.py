"""Tests for poisson_solver pattern module."""

import numpy as np
import pytest
import asyncio

from src.patterns.library.poisson_solver import (
    PoissonConfig,
    PoissonSolverPattern,
    MultigridCycle,
    RelaxationMethod,
)
from src.patterns.core import Hypothesis



class TestPoissonConfig:
    def test_default_values(self):
        cfg = PoissonConfig()
        assert cfg.nx == 128
        assert cfg.ny == 128
        assert cfg.equation == "poisson"
        assert cfg.cycle_type == "v_cycle"
        assert cfg.relaxation_method == "gauss_seidel"

    def test_post_init(self):
        cfg = PoissonConfig(x_min=0.0, x_max=1.0, nx=5)
        assert cfg.dx == pytest.approx(0.25, abs=1e-10)


class TestPoissonSolverPattern:
    @pytest.fixture
    def pattern(self):
        return PoissonSolverPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Poisson equation solver",
            description="Multigrid solver for electrostatic potential",
        )

    def test_init(self, pattern):
        assert pattern.iteration_count == 0
        assert pattern.residual_history == []

    def test_can_simulate_matching(self, pattern, hypothesis):
        assert pattern.can_simulate(hypothesis) is True

    def test_can_simulate_non_matching(self, pattern):
        h = Hypothesis(title="Quantum mechanics", description="Particle physics")
        assert pattern.can_simulate(h) is False

    def test_parse_config(self, pattern):
        cfg = pattern._parse_config({"grid_size": 64, "equation": "laplace", "cycle_type": "w_cycle"})
        assert cfg.nx == 64
        assert cfg.equation == "laplace"
        assert cfg.cycle_type == "w_cycle"

    def test_initialize_rhs_poisson(self, pattern):
        cfg = PoissonConfig(nx=16, ny=16, equation="poisson")
        f = pattern._initialize_rhs(cfg)
        assert f.shape == (16, 16)
        assert f[8, 8] > 0

    def test_initialize_rhs_laplace(self, pattern):
        cfg = PoissonConfig(nx=16, ny=16, equation="laplace")
        f = pattern._initialize_rhs(cfg)
        assert np.allclose(f, 0)

    def test_apply_boundary_conditions_dirichlet(self, pattern):
        cfg = PoissonConfig(nx=8, ny=8, boundary_condition="dirichlet")
        phi = np.ones((8, 8))
        pattern._apply_boundary_conditions(phi, cfg)
        assert np.all(phi[0, :] == 0)
        assert np.all(phi[-1, :] == 0)
        assert np.all(phi[:, 0] == 0)
        assert np.all(phi[:, -1] == 0)

    def test_apply_boundary_conditions_neumann(self, pattern):
        cfg = PoissonConfig(nx=8, ny=8, boundary_condition="neumann")
        phi = np.arange(64).reshape(8, 8).astype(float)
        phi_orig = phi.copy()
        pattern._apply_boundary_conditions(phi, cfg)
        assert phi[0, 3] == pytest.approx(phi_orig[1, 3])

    def test_relax_jacobi(self, pattern):
        cfg = PoissonConfig(nx=8, ny=8, relaxation_method="jacobi", pre_smooth=2)
        phi = np.zeros((8, 8))
        f = np.ones((8, 8))
        phi_new = pattern._relax(phi, f, cfg, 2)
        assert phi_new.shape == (8, 8)
        assert not np.allclose(phi_new, 0)

    def test_relax_gauss_seidel(self, pattern):
        cfg = PoissonConfig(nx=8, ny=8, relaxation_method="gauss_seidel", pre_smooth=2)
        phi = np.zeros((8, 8))
        f = np.ones((8, 8))
        phi_new = pattern._relax(phi, f, cfg, 2)
        assert phi_new.shape == (8, 8)

    def test_relax_sor(self, pattern):
        cfg = PoissonConfig(nx=8, ny=8, relaxation_method="sor", pre_smooth=2, omega=1.5)
        phi = np.zeros((8, 8))
        f = np.ones((8, 8))
        phi_new = pattern._relax(phi, f, cfg, 2)
        assert phi_new.shape == (8, 8)

    def test_compute_residual(self, pattern):
        cfg = PoissonConfig(nx=8, ny=8)
        phi = np.zeros((8, 8))
        f = np.ones((8, 8))
        residual = pattern._compute_residual(phi, f, cfg)
        assert residual > 0

    def test_compute_laplacian(self, pattern):
        cfg = PoissonConfig(nx=8, ny=8)
        phi = np.ones((8, 8))
        lapl = pattern._compute_laplacian(phi, cfg)
        assert lapl.shape == (8, 8)
        assert np.allclose(lapl, 0, atol=1e-10)

    def test_restrict_prolong(self, pattern):
        phi_fine = np.random.randn(16, 16)
        phi_coarse = pattern._restrict(phi_fine)
        assert phi_coarse.shape == (8, 8)
        phi_fine2 = pattern._prolong(phi_coarse, 16, 16)
        assert phi_fine2.shape == (16, 16)

    def test_coarsen_config(self, pattern):
        cfg = PoissonConfig(nx=16, ny=16, max_levels=4)
        cfg_coarse = pattern._coarsen_config(cfg)
        assert cfg_coarse.nx == 8
        assert cfg_coarse.max_levels == 3

    def test_v_cycle(self, pattern):
        cfg = PoissonConfig(nx=16, ny=16, max_levels=3, pre_smooth=2, post_smooth=2)
        phi = np.zeros((16, 16))
        f = pattern._initialize_rhs(cfg)
        phi_new = pattern._v_cycle(phi, f, cfg, 3)
        assert phi_new.shape == (16, 16)

    def test_calculate_confidence(self, pattern):
        results = {"metrics": {"converged": 1.0, "residual_ratio": 1e-8, "iterations": 20}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.9

    def test_estimate_resources(self, pattern):
        h = Hypothesis(title="test", description="test")
        h.parameters = {"grid_size": 128, "max_iterations": 100}
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    @pytest.mark.asyncio
    async def test_run_multigrid(self, pattern, hypothesis):
        result = await pattern.run(hypothesis, {"grid_size": 16, "max_iterations": 10})
        assert result.status.value == "completed"
        assert hasattr(result, "metrics")

    @pytest.mark.asyncio
    async def test_run_direct(self, pattern, hypothesis):
        result = await pattern.run(
            hypothesis, {"grid_size": 16, "use_direct": True, "max_iterations": 10}
        )
        assert result.status.value == "completed"

    @pytest.mark.asyncio
    async def test_run_laplace(self, pattern, hypothesis):
        result = await pattern.run(
            hypothesis, {"grid_size": 16, "equation": "laplace", "max_iterations": 10}
        )
        assert result.status.value == "completed"

    @pytest.mark.asyncio
    async def test_run_w_cycle(self, pattern, hypothesis):
        result = await pattern.run(
            hypothesis, {"grid_size": 16, "cycle_type": "w_cycle", "max_iterations": 10}
        )
        assert result.status.value == "completed"
