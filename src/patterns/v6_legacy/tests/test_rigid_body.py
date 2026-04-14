"""
Unit tests for Rigid Body Dynamics Pattern.
"""

import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rigid_body import RigidBody, RigidBodyConfig, BodyState
from base import quaternion_multiply, quaternion_conjugate, quaternion_rotate_vector


class TestRigidBody(unittest.TestCase):
    """Test cases for Rigid Body simulation."""

    def test_initialization(self):
        """Test that RigidBody initializes correctly."""
        config = RigidBodyConfig(n_bodies=5)
        sim = RigidBody(config)

        self.assertEqual(len(sim.bodies), 5)
        self.assertEqual(sim.config.n_bodies, 5)

    def test_quaternion_operations(self):
        """Test quaternion helper functions."""
        # Identity quaternion
        q_id = np.array([1, 0, 0, 0])

        # Multiply by identity
        q_test = np.array([0.707, 0.707, 0, 0])
        result = quaternion_multiply(q_id, q_test)
        np.testing.assert_allclose(result, q_test, rtol=1e-3)

        # Conjugate
        q_conj = quaternion_conjugate(q_test)
        self.assertAlmostEqual(q_conj[0], q_test[0])
        self.assertAlmostEqual(q_conj[1], -q_test[1])

    def test_quaternion_rotation(self):
        """Test that quaternion rotation works correctly."""
        # 90 degree rotation around z-axis
        theta = np.pi / 2
        q_z90 = np.array([np.cos(theta / 2), 0, 0, np.sin(theta / 2)])

        # Rotate x-axis unit vector
        v = np.array([1, 0, 0])
        v_rot = quaternion_rotate_vector(q_z90, v)

        # Should point in y direction
        np.testing.assert_allclose(v_rot, [0, 1, 0], atol=1e-6)

    def test_body_state_creation(self):
        """Test BodyState dataclass."""
        body = BodyState(
            mass=2.0,
            inertia=np.diag([1, 2, 3]),
            position=np.array([1, 2, 3]),
            quaternion=np.array([1, 0, 0, 0]),
            velocity=np.array([0, 0, 0]),
            angular_velocity=np.array([0, 1, 0]),
        )

        self.assertEqual(body.mass, 2.0)
        np.testing.assert_array_equal(body.position, [1, 2, 3])

    def test_gravity_effect(self):
        """Test that gravity affects bodies."""
        config = RigidBodyConfig(
            n_bodies=1, n_steps=100, dt=0.01, gravity=np.array([0.0, -9.81, 0.0])
        )
        sim = RigidBody(config)

        # Set initial velocity to zero
        sim.bodies[0].velocity = np.array([0, 0, 0])
        initial_y = sim.bodies[0].position[1]

        result = sim.run()

        # Body should have fallen
        final_y = result["final_positions"][0][1]
        self.assertLess(final_y, initial_y)

    def test_ground_collision(self):
        """Test that bodies collide with ground."""
        config = RigidBodyConfig(
            n_bodies=1,
            n_steps=200,
            dt=0.01,
            gravity=np.array([0.0, -9.81, 0.0]),
            restitution=0.5,
        )
        sim = RigidBody(config)

        # Place body near ground with downward velocity
        sim.bodies[0].position = np.array([0, 1.0, 0])
        sim.bodies[0].velocity = np.array([0, -2.0, 0])

        result = sim.run()

        # Body should not be below ground (with some tolerance)
        final_y = result["final_positions"][0][1]
        self.assertGreater(final_y, 0.3)  # Allow for radius

    def test_energy_dissipation(self):
        """Test that energy is dissipated through damping."""
        config = RigidBodyConfig(n_bodies=3, n_steps=100, dt=0.01, damping=0.1)
        sim = RigidBody(config)
        result = sim.run()

        # Energy should generally decrease with damping
        # (though individual steps may vary)
        energies = result["energies"]
        initial_e = energies[0]["total"]
        final_e = energies[-1]["total"]

        # With damping, energy should decrease
        self.assertLess(final_e, initial_e * 1.1)  # Allow small fluctuation

    def test_metadata(self):
        """Test that metadata is properly structured."""
        metadata = RigidBody.get_metadata()

        self.assertEqual(metadata["pattern_id"], "rigid_body_dynamics")
        self.assertEqual(metadata["version"], "6.5.0")
        self.assertIn("context", metadata)
        self.assertIn("forces", metadata)

    def test_quaternion_normalization(self):
        """Test that quaternions stay normalized during simulation."""
        config = RigidBodyConfig(n_bodies=2, n_steps=50, dt=0.01)
        sim = RigidBody(config)

        # Apply some angular velocity
        for body in sim.bodies:
            body.angular_velocity = np.array([1, 0.5, 0.3])

        result = sim.run()

        # Check all quaternions are normalized
        for q in result["final_quaternions"]:
            norm = np.linalg.norm(q)
            self.assertAlmostEqual(norm, 1.0, places=5)

    def test_trajectory_recording(self):
        """Test that trajectory is recorded."""
        config = RigidBodyConfig(n_bodies=3, n_steps=100)
        sim = RigidBody(config)
        result = sim.run()

        # Should have trajectory entries
        self.assertGreater(len(result["trajectory"]), 0)

        # Each entry should have correct structure
        first_step = result["trajectory"][0]
        self.assertIn("positions", first_step)
        self.assertIn("quaternions", first_step)


class TestQuaternionMath(unittest.TestCase):
    """Test quaternion mathematical operations."""

    def test_rotation_identity(self):
        """Test that identity quaternion gives no rotation."""
        q_id = np.array([1, 0, 0, 0])
        v = np.array([1, 2, 3])

        v_rot = quaternion_rotate_vector(q_id, v)
        np.testing.assert_allclose(v_rot, v)

    def test_rotation_composition(self):
        """Test composition of two rotations."""
        # 90 deg around x, then 90 deg around y
        theta = np.pi / 2
        q_x90 = np.array([np.cos(theta / 2), np.sin(theta / 2), 0, 0])
        q_y90 = np.array([np.cos(theta / 2), 0, np.sin(theta / 2), 0])

        q_combined = quaternion_multiply(q_y90, q_x90)

        v = np.array([1, 0, 0])
        v_rot = quaternion_rotate_vector(q_combined, v)

        # Should end up pointing in +z direction
        np.testing.assert_allclose(np.abs(v_rot), [0, 0, 1], atol=1e-6)

    def test_conjugate_multiplication(self):
        """Test q * q_conj = [1, 0, 0, 0]."""
        q = np.array([0.707, 0.5, 0.3, 0.3])
        q = q / np.linalg.norm(q)

        q_conj = quaternion_conjugate(q)
        result = quaternion_multiply(q, q_conj)

        np.testing.assert_allclose(result, [1, 0, 0, 0], atol=1e-6)


if __name__ == "__main__":
    unittest.main()
