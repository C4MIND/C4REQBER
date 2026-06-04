"""Tests for crystal_growth pattern module."""

import numpy as np
import pytest

from src.patterns.library.crystal_growth import (

    CrystalGrowthConfig,
    CrystalGrowthPattern,
    CrystalSymmetry,
    NucleationModel,
)


class TestCrystalSymmetry:
    def test_values(self):
        assert CrystalSymmetry.ISOTROPIC.value == "isotropic"
        assert CrystalSymmetry.CUBIC.value == "cubic"
        assert CrystalSymmetry.HEXAGONAL.value == "hexagonal"
        assert CrystalSymmetry.TETRAGONAL.value == "tetragonal"


class TestNucleationModel:
    def test_values(self):
        assert NucleationModel.HOMOGENEOUS.value == "homogeneous"
        assert NucleationModel.HETEROGENEOUS.value == "heterogeneous"
        assert NucleationModel.PREDEFINED.value == "predefined"


class TestCrystalGrowthConfig:
    def test_default_values(self):
        cfg = CrystalGrowthConfig()
        assert cfg.nx == 128
        assert cfg.ny == 128
        assert cfg.dx == 0.5
        assert cfg.T_melt == 1000.0
        assert cfg.symmetry == CrystalSymmetry.CUBIC
        assert cfg.nucleation_model == NucleationModel.HETEROGENEOUS

    def test_custom_values(self):
        cfg = CrystalGrowthConfig(nx=64, ny=64, symmetry=CrystalSymmetry.HEXAGONAL)
        assert cfg.nx == 64
        assert cfg.symmetry == CrystalSymmetry.HEXAGONAL


class TestCrystalGrowthPattern:
    @pytest.fixture
    def small_config(self):
        return CrystalGrowthConfig(nx=32, ny=32, n_steps=100, output_interval=50)

    @pytest.fixture
    def pattern(self, small_config):
        return CrystalGrowthPattern(small_config)

    def test_init(self, pattern, small_config):
        assert pattern.config == small_config
        assert pattern.phi is not None
        assert pattern.T is not None
        assert pattern.phi.shape == (32, 32)

    def test_pattern_id(self):
        assert CrystalGrowthPattern.PATTERN_ID == "crystal_growth"
        assert CrystalGrowthPattern.PATTERN_VERSION == "6.0.0"

    def test_initial_nuclei(self, pattern):
        assert np.sum(pattern.phi > -0.9) > 0  # Some solid regions

    def test_anisotropy_isotropic(self):
        config = CrystalGrowthConfig(nx=32, ny=32, symmetry=CrystalSymmetry.ISOTROPIC)
        pattern = CrystalGrowthPattern(config)
        theta = np.linspace(0, 2 * np.pi, 100)
        a = pattern._anisotropy_function(theta)
        assert np.allclose(a, 1.0)

    def test_anisotropy_cubic(self):
        config = CrystalGrowthConfig(symmetry=CrystalSymmetry.CUBIC, anisotropy_strength=0.05)
        pattern = CrystalGrowthPattern(config)
        theta = np.linspace(0, 2 * np.pi, 100)
        a = pattern._anisotropy_function(theta)
        assert np.all(a > 0)
        assert not np.allclose(a, 1.0)

    def test_anisotropy_hexagonal(self):
        config = CrystalGrowthConfig(symmetry=CrystalSymmetry.HEXAGONAL, anisotropy_strength=0.05)
        pattern = CrystalGrowthPattern(config)
        theta = np.linspace(0, 2 * np.pi, 100)
        a = pattern._anisotropy_function(theta)
        assert np.all(a > 0)

    def test_gradient(self, pattern):
        field = np.random.randn(32, 32)
        dfdx, dfdy = pattern._gradient(field)
        assert dfdx.shape == field.shape
        assert dfdy.shape == field.shape
        assert np.all(np.isfinite(dfdx))

    def test_laplacian(self, pattern):
        field = np.ones((32, 32))
        lapl = pattern._laplacian(field)
        assert lapl.shape == field.shape
        assert np.allclose(lapl, 0, atol=1e-10)

    def test_anisotropic_laplacian(self, pattern):
        phi = np.random.randn(32, 32)
        lapl = pattern._anisotropic_laplacian(phi)
        assert lapl.shape == phi.shape
        assert np.all(np.isfinite(lapl))

    def test_phase_field_rhs(self, pattern):
        rhs = pattern._phase_field_rhs()
        assert rhs.shape == pattern.phi.shape
        assert np.all(np.isfinite(rhs))

    def test_thermal_rhs(self, pattern):
        rhs = pattern._thermal_rhs()
        assert rhs.shape == pattern.T.shape
        assert np.all(np.isfinite(rhs))

    def test_step(self, pattern):
        phi_before = pattern.phi.copy()
        pattern._step()
        assert np.all(pattern.phi >= -1)
        assert np.all(pattern.phi <= 1)
        assert not np.allclose(pattern.phi, phi_before)

    def test_solid_fraction(self, pattern):
        frac = pattern._compute_solid_fraction()
        assert 0 <= frac <= 1

    def test_interface_length(self, pattern):
        length = pattern._compute_interface_length()
        assert length >= 0

    def test_tip_velocity(self, pattern):
        vel = pattern._compute_tip_velocity()
        assert vel >= 0

    def test_run(self):
        config = CrystalGrowthConfig(nx=32, ny=32, n_steps=100, output_interval=50)
        pattern = CrystalGrowthPattern(config)
        result = pattern.run()
        assert "symmetry" in result
        assert "final_solid_fraction" in result
        assert "final_interface_length" in result
        assert "phi_history" in result
        assert "T_history" in result
        assert "mean_temperature" in result
        assert result["final_solid_fraction"] > 0

    def test_run_isotropic(self):
        config = CrystalGrowthConfig(
            nx=32, ny=32, n_steps=100, symmetry=CrystalSymmetry.ISOTROPIC, anisotropy_strength=0.0
        )
        pattern = CrystalGrowthPattern(config)
        result = pattern.run()
        assert result["symmetry"] == "isotropic"

    def test_run_no_noise(self):
        config = CrystalGrowthConfig(
            nx=32, ny=32, n_steps=100, thermal_noise=False
        )
        pattern = CrystalGrowthPattern(config)
        result = pattern.run()
        assert result["final_solid_fraction"] >= 0

    def test_metadata(self):
        metadata = CrystalGrowthPattern.get_metadata()
        assert metadata["id"] == "crystal_growth"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0
