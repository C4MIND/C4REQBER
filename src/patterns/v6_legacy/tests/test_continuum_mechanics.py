"""
Unit tests for Continuum Mechanics Pattern.
"""

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from continuum_mechanics import ContinuumMechanics, ContinuumMechanicsConfig, FiniteElement


class TestContinuumMechanics(unittest.TestCase):
    """Test cases for Continuum Mechanics simulation."""
    
    def test_initialization(self):
        """Test that ContinuumMechanics initializes correctly."""
        config = ContinuumMechanicsConfig(
            n_elements_x=4,
            n_elements_y=4,
            n_elements_z=2
        )
        sim = ContinuumMechanics(config)
        
        self.assertEqual(sim.config.n_elements_x, 4)
        self.assertGreater(len(sim.elements), 0)
        self.assertGreater(len(sim.nodes), 0)
    
    def test_mesh_creation(self):
        """Test that mesh is created correctly."""
        config = ContinuumMechanicsConfig(
            n_elements_x=2,
            n_elements_y=2,
            n_elements_z=2
        )
        sim = ContinuumMechanics(config)
        
        # Should have (2+1)^3 = 27 nodes
        expected_nodes = 3 * 3 * 3
        self.assertEqual(len(sim.nodes), expected_nodes)
        
        # Should have 2^3 = 8 elements
        expected_elements = 8
        self.assertEqual(len(sim.elements), expected_elements)
    
    def test_boundary_conditions(self):
        """Test that boundary conditions are applied."""
        config = ContinuumMechanicsConfig(
            n_elements_x=4,
            n_elements_y=4,
            n_elements_z=2,
            fixed_boundary="bottom"
        )
        sim = ContinuumMechanics(config)
        
        # Should have fixed DOFs
        self.assertGreater(len(sim.fixed_dofs), 0)
        
        # Bottom layer should be fixed
        nx, ny = 5, 5
        for j in range(ny):
            for i in range(nx):
                node_idx = j * nx + i
                self.assertIn(node_idx * 3, sim.fixed_dofs)
    
    def test_gravity_loading(self):
        """Test that gravity causes deformation."""
        config = ContinuumMechanicsConfig(
            n_elements_x=4,
            n_elements_y=4,
            n_elements_z=2,
            load_type="gravity",
            load_magnitude=9.81,
            n_steps=50
        )
        sim = ContinuumMechanics(config)
        result = sim.run()
        
        # Should have some displacement
        self.assertGreater(result["max_displacement"], 0)
        
        # Top should move down more than bottom
        top_disp = result["top_surface_displacement"]
        mean_top_y = np.mean(top_disp[:, 1])
        self.assertLess(mean_top_y, 0)  # Moving in -y direction
    
    def test_compression_loading(self):
        """Test compression loading."""
        config = ContinuumMechanicsConfig(
            n_elements_x=4,
            n_elements_y=4,
            n_elements_z=2,
            load_type="compression",
            load_magnitude=1000.0,
            n_steps=50
        )
        sim = ContinuumMechanics(config)
        result = sim.run()
        
        # Top should move down
        top_disp = result["top_surface_displacement"]
        mean_top_y = np.mean(top_disp[:, 1])
        self.assertLess(mean_top_y, 0)
    
    def test_material_models(self):
        """Test different material models."""
        for model in ["linear", "neo_hookean"]:
            config = ContinuumMechanicsConfig(
                n_elements_x=4,
                n_elements_y=4,
                n_elements_z=2,
                material_model=model,
                n_steps=20
            )
            sim = ContinuumMechanics(config)
            result = sim.run()
            
            self.assertEqual(result["material_model"], model)
            self.assertGreaterEqual(result["max_displacement"], 0)
    
    def test_strain_energy(self):
        """Test strain energy computation."""
        config = ContinuumMechanicsConfig(
            n_elements_x=4,
            n_elements_y=4,
            n_elements_z=2,
            load_type="compression",
            n_steps=50
        )
        sim = ContinuumMechanics(config)
        result = sim.run()
        
        # Strain energy should be positive
        self.assertGreater(result["final_strain_energy"], 0)
    
    def test_metadata(self):
        """Test that metadata is properly structured."""
        metadata = ContinuumMechanics.get_metadata()
        
        self.assertEqual(metadata["pattern_id"], "continuum_mechanics")
        self.assertEqual(metadata["version"], "6.5.0")
        self.assertIn("context", metadata)
        self.assertIn("forces", metadata)
    
    def test_displacement_history(self):
        """Test that displacement history is recorded."""
        config = ContinuumMechanicsConfig(
            n_elements_x=4,
            n_elements_y=4,
            n_elements_z=2,
            n_steps=100
        )
        sim = ContinuumMechanics(config)
        result = sim.run()
        
        # Should have displacement history entries
        self.assertGreater(len(result["displacement_history"]), 0)
        
        # Energy history should track strain energy
        self.assertGreater(len(result["energy_history"]), 0)


class TestFiniteElement(unittest.TestCase):
    """Test FiniteElement class."""
    
    def test_element_initialization(self):
        """Test FiniteElement creation."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        
        elem = FiniteElement(nodes, indices)
        
        self.assertEqual(elem.volume_ref, 1.0)
        self.assertEqual(len(elem.gauss_points), 8)
    
    def test_shape_functions(self):
        """Test shape function properties."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        elem = FiniteElement(nodes, indices)
        
        # Test at center
        xi = np.array([0, 0, 0])
        N = elem.shape_functions(xi)
        
        # Shape functions should sum to 1
        self.assertAlmostEqual(np.sum(N), 1.0)
        
        # All shape functions should be 0.125 at center
        np.testing.assert_allclose(N, 0.125)
    
    def test_deformation_gradient(self):
        """Test deformation gradient computation."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        elem = FiniteElement(nodes, indices)
        
        # Zero displacement - F should be identity
        disp = np.zeros((8, 3))
        xi = np.array([0, 0, 0])
        F = elem.compute_deformation_gradient(disp, xi)
        
        np.testing.assert_allclose(F, np.eye(3), atol=1e-10)
        
        # Uniform expansion
        disp = nodes * 0.1  # 10% expansion
        F = elem.compute_deformation_gradient(disp, xi)
        expected_F = np.eye(3) * 1.1
        np.testing.assert_allclose(F, expected_F, rtol=1e-6)
    
    def test_stress_computation(self):
        """Test stress computation."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        elem = FiniteElement(nodes, indices)
        
        # Uniaxial strain
        disp = np.zeros((8, 3))
        disp[:, 0] = nodes[:, 0] * 0.1  # 10% strain in x
        
        xi = np.array([0, 0, 0])
        F = elem.compute_deformation_gradient(disp, xi)
        
        E = 1e7
        nu = 0.3
        S = elem.compute_stress_linear(F, E, nu)
        
        # Should have positive stress in x direction
        self.assertGreater(S[0, 0], 0)


if __name__ == "__main__":
    unittest.main()
