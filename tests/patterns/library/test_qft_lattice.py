"""
Tests for qft_lattice pattern module.
"""
import numpy as np
import pytest
import asyncio

from src.patterns.library.qft_lattice import (
    GaugeGroup,
    FermionType,
    LatticeQFTConfig,
    LatticeQFTPattern,
)


class TestEnums:
    def test_gauge_group_values(self):
        assert GaugeGroup.U1.value == "u1"
        assert GaugeGroup.SU2.value == "su2"
        assert GaugeGroup.SU3.value == "su3"

    def test_fermion_type_values(self):
        assert FermionType.NONE.value == "none"
        assert FermionType.STAGGERED.value == "staggered"
        assert FermionType.WILSON.value == "wilson"


class TestConfig:
    def test_default_config(self):
        cfg = LatticeQFTConfig()
        assert cfg.nx == 16
        assert cfg.beta == 1.0
        assert cfg.gauge_group == "u1"

    def test_post_init(self):
        cfg = LatticeQFTConfig(nt=1)
        assert cfg.ndim == 3


class TestInit:
    def test_pattern_init(self):
        pattern = LatticeQFTPattern()
        assert pattern.rng is not None


class TestCanSimulate:
    def test_can_simulate_lattice(self):
        pattern = LatticeQFTPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="lattice gauge theory", description="wilson loop")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self):
        pattern = LatticeQFTPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="weather forecast", description="")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_parse_config(self):
        pattern = LatticeQFTPattern()
        cfg = pattern._parse_config({"lattice_size": 8, "beta": 2.0})
        assert cfg.nx == 8
        assert cfg.beta == 2.0


class TestU1Simulation:
    @pytest.mark.asyncio
    async def test_u1_simulation(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(
            nx=8, ny=8, nz=8, nt=8,
            n_thermalization=10,
            n_measurements=20,
            n_sweeps_between=5,
        )
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        result = await pattern._u1_simulation(h, cfg)
        assert "metrics" in result
        assert "logs" in result
        assert result["metrics"]["beta"] == 1.0

    @pytest.mark.asyncio
    async def test_u1_plaquette(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(
            nx=8, ny=8, nz=8, nt=8,
            n_thermalization=5,
            n_measurements=10,
        )
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        result = await pattern._u1_simulation(h, cfg)
        assert 0 < result["metrics"]["avg_plaquette"] < 1


class TestSU2Simulation:
    @pytest.mark.asyncio
    async def test_su2_simulation(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(
            nx=8, ny=8, nz=8, nt=8,
            gauge_group="su2",
            n_thermalization=5,
            n_measurements=10,
        )
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        result = await pattern._su2_simulation(h, cfg)
        assert result["metrics"]["gauge_group"] == "SU(2)"


class TestMeasurements:
    def test_measure_plaquette(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(nx=8, ny=8, nz=8, nt=8)
        theta = 2 * np.pi * (pattern.rng.random((8, 8, 8, 8, 4)) - 0.5)
        plaq = pattern._measure_plaquette(theta, cfg)
        assert -1 <= plaq <= 1

    def test_measure_wilson_loop(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(nx=8, ny=8, nz=8, nt=8)
        theta = 2 * np.pi * (pattern.rng.random((8, 8, 8, 8, 4)) - 0.5)
        w = pattern._measure_wilson_loop(theta, 1, 1, cfg)
        assert -1 <= w <= 1

    def test_measure_polyakov(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(nx=8, ny=8, nz=8, nt=8)
        theta = 2 * np.pi * (pattern.rng.random((8, 8, 8, 8, 4)) - 0.5)
        poly = pattern._measure_polyakov_loop(theta, cfg)
        assert isinstance(poly, complex)


class TestSweep:
    def test_sweep_u1(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(nx=4, ny=4, nz=4, nt=4)
        theta = 2 * np.pi * (pattern.rng.random((4, 4, 4, 4, 4)) - 0.5)
        pattern._sweep_u1(theta, cfg)
        assert np.all(np.isfinite(theta))


class TestStaple:
    def test_calculate_staple(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(nx=4, ny=4, nz=4, nt=4)
        theta = 2 * np.pi * (pattern.rng.random((4, 4, 4, 4, 4)) - 0.5)
        staple = pattern._calculate_staple(theta, 0, 0, 0, 0, 0, cfg)
        assert np.isfinite(staple)


class TestRun:
    @pytest.mark.asyncio
    async def test_run_u1(self):
        pattern = LatticeQFTPattern()
        from src.patterns.core import Hypothesis
        h = Hypothesis(title="test", description="test")
        result = await pattern.run(
            hypothesis=h,
            config={"lattice_size": 8, "beta": 1.0, "gauge_group": "u1", "n_measurements": 10},
        )
        assert result.status.name == "COMPLETED"


class TestEdgeCases:
    def test_confidence(self):
        pattern = LatticeQFTPattern()
        results = {"metrics": {"n_measurements": 1000, "avg_plaquette": 0.5, "wilson_loop_1x1": 0.3, "std_plaquette": 0.05}}
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.85

    def test_estimate_resources(self):
        pattern = LatticeQFTPattern()
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="test", description="test", parameters={"lattice_size": 16, "n_measurements": 1000})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    def test_small_lattice(self):
        pattern = LatticeQFTPattern()
        cfg = LatticeQFTConfig(nx=4, ny=4, nz=4, nt=4)
        assert cfg.ndim == 4
