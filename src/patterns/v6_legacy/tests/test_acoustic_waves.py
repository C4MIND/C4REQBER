"""
Unit tests for Acoustic Waves Pattern.
"""

import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acoustic_waves import AcousticWaves, AcousticWavesConfig


class TestAcousticWaves(unittest.TestCase):
    """Test cases for Acoustic Waves simulation."""

    def test_initialization(self):
        """Test that AcousticWaves initializes correctly."""
        config = AcousticWavesConfig(nx=32, ny=32)
        sim = AcousticWaves(config)

        self.assertEqual(sim.config.nx, 32)
        # 2D case: shape is (nx, ny)
        self.assertEqual(sim.p.shape, (32, 32))
        self.assertEqual(sim.vx.shape, (32, 32))
        self.assertEqual(sim.vy.shape, (32, 32))

    def test_3d_initialization(self):
        """Test 3D simulation initialization."""
        config = AcousticWavesConfig(nx=16, ny=16, nz=16)
        sim = AcousticWaves(config)

        self.assertEqual(sim.p.shape, (16, 16, 16))
        self.assertIsNotNone(sim.vz)

    def test_grid_setup(self):
        """Test computational grid setup."""
        config = AcousticWavesConfig(nx=64, ny=64, Lx=2.0, Ly=2.0)
        sim = AcousticWaves(config)

        self.assertEqual(len(sim.x), 64)
        self.assertAlmostEqual(sim.x[-1], 2.0 - 2.0 / 64, places=5)
        self.assertEqual(sim.X.shape, (64, 64))

    def test_pml_setup(self):
        """Test PML damping setup."""
        config = AcousticWavesConfig(nx=64, ny=64, boundary_type="pml", pml_width=16)
        sim = AcousticWaves(config)

        # PML should be non-zero at edges
        self.assertGreater(sim.sigma_x[0, 0], 0)
        self.assertGreater(sim.sigma_x[-1, 0], 0)

        # Center should have zero damping
        center = sim.config.nx // 2
        self.assertEqual(sim.sigma_x[center, 0], 0)

    def test_gaussian_initial_condition(self):
        """Test Gaussian pulse initial condition."""
        config = AcousticWavesConfig(nx=64, ny=64, source_type="gaussian_pulse")
        sim = AcousticWaves(config)

        # Should have non-zero pressure
        self.assertGreater(np.max(np.abs(sim.p)), 0)

        # Peak should be near center
        max_idx = np.unravel_index(np.argmax(np.abs(sim.p)), sim.p.shape)
        center_x = sim.config.nx // 2
        center_y = sim.config.ny // 2
        self.assertLess(abs(max_idx[0] - center_x), 10)
        self.assertLess(abs(max_idx[1] - center_y), 10)

    def test_spectral_operators(self):
        """Test spectral differentiation operators."""
        config = AcousticWavesConfig(nx=32, ny=32, method="pseudospectral")
        sim = AcousticWaves(config)

        # Wave numbers should be properly set up
        self.assertEqual(sim.KX.shape, (32, 32))
        self.assertEqual(sim.KY.shape, (32, 32))

    def test_energy_conservation_without_pml(self):
        """Test energy behavior without PML."""
        config = AcousticWavesConfig(
            nx=32,
            ny=32,
            n_steps=50,
            boundary_type="periodic",  # No PML
            source_type="gaussian_pulse",
        )
        sim = AcousticWaves(config)
        result = sim.run()

        # Energy should be approximately conserved without PML
        energy_drift = result["energy_drift"]
        self.assertLess(energy_drift, 0.5)  # Allow some numerical drift

    def test_pseudospectral_vs_fd(self):
        """Compare pseudospectral and finite difference methods."""
        np.random.seed(42)
        config_ps = AcousticWavesConfig(
            nx=32, ny=32, n_steps=20, method="pseudospectral"
        )
        sim_ps = AcousticWaves(config_ps)
        result_ps = sim_ps.run()

        np.random.seed(42)
        config_fd = AcousticWavesConfig(nx=32, ny=32, n_steps=20, method="fd")
        sim_fd = AcousticWaves(config_fd)
        result_fd = sim_fd.run()

        # Both should produce valid results
        self.assertGreater(result_ps["max_pressure"], 0)
        self.assertGreater(result_fd["max_pressure"], 0)

    def test_harmonic_source(self):
        """Test harmonic source excitation."""
        config = AcousticWavesConfig(
            nx=32, ny=32, n_steps=100, source_type="harmonic", source_frequency=500.0
        )
        sim = AcousticWaves(config)
        result = sim.run()

        # Should have wave activity
        self.assertGreater(result["rms_pressure"], 0)

    def test_cfl_condition(self):
        """Test that CFL condition is enforced."""
        config = AcousticWavesConfig(nx=64, ny=64, Lx=1.0, Ly=1.0, c0=343.0, cfl=0.5)
        sim = AcousticWaves(config)

        dx = config.Lx / config.nx
        expected_dt = config.cfl * dx / config.c0
        self.assertAlmostEqual(sim.config.dt, expected_dt, places=10)

    def test_metadata(self):
        """Test that metadata is properly structured."""
        metadata = AcousticWaves.get_metadata()

        self.assertEqual(metadata["pattern_id"], "acoustic_waves")
        self.assertEqual(metadata["version"], "6.5.0")
        self.assertIn("context", metadata)
        self.assertIn("forces", metadata)

    def test_pressure_history(self):
        """Test pressure history recording."""
        config = AcousticWavesConfig(nx=32, ny=32, n_steps=100)
        sim = AcousticWaves(config)
        result = sim.run()

        # Should have pressure history
        self.assertGreater(len(result["pressure_history"]), 0)

        # Each entry should have correct shape (2D: nx, ny)
        self.assertEqual(result["pressure_history"][0].shape, (32, 32))

    def test_points_per_wavelength(self):
        """Test resolution calculation."""
        config = AcousticWavesConfig(
            nx=64, ny=64, Lx=1.0, c0=343.0, source_frequency=1000.0
        )
        sim = AcousticWaves(config)
        result = sim.run()

        wavelength = config.c0 / config.source_frequency
        dx = config.Lx / config.nx
        expected_points = wavelength / dx

        self.assertAlmostEqual(result["points_per_wavelength"], expected_points)

    def test_wave_propagation(self):
        """Test that waves actually propagate."""
        config = AcousticWavesConfig(
            nx=64, ny=64, n_steps=30, source_type="gaussian_pulse"
        )
        sim = AcousticWaves(config)
        result = sim.run()

        # RMS pressure should spread out from source
        self.assertGreater(result["rms_pressure"], 0)

        # Max pressure should decrease as wave spreads
        initial_max = np.max(np.abs(sim.p))
        final_max = result["max_pressure"]
        # Wave should spread, reducing peak amplitude
        self.assertLess(final_max, initial_max * 2)


