"""
Unit tests for 3D Elasticity Pattern.
"""

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticity_3d import Elasticity3D, Elasticity3DConfig, HexahedralElement


class TestElasticity3D(unittest.TestCase):
    """Test cases for 3D Elasticity simulation."""
    
    def test_initialization(self):
        """Test that Elasticity3D initializes correctly."""
        config = Elasticity3DConfig(nx=4, ny=4, nz=2)
        sim = Elasticity3D(config)
        
        self.assertEqual(sim.config.nx, 4)
        self.assertGreater(len(sim.elements), 0)
        self.assertGreater(len(sim.nodes), 0)
    
    def test_material_matrix(self):
        """Test material matrix computation."""
        config = Elasticity3DConfig(E=1e6, nu=0.3)
        sim = Elasticity3D(config)
        
        # Check Lamé parameters
        expected_mu = 1e6 / (2 * (1 + 0.3))
        expected_lam = 1e6 * 0.3 / ((1 + 0.3) * (1 - 2 * 0.3))
        
        self.assertAlmostEqual(sim.mu, expected_mu, places=2)
        self.assertAlmostEqual(sim.lam, expected_lam, places=2)
        
        # Check elasticity matrix shape
        self.assertEqual(sim.D.shape, (6, 6))
    
    def test_mesh_generation(self):
        """Test mesh generation."""
        config = Elasticity3DConfig(nx=2, ny=2, nz=2)
        sim = Elasticity3D(config)
        
        # Should have (2+1)^3 = 27 nodes
        expected_nodes = 3 * 3 * 3
        self.assertEqual(len(sim.nodes), expected_nodes)
        
        # Should have 2^3 = 8 elements
        expected_elements = 8
        self.assertEqual(len(sim.elements), expected_elements)
    
    def test_boundary_conditions(self):
        """Test boundary condition application."""
        config = Elasticity3DConfig(nx=4, ny=4, nz=2, fixed_boundary="bottom")
        sim = Elasticity3D(config)
        
        # Should have fixed DOFs on bottom surface
        self.assertGreater(len(sim.fixed_dofs), 0)
        
        # Check that displacements at fixed DOFs are zero
        for dof in sim.fixed_dofs:
            self.assertEqual(sim.displacements[dof], 0)
    
    def test_compression_simulation(self):
        """Test compression loading simulation."""
        config = Elasticity3DConfig(
            nx=4, ny=4, nz=2,
            load_type="compression",
            load_magnitude=1e4,
            solver_type="direct"
        )
        sim = Elasticity3D(config)
        result = sim.run()
        
        # Should have displacements
        self.assertGreater(result["max_displacement"], 0)
        
        # Top surface should move down
        top_disp = result["top_surface_displacement"]
        mean_top_z = np.mean(top_disp[:, 2])
        self.assertLess(mean_top_z, 0)
    
    def test_shear_simulation(self):
        """Test shear loading simulation."""
        config = Elasticity3DConfig(
            nx=4, ny=4, nz=2,
            load_type="shear",
            load_magnitude=1e4,
            solver_type="direct"
        )
        sim = Elasticity3D(config)
        result = sim.run()
        
        # Should have displacements
        self.assertGreater(result["max_displacement"], 0)
    
    def test_mixed_formulation(self):
        """Test mixed u-p formulation."""
        config = Elasticity3DConfig(
            nx=4, ny=4, nz=2,
            formulation="mixed_up",
            nu=0.49,  # Nearly incompressible
            solver_type="direct"
        )
        sim = Elasticity3D(config)
        result = sim.run()
        
        # Should have pressure field
        self.assertEqual(len(result["pressures"]), len(sim.elements))
        
        # Von Mises stress should be computed
        self.assertEqual(len(result["von_mises_stress"]), len(sim.elements))
    
    def test_strain_energy(self):
        """Test strain energy computation."""
        config = Elasticity3DConfig(
            nx=4, ny=4, nz=2,
            load_type="compression",
            solver_type="direct"
        )
        sim = Elasticity3D(config)
        result = sim.run()
        
        # Strain energy should be positive
        self.assertGreater(result["strain_energy"], 0)
    
    def test_incompressibility_handling(self):
        """Test that high Poisson ratio is handled."""
        config = Elasticity3DConfig(
            nx=4, ny=4, nz=2,
            nu=0.499,  # Very close to incompressible
            formulation="mixed_up"
        )
        sim = Elasticity3D(config)
        result = sim.run()
        
        # Should complete without error
        self.assertIsNotNone(result["displacements"])
        self.assertGreater(result["max_displacement"], 0)
    
    def test_metadata(self):
        """Test that metadata is properly structured."""
        metadata = Elasticity3D.get_metadata()
        
        self.assertEqual(metadata["pattern_id"], "elasticity_3d_mixed")
        self.assertEqual(metadata["version"], "6.5.0")
        self.assertIn("context", metadata)
        self.assertIn("forces", metadata)
    
    def test_stress_recovery(self):
        """Test stress computation."""
        config = Elasticity3DConfig(
            nx=4, ny=4, nz=2,
            load_type="compression",
            solver_type="direct"
        )
        sim = Elasticity3D(config)
        result = sim.run()
        
        # Stress should be non-zero
        max_stress = np.max(np.abs(result["stresses"]))
        self.assertGreater(max_stress, 0)
        
        # Von Mises stress should be positive
        self.assertTrue(np.all(result["von_mises_stress"] >= 0))


