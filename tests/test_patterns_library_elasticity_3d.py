"""Tests for src/patterns/library/elasticity_3d.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from patterns.library.elasticity_3d import (
    Elasticity3D,
    Elasticity3DConfig,
    HexahedralElement,
)


class TestElasticity3DConfig:
    def test_defaults(self):
        cfg = Elasticity3DConfig()
        assert cfg.nx == 8
        assert cfg.ny == 8
        assert cfg.nz == 4
        assert cfg.E == 1e6
        assert cfg.nu == 0.49
        assert cfg.formulation == "mixed_up"

    def test_custom_values(self):
        cfg = Elasticity3DConfig(nx=4, ny=4, nz=2, E=2e6, nu=0.3)
        assert cfg.nx == 4
        assert cfg.ny == 4
        assert cfg.nz == 2
        assert cfg.E == 2e6
        assert cfg.nu == 0.3


class TestHexahedralElement:
    def test_init_q1(self):
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=float)
        indices = np.arange(8)
        elem = HexahedralElement(nodes, indices, is_quadratic=False)
        assert elem.n_pressure_nodes == 1
        assert elem.volume_ref > 0

    def test_init_q2(self):
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=float)
        indices = np.arange(8)
        elem = HexahedralElement(nodes, indices, is_quadratic=True)
        assert elem.n_pressure_nodes == 8
        assert elem.volume_ref > 0

    def test_shape_functions_q1(self):
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=float)
        elem = HexahedralElement(nodes, np.arange(8))
        N = elem.shape_functions_q1(np.array([0.0, 0.0, 0.0]))
        assert len(N) == 8
        assert np.isclose(np.sum(N), 1.0)

    def test_shape_function_derivatives_q1(self):
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=float)
        elem = HexahedralElement(nodes, np.arange(8))
        dN = elem.shape_function_derivatives_q1(np.array([0.0, 0.0, 0.0]))
        assert dN.shape == (8, 3)

    def test_compute_b_matrix(self):
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=float)
        elem = HexahedralElement(nodes, np.arange(8))
        B, detJ = elem.compute_b_matrix(np.array([0.0, 0.0, 0.0]))
        assert B.shape == (6, 24)
        assert detJ > 0

    def test_compute_divergence_operator(self):
        nodes = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=float)
        elem = HexahedralElement(nodes, np.arange(8))
        div = elem.compute_divergence_operator(np.array([0.0, 0.0, 0.0]))
        assert len(div) == 24


class TestElasticity3DInit:
    def test_init_default(self):
        pattern = Elasticity3D()
        assert pattern.config is not None
        assert len(pattern.elements) > 0
        assert pattern.nodes is not None
        assert pattern.displacements is not None
        assert pattern.pressures is not None

    def test_init_custom(self):
        cfg = Elasticity3DConfig(nx=2, ny=2, nz=1)
        pattern = Elasticity3D(cfg)
        assert len(pattern.nodes) == 3 * 3 * 2
        assert len(pattern.elements) == 2 * 2 * 1

    def test_material_properties(self):
        pattern = Elasticity3D()
        assert pattern.mu > 0
        assert pattern.lam > 0
        assert pattern.K > 0
        assert pattern.D.shape == (6, 6)


class TestElasticity3DBoundaryConditions:
    def test_fixed_dofs(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1))
        assert len(pattern.fixed_dofs) > 0


class TestElasticity3DLoadVector:
    def test_compression_load(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, load_type="compression"))
        f = pattern._compute_load_vector()
        assert len(f) == len(pattern.nodes) * 3
        assert np.any(f != 0)

    def test_shear_load(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, load_type="shear"))
        f = pattern._compute_load_vector()
        assert len(f) == len(pattern.nodes) * 3
        assert np.any(f != 0)

    def test_unknown_load(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, load_type="unknown"))
        f = pattern._compute_load_vector()
        assert len(f) == len(pattern.nodes) * 3


class TestElasticity3DAssembly:
    def test_assemble_system(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1))
        K, G, C, f = pattern._assemble_system()
        assert K.shape[0] == len(pattern.nodes) * 3
        assert G.shape[0] == len(pattern.elements)
        assert C.shape[0] == len(pattern.elements)
        assert len(f) == len(pattern.nodes) * 3


class TestElasticity3DSolve:
    def test_solve_mixed_system_direct(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, solver_type="direct"))
        u, p = pattern._solve_mixed_system()
        assert len(u) == len(pattern.nodes) * 3
        assert len(p) == len(pattern.elements)

    def test_solve_mixed_system_iterative(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, solver_type="cg", max_iter=10))
        u, p = pattern._solve_mixed_system()
        assert len(u) == len(pattern.nodes) * 3
        assert len(p) == len(pattern.elements)

    def test_solve_singular_fallback(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, solver_type="direct"))
        with patch("numpy.linalg.solve", side_effect=np.linalg.LinAlgError("singular")):
            u, p = pattern._solve_mixed_system()
            assert len(u) == len(pattern.nodes) * 3


class TestElasticity3DStresses:
    def test_compute_stresses(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1))
        pattern.displacements = np.random.randn(len(pattern.displacements)) * 0.01
        pattern.pressures = np.random.randn(len(pattern.pressures)) * 0.01
        stresses = pattern._compute_stresses()
        assert stresses.shape == (len(pattern.elements), 6)


class TestElasticity3DStrainEnergy:
    def test_compute_strain_energy(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1))
        pattern.displacements = np.random.randn(len(pattern.displacements)) * 0.01
        energy = pattern._compute_strain_energy()
        assert np.isfinite(energy)


class TestElasticity3DRun:
    def test_run_default(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1))
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = False
            mock_cls.return_value = mock_bridge
            result = pattern.run()
        assert result["pattern_id"] == "elasticity_3d_mixed"
        assert "displacements" in result
        assert "pressures" in result
        assert "stresses" in result
        assert "von_mises_stress" in result
        assert "strain_energy" in result

    def test_run_with_newton_bridge(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1))
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = True
            mock_bridge.run_simulation = MagicMock(return_value={"status": "success", "displacements": []})
            mock_cls.return_value = mock_bridge
            result = pattern.run()
            assert result.get("status") == "success"

    def test_run_with_newton_bridge_fallback(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1))
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = True
            mock_bridge.run_simulation = MagicMock(return_value={"status": "error"})
            mock_cls.return_value = mock_bridge
            result = pattern.run()
            assert result["pattern_id"] == "elasticity_3d_mixed"

    def test_run_nearly_incompressible(self):
        pattern = Elasticity3D(Elasticity3DConfig(nx=2, ny=2, nz=1, nu=0.499))
        with patch("src.simulations.newton_bridge.NewtonBridge") as mock_cls:
            mock_bridge = MagicMock()
            mock_bridge.available = False
            mock_cls.return_value = mock_bridge
            result = pattern.run()
        assert result["locking_ratio"] > 0.99


class TestElasticity3DMetadata:
    def test_get_metadata(self):
        meta = Elasticity3D.get_metadata()
        assert meta["pattern_id"] == "elasticity_3d_mixed"
        assert "context" in meta
        assert "forces" in meta
        assert "solution" in meta
        assert "parameters" in meta
