"""
Tests for dft pattern module.
"""

import asyncio

import numpy as np
import pytest

from src.patterns.library.dft import BasisSet, DFTConfig, DFTFunctional, DFTPattern


class TestEnums:
    def test_functional_values(self):
        assert DFTFunctional.LDA.value == "lda"
        assert DFTFunctional.LSDA.value == "lsda"

    def test_basis_set_values(self):
        assert BasisSet.PLANE_WAVE.value == "plane_wave"
        assert BasisSet.GAUSSIAN.value == "gaussian"
        assert BasisSet.NUMERICAL.value == "numerical"


class TestConfig:
    def test_default_config(self):
        cfg = DFTConfig()
        assert cfg.n_electrons == 2
        assert cfg.n_grid == 100
        assert cfg.box_size == 10.0
        assert cfg.max_scf_iter == 100

    def test_post_init(self):
        cfg = DFTConfig(n_grid=100, box_size=10.0)
        assert cfg.dx == 0.1
        assert len(cfg.k_points) == 100


class TestInit:
    def test_pattern_init(self):
        pattern = DFTPattern()
        assert pattern.hbar == 1.0
        assert pattern.Ha == 27.2114


class TestCanSimulate:
    def test_can_simulate_dft(self):
        pattern = DFTPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="density functional theory", description="electronic structure")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self):
        pattern = DFTPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="weather forecast", description="")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_parse_config(self):
        pattern = DFTPattern()
        cfg = pattern._parse_config({"n_electrons": 4, "n_grid": 50})
        assert cfg.n_electrons == 4
        assert cfg.n_grid == 50


class TestKineticMatrix:
    def test_kinetic_matrix_shape(self):
        pattern = DFTPattern()
        T = pattern._kinetic_matrix(50, 0.1)
        assert T.shape == (50, 50)
        assert np.all(np.isfinite(T))

    def test_kinetic_matrix_symmetric(self):
        pattern = DFTPattern()
        T = pattern._kinetic_matrix(50, 0.1)
        assert np.allclose(T, T.T)


class TestPotential:
    def test_effective_potential(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_grid=50, box_size=10.0)
        x = np.linspace(-5, 5, 50)
        n_density = np.ones(50) * 2 / 10.0
        V_eff = pattern._effective_potential(n_density, x, cfg)
        assert len(V_eff) == 50
        assert np.all(np.isfinite(V_eff))

    def test_hartree_potential(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_grid=50, box_size=10.0)
        x = np.linspace(-5, 5, 50)
        n_density = np.ones(50) * 2 / 10.0
        V_h = pattern._hartree_potential(n_density, x, cfg)
        assert len(V_h) == 50
        assert np.all(np.isfinite(V_h))

    def test_xc_potential(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_grid=50, box_size=10.0)
        n_density = np.ones(50) * 2 / 10.0
        V_xc = pattern._xc_potential(n_density, cfg)
        assert len(V_xc) == 50
        assert np.all(np.isfinite(V_xc))


class TestEnergy:
    def test_hartree_energy(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_grid=50, box_size=10.0)
        x = np.linspace(-5, 5, 50)
        n_density = np.ones(50) * 2 / 10.0
        E_h = pattern._hartree_energy(n_density, x, cfg)
        assert isinstance(E_h, float)

    def test_xc_energy(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_grid=50, box_size=10.0)
        n_density = np.ones(50) * 2 / 10.0
        E_xc = pattern._exchange_correlation_energy(n_density, cfg)
        assert isinstance(E_xc, float)


class TestFermi:
    def test_fermi_occupations_zero_temp(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_electrons=4, temperature=0.0)
        eigenvalues = np.linspace(-1, 1, 20)
        occ = pattern._fermi_occupations(eigenvalues, cfg)
        assert np.sum(occ) == 4.0

    def test_calculate_fermi_energy(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_electrons=2, temperature=0.0)
        eigenvalues = np.linspace(-1, 1, 20)
        occ = pattern._fermi_occupations(eigenvalues, cfg)
        Ef = pattern._calculate_fermi_energy(eigenvalues, occ)
        assert isinstance(Ef, float)


class TestKohnSham:
    @pytest.mark.asyncio
    async def test_kohn_sham_solve(self):
        pattern = DFTPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="test", description="test")
        cfg = DFTConfig(n_electrons=2, n_grid=50, max_scf_iter=20)
        result = await pattern._kohn_sham_solve(h, cfg)
        assert "metrics" in result
        assert "density" in result
        assert result["metrics"]["n_electrons"] == 2

    @pytest.mark.asyncio
    async def test_kohn_sham_convergence(self):
        pattern = DFTPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="test", description="test")
        cfg = DFTConfig(n_electrons=2, n_grid=50, max_scf_iter=50, scf_tolerance=1e-4)
        result = await pattern._kohn_sham_solve(h, cfg)
        assert result["metrics"]["scf_converged"] in [0, 1]


class TestRun:
    @pytest.mark.asyncio
    async def test_run(self):
        pattern = DFTPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="test", description="test")
        result = await pattern.run(
            hypothesis=h,
            config={"n_electrons": 2, "n_grid": 50, "max_scf_iter": 20},
        )
        assert result.status.name == "COMPLETED"


class TestEdgeCases:
    def test_confidence(self):
        pattern = DFTPattern()
        results = {
            "metrics": {
                "scf_converged": 1,
                "final_density_residual": 1e-9,
                "total_energy": 10.0,
                "homo_lumo_gap": 0.5,
            }
        }
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.85

    def test_estimate_resources(self):
        pattern = DFTPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(
            title="test", description="test", parameters={"n_grid": 100, "max_scf_iter": 100}
        )
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    def test_small_grid(self):
        pattern = DFTPattern()
        cfg = DFTConfig(n_grid=20, box_size=5.0)
        assert cfg.dx == 0.25
