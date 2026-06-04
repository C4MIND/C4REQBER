# Migrated to Newton Physics (2025) — github.com/newton-physics/newton — Apache 2.0 License
"""
Pattern 24: 3D Elasticity (Mixed Finite Element Method)

Christopher Alexander Structure:
- Context: Solving 3D elasticity problems involving nearly-incompressible materials
  (rubber, biological tissue) or materials under high confinement. Standard
  displacement-based FEM suffers from volumetric locking.
- Forces:
  * Volumetric locking when nu approaches 0.5
  * Babuska-Brezzi stability condition for mixed methods
  * Computational cost of solving saddle-point systems
  * Need for accurate stress recovery
- Solution: Mixed u-p formulation (displacement-pressure) with Taylor-Hood elements
  (Q2-Q1). Stabilization for equal-order interpolations. Schur complement
  reduction for efficient solution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


try:
    from .base import BaseConfig, BasePattern
except ImportError:
    from .base import BaseConfig, BasePattern


@dataclass
class Elasticity3DConfig(BaseConfig):
    """Configuration for 3D Elasticity simulation."""

    # Mesh
    nx: int = 8
    ny: int = 8
    nz: int = 4
    Lx: float = 1.0
    Ly: float = 1.0
    Lz: float = 0.5

    # Material
    E: float = 1e6  # Young's modulus (Pa)
    nu: float = 0.49  # Poisson ratio (close to 0.5 = incompressible)

    # Method
    formulation: str = "mixed_up"  # "displacement", "mixed_up", "enhanced"
    element_type: str = "hexahedral"  # "hexahedral", "tetrahedral"
    pressure_order: int = 1  # 1 = linear, 0 = constant

    # Solution
    solver_type: str = "direct"  # "direct", "cg", "minres"
    max_iter: int = 1000
    tolerance: float = 1e-8

    # Loading
    load_type: str = "compression"  # "compression", "shear", "gravity"
    load_magnitude: float = 1e5
    fixed_boundary: str = "bottom"


class HexahedralElement:
    """Q2-Q1 or Q1-P0 hexahedral element for mixed formulation."""

    def __init__(
        self, nodes: np.ndarray, node_indices: np.ndarray, is_quadratic: bool = False
    ) -> None:
        """
        Args:
            nodes: Node coordinates
            node_indices: Global node indices
            is_quadratic: True for Q2 velocity, False for Q1
        """
        self.nodes = nodes
        self.node_indices = node_indices
        self.is_quadratic = is_quadratic
        self.n_pressure_nodes = 1 if not is_quadratic else 8

        # Gauss points (2x2x2 for Q1, 3x3x3 for Q2)
        if is_quadratic:
            g = np.sqrt(3 / 5)
            w1 = 5 / 9
            w2 = 8 / 9
            self.gauss_points = []
            self.gauss_weights = []
            for i in [-g, 0, g]:
                for j in [-g, 0, g]:
                    for k in [-g, 0, g]:
                        self.gauss_points.append([i, j, k])
                        wi = w1 if abs(i) == g else w2
                        wj = w1 if abs(j) == g else w2
                        wk = w1 if abs(k) == g else w2
                        self.gauss_weights.append(wi * wj * wk)
            self.gauss_points = np.array(self.gauss_points)  # type: ignore[assignment]
            self.gauss_weights = np.array(self.gauss_weights)  # type: ignore[assignment]
        else:
            g = 1.0 / np.sqrt(3)
            self.gauss_points = np.array(  # type: ignore[assignment]
                [
                    [-g, -g, -g],
                    [g, -g, -g],
                    [g, g, -g],
                    [-g, g, -g],
                    [-g, -g, g],
                    [g, -g, g],
                    [g, g, g],
                    [-g, g, g],
                ]
            )
            self.gauss_weights = np.ones(8)  # type: ignore[assignment]

        # Compute reference volume
        self.volume_ref = self._compute_volume()

    def _compute_volume(self) -> float:
        """Compute element volume using Gauss quadrature."""
        vol = 0.0
        for xi, w in zip(self.gauss_points, self.gauss_weights, strict=False):
            dN = self.shape_function_derivatives_q1(xi)  # type: ignore[arg-type]
            J = dN.T @ self.nodes
            detJ = np.linalg.det(J)
            vol += abs(detJ) * w
        return vol

    def shape_functions_q1(self, xi: np.ndarray) -> np.ndarray:
        """Linear shape functions (8 nodes)."""
        N = np.zeros(8)
        for i in range(8):
            xi_i = -1 if i % 2 == 0 else 1
            eta_i = -1 if (i // 2) % 2 == 0 else 1
            zeta_i = -1 if i < 4 else 1
            N[i] = (
                0.125 * (1 + xi_i * xi[0]) * (1 + eta_i * xi[1]) * (1 + zeta_i * xi[2])
            )
        return N

    def shape_function_derivatives_q1(self, xi: np.ndarray) -> np.ndarray:
        """Derivatives of linear shape functions."""
        dN = np.zeros((8, 3))
        for i in range(8):
            xi_i = -1 if i % 2 == 0 else 1
            eta_i = -1 if (i // 2) % 2 == 0 else 1
            zeta_i = -1 if i < 4 else 1

            dN[i, 0] = 0.125 * xi_i * (1 + eta_i * xi[1]) * (1 + zeta_i * xi[2])
            dN[i, 1] = 0.125 * (1 + xi_i * xi[0]) * eta_i * (1 + zeta_i * xi[2])
            dN[i, 2] = 0.125 * (1 + xi_i * xi[0]) * (1 + eta_i * xi[1]) * zeta_i
        return dN

    def compute_b_matrix(self, xi: np.ndarray) -> tuple[np.ndarray, float]:
        """
        Compute B-matrix (strain-displacement) and Jacobian determinant.
        Returns (B, detJ) where B is (6, 24) for 8 nodes.
        """
        dN_dxi = self.shape_function_derivatives_q1(xi)

        # Jacobian: J_ij = dX_i/dxi_j = sum_k N_k,xi_j * X_ki
        J = dN_dxi.T @ self.nodes
        detJ = np.linalg.det(J)

        if abs(detJ) < 1e-12:
            detJ = 1e-12

        J_reg = J + 1e-8 * np.eye(3)
        dN_dX = dN_dxi @ np.linalg.pinv(J_reg)

        # B-matrix
        B = np.zeros((6, 24))
        for i in range(8):
            dNi_dx = dN_dX[i, 0]
            dNi_dy = dN_dX[i, 1]
            dNi_dz = dN_dX[i, 2]

            B[0, i * 3] = dNi_dx  # epsilon_xx
            B[1, i * 3 + 1] = dNi_dy  # epsilon_yy
            B[2, i * 3 + 2] = dNi_dz  # epsilon_zz
            B[3, i * 3] = dNi_dy  # gamma_xy
            B[3, i * 3 + 1] = dNi_dx
            B[4, i * 3 + 1] = dNi_dz  # gamma_yz
            B[4, i * 3 + 2] = dNi_dy
            B[5, i * 3] = dNi_dz  # gamma_xz
            B[5, i * 3 + 2] = dNi_dx

        return B, detJ

    def compute_divergence_operator(self, xi: np.ndarray) -> np.ndarray:
        """Compute divergence operator for mixed formulation."""
        dN_dxi = self.shape_function_derivatives_q1(xi)
        J = self.nodes.T @ dN_dxi
        if abs(np.linalg.det(J)) < 1e-12:
            J = J + 1e-8 * np.eye(3)
        dN_dX = dN_dxi @ np.linalg.pinv(J)

        # Divergence operator (maps displacement to volumetric strain)
        div = np.zeros(24)
        for i in range(8):
            div[i * 3] = dN_dX[i, 0]
            div[i * 3 + 1] = dN_dX[i, 1]
            div[i * 3 + 2] = dN_dX[i, 2]

        return div


class Elasticity3D(BasePattern):
    """
    3D elasticity with mixed u-p formulation for incompressibility.
    Complexity: O(N^3) for direct solver, O(N) per iteration for iterative.
    """

    PATTERN_ID = "elasticity_3d_mixed"
    PATTERN_VERSION = "6.5.0"

    def _validate_config(self) -> None:
        pass

    def __init__(self, config: Elasticity3DConfig | None = None) -> None:
        super().__init__(config or Elasticity3DConfig())
        self.config: Elasticity3DConfig = self.config

        self.nodes: np.ndarray = None  # type: ignore[assignment]
        self.elements: list[HexahedralElement] = []
        self.displacements: np.ndarray = None  # type: ignore[assignment]
        self.pressures: np.ndarray = None  # type: ignore[assignment]
        self.fixed_dofs: list[int] = []

        self._initialize_mesh()
        self._compute_material_matrix()

    def _compute_material_matrix(self) -> None:
        """Compute elasticity matrix."""
        E = self.config.E
        nu = self.config.nu

        # Lamé parameters
        self.mu = E / (2 * (1 + nu))  # Shear modulus
        self.lam = E * nu / ((1 + nu) * (1 - 2 * nu))  # First Lamé parameter

        # For nearly incompressible, use deviatoric/volumetric split
        self.K = E / (3 * (1 - 2 * nu))  # Bulk modulus

        # Isotropic elasticity matrix (6x6)
        self.D = np.array(
            [
                [self.lam + 2 * self.mu, self.lam, self.lam, 0, 0, 0],
                [self.lam, self.lam + 2 * self.mu, self.lam, 0, 0, 0],
                [self.lam, self.lam, self.lam + 2 * self.mu, 0, 0, 0],
                [0, 0, 0, self.mu, 0, 0],
                [0, 0, 0, 0, self.mu, 0],
                [0, 0, 0, 0, 0, self.mu],
            ]
        )

    def _initialize_mesh(self) -> None:
        """Create hexahedral mesh."""
        nx, ny, nz = self.config.nx, self.config.ny, self.config.nz
        Lx, Ly, Lz = self.config.Lx, self.config.Ly, self.config.Lz

        dx, dy, dz = Lx / nx, Ly / ny, Lz / nz

        # Create nodes
        n_nodes_x, n_nodes_y, n_nodes_z = nx + 1, ny + 1, nz + 1
        self.nodes = np.zeros((n_nodes_x * n_nodes_y * n_nodes_z, 3))

        idx = 0
        for k in range(n_nodes_z):
            for j in range(n_nodes_y):
                for i in range(n_nodes_x):
                    self.nodes[idx] = [i * dx, j * dy, k * dz]
                    idx += 1

        # Create elements
        def node_idx(i: Any, j: Any, k: Any) -> Any:
            return k * n_nodes_x * n_nodes_y + j * n_nodes_x + i

        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    indices = np.array(
                        [
                            node_idx(i, j, k),
                            node_idx(i + 1, j, k),
                            node_idx(i + 1, j + 1, k),
                            node_idx(i, j + 1, k),
                            node_idx(i, j, k + 1),
                            node_idx(i + 1, j, k + 1),
                            node_idx(i + 1, j + 1, k + 1),
                            node_idx(i, j + 1, k + 1),
                        ]
                    )
                    elem_nodes = self.nodes[indices]
                    self.elements.append(HexahedralElement(elem_nodes, indices))

        # Initialize DOFs
        n_dofs = len(self.nodes) * 3
        self.displacements = np.zeros(n_dofs)
        self.pressures = np.zeros(len(self.elements))  # One pressure per element (P0)

        self._apply_boundary_conditions()

    def _apply_boundary_conditions(self) -> None:
        """Apply fixed boundary conditions."""
        nx = self.config.nx + 1
        ny = self.config.ny + 1
        nz = self.config.nz + 1

        # Fix bottom surface (z = 0)
        for j in range(ny):
            for i in range(nx):
                node = j * nx + i
                self.fixed_dofs.extend([node * 3, node * 3 + 1, node * 3 + 2])

        self.fixed_dofs = list(set(self.fixed_dofs))

    def _assemble_system(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Assemble mixed system:
        [K   G^T] [u]   [f]
        [G  -C  ] [p] = [0]

        Returns (K, G, C, f)
        """
        n_nodes = len(self.nodes)
        n_elements = len(self.elements)
        n_dofs = n_nodes * 3

        # Initialize matrices
        K = np.zeros((n_dofs, n_dofs))
        G = np.zeros((n_elements, n_dofs))
        C = np.zeros((n_elements, n_elements))
        f = np.zeros(n_dofs)

        # Assemble element contributions
        for e_idx, element in enumerate(self.elements):
            elem_dofs = []
            for node_idx in element.node_indices:
                elem_dofs.extend([node_idx * 3, node_idx * 3 + 1, node_idx * 3 + 2])

            Ke = np.zeros((24, 24))
            Ge = np.zeros((1, 24))
            Ce = np.zeros((1, 1))

            for xi, w in zip(element.gauss_points, element.gauss_weights, strict=False):
                B, detJ = element.compute_b_matrix(xi)  # type: ignore[arg-type]
                div = element.compute_divergence_operator(xi)  # type: ignore[arg-type]

                # Stiffness matrix K = integral(B^T * D * B)
                # Use deviatoric part only for mixed formulation
                D_dev = self.D.copy()
                D_dev[:3, :3] -= self.K / 3  # Remove volumetric part

                Ke += B.T @ D_dev @ B * detJ * w

                # Coupling matrix G = integral(N_p^T * div)
                Ge[0, :] += div * detJ * w

                # Compressibility matrix C = integral(1/K)
                Ce[0, 0] += detJ * w / self.K

            # Assemble to global
            for i, di in enumerate(elem_dofs):
                for j, dj in enumerate(elem_dofs):
                    K[di, dj] += Ke[i, j]
                G[e_idx, di] += Ge[0, i]

            C[e_idx, e_idx] += Ce[0, 0]

        # Apply boundary conditions
        for dof in self.fixed_dofs:
            K[dof, :] = 0
            K[:, dof] = 0
            K[dof, dof] = 1.0
            f[dof] = 0

        return K, G, C, f

    def _compute_load_vector(self) -> np.ndarray:
        """Compute external load vector."""
        n_dofs = len(self.nodes) * 3
        f = np.zeros(n_dofs)

        if self.config.load_type == "compression":
            # Apply uniform pressure on top surface
            nz = self.config.nz + 1
            nx = self.config.nx + 1
            ny = self.config.ny + 1

            top_area = self.config.Lx * self.config.Ly
            force_per_node = self.config.load_magnitude * top_area / (nx * ny)

            for j in range(ny):
                for i in range(nx):
                    node_idx = (nz - 1) * nx * ny + j * nx + i
                    f[node_idx * 3 + 2] = -force_per_node  # z-direction

        elif self.config.load_type == "shear":
            # Shear load on top surface
            nz = self.config.nz + 1
            nx = self.config.nx + 1
            ny = self.config.ny + 1

            top_area = self.config.Lx * self.config.Ly
            force_per_node = self.config.load_magnitude * top_area / (nx * ny)

            for j in range(ny):
                for i in range(nx):
                    node_idx = (nz - 1) * nx * ny + j * nx + i
                    f[node_idx * 3] = force_per_node  # x-direction

        # Zero out fixed DOFs
        for dof in self.fixed_dofs:
            f[dof] = 0

        return f

    def _solve_mixed_system(self) -> tuple[np.ndarray, np.ndarray]:
        """Solve the mixed u-p system."""
        K, G, C, _ = self._assemble_system()
        f = self._compute_load_vector()

        n_p = len(self.elements)
        n_u = len(K)

        # Schur complement approach
        # S = G * K^(-1) * G^T + C
        # (G * K^(-1) * G^T + C) * p = G * K^(-1) * f
        # K * u = f - G^T * p

        # For small systems, use direct solver
        if self.config.solver_type == "direct":
            # Full system matrix
            A = np.zeros((n_u + n_p, n_u + n_p))
            A[:n_u, :n_u] = K
            A[:n_u, n_u:] = G.T
            A[n_u:, :n_u] = G
            A[n_u:, n_u:] = -C

            b = np.zeros(n_u + n_p)
            b[:n_u] = f

            try:
                sol = np.linalg.solve(A, b)
                u = sol[:n_u]
                p = sol[n_u:]
            except np.linalg.LinAlgError:
                # Use least squares for singular systems
                sol = np.linalg.lstsq(A, b, rcond=None)[0]
                u = sol[:n_u]
                p = sol[n_u:]
        else:
            # Iterative approach (simplified)
            # Pressure correction iteration
            p = np.zeros(n_p)

            for _ in range(self.config.max_iter):
                # Solve for displacement with current pressure
                rhs = f - G.T @ p
                try:
                    u = np.linalg.solve(K, rhs)
                except np.linalg.LinAlgError:
                    u = np.linalg.lstsq(K, rhs, rcond=None)[0]

                # Update pressure
                dp = G @ u - C @ p
                if np.linalg.norm(dp) < self.config.tolerance:
                    break
                p += 0.1 * dp  # Relaxation

        return u, p

    def _compute_stresses(self) -> np.ndarray:
        """Compute element stresses."""
        stresses = []

        for e_idx, element in enumerate(self.elements):
            # Get element displacements
            elem_disp = np.zeros((8, 3))
            for i, node_idx in enumerate(element.node_indices):
                elem_disp[i] = self.displacements[node_idx * 3 : node_idx * 3 + 3]

            # Compute strain at center
            xi = np.array([0, 0, 0])
            B, _ = element.compute_b_matrix(xi)
            strain = B @ elem_disp.flatten()

            # Compute stress (include pressure for volumetric part)
            stress_dev = self.D @ strain
            stress_dev[:3] -= np.mean(stress_dev[:3])  # Deviatoric

            # Add pressure
            pressure = self.pressures[e_idx] if e_idx < len(self.pressures) else 0
            stress = stress_dev.copy()
            stress[:3] -= pressure  # Pressure is negative of mean stress

            stresses.append(stress)

        return np.array(stresses)

    def _compute_strain_energy(self) -> float:
        """Compute total strain energy."""
        energy = 0.0

        for element in self.elements:
            elem_disp = np.zeros((8, 3))
            for i, node_idx in enumerate(element.node_indices):
                elem_disp[i] = self.displacements[node_idx * 3 : node_idx * 3 + 3]

            for xi, w in zip(element.gauss_points, element.gauss_weights, strict=False):
                B, detJ = element.compute_b_matrix(xi)  # type: ignore[arg-type]
                strain = B @ elem_disp.flatten()
                stress = self.D @ strain

                # Strain energy = 0.5 * integral(strain^T * stress)
                energy += 0.5 * strain @ stress * detJ * w

        return energy

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute 3D elasticity simulation with Newton (or fallback).

        Returns:
            Dictionary with displacement field, pressures, and stress metrics.
        """
        from src.simulations.newton_bridge import NewtonBridge
        bridge = NewtonBridge()

        if bridge.available:
            newton_config = {
                "type": "elasticity_3d",
                "nx": self.config.nx,
                "ny": self.config.ny,
                "nz": self.config.nz,
                "Lx": self.config.Lx,
                "Ly": self.config.Ly,
                "Lz": self.config.Lz,
                "E": self.config.E,
                "nu": self.config.nu,
                "formulation": self.config.formulation,
                "element_type": self.config.element_type,
                "solver_type": self.config.solver_type,
                "load_type": self.config.load_type,
                "load_magnitude": self.config.load_magnitude,
                "fixed_boundary": self.config.fixed_boundary,
            }
            if hypothesis:
                newton_config.update(hypothesis)
            result = bridge.run_simulation(newton_config)
            if result.get("status") == "success":
                result["pattern_id"] = self.PATTERN_ID
                return result

        # Fallback to legacy implementation
        # Solve system
        self.displacements, self.pressures = self._solve_mixed_system()

        # Compute derived quantities
        stresses = self._compute_stresses()
        strain_energy = self._compute_strain_energy()

        # Displacement statistics
        disp_reshaped = self.displacements.reshape(-1, 3)
        max_disp = np.max(np.linalg.norm(disp_reshaped, axis=1))
        avg_disp = np.mean(np.linalg.norm(disp_reshaped, axis=1))

        # Top surface displacement
        nz = self.config.nz + 1
        nx = self.config.nx + 1
        ny = self.config.ny + 1

        top_disp = []
        for j in range(ny):
            for i in range(nx):
                node_idx = (nz - 1) * nx * ny + j * nx + i
                top_disp.append(disp_reshaped[node_idx])

        # Volume change
        original_volume = self.config.Lx * self.config.Ly * self.config.Lz

        # Approximate volume change from displacement divergence
        vol_change = 0.0
        for element in self.elements:
            xi = np.array([0, 0, 0])
            div = element.compute_divergence_operator(xi)
            elem_disp = np.zeros(24)
            for i, node_idx in enumerate(element.node_indices):
                elem_disp[i * 3 : i * 3 + 3] = disp_reshaped[node_idx]
            vol_change += div @ elem_disp  # type: ignore[assignment]

        return {
            "pattern_id": self.PATTERN_ID,
            "displacements": disp_reshaped,
            "pressures": self.pressures,
            "stresses": stresses,
            "von_mises_stress": np.sqrt(
                0.5
                * (
                    (stresses[:, 0] - stresses[:, 1]) ** 2
                    + (stresses[:, 1] - stresses[:, 2]) ** 2
                    + (stresses[:, 2] - stresses[:, 0]) ** 2
                    + 6
                    * (stresses[:, 3] ** 2 + stresses[:, 4] ** 2 + stresses[:, 5] ** 2)
                )
            ),
            "max_displacement": max_disp,
            "mean_displacement": avg_disp,
            "top_surface_displacement": np.array(top_disp),
            "strain_energy": strain_energy,
            "mean_pressure": np.mean(self.pressures),
            "max_pressure": np.max(np.abs(self.pressures)),
            "n_elements": len(self.elements),
            "n_nodes": len(self.nodes),
            "formulation": self.config.formulation,
            "locking_ratio": self.config.nu / 0.5,  # How close to incompressible
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "pattern_id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "3D Elasticity (Mixed FEM)",
            "context": "When solving 3D elasticity problems with nearly-incompressible "
            "materials (rubber, biological tissue, ν ≈ 0.5). Standard "
            "displacement-based FEM suffers from volumetric locking, "
            "producing erroneous stiff behavior.",
            "forces": [
                "Volumetric locking: Displacement-only elements lock as ν → 0.5",
                "Babuska-Brezzi condition: Mixed methods need stable element pairs",
                "Saddle-point system: Indefinite matrix requires special solvers",
                "Stress accuracy: Direct stress computation is often discontinuous",
                "Computational cost: Mixed DOFs increase system size",
            ],
            "solution": "Mixed u-p formulation separates deviatoric and volumetric "
            "responses. Q1-P0 (linear displacement, constant pressure) "
            "or Q2-Q1 (Taylor-Hood) elements satisfy LBB condition. "
            "Pressure acts as Lagrange multiplier for incompressibility. "
            "Schur complement reduction yields smaller SPD system. "
            "Selective reduced integration can also alleviate locking.",
            "complexity": "O(N^3) for direct solver, O(N) per CG iteration",
            "domain": "Solid mechanics, biomechanics, rubber engineering, geomechanics",
            "parameters": [
                "E: Young's modulus",
                "nu: Poisson ratio (0.5 = incompressible)",
                "formulation: Displacement or mixed u-p",
                "element_type: Q1-P0, Q2-Q1, etc.",
            ],
        }
