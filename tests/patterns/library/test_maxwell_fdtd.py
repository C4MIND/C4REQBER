"""
Tests for maxwell_fdtd pattern module.
"""
import numpy as np
import pytest
import asyncio

from src.patterns.library.maxwell_fdtd import (
    BoundaryCondition,
    SourceType,
    FDTDConfig,
    MaxwellFDTDPattern,
)


class TestEnums:
    def test_boundary_condition_values(self):
        assert BoundaryCondition.PEC.value == "pec"
        assert BoundaryCondition.PMC.value == "pmc"
        assert BoundaryCondition.PML.value == "pml"
        assert BoundaryCondition.PERIODIC.value == "periodic"

    def test_source_type_values(self):
        assert SourceType.GAUSSIAN_PULSE.value == "gaussian_pulse"
        assert SourceType.SINE_WAVE.value == "sine_wave"
        assert SourceType.RICKER_WAVELET.value == "ricker_wavelet"


class TestConfig:
    def test_default_config(self):
        cfg = FDTDConfig()
        assert cfg.nx == 100
        assert cfg.ny == 100
        assert cfg.nz == 1
        assert cfg.courant_factor == 0.5

    def test_post_init(self):
        cfg = FDTDConfig(dx=1e-3)
        assert cfg.dt > 0


class TestInit:
    def test_pattern_init(self):
        pattern = MaxwellFDTDPattern()
        assert pattern.c == 299792458.0
        assert pattern.eps0 > 0


class TestCanSimulate:
    def test_can_simulate_fdtd(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="fdtd simulation", description="electromagnetic wave")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="weather forecast", description="")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_parse_config_2d(self):
        pattern = MaxwellFDTDPattern()
        cfg = pattern._parse_config({"dimensions": "2d", "grid_size": 50})
        assert cfg.nz == 1

    def test_parse_config_3d(self):
        pattern = MaxwellFDTDPattern()
        cfg = pattern._parse_config({"dimensions": "3d", "grid_size": 30})
        assert cfg.nz == 30


class TestFDTD2D:
    @pytest.mark.asyncio
    async def test_fdtd_2d(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        cfg = FDTDConfig(nx=50, ny=50, nz=1, n_steps=100, source_position=(25, 25, 0))
        result = await pattern._fdtd_2d(h, cfg)
        assert "metrics" in result
        assert result["metrics"]["n_steps"] == 100

    @pytest.mark.asyncio
    async def test_fdtd_2d_fields(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        cfg = FDTDConfig(nx=50, ny=50, nz=1, n_steps=50, source_position=(25, 25, 0))
        result = await pattern._fdtd_2d(h, cfg)
        assert result["metrics"]["max_ez"] > 0


class TestFDTD3D:
    @pytest.mark.asyncio
    async def test_fdtd_3d(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        cfg = FDTDConfig(nx=20, ny=20, nz=20, n_steps=50, source_position=(10, 10, 10))
        result = await pattern._fdtd_3d(h, cfg)
        assert "metrics" in result
        assert result["metrics"]["grid_cells"] == 20 * 20 * 20


class TestBoundary:
    def test_apply_boundary_pec(self):
        pattern = MaxwellFDTDPattern()
        Ez = np.ones((10, 10))
        pattern._apply_boundary_2d(Ez, "pec")
        assert Ez[0, 0] == 0
        assert Ez[-1, -1] == 0

    def test_apply_boundary_pmc(self):
        pattern = MaxwellFDTDPattern()
        Ez = np.ones((10, 10))
        Ez[1, :] = 2.0
        Ez[-2, :] = 3.0
        pattern._apply_boundary_2d(Ez, "pmc")
        assert Ez[0, 0] == 2.0
        assert Ez[-1, -1] == 3.0

    def test_setup_pml(self):
        pattern = MaxwellFDTDPattern()
        cfg = FDTDConfig(nx=50, ny=50, pml_layers=10)
        sigma_ex = np.zeros((50, 50))
        sigma_ey = np.zeros((50, 50))
        pattern._setup_pml_2d(sigma_ex, sigma_ey, cfg)
        assert np.any(sigma_ex > 0)
        assert np.any(sigma_ey > 0)


class TestRun:
    @pytest.mark.asyncio
    async def test_run_2d(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        result = await pattern.run(
            hypothesis=h,
            config={"dimensions": "2d", "grid_size": 60, "n_steps": 100},
        )
        assert result.status.name == "COMPLETED"

    @pytest.mark.asyncio
    async def test_run_3d(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        result = await pattern.run(
            hypothesis=h,
            config={"dimensions": "3d", "grid_size": 60, "n_steps": 50},
        )
        assert result.status.name == "COMPLETED"


class TestEdgeCases:
    def test_confidence(self):
        pattern = MaxwellFDTDPattern()
        results = {"metrics": {"courant_number": 0.5, "max_ez": 1.0, "n_steps": 500, "wavelength": 0.3}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.85

    def test_estimate_resources(self):
        pattern = MaxwellFDTDPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="test", description="test", parameters={"dimensions": "2d", "grid_size": 100, "n_steps": 500})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    def test_small_grid(self):
        pattern = MaxwellFDTDPattern()
        cfg = FDTDConfig(nx=10, ny=10, nz=1, n_steps=10)
        assert cfg.dt > 0
