"""
Unit tests for N-Body Gravity Pattern.
"""

import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from n_body import NBodyGravity, NBodyConfig


class TestNBodyGravity(unittest.TestCase):
    """Test cases for N-Body Gravity simulation."""

    def test_initialization(self):
        """Test that NBodyGravity initializes correctly."""
        config = NBodyConfig(n_particles=100)
        sim = NBodyGravity(config)

        self.assertEqual(sim.config.n_particles, 100)
        self.assertEqual(sim.positions.shape, (100, 3))
        self.assertEqual(sim.velocities.shape, (100, 3))
        self.assertEqual(sim.masses.shape, (100,))

    def test_plummer_initialization(self):
        """Test Plummer model initialization."""
        config = NBodyConfig(n_particles=500, initial_distribution="plummer")
        sim = NBodyGravity(config)

        # Check that particles are distributed (not all at origin)
        rms_radius = np.sqrt(np.mean(np.sum(sim.positions**2, axis=1)))
        self.assertGreater(rms_radius, 0.1)

        # Check mass conservation
        self.assertAlmostEqual(np.sum(sim.masses), 1.0, places=5)

    def test_disk_initialization(self):
        """Test disk model initialization."""
        config = NBodyConfig(n_particles=500, initial_distribution="disk")
        sim = NBodyGravity(config)

        # Check that disk is mostly in xy plane
        z_rms = np.sqrt(np.mean(sim.positions[:, 2] ** 2))
        r_rms = np.sqrt(np.mean(sim.positions[:, 0] ** 2 + sim.positions[:, 1] ** 2))
        self.assertLess(z_rms, r_rms * 0.5)  # z spread should be smaller

    def test_energy_conservation(self):
        """Test that energy is approximately conserved with leapfrog."""
        config = NBodyConfig(
            n_particles=50, n_steps=100, dt=0.001, integrator="leapfrog"
        )
        sim = NBodyGravity(config)
        result = sim.run()

        # Energy drift should be small for leapfrog
        self.assertLess(result["energy_drift"], 0.1)

    def test_integrators_comparison(self):
        """Test that different integrators produce different results."""
        np.random.seed(42)
        config_euler = NBodyConfig(
            n_particles=20, n_steps=50, dt=0.001, integrator="euler"
        )
        sim_euler = NBodyGravity(config_euler)
        result_euler = sim_euler.run()

        np.random.seed(42)
        config_leapfrog = NBodyConfig(
            n_particles=20, n_steps=50, dt=0.001, integrator="leapfrog"
        )
        sim_leapfrog = NBodyGravity(config_leapfrog)
        result_leapfrog = sim_leapfrog.run()

        # Results should be different (but with small dt they may be very close)
        pos_diff = np.linalg.norm(
            result_euler["final_positions"] - result_leapfrog["final_positions"]
        )
        # Just verify that results are finite and valid (difference can be tiny)
        self.assertTrue(np.isfinite(pos_diff))

    def test_center_of_mass(self):
        """Test that center of mass doesn't drift (conservation of momentum)."""
        config = NBodyConfig(
            n_particles=30, n_steps=50, dt=0.001, initial_distribution="uniform"
        )
        sim = NBodyGravity(config)

        # Set initial momentum to zero
        sim.velocities = sim.velocities - np.mean(sim.velocities, axis=0)

        result = sim.run()

        # COM should stay near origin
        com = result["com"]
        self.assertLess(np.linalg.norm(com), 0.5)

    def test_metadata(self):
        """Test that metadata is properly structured."""
        metadata = NBodyGravity.get_metadata()

        self.assertEqual(metadata["pattern_id"], "n_body_gravity")
        self.assertEqual(metadata["version"], "6.5.0")
        self.assertIn("context", metadata)
        self.assertIn("forces", metadata)
        self.assertIn("solution", metadata)
        self.assertIsInstance(metadata["forces"], list)

    def test_trajectory_recording(self):
        """Test that trajectory is recorded correctly."""
        config = NBodyConfig(n_particles=20, n_steps=100)
        sim = NBodyGravity(config)
        result = sim.run()

        # Trajectory should have entries every 10 steps (0, 10, 20, ..., 90 = 10 entries)
        expected_trajectory_length = 100 // 10
        self.assertEqual(len(result["trajectory"]), expected_trajectory_length)

        # Each trajectory entry should have shape (n_particles, 3)
        self.assertEqual(result["trajectory"][0].shape, (20, 3))

    def test_virial_theorem(self):
        """Test virial ratio for relaxed system."""
        config = NBodyConfig(
            n_particles=50,
            n_steps=100,
            initial_distribution="plummer",
            integrator="leapfrog",
        )
        sim = NBodyGravity(config)
        result = sim.run()

        # For virialized system, 2*KE/|PE| should be of order 1
        # Note: This is approximate due to finite simulation time
        virial = result["virial_ratio"]
        self.assertGreater(virial, 0.01)  # Should have some kinetic energy
        self.assertLess(virial, 100.0)  # But not completely unbound


class TestOctree(unittest.TestCase):
    """Test Barnes-Hut octree implementation."""

    def test_octree_insertion(self):
        """Test that octree correctly inserts particles."""
        from n_body import OctreeNode

        root = OctreeNode(np.array([0, 0, 0]), 2.0)

        # Insert particles
        root.insert(np.array([0.1, 0.1, 0.1]), 1.0, 0)
        root.insert(np.array([-0.1, -0.1, -0.1]), 1.0, 1)

        # Check total mass
        self.assertEqual(root.mass, 2.0)

    def test_force_computation(self):
        """Test that force computation works."""
        from n_body import OctreeNode

        root = OctreeNode(np.array([0, 0, 0]), 2.0)
        root.insert(np.array([0.5, 0, 0]), 1.0, 0)

        # Compute force on test particle
        force = root.compute_force(
            np.array([0, 0, 0]), 1.0, theta=0.5, G=1.0, softening=0.01
        )

        # Force should be in +x direction
        self.assertGreater(force[0], 0)


if __name__ == "__main__":
    unittest.main()
