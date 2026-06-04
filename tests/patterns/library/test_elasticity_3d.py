"""Tests for elasticity_3d pattern module."""

import numpy as np
import pytest

from src.patterns.library.elasticity_3d import (

    Elasticity3DConfig,
    Elasticity3D,
    HexahedralElement,
)


class TestElasticity3DConfig:
    def test_default_values(self):
        cfg = Elasticity3DConfig()
        assert cfg.nx == 8
        assert cfg.ny == 8
        assert cfg.nz == 4
        assert cfg.E == 1e6
        assert cfg.nu == 0.49
        assert cfg.formulation == "mixed_up"
        assert cfg.load_type == "compression"

    def test_custom_values(self):
        cfg = Elasticity3DConfig(nx=4, ny=4, nz=2, E=2e6, nu=0.3)
        assert cfg.nx == 4
        assert cfg.E == 2e6
        assert cfg.nu == 0.3


class TestHexahedralElement:
    @pytest.fixture
    def unit_element(self):
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=float)
        indices = np.arange(8)
        return HexahedralElement(nodes, indices, is_quadratic=False)

    def test_init(self, unit_element):
        assert unit_element.volume_ref > 0
        assert len(unit_element.gauss_points) == 8

    def test_shape_functions_q1(self, unit_element):
        xi = np.array([0, 0, 0])
        N = unit_element.shape_functions_q1(xi)
        assert len(N) == 8
        assert np.isclose(np.sum(N), 1.0)

    def test_shape_function_derivatives(self, unit_element):
        xi = np.array([0, 0, 0])
        dN = unit_element.shape_function_derivatives_q1(xi)
        assert dN.shape == (8, 3)

    def test_compute_b_matrix(self, unit_element):
        xi = np.array([0, 0, 0])
        B, detJ = unit_element.compute_b_matrix(xi)
        assert B.shape == (6, 24)
        assert detJ > 0

    def test_compute_divergence_operator(self, unit_element):
        xi = np.array([0, 0, 0])
        div = unit_element.compute_divergence_operator(xi)
        assert len(div) == 24


class TestElasticity3D:
    @pytest.fixture
    def small_pattern(self):
        return Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, E=1e6, nu=0.3))

    def test_init(self, small_pattern):
        assert small_pattern.nodes is not None
        assert len(small_pattern.elements) > 0
        assert small_pattern.displacements is not None
        assert small_pattern.pressures is not None

    def test_pattern_id(self):
        assert Elasticity3D.PATTERN_ID == "elasticity_3d_mixed"
        assert Elasticity3D.PATTERN_VERSION == "6.5.0"

    def test_compute_material_matrix(self, small_pattern):
        assert small_pattern.mu > 0
        assert small_pattern.K > 0
        assert small_pattern.D.shape == (6, 6)

    def test_initialize_mesh(self, small_pattern):
        nx, ny, nz = small_pattern.config.nx, small_pattern.config.ny, small_pattern.config.nz
        expected_nodes = (nx + 1) * (ny + 1) * (nz + 1)
        assert len(small_pattern.nodes) == expected_nodes
        assert len(small_pattern.elements) == nx * ny * nz

    def test_apply_boundary_conditions(self, small_pattern):
        assert len(small_pattern.fixed_dofs) > 0

    def test_assemble_system(self, small_pattern):
        K, G, C, f = small_pattern._assemble_system()
        assert K.shape[0] == len(small_pattern.nodes) * 3
        assert G.shape[0] == len(small_pattern.elements)
        assert C.shape[0] == len(small_pattern.elements)
        assert len(f) == len(small_pattern.nodes) * 3

    def test_compute_load_vector_compression(self, small_pattern):
        f = small_pattern._compute_load_vector()
        assert len(f) == len(small_pattern.nodes) * 3
        assert np.any(f != 0)

    def test_compute_load_vector_shear(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, load_type="shear"))
        f = pattern._compute_load_vector()
        assert np.any(f != 0)

    def test_solve_mixed_system(self, small_pattern):
        u, p = small_pattern._solve_mixed_system()
        assert len(u) == len(small_pattern.nodes) * 3
        assert len(p) == len(small_pattern.elements)

    def test_compute_stresses(self, small_pattern):
        small_pattern.displacements, small_pattern.pressures = small_pattern._solve_mixed_system()
        stresses = small_pattern._compute_stresses()
        assert stresses.shape[0] == len(small_pattern.elements)
        assert stresses.shape[1] == 6

    def test_compute_strain_energy(self, small_pattern):
        small_pattern.displacements, small_pattern.pressures = small_pattern._solve_mixed_system()
        energy = small_pattern._compute_strain_energy()
        assert energy >= 0

    def test_run(self, small_pattern):
        result = small_pattern.run()
        assert "displacements" in result
        assert "pressures" in result
        assert "stresses" in result
        assert "von_mises_stress" in result
        assert "max_displacement" in result
        assert "strain_energy" in result
        assert result["n_elements"] == len(small_pattern.elements)
        assert result["formulation"] == "mixed_up"

    def test_run_incompressible(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, nu=0.49))
        result = pattern.run()
        assert result["locking_ratio"] == pytest.approx(0.98)
        assert result["max_displacement"] > 0

    def test_metadata(self):
        metadata = Elasticity3D.get_metadata()
        assert metadata["pattern_id"] == "elasticity_3d_mixed"
        assert "parameters" in metadata
