"""
Tests for continuum_mechanics pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.continuum_mechanics import ContinuumMechanics, ContinuumMechanicsConfig


class TestConfig:
    def test_default_config(self):
        cfg = ContinuumMechanicsConfig()
        assert cfg.n_elements_x == 10
        assert cfg.n_elements_y == 10
        assert cfg.n_elements_z == 5
        assert cfg.material_model == "neo_hookean"

    def test_custom_config(self):
        cfg = ContinuumMechanicsConfig(n_elements_x=5, youngs_modulus=1e8)
        assert cfg.n_elements_x == 5
        assert cfg.youngs_modulus == 1e8


class TestInit:
    def test_pattern_init_default(self):
        pattern = ContinuumMechanics()
        assert pattern.config is not None
        assert pattern.nodes is not None
        assert len(pattern.elements) > 0

    def test_pattern_init_custom(self):
        cfg = ContinuumMechanicsConfig(n_elements_x=5, n_elements_y=5, n_elements_z=2)
        pattern = ContinuumMechanics(cfg)
        assert pattern.nodes is not None


class TestMesh:
    def test_node_count(self):
        cfg = ContinuumMechanicsConfig(n_elements_x=2, n_elements_y=2, n_elements_z=2)
        pattern = ContinuumMechanics(cfg)
        expected_nodes = (2 + 1) * (2 + 1) * (2 + 1)
        assert len(pattern.nodes) == expected_nodes

    def test_element_count(self):
        cfg = ContinuumMechanicsConfig(n_elements_x=2, n_elements_y=2, n_elements_z=2)
        pattern = ContinuumMechanics(cfg)
        expected_elements = 2 * 2 * 2
        assert len(pattern.elements) == expected_elements


class TestFiniteElement:
    def test_element_volume(self):
        pattern = ContinuumMechanics()
        elem = pattern.elements[0]
        assert elem.volume_ref > 0

    def test_shape_functions(self):
        pattern = ContinuumMechanics()
        elem = pattern.elements[0]
        N = elem.shape_functions(np.array([0.0, 0.0, 0.0]))
        assert len(N) == 8
        assert np.isclose(np.sum(N), 1.0, atol=0.1)

    def test_deformation_gradient(self):
        pattern = ContinuumMechanics()
        elem = pattern.elements[0]
        disp = np.zeros((8, 3))
        F = elem.compute_deformation_gradient(disp, np.array([0.0, 0.0, 0.0]))
        assert F.shape == (3, 3)
        assert np.allclose(F, np.eye(3), atol=0.1)


class TestStress:
    def test_neo_hookean_stress(self):
        pattern = ContinuumMechanics()
        elem = pattern.elements[0]
        F = np.eye(3)
        S = elem.compute_stress_neo_hookean(F, 1e7, 0.3)
        assert S.shape == (3, 3)
        assert np.all(np.isfinite(S))

    def test_linear_stress(self):
        pattern = ContinuumMechanics()
        elem = pattern.elements[0]
        F = np.eye(3)
        S = elem.compute_stress_linear(F, 1e7, 0.3)
        assert S.shape == (3, 3)
        assert np.all(np.isfinite(S))


class TestForces:
    def test_external_forces(self):
        pattern = ContinuumMechanics()
        f_ext = pattern._compute_external_forces()
        assert len(f_ext) == len(pattern.nodes) * 3

    def test_assemble_forces(self):
        pattern = ContinuumMechanics()
        f_int = pattern._assemble_forces()
        assert len(f_int) == len(pattern.nodes) * 3


class TestStep:
    def test_single_step(self):
        pattern = ContinuumMechanics()
        disp_before = pattern.displacements.copy()
        pattern._step()
        assert not np.allclose(pattern.displacements, disp_before)


class TestEnergy:
    def test_strain_energy(self):
        pattern = ContinuumMechanics()
        energy = pattern._compute_strain_energy()
        assert isinstance(energy, float)
        assert energy >= 0


class TestRun:
    def test_short_simulation(self):
        cfg = ContinuumMechanicsConfig(n_elements_x=3, n_elements_y=3, n_elements_z=2, n_steps=10)
        pattern = ContinuumMechanics(cfg)
        result = pattern.run()
        assert "displacements" in result
        assert "max_displacement" in result
        assert result["n_elements"] > 0

    def test_metadata(self):
        meta = ContinuumMechanics.get_metadata()
        assert "pattern_id" in meta
        assert "name" in meta


class TestEdgeCases:
    def test_fixed_boundary(self):
        cfg = ContinuumMechanicsConfig(fixed_boundary="bottom")
        pattern = ContinuumMechanics(cfg)
        assert len(pattern.fixed_dofs) > 0

    def test_compression_load(self):
        cfg = ContinuumMechanicsConfig(load_type="compression", load_magnitude=1000)
        pattern = ContinuumMechanics(cfg)
        f_ext = pattern._compute_external_forces()
        assert np.any(f_ext != 0)

    def test_gravity_load(self):
        cfg = ContinuumMechanicsConfig(load_type="gravity")
        pattern = ContinuumMechanics(cfg)
        f_ext = pattern._compute_external_forces()
        assert np.any(f_ext != 0)