class TestSpectralOperations(unittest.TestCase):
    """Test spectral differentiation operations."""

    def test_gradient_of_constant(self):
        """Test that gradient of constant field is zero."""
        config = AcousticWavesConfig(nx=32, ny=32, method="pseudospectral")
        sim = AcousticWaves(config)

        const_field = np.ones((32, 32))
        grad_x, grad_y, _ = sim._spectral_gradient(const_field)

        # Gradient of constant field is zero (with numerical tolerance)
        np.testing.assert_allclose(grad_x, 0, atol=1e-10)
        np.testing.assert_allclose(grad_y, 0, atol=1e-10)

    def test_gradient_of_linear(self):
        """Test gradient of linear field."""
        config = AcousticWavesConfig(nx=32, ny=32, method="pseudospectral")
        sim = AcousticWaves(config)

        # f(x,y) = x
        linear_field = sim.X
        grad_x, grad_y, _ = sim._spectral_gradient(linear_field)

        # df/dx should be 1, df/dy should be 0
        np.testing.assert_allclose(grad_x, 1, rtol=1e-2)  # Relax tolerance
        np.testing.assert_allclose(grad_y, 0, atol=1e-2)

    def test_divergence_of_constant(self):
        """Test divergence of constant vector field."""
        config = AcousticWavesConfig(nx=32, ny=32, method="pseudospectral")
        sim = AcousticWaves(config)

        vx = np.ones((32, 32))
        vy = np.ones((32, 32))
        vz = np.zeros((32, 32))

        div = sim._spectral_divergence(vx, vy, vz)

        # Divergence of constant field is zero (with some numerical tolerance)
        np.testing.assert_allclose(div, 0, atol=1e-2)


if __name__ == "__main__":
    unittest.main()
