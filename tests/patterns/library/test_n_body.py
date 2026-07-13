"""
Tests for src/patterns/library/n_body.py (N-Body Gravity pattern)

Covers:
- NBodyConfig dataclass
- OctreeNode initialization and operations
- NBodyGravity initialization
- _initialize_particles()
- _plummer_model() and _disk_model()
- _build_tree()
- _compute_forces_direct() and _compute_forces_tree()
- Integration methods: _integrate_euler, _integrate_leapfrog, _integrate_rk4
- _compute_energy()
- run() integration
- get_metadata()
- Edge cases: few particles, different distributions, integrator comparison
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.n_body import NBodyConfig, NBodyGravity, OctreeNode


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestNBodyConfig:
    def test_default_init(self):
        cfg = NBodyConfig()
        assert cfg.n_particles == 1000
        assert cfg.G == 6.67430e-11
        assert cfg.softening == 1e-3
        assert cfg.theta == 0.5
        assert cfg.dt == 0.001
        assert cfg.n_steps == 100
        assert cfg.integrator == "leapfrog"

    def test_custom_init(self):
        cfg = NBodyConfig(n_particles=500, theta=0.3, dt=0.01, integrator="rk4")
        assert cfg.n_particles == 500
        assert cfg.theta == 0.3
        assert cfg.dt == 0.01
        assert cfg.integrator == "rk4"


# ═══════════════════════════════════════════════════════════════════
# Octree Tests
# ═══════════════════════════════════════════════════════════════════


class TestOctreeNode:
    def test_init(self):
        node = OctreeNode(center=np.array([0.5, 0.5, 0.5]), size=1.0)
        assert node.size == 1.0
        assert np.allclose(node.center, [0.5, 0.5, 0.5])
        assert node.is_leaf is True
        assert node.particle_idx == -1

    def test_get_octant(self):
        node = OctreeNode(center=np.array([0.5, 0.5, 0.5]), size=1.0)
        # Position in positive x, y, z quadrant
        octant = node.get_octant(np.array([0.6, 0.6, 0.6]))
        assert octant == 7  # 0b111

        # Position in negative x quadrant
        octant = node.get_octant(np.array([0.4, 0.6, 0.6]))
        assert octant == 6  # 0b110

    def test_insert_particle(self):
        node = OctreeNode(center=np.array([0.5, 0.5, 0.5]), size=1.0)
        node.insert(pos=np.array([0.6, 0.6, 0.6]), mass=1.0, idx=0)
        assert node.mass == 1.0
        assert node.is_leaf is True
        assert node.particle_idx == 0


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestNBodyGravityInit:
    def test_default_init(self):
        pattern = NBodyGravity()
        assert pattern.PATTERN_ID == "n_body_gravity"
        assert pattern.positions is not None
        assert pattern.velocities is not None
        assert pattern.masses is not None

    def test_custom_config(self):
        cfg = NBodyConfig(n_particles=100)
        pattern = NBodyGravity(cfg)
        assert pattern.config.n_particles == 100
        assert pattern.positions.shape == (100, 3)

    def test_masses_normalized(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=100))
        assert np.sum(pattern.masses) == pytest.approx(1.0)


class TestInitializeParticles:
    def test_plummer_distribution(self):
        cfg = NBodyConfig(n_particles=100, initial_distribution="plummer")
        pattern = NBodyGravity(cfg)
        assert pattern.positions.shape == (100, 3)
        assert pattern.velocities.shape == (100, 3)

    def test_disk_distribution(self):
        cfg = NBodyConfig(n_particles=100, initial_distribution="disk")
        pattern = NBodyGravity(cfg)
        assert pattern.positions.shape == (100, 3)
        assert pattern.velocities.shape == (100, 3)

    def test_uniform_distribution(self):
        cfg = NBodyConfig(n_particles=100, initial_distribution="uniform")
        pattern = NBodyGravity(cfg)
        assert pattern.positions.shape == (100, 3)


class TestPlummerModel:
    def test_particle_count(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=50))
        positions, velocities = pattern._plummer_model(50)
        assert positions.shape == (50, 3)
        assert velocities.shape == (50, 3)

    def test_spherical_symmetry(self):
        """Plummer model should be roughly spherical"""
        pattern = NBodyGravity(NBodyConfig(n_particles=1000))
        positions, _ = pattern._plummer_model(1000)
        # Mean position should be near origin
        assert np.allclose(np.mean(positions, axis=0), 0, atol=1.0)


class TestDiskModel:
    def test_particle_count(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=50))
        positions, velocities = pattern._disk_model(50)
        assert positions.shape == (50, 3)
        assert velocities.shape == (50, 3)

    def test_flattened_distribution(self):
        """Disk should be flattened in z-direction"""
        pattern = NBodyGravity(NBodyConfig(n_particles=1000))
        positions, _ = pattern._disk_model(1000)
        # Z spread should be smaller than R spread
        z_spread = np.std(positions[:, 2])
        r_spread = np.std(np.sqrt(positions[:, 0] ** 2 + positions[:, 1] ** 2))
        assert z_spread < r_spread

    def test_rotation(self):
        """Disk should have rotational velocity pattern"""
        pattern = NBodyGravity(NBodyConfig(n_particles=100))
        positions, velocities = pattern._disk_model(100)
        # Check that velocities are roughly perpendicular to positions
        dot_products = np.sum(positions[:, :2] * velocities[:, :2], axis=1)
        # On average, v should be perpendicular to r (v·r ≈ 0)
        assert np.mean(np.abs(dot_products)) < np.mean(np.linalg.norm(velocities[:, :2], axis=1))


# ═══════════════════════════════════════════════════════════════════
# Tree Building Tests
# ═══════════════════════════════════════════════════════════════════


class TestBuildTree:
    def test_tree_created(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        root = pattern._build_tree()
        assert root is not None
        assert root.mass > 0

    def test_tree_mass_conservation(self):
        """Total mass in tree should equal sum of particle masses"""
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        total_mass = np.sum(pattern.masses)
        root = pattern._build_tree()
        assert root.mass == pytest.approx(total_mass)


# ═══════════════════════════════════════════════════════════════════
# Force Computation Tests
# ═══════════════════════════════════════════════════════════════════


class TestComputeForces:
    def test_direct_forces_shape(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        forces = pattern._compute_forces_direct()
        assert forces.shape == (10, 3)

    def test_tree_forces_shape(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        forces = pattern._compute_forces_tree()
        assert forces.shape == (10, 3)

    def test_direct_vs_tree_similar(self):
        """Tree and direct forces should be similar for small theta"""
        cfg = NBodyConfig(n_particles=20, theta=0.1)
        pattern = NBodyGravity(cfg)
        forces_direct = pattern._compute_forces_direct()
        forces_tree = pattern._compute_forces_tree()
        # Forces should be similar within tolerance
        assert np.allclose(forces_direct, forces_tree, rtol=0.5)

    def test_forces_not_zero(self):
        """Forces should be non-zero for non-uniform distributions"""
        pattern = NBodyGravity(NBodyConfig(n_particles=10, initial_distribution="plummer"))
        forces = pattern._compute_forces_direct()
        assert np.linalg.norm(forces) > 0


# ═══════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestIntegrateEuler:
    def test_positions_change(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        forces = pattern._compute_forces_tree()
        pos_before = pattern.positions.copy()
        pattern._integrate_euler(forces)
        assert not np.allclose(pattern.positions, pos_before)


class TestIntegrateLeapfrog:
    def test_positions_change(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        forces = pattern._compute_forces_tree()
        pos_before = pattern.positions.copy()
        pattern._integrate_leapfrog(forces)
        assert not np.allclose(pattern.positions, pos_before)

    def test_symplectic_property(self):
        """Leapfrog should approximately conserve energy over short time"""
        cfg = NBodyConfig(n_particles=10, dt=0.001, integrator="leapfrog")
        pattern = NBodyGravity(cfg)
        ke0, pe0, e0 = pattern._compute_energy()

        for _ in range(10):
            forces = pattern._compute_forces_tree()
            pattern._integrate_leapfrog(forces)

        ke1, pe1, e1 = pattern._compute_energy()
        # Energy should be approximately conserved
        assert abs(e1 - e0) / abs(e0) < 0.1


class TestIntegrateRK4:
    def test_positions_change(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        forces = pattern._compute_forces_tree()
        pos_before = pattern.positions.copy()
        pattern._integrate_rk4(forces)
        assert not np.allclose(pattern.positions, pos_before)


# ═══════════════════════════════════════════════════════════════════
# Energy Tests
# ═══════════════════════════════════════════════════════════════════


class TestComputeEnergy:
    def test_energy_positive(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10))
        ke, pe, total = pattern._compute_energy()
        assert ke >= 0
        assert pe <= 0  # Gravitational potential is negative
        assert total == pytest.approx(ke + pe)

    def test_kinetic_energy_nonzero(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, initial_distribution="disk"))
        ke, _, _ = pattern._compute_energy()
        assert ke > 0  # Disk has rotation


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_default(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=10))
        result = pattern.run()
        assert result["pattern_id"] == "n_body_gravity"
        assert "final_positions" in result
        assert "energies" in result

    def test_run_euler(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=10, integrator="euler"))
        result = pattern.run()
        assert len(result["trajectory"]) > 0

    def test_run_rk4(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=10, integrator="rk4"))
        result = pattern.run()
        assert len(result["trajectory"]) > 0

    def test_energy_drift_calculated(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=10))
        result = pattern.run()
        assert "energy_drift" in result
        assert isinstance(result["energy_drift"], float)

    def test_virial_ratio(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=10))
        result = pattern.run()
        assert "virial_ratio" in result

    def test_trajectory_recorded(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=20))
        result = pattern.run()
        assert len(result["trajectory"]) > 0

    def test_energies_recorded(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=20))
        result = pattern.run()
        assert len(result["energies"]) > 0
        # Each energy entry should have kinetic, potential, total
        for entry in result["energies"]:
            assert "kinetic" in entry
            assert "potential" in entry
            assert "total" in entry


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = NBodyGravity.get_metadata()
        assert meta["pattern_id"] == "n_body_gravity"
        assert "name" in meta
        assert "context" in meta
        assert "forces" in meta
        assert "solution" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_two_particles(self):
        """Simulation should work with just 2 particles"""
        pattern = NBodyGravity(NBodyConfig(n_particles=2, n_steps=10))
        result = pattern.run()
        assert result["final_positions"].shape == (2, 3)

    def test_single_particle(self):
        """Simulation should work with 1 particle (no interactions)"""
        pattern = NBodyGravity(NBodyConfig(n_particles=1, n_steps=10))
        result = pattern.run()
        assert result["final_positions"].shape == (1, 3)

    def test_zero_steps(self):
        pattern = NBodyGravity(NBodyConfig(n_particles=10, n_steps=0))
        result = pattern.run()
        assert len(result["energies"]) == 1  # Just initial energy

    def test_very_small_softening(self):
        """Small softening should give more accurate forces"""
        cfg = NBodyConfig(n_particles=10, softening=1e-6)
        pattern = NBodyGravity(cfg)
        forces = pattern._compute_forces_direct()
        assert np.all(np.isfinite(forces))

    def test_large_theta(self):
        """Large theta should speed up but be less accurate"""
        cfg = NBodyConfig(n_particles=20, theta=1.0)
        pattern = NBodyGravity(cfg)
        result = pattern.run()
        assert result["energy_drift"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
