"""
Tests for src/patterns/library/rigid_body.py (Rigid Body Dynamics Pattern)

Covers:
- RigidBodyConfig dataclass
- BodyState dataclass
- RigidBody initialization
- _quaternion_derivative()
- _integrate_quaternion()
- _get_rotation_matrix()
- _compute_forces()
- _step()
- _compute_energy()
- run() simulation
- get_metadata()
- Edge cases: single body, zero gravity
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.rigid_body import (

    RigidBody,
    RigidBodyConfig,
    BodyState,
)


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestRigidBodyConfig:
    def test_default_init(self):
        cfg = RigidBodyConfig()
        assert cfg.n_bodies == 10
        assert cfg.dt == 0.01
        assert cfg.n_steps == 1000
        assert cfg.use_quaternion is True
        assert cfg.friction_coefficient == 0.3
        assert cfg.restitution == 0.5

    def test_gravity_default(self):
        cfg = RigidBodyConfig()
        assert np.array_equal(cfg.gravity, np.array([0.0, -9.81, 0.0]))

    def test_custom_init(self):
        cfg = RigidBodyConfig(
            n_bodies=5,
            dt=0.001,
            n_steps=500,
            gravity=np.array([0.0, 0.0, -9.81]),
        )
        assert cfg.n_bodies == 5
        assert cfg.dt == 0.001
        assert cfg.n_steps == 500
        assert np.array_equal(cfg.gravity, np.array([0.0, 0.0, -9.81]))


# ═══════════════════════════════════════════════════════════════════
# BodyState Tests
# ═══════════════════════════════════════════════════════════════════


class TestBodyState:
    def test_default_init(self):
        state = BodyState(
            mass=1.0,
            inertia=np.diag([1.0, 1.0, 1.0]),
            position=np.array([0.0, 1.0, 0.0]),
            quaternion=np.array([1.0, 0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            angular_velocity=np.array([0.0, 0.0, 0.0]),
        )
        assert state.mass == 1.0
        assert np.array_equal(state.position, np.array([0.0, 1.0, 0.0]))

    def test_list_conversion(self):
        state = BodyState(
            mass=1.0,
            inertia=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            position=[0.0, 1.0, 0.0],
            quaternion=[1.0, 0.0, 0.0, 0.0],
            velocity=[0.0, 0.0, 0.0],
            angular_velocity=[0.0, 0.0, 0.0],
        )
        assert isinstance(state.inertia, np.ndarray)
        assert isinstance(state.position, np.ndarray)


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestRigidBodyInit:
    def test_init_default(self):
        sim = RigidBody()
        assert sim is not None
        assert len(sim.bodies) == 10
        assert len(sim.constraints) > 0

    def test_init_with_config(self):
        cfg = RigidBodyConfig(n_bodies=5)
        sim = RigidBody(cfg)
        assert len(sim.bodies) == 5

    def test_class_constants(self):
        assert RigidBody.PATTERN_ID == "rigid_body_dynamics"
        assert RigidBody.PATTERN_VERSION == "6.5.0"


# ═══════════════════════════════════════════════════════════════════
# Quaternion Tests
# ═══════════════════════════════════════════════════════════════════


class TestQuaternionOperations:
    def test_quaternion_derivative_shape(self):
        cfg = RigidBodyConfig(n_bodies=1)
        sim = RigidBody(cfg)
        q = np.array([1.0, 0.0, 0.0, 0.0])
        omega = np.array([0.0, 0.0, 1.0])
        dqdt = sim._quaternion_derivative(q, omega)
        assert dqdt.shape == (4,)

    def test_integrate_quaternion_normalization(self):
        cfg = RigidBodyConfig(n_bodies=1)
        sim = RigidBody(cfg)
        body = sim.bodies[0]
        initial_norm = np.linalg.norm(body.quaternion)
        sim._integrate_quaternion(body, dt=0.01)
        final_norm = np.linalg.norm(body.quaternion)
        assert abs(final_norm - 1.0) < 1e-10

    def test_get_rotation_matrix_shape(self):
        cfg = RigidBodyConfig(n_bodies=1)
        sim = RigidBody(cfg)
        body = sim.bodies[0]
        R = sim._get_rotation_matrix(body)
        assert R.shape == (3, 3)


# ═══════════════════════════════════════════════════════════════════
# Force and Energy Tests
# ═══════════════════════════════════════════════════════════════════


class TestForcesAndEnergy:
    def test_compute_forces_returns_tuple(self):
        cfg = RigidBodyConfig(n_bodies=1)
        sim = RigidBody(cfg)
        body = sim.bodies[0]
        force, torque = sim._compute_forces(body)
        assert isinstance(force, np.ndarray)
        assert isinstance(torque, np.ndarray)
        assert force.shape == (3,)
        assert torque.shape == (3,)

    def test_gravity_effect(self):
        cfg = RigidBodyConfig(n_bodies=1, gravity=np.array([0.0, -10.0, 0.0]))
        sim = RigidBody(cfg)
        body = sim.bodies[0]
        force, _ = sim._compute_forces(body)
        # Gravity force should be mass * gravity
        expected_force = body.mass * np.array([0.0, -10.0, 0.0])
        assert np.allclose(force[:2], expected_force[:2], atol=0.1)

    def test_compute_energy(self):
        cfg = RigidBodyConfig(n_bodies=2)
        sim = RigidBody(cfg)
        ke, pe, total = sim._compute_energy()
        assert ke >= 0
        assert isinstance(total, float)


# ═══════════════════════════════════════════════════════════════════
# Step Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestStep:
    def test_step_changes_position(self):
        cfg = RigidBodyConfig(n_bodies=1, dt=0.01)
        sim = RigidBody(cfg)
        body = sim.bodies[0]
        initial_pos = body.position.copy()
        sim._step(0.01)
        assert not np.array_equal(body.position, initial_pos)

    def test_bodies_above_ground(self):
        cfg = RigidBodyConfig(n_bodies=3, n_steps=10)
        sim = RigidBody(cfg)
        for step in range(10):
            sim._step(0.01)
        for body in sim.bodies:
            assert body.position[1] >= 0.4  # Approximate ground level


# ═══════════════════════════════════════════════════════════════════
# Run Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_default(self):
        cfg = RigidBodyConfig(n_bodies=3, n_steps=100)
        sim = RigidBody(cfg)
        result = sim.run()
        assert result is not None
        assert "final_positions" in result
        assert "energies" in result

    def test_final_positions_shape(self):
        cfg = RigidBodyConfig(n_bodies=5, n_steps=50)
        sim = RigidBody(cfg)
        result = sim.run()
        assert result["final_positions"].shape == (5, 3)

    def test_energies_recorded(self):
        cfg = RigidBodyConfig(n_bodies=3, n_steps=100)
        sim = RigidBody(cfg)
        result = sim.run()
        assert len(result["energies"]) > 0
        assert "kinetic" in result["energies"][0]
        assert "potential" in result["energies"][0]
        assert "total" in result["energies"][0]

    def test_trajectory_recorded(self):
        cfg = RigidBodyConfig(n_bodies=3, n_steps=100)
        sim = RigidBody(cfg)
        result = sim.run()
        assert "trajectory" in result
        assert len(result["trajectory"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    def test_metadata_structure(self):
        meta = RigidBody.get_metadata()
        assert meta["pattern_id"] == "rigid_body_dynamics"
        assert meta["version"] == "6.5.0"
        assert meta["name"] == "Rigid Body Dynamics"
        assert "forces" in meta
        assert "solution" in meta

    def test_metadata_complexity(self):
        meta = RigidBody.get_metadata()
        assert "complexity" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_single_body(self):
        cfg = RigidBodyConfig(n_bodies=1, n_steps=50)
        sim = RigidBody(cfg)
        result = sim.run()
        assert result["final_positions"].shape == (1, 3)

    def test_zero_gravity(self):
        cfg = RigidBodyConfig(n_bodies=2, n_steps=50, gravity=np.array([0.0, 0.0, 0.0]))
        sim = RigidBody(cfg)
        result = sim.run()
        assert "final_positions" in result

    def test_high_damping(self):
        cfg = RigidBodyConfig(n_bodies=2, n_steps=50, damping=0.1)
        sim = RigidBody(cfg)
        result = sim.run()
        assert "final_velocities" in result

    def test_high_restitution(self):
        cfg = RigidBodyConfig(n_bodies=2, n_steps=50, restitution=0.9)
        sim = RigidBody(cfg)
        result = sim.run()
        assert "final_positions" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