class TestHexahedralElement(unittest.TestCase):
    """Test HexahedralElement class."""
    
    def test_element_creation(self):
        """Test element initialization."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        
        elem = HexahedralElement(nodes, indices)
        
        self.assertEqual(elem.volume_ref, 1.0)
        self.assertEqual(len(elem.gauss_points), 8)
    
    def test_b_matrix(self):
        """Test B-matrix computation."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        elem = HexahedralElement(nodes, indices)
        
        xi = np.array([0, 0, 0])
        B, detJ = elem.compute_b_matrix(xi)
        
        self.assertEqual(B.shape, (6, 24))
        self.assertAlmostEqual(detJ, 0.125, places=5)
    
    def test_shape_functions(self):
        """Test shape function properties."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        elem = HexahedralElement(nodes, indices)
        
        # Test at center
        xi = np.array([0, 0, 0])
        N = elem.shape_functions_q1(xi)
        
        # Shape functions should sum to 1
        self.assertAlmostEqual(np.sum(N), 1.0)
    
    def test_shape_function_derivatives(self):
        """Test shape function derivatives."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        elem = HexahedralElement(nodes, indices)
        
        xi = np.array([0, 0, 0])
        dN = elem.shape_function_derivatives_q1(xi)
        
        self.assertEqual(dN.shape, (8, 3))
    
    def test_divergence_operator(self):
        """Test divergence operator computation."""
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        indices = np.arange(8)
        elem = HexahedralElement(nodes, indices)
        
        xi = np.array([0, 0, 0])
        div = elem.compute_divergence_operator(xi)
        
        self.assertEqual(len(div), 24)
        
        # Divergence of rigid body motion should be zero
        # (simplified test: sum of derivatives)
        for i in range(3):
            component_sum = np.sum(div[i::3])
            self.assertAlmostEqual(component_sum, 0, places=5)


class TestMaterialModels(unittest.TestCase):
    """Test material behavior."""
    
    def test_nearly_incompressible(self):
        """Test behavior with Poisson ratio close to 0.5."""
        nu_values = [0.3, 0.4, 0.45, 0.49]
        
        for nu in nu_values:
            config = Elasticity3DConfig(
                nx=4, ny=4, nz=2,
                nu=nu,
                formulation="mixed_up"
            )
            sim = Elasticity3D(config)
            result = sim.run()
            
            # Should produce valid results
            self.assertIsNotNone(result)
            self.assertGreaterEqual(result["max_displacement"], 0)


if __name__ == "__main__":
    unittest.main()
