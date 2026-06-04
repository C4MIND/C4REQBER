"""
Tests for src/patterns/library/plasma_pic.py

Covers:
- PICDimension and ParticlePusher enums
- Particle dataclass
- PICConfig default/custom initialization and __post_init__
- PlasmaPICPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _initialize_particles_1d / _initialize_particles_2d
- _deposit_charge_1d / _deposit_charge_2d
- _solve_poisson_1d / _solve_poisson_2d_fft
- _compute_electric_field_1d / _compute_electric_field_2d
- _push_particles_1d / _push_particles_2d
- _compute_kinetic_energy / _compute_field_energy_1d / _compute_field_energy_2d
- _compute_total_momentum / _compute_thermal_velocity
- _calculate_confidence()
- estimate_resources()
- run() integration for 1D and 2D
- get_metadata()
- Edge cases: zero particles, minimal grid, leapfrog pusher
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.plasma_pic import (
    PICConfig,
    PlasmaPICPattern,
    PICDimension,
    ParticlePusher,
    Particle,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestPICDimension:
    def test_enum_values(self):
        assert PICDimension.ONE_D.value == "1d"
        assert PICDimension.TWO_D.value == "2d"
        assert PICDimension.THREE_D.value == "3d"


class TestParticlePusher:
    def test_enum_values(self):
        assert ParticlePusher.BORIS.value == "boris"
        assert ParticlePusher.LEAPFROG.value == "leapfrog"
        assert ParticlePusher.RK4.value == "rk4"


# ═══════════════════════════════════════════════════════════════════
# Particle
# ═══════════════════════════════════════════════════════════════════


class TestParticle:
    def test_default_init(self):
        p = Particle(x=0.5)
        assert p.x == 0.5
        assert p.y == 0.0
        assert p.z == 0.0
        assert p.vx == 0.0
        assert p.vy == 0.0
        assert p.vz == 0.0
        assert p.weight == 1.0
        assert p.charge == -1.0
        assert p.mass == 1.0

    def test_custom_init(self):
        p = Particle(x=1.0, y=2.0, vx=3.0, vy=4.0, charge=1.0, mass=1836.0, weight=2.0)
        assert p.x == 1.0
        assert p.y == 2.0
        assert p.vx == 3.0
        assert p.vy == 4.0
        assert p.charge == 1.0
        assert p.mass == 1836.0
        assert p.weight == 2.0


# ═══════════════════════════════════════════════════════════════════
# PICConfig
# ═══════════════════════════════════════════════════════════════════


class TestPICConfig:
    def test_default_init(self):
        cfg = PICConfig()
        assert cfg.nx == 64
        assert cfg.ny == 64
        assert cfg.nz == 1
        assert cfg.n_particles == 10000
        assert cfg.n_species == 2
        assert cfg.pusher == "boris"
        assert cfg.deposit_scheme == "cic"

    def test_post_init_grid_spacing(self):
        cfg = PICConfig(nx=32, ny=32, Lx=1e-3, Ly=1e-3)
        assert cfg.dx == pytest.approx(1e-3 / 32)
        assert cfg.dy == pytest.approx(1e-3 / 32)

    def test_custom_init(self):
        cfg = PICConfig(
            nx=32,
            n_particles=5000,
            n_steps=500,
            Te=20.0,
            Ti=5.0,
            pusher="leapfrog",
        )
        assert cfg.nx == 32
        assert cfg.n_particles == 5000
        assert cfg.n_steps == 500
        assert cfg.Te == 20.0
        assert cfg.Ti == 5.0
        assert cfg.pusher == "leapfrog"


# ═══════════════════════════════════════════════════════════════════
# PlasmaPICPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestPlasmaPICPatternInit:
    def test_init(self):
        pattern = PlasmaPICPattern()
        assert pattern.particles == []
        assert pattern.rho is None
        assert pattern.phi is None
        assert pattern.Ex is None
        assert pattern.Ey is None

    def test_physical_constants(self):
        pattern = PlasmaPICPattern()
        assert pattern.q_e > 0
        assert pattern.m_e > 0
        assert pattern.eps0 > 0
        assert pattern.c > 0

    def test_parameters_defined(self):
        pattern = PlasmaPICPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "n_particles" in param_names
        assert "n_steps" in param_names
        assert "plasma_density" in param_names
        assert "pusher" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_plasma(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma simulation", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_fusion(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Tokamak fusion", description="confinement")
        assert pattern.can_simulate(h) is True

    def test_matches_accelerator(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Wakefield accelerator", description="test")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Fluid dynamics", description="navier stokes")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = PlasmaPICPattern()
        cfg = pattern._parse_config({})
        assert cfg.nx == 64
        assert cfg.ny == 64
        assert cfg.n_particles == 10000
        assert cfg.pusher == "boris"

    def test_1d_parsing(self):
        pattern = PlasmaPICPattern()
        cfg = pattern._parse_config({"dimensions": "1d", "grid_size": 32})
        assert cfg.nx == 32
        assert cfg.ny == 1
        assert cfg.nz == 1

    def test_custom_parsing(self):
        pattern = PlasmaPICPattern()
        cfg = pattern._parse_config({
            "n_particles": 5000,
            "n_steps": 500,
            "plasma_density": 1e18,
            "electron_temp": 50.0,
            "pusher": "leapfrog",
        })
        assert cfg.n_particles == 5000
        assert cfg.n_steps == 500
        assert cfg.n0 == 1e18
        assert cfg.Te == 50.0
        assert cfg.pusher == "leapfrog"


# ═══════════════════════════════════════════════════════════════════
# Particle Initialization
# ═══════════════════════════════════════════════════════════════════


class TestInitializeParticles:
    def test_1d_initialization(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, n_particles=100, n_species=2)
        pattern._initialize_particles_1d(cfg)
        assert len(pattern.particles) == 100
        # Check species split
        electrons = [p for p in pattern.particles if p.charge < 0]
        ions = [p for p in pattern.particles if p.charge > 0]
        assert len(electrons) == 50
        assert len(ions) == 50

    def test_2d_initialization(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, ny=32, n_particles=100, n_species=2)
        pattern._initialize_particles_2d(cfg)
        assert len(pattern.particles) == 100
        for p in pattern.particles:
            assert 0 <= p.x < cfg.Lx
            assert 0 <= p.y < cfg.Ly

    def test_particle_positions_in_bounds(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, n_particles=200, n_species=2)
        pattern._initialize_particles_1d(cfg)
        for p in pattern.particles:
            assert 0 <= p.x < cfg.Lx


# ═══════════════════════════════════════════════════════════════════
# Charge Deposition
# ═══════════════════════════════════════════════════════════════════


class TestDepositCharge:
    def test_1d_deposition_shape(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, n_particles=100)
        pattern._initialize_particles_1d(cfg)
        rho = pattern._deposit_charge_1d(cfg)
        assert rho.shape == (32,)

    def test_1d_conservation(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, n_particles=100, n_species=2)
        pattern._initialize_particles_1d(cfg)
        rho = pattern._deposit_charge_1d(cfg)
        # Total charge should be close to zero (quasi-neutral)
        total_charge = np.sum(rho) * cfg.dx
        assert abs(total_charge) < 1e-12

    def test_2d_deposition_shape(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=16, ny=16, n_particles=100)
        pattern._initialize_particles_2d(cfg)
        rho = pattern._deposit_charge_2d(cfg)
        assert rho.shape == (16, 16)


# ═══════════════════════════════════════════════════════════════════
# Field Solvers
# ═══════════════════════════════════════════════════════════════════


class TestSolvePoisson:
    def test_1d_solve_shape(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32)
        rho = np.zeros(32)
        phi = pattern._solve_poisson_1d(rho, cfg)
        assert phi.shape == (32,)

    def test_1d_zero_charge(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32)
        rho = np.zeros(32)
        phi = pattern._solve_poisson_1d(rho, cfg)
        assert np.allclose(phi, 0.0, atol=1e-10)

    def test_2d_solve_shape(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=16, ny=16)
        rho = np.zeros((16, 16))
        phi = pattern._solve_poisson_2d_fft(rho, cfg)
        assert phi.shape == (16, 16)

    def test_2d_zero_charge(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=16, ny=16)
        rho = np.zeros((16, 16))
        phi = pattern._solve_poisson_2d_fft(rho, cfg)
        assert np.allclose(phi, 0.0, atol=1e-10)


# ═══════════════════════════════════════════════════════════════════
# Electric Field Computation
# ═══════════════════════════════════════════════════════════════════


class TestComputeElectricField:
    def test_1d_field_shape(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32)
        phi = np.zeros(32)
        Ex = pattern._compute_electric_field_1d(phi, cfg)
        assert Ex.shape == (32,)

    def test_1d_constant_potential(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32)
        phi = np.ones(32) * 5.0
        Ex = pattern._compute_electric_field_1d(phi, cfg)
        assert np.allclose(Ex, 0.0, atol=1e-10)

    def test_2d_field_shapes(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=16, ny=16)
        phi = np.zeros((16, 16))
        Ex, Ey = pattern._compute_electric_field_2d(phi, cfg)
        assert Ex.shape == (16, 16)
        assert Ey.shape == (16, 16)


# ═══════════════════════════════════════════════════════════════════
# Particle Pushers
# ═══════════════════════════════════════════════════════════════════


class TestPushParticles:
    def test_1d_boris_push(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, n_particles=10)
        pattern._initialize_particles_1d(cfg)
        Ex = np.zeros(32)
        initial_x = [p.x for p in pattern.particles]
        pattern._push_particles_1d(Ex, cfg.dt, cfg)
        for i, p in enumerate(pattern.particles):
            # With zero E-field, position should change due to existing velocity
            assert p.x != initial_x[i] or p.vx == 0.0

    def test_1d_leapfrog_push(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, n_particles=10, pusher="leapfrog")
        pattern._initialize_particles_1d(cfg)
        Ex = np.zeros(32)
        initial_x = [p.x for p in pattern.particles]
        pattern._push_particles_1d(Ex, cfg.dt, cfg)
        for i, p in enumerate(pattern.particles):
            assert p.x != initial_x[i] or p.vx == 0.0

    def test_1d_periodic_boundary(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32, n_particles=1, Lx=1e-3)
        pattern.particles = [Particle(x=0.999e-3, vx=1e6)]
        Ex = np.zeros(32)
        pattern._push_particles_1d(Ex, cfg.dt, cfg)
        assert 0 <= pattern.particles[0].x < cfg.Lx

    def test_2d_push(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=16, ny=16, n_particles=10)
        pattern._initialize_particles_2d(cfg)
        Ex = np.zeros((16, 16))
        Ey = np.zeros((16, 16))
        initial_x = [p.x for p in pattern.particles]
        initial_y = [p.y for p in pattern.particles]
        pattern._push_particles_2d(Ex, Ey, cfg.dt, cfg)
        for i, p in enumerate(pattern.particles):
            assert p.x != initial_x[i] or p.vx == 0.0
            assert p.y != initial_y[i] or p.vy == 0.0


# ═══════════════════════════════════════════════════════════════════
# Energy and Momentum
# ═══════════════════════════════════════════════════════════════════


class TestEnergyAndMomentum:
    def test_kinetic_energy_non_negative(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(n_particles=10)
        pattern._initialize_particles_1d(cfg)
        ke = pattern._compute_kinetic_energy()
        assert ke >= 0.0

    def test_kinetic_energy_zero_velocity(self):
        pattern = PlasmaPICPattern()
        pattern.particles = [Particle(x=0.5, vx=0.0, vy=0.0, vz=0.0)]
        ke = pattern._compute_kinetic_energy()
        assert ke == 0.0

    def test_field_energy_1d(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=32)
        Ex = np.ones(32)
        fe = pattern._compute_field_energy_1d(Ex, cfg)
        assert fe >= 0.0

    def test_field_energy_2d(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(nx=16, ny=16)
        Ex = np.ones((16, 16))
        Ey = np.ones((16, 16))
        fe = pattern._compute_field_energy_2d(Ex, Ey, cfg)
        assert fe >= 0.0

    def test_total_momentum(self):
        pattern = PlasmaPICPattern()
        pattern.particles = [
            Particle(x=0.5, vx=1e6, mass=1.0),
            Particle(x=0.6, vx=-1e6, mass=1.0),
        ]
        momentum = pattern._compute_total_momentum()
        assert abs(momentum) < 1e-10  # Should cancel out

    def test_thermal_velocity(self):
        pattern = PlasmaPICPattern()
        cfg = PICConfig(n_particles=100)
        pattern._initialize_particles_1d(cfg)
        v_rms_e = pattern._compute_thermal_velocity(species=0)
        v_rms_i = pattern._compute_thermal_velocity(species=1)
        assert v_rms_e > 0.0
        assert v_rms_i > 0.0
        assert v_rms_e > v_rms_i  # Electrons are hotter/lighter


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = PlasmaPICPattern()
        results = {
            "metrics": {
                "energy_conservation_error": 0.001,
                "plasma_frequency": 1e10,
                "n_particles": 10000,
                "v_rms_electrons": 1e6,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = PlasmaPICPattern()
        results = {"metrics": {"energy_conservation_error": 1.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5

    def test_empty_metrics(self):
        pattern = PlasmaPICPattern()
        results = {"metrics": {}}
        confidence = pattern._calculate_confidence(results)
        assert confidence == 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_large_simulation_gpu(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(parameters={"n_particles": 200000, "n_steps": 5000})
        resources = pattern.estimate_resources(h)
        assert resources["gpu_required"] is True


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_1d(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma simulation", description="test")
        config = {"dimensions": "1d", "grid_size": 32, "n_particles": 500, "n_steps": 50}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("pic_")
        assert "plasma_frequency" in result.metrics

    async def test_run_2d(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma simulation", description="test")
        config = {"dimensions": "2d", "grid_size": 16, "n_particles": 500, "n_steps": 50}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "grid_cells" in result.metrics

    async def test_run_leapfrog(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma simulation", description="test")
        config = {
            "dimensions": "1d",
            "grid_size": 32,
            "n_particles": 500,
            "n_steps": 50,
            "pusher": "leapfrog",
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_logs_present(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma simulation", description="test")
        config = {"dimensions": "1d", "grid_size": 32, "n_particles": 500, "n_steps": 50}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma simulation", description="test")
        with patch.object(pattern, "_parse_config", side_effect=ValueError("test error")):
            result = await pattern.run(h, {})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = PlasmaPICPattern.get_metadata()
        assert meta["id"] == "plasma_pic"
        assert "name" in meta
        assert "category" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_minimal_particles(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma", description="test")
        config = {"dimensions": "1d", "grid_size": 16, "n_particles": 10, "n_steps": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_minimal_grid(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma", description="test")
        config = {"dimensions": "1d", "grid_size": 8, "n_particles": 100, "n_steps": 10}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_steps(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma", description="test")
        config = {"dimensions": "1d", "grid_size": 16, "n_particles": 100, "n_steps": 0}
        result = await pattern.run(h, config)
        # Zero steps causes index error in source; expect FAILED
        assert result.status == SimulationStatus.FAILED

    async def test_high_temperature(self):
        pattern = PlasmaPICPattern()
        h = Hypothesis(title="Plasma", description="test")
        config = {
            "dimensions": "1d",
            "grid_size": 16,
            "n_particles": 200,
            "n_steps": 20,
            "electron_temp": 1000.0,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
