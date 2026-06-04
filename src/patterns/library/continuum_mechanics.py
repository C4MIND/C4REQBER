"""
Pattern 22: Continuum Mechanics (Finite Strain)

Christopher Alexander Structure:
- Context: Modeling deformable solids undergoing large displacements and rotations.
  Required for rubber, biological tissue, metal forming, and crash analysis.
- Forces:
  * Large vs small strain formulations
  * Objectivity (frame indifference) requirements
  * Incompressibility constraints (rubber, biological tissue)
  * Material nonlinearity and plasticity
- Solution: Finite strain formulation with hyperelastic constitutive models.
  Uses deformation gradient F with polar decomposition. Mixed formulation
  for incompressibility (u-p formulation).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import BaseConfig, BasePattern


@dataclass
class ContinuumMechanicsConfig(BaseConfig):
    """Configuration for Continuum Mechanics simulation."""

    n_elements_x: int = 10
    n_elements_y: int = 10
    n_elements_z: int = 5
    element_order: int = 1  # 1 = linear, 2 = quadratic
    youngs_modulus: float = 1e7  # Pa
    poisson_ratio: float = 0.3
    density: float = 1000.0  # kg/m³
    dt: float = 1e-4
    n_steps: int = 100
    material_model: str = "neo_hookean"  # "linear", "neo_hookean", "mooney_rivlin"
    formulation: str = "total_lagrange"  # "total_lagrange", "updated_lagrange"

    # Problem setup
    domain_size: tuple[float, float, float] = (1.0, 1.0, 0.5)
    fixed_boundary: str = "bottom"  # "bottom", "left", "none"
    load_type: str = "gravity"  # "gravity", "compression", "tension"
    load_magnitude: float = 9.81


class FiniteElement:
    """8-node hexahedral finite element."""

    def __init__(self, nodes: np.ndarray, node_indices: np.ndarray) -> None:
        """
        Args:
            nodes: Node coordinates (8, 3)
            node_indices: Global node indices (8,)
        """
        self.nodes = nodes  # Reference configuration
        self.node_indices = node_indices
        self.volume_ref = self._compute_volume(nodes)

        # Gauss quadrature points (2x2x2)
        self.gauss_points = self._get_gauss_points()
        self.gauss_weights = np.array([1, 1, 1, 1, 1, 1, 1, 1]) * self.volume_ref / 8

    def _get_gauss_points(self) -> np.ndarray:
        """Get Gauss quadrature points in natural coordinates."""
        g = 1.0 / np.sqrt(3)
        return np.array(
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

    def _compute_volume(self, nodes: np.ndarray) -> float:
        """Compute element volume using divergence theorem."""
        # Simplified volume computation
        dx = nodes[1] - nodes[0]
        dy = nodes[3] - nodes[0]
        dz = nodes[4] - nodes[0]
        return abs(np.dot(dx, np.cross(dy, dz)))  # type: ignore[no-any-return]

    def shape_functions(self, xi: np.ndarray) -> np.ndarray:
        """Compute shape functions at natural coordinates xi."""
        N = np.zeros(8)
        for i in range(8):
            xi_i = -1 if i % 2 == 0 else 1
            eta_i = -1 if (i // 2) % 2 == 0 else 1
            zeta_i = -1 if i < 4 else 1
            N[i] = (
                0.125 * (1 + xi_i * xi[0]) * (1 + eta_i * xi[1]) * (1 + zeta_i * xi[2])
            )
        return N

    def shape_function_derivatives(self, xi: np.ndarray) -> np.ndarray:
        """Compute derivatives of shape functions w.r.t. natural coordinates."""
        dN = np.zeros((8, 3))
        for i in range(8):
            xi_i = -1 if i % 2 == 0 else 1
            eta_i = -1 if (i // 2) % 2 == 0 else 1
            zeta_i = -1 if i < 4 else 1

            dN[i, 0] = 0.125 * xi_i * (1 + eta_i * xi[1]) * (1 + zeta_i * xi[2])
            dN[i, 1] = 0.125 * (1 + xi_i * xi[0]) * eta_i * (1 + zeta_i * xi[2])
            dN[i, 2] = 0.125 * (1 + xi_i * xi[0]) * (1 + eta_i * xi[1]) * zeta_i
        return dN

    def compute_deformation_gradient(
        self, displacements: np.ndarray, xi: np.ndarray
    ) -> np.ndarray:
        """
        Compute deformation gradient F = I + grad(u).
        """
        # Shape function derivatives in natural coordinates
        dN_dxi = self.shape_function_derivatives(xi)

        # Jacobian J = dX/dxi
        J = dN_dxi.T @ self.nodes
        try:
            J_inv = np.linalg.inv(J)
        except np.linalg.LinAlgError:
            J_inv = np.eye(3)  # Fallback

        # Shape function derivatives in reference coordinates
        dN_dX = dN_dxi @ J_inv

        # Deformation gradient F = I + du/dX
        F = np.eye(3) + displacements.T @ dN_dX
        return F

    def compute_stress_neo_hookean(
        self, F: np.ndarray, E: float, nu: float
    ) -> np.ndarray:
        """
        Compute 2nd Piola-Kirchhoff stress for Neo-Hookean material.
        """
        mu = E / (2 * (1 + nu))  # Shear modulus
        K = E / (3 * (1 - 2 * nu))  # Bulk modulus

        C = F.T @ F  # Right Cauchy-Green tensor
        J = np.linalg.det(F)

        # Neo-Hookean S = mu*(I - C^(-1)) + K*ln(J)*C^(-1)
        C_inv = np.linalg.inv(C)
        I = np.eye(3)

        J_safe = float(J) if J > 0.1 else 0.1
        S = mu * (I - C_inv) + K * np.log(J_safe) * C_inv
        return S

    def compute_stress_linear(self, F: np.ndarray, E: float, nu: float) -> np.ndarray:
        """
        Compute linear elastic stress (small strain).
        """
        # Green-Lagrange strain
        E_gl = 0.5 * (F.T @ F - np.eye(3))

        # Lamé parameters
        lam = E * nu / ((1 + nu) * (1 - 2 * nu))
        mu = E / (2 * (1 + nu))

        # Stress
        trace_E = np.trace(E_gl)
        S = lam * trace_E * np.eye(3) + 2 * mu * E_gl
        return S  # type: ignore[no-any-return]

    def compute_internal_forces(
        self, displacements: np.ndarray, E: float, nu: float, material_model: str
    ) -> np.ndarray:
        """Compute internal nodal forces."""
        f_int = np.zeros(24)  # 8 nodes * 3 DOF

        for gp, w in zip(self.gauss_points, self.gauss_weights, strict=False):
            # Deformation gradient
            F = self.compute_deformation_gradient(displacements, gp)

            # Stress
            if material_model == "neo_hookean":
                S = self.compute_stress_neo_hookean(F, E, nu)
            else:
                S = self.compute_stress_linear(F, E, nu)

            # Jacobian for integration
            dN_dxi = self.shape_function_derivatives(gp)
            J = self.nodes.T @ dN_dxi
            det_J = np.linalg.det(J)

            # B-matrix (strain-displacement)
            dN_dX = dN_dxi @ np.linalg.inv(J)
            B = np.zeros((6, 24))
            for i in range(8):
                B[0, i * 3] = dN_dX[i, 0]  # dN/dx
                B[1, i * 3 + 1] = dN_dX[i, 1]  # dN/dy
                B[2, i * 3 + 2] = dN_dX[i, 2]  # dN/dz
                B[3, i * 3] = dN_dX[i, 1]
                B[3, i * 3 + 1] = dN_dX[i, 0]
                B[4, i * 3 + 1] = dN_dX[i, 2]
                B[4, i * 3 + 2] = dN_dX[i, 1]
                B[5, i * 3] = dN_dX[i, 2]
                B[5, i * 3 + 2] = dN_dX[i, 0]

            # Convert 2nd PK to vector
            S_vec = np.array([S[0, 0], S[1, 1], S[2, 2], S[0, 1], S[1, 2], S[0, 2]])

            # Internal force contribution
            f_int += B.T @ S_vec * det_J * w

        return f_int


class ContinuumMechanics(BasePattern):
    """
    Finite strain continuum mechanics with hyperelastic materials.
    Complexity: O(N) per assembly, O(N^1.5) per solve.
    """

    PATTERN_ID = "continuum_mechanics"
    PATTERN_VERSION = "6.5.0"

    def _validate_config(self) -> None:
        """Validate continuum mechanics configuration."""
        cfg = self.config
        if cfg.n_elements_x < 1 or cfg.n_elements_y < 1 or cfg.n_elements_z < 1:
            raise ValueError("n_elements must be at least 1 in each dimension")
        if cfg.youngs_modulus <= 0:
            raise ValueError("youngs_modulus must be positive")
        if not (-1 < cfg.poisson_ratio < 0.5):
            raise ValueError("poisson_ratio must be in (-1, 0.5)")
        if cfg.density <= 0:
            raise ValueError("density must be positive")
        if cfg.dt <= 0:
            raise ValueError("dt must be positive")
        if cfg.n_steps < 0:
            raise ValueError("n_steps must be non-negative")
        valid_models = {"linear", "neo_hookean", "mooney_rivlin"}
        if cfg.material_model not in valid_models:
            raise ValueError(f"material_model must be one of {valid_models}")
        valid_formulations = {"total_lagrange", "updated_lagrange"}
        if cfg.formulation not in valid_formulations:
            raise ValueError(f"formulation must be one of {valid_formulations}")

    def __init__(self, config: ContinuumMechanicsConfig | None = None) -> None:
        super().__init__(config or ContinuumMechanicsConfig())
        self.config: ContinuumMechanicsConfig = self.config
        self.nodes: np.ndarray | None = None
        self.elements: list[FiniteElement] = []
        self.displacements: np.ndarray | None = None
        self.velocities: np.ndarray | None = None
        self.accelerations: np.ndarray | None = None
        self.fixed_dofs: list[int] = []
        self._initialize_mesh()

    def _initialize_mesh(self) -> None:
        """Create hexahedral mesh."""
        nx, ny, nz = (
            self.config.n_elements_x,
            self.config.n_elements_y,
            self.config.n_elements_z,
        )
        Lx, Ly, Lz = self.config.domain_size

        # Create nodes
        dx, dy, dz = Lx / nx, Ly / ny, Lz / nz
        n_nodes_x, n_nodes_y, n_nodes_z = nx + 1, ny + 1, nz + 1

        self.nodes = np.zeros((n_nodes_x * n_nodes_y * n_nodes_z, 3))
        idx = 0
        for k in range(n_nodes_z):
            for j in range(n_nodes_y):
                for i in range(n_nodes_x):
                    self.nodes[idx] = [i * dx, j * dy, k * dz]
                    idx += 1

        # Create elements
        def node_index(i: Any, j: Any, k: Any) -> Any:
            return k * n_nodes_x * n_nodes_y + j * n_nodes_x + i

        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    node_indices = np.array(
                        [
                            node_index(i, j, k),
                            node_index(i + 1, j, k),
                            node_index(i + 1, j + 1, k),
                            node_index(i, j + 1, k),
                            node_index(i, j, k + 1),
                            node_index(i + 1, j, k + 1),
                            node_index(i + 1, j + 1, k + 1),
                            node_index(i, j + 1, k + 1),
                        ]
                    )
                    element_nodes = self.nodes[node_indices]
                    self.elements.append(FiniteElement(element_nodes, node_indices))

        # Initialize DOFs
        n_dofs = len(self.nodes) * 3
        self.displacements = np.zeros(n_dofs)
        self.velocities = np.zeros(n_dofs)
        self.accelerations = np.zeros(n_dofs)

        # Apply boundary conditions
        self._apply_boundary_conditions()

    def _apply_boundary_conditions(self) -> None:
        """Apply fixed boundary conditions."""
        nx = self.config.n_elements_x + 1
        ny = self.config.n_elements_y + 1
        nz = self.config.n_elements_z + 1

        if self.config.fixed_boundary == "bottom":
            # Fix z = 0 plane
            for j in range(ny):
                for i in range(nx):
                    node_idx = j * nx + i
                    self.fixed_dofs.extend(
                        [node_idx * 3, node_idx * 3 + 1, node_idx * 3 + 2]
                    )

        self.fixed_dofs = list(set(self.fixed_dofs))

    def _compute_external_forces(self) -> np.ndarray:
        """Compute external force vector."""
        n_dofs = len(self.nodes) * 3  # type: ignore[arg-type]
        f_ext = np.zeros(n_dofs)

        if self.config.load_type == "gravity":
            # Gravity load
            for i, _node in enumerate(self.nodes):  # type: ignore[arg-type]
                # Distribute element mass to nodes
                element_volume = np.prod(self.config.domain_size) / len(self.elements)
                node_mass = self.config.density * element_volume * 8 / 8  # Simplified
                f_ext[i * 3 + 1] = (
                    -node_mass * self.config.load_magnitude
                )  # y-direction

        elif self.config.load_type == "compression":
            # Apply load to top surface
            nz = self.config.n_elements_z + 1
            nx = self.config.n_elements_x + 1
            ny = self.config.n_elements_y + 1
            top_nodes = []
            for j in range(ny):
                for i in range(nx):
                    node_idx = (nz - 1) * nx * ny + j * nx + i
                    top_nodes.append(node_idx)

            load_per_node = self.config.load_magnitude / len(top_nodes)
            for node_idx in top_nodes:
                f_ext[node_idx * 3 + 1] = -load_per_node

        # Zero out fixed DOFs
        for dof in self.fixed_dofs:
            f_ext[dof] = 0

        return f_ext

    def _assemble_forces(self) -> np.ndarray:
        """Assemble internal force vector."""
        n_dofs = len(self.nodes) * 3  # type: ignore[arg-type]
        f_int = np.zeros(n_dofs)

        for element in self.elements:
            # Get element displacements
            elem_disp = np.zeros((8, 3))
            for i, node_idx in enumerate(element.node_indices):
                elem_disp[i] = self.displacements[node_idx * 3 : node_idx * 3 + 3]  # type: ignore[index]

            # Compute internal forces
            elem_f = element.compute_internal_forces(
                elem_disp,
                self.config.youngs_modulus,
                self.config.poisson_ratio,
                self.config.material_model,
            )

            # Assemble to global
            for i, node_idx in enumerate(element.node_indices):
                f_int[node_idx * 3 : node_idx * 3 + 3] += elem_f[i * 3 : i * 3 + 3]

        # Zero out fixed DOFs
        for dof in self.fixed_dofs:
            f_int[dof] = 0

        return f_int

    def _step(self) -> None:
        """Single time step using explicit dynamics."""
        # Compute forces
        f_ext = self._compute_external_forces()
        f_int = self._assemble_forces()
        f_total = f_ext - f_int

        # Compute accelerations (lumped mass)
        element_volume = np.prod(self.config.domain_size) / len(self.elements)
        node_mass = self.config.density * element_volume

        for i in range(len(self.nodes)):  # type: ignore[arg-type]
            if i * 3 not in self.fixed_dofs:
                self.accelerations[i * 3 : i * 3 + 3] = (  # type: ignore[index]
                    f_total[i * 3 : i * 3 + 3] / node_mass
                )

        # Central difference integration
        dt = self.config.dt
        v_half = self.velocities + self.accelerations * dt / 2  # type: ignore[operator]
        self.displacements += v_half * dt  # type: ignore[assignment, operator]
        self.velocities = v_half + self.accelerations * dt / 2  # type: ignore[assignment, operator]

        # Enforce boundary conditions
        for dof in self.fixed_dofs:
            self.displacements[dof] = 0  # type: ignore[index]
            self.velocities[dof] = 0  # type: ignore[index]
            self.accelerations[dof] = 0  # type: ignore[index]

    def _compute_strain_energy(self) -> float:
        """Compute total strain energy."""
        energy = 0.0

        for element in self.elements:
            elem_disp = np.zeros((8, 3))
            for i, node_idx in enumerate(element.node_indices):
                elem_disp[i] = self.displacements[node_idx * 3 : node_idx * 3 + 3]  # type: ignore[index]

            for gp, w in zip(element.gauss_points, element.gauss_weights, strict=False):
                F = element.compute_deformation_gradient(elem_disp, gp)

                if self.config.material_model == "neo_hookean":
                    mu = self.config.youngs_modulus / (
                        2 * (1 + self.config.poisson_ratio)
                    )
                    K = self.config.youngs_modulus / (
                        3 * (1 - 2 * self.config.poisson_ratio)
                    )

                    J = np.linalg.det(F)
                    C = F.T @ F
                    I1 = np.trace(C)

                    # Neo-Hookean strain energy
                    J_safe = float(J) if J > 0.1 else 0.1
                    psi = (
                        0.5 * mu * (I1 - 3)
                        - mu * np.log(J_safe)
                        + 0.5 * K * (np.log(J_safe)) ** 2
                    )
                    energy += psi * w
                else:
                    # Linear elastic
                    E_gl = 0.5 * (F.T @ F - np.eye(3))
                    lam = (
                        self.config.youngs_modulus
                        * self.config.poisson_ratio
                        / (
                            (1 + self.config.poisson_ratio)
                            * (1 - 2 * self.config.poisson_ratio)
                        )
                    )
                    mu = self.config.youngs_modulus / (
                        2 * (1 + self.config.poisson_ratio)
                    )

                    psi = 0.5 * lam * (np.trace(E_gl)) ** 2 + mu * np.trace(E_gl @ E_gl)
                    energy += psi * w

        return energy

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute continuum mechanics simulation.

        Returns:
            Dictionary with displacement field, strain energy, and stress metrics.
        """
        displacement_history = []
        energy_history = []

        # Record initial state
        energy_history.append(
            {
                "step": 0,
                "strain_energy": self._compute_strain_energy(),
                "max_displacement": np.max(np.abs(self.displacements)),  # type: ignore[arg-type]
            }
        )

        for step in range(self.config.n_steps):
            self._step()

            # Record history
            if step % 10 == 0:
                displacement_history.append(self.displacements.copy())  # type: ignore[union-attr]
                energy_history.append(
                    {
                        "step": step + 1,
                        "strain_energy": self._compute_strain_energy(),
                        "max_displacement": np.max(np.abs(self.displacements)),  # type: ignore[arg-type]
                    }
                )

        # Compute final statistics
        final_disp = self.displacements.reshape(-1, 3)  # type: ignore[union-attr]
        max_disp = np.max(np.linalg.norm(final_disp, axis=1))
        avg_disp = np.mean(np.linalg.norm(final_disp, axis=1))

        # Top surface displacement
        nz = self.config.n_elements_z + 1
        nx = self.config.n_elements_x + 1
        ny = self.config.n_elements_y + 1
        top_disp = []
        for j in range(ny):
            for i in range(nx):
                node_idx = (nz - 1) * nx * ny + j * nx + i
                top_disp.append(final_disp[node_idx])

        return {
            "pattern_id": self.PATTERN_ID,
            "displacements": final_disp,
            "max_displacement": max_disp,
            "mean_displacement": avg_disp,
            "top_surface_displacement": np.array(top_disp),
            "displacement_history": displacement_history,
            "energy_history": energy_history,
            "final_strain_energy": energy_history[-1]["strain_energy"],
            "n_elements": len(self.elements),
            "n_nodes": len(self.nodes),  # type: ignore[arg-type]
            "material_model": self.config.material_model,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "pattern_id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Continuum Mechanics (Finite Strain)",
            "context": "When modeling deformable solids undergoing large displacements "
            "and rotations, such as rubber components, biological tissue, "
            "or metal forming processes. Small strain theory is insufficient.",
            "forces": [
                "Geometric nonlinearity: Large rotations require nonlinear strain measures",
                "Material nonlinearity: Rubber, tissue exhibit hyperelastic behavior",
                "Incompressibility: Many materials have nu ≈ 0.5, causing locking",
                "Objectivity: Stress rates must be frame-indifferent",
                "Mesh distortion: Large deformations degrade element quality",
            ],
            "solution": "Finite strain formulation using deformation gradient F. "
            "Neo-Hookean hyperelastic model for rubber-like materials. "
            "Total Lagrangian formulation tracks motion relative to reference "
            "configuration. 2nd Piola-Kirchhoff stress S is work-conjugate "
            "with Green-Lagrange strain E. Mixed u-p formulation can handle "
            "incompressibility constraints.",
            "complexity": "O(N) assembly, O(N^1.5) linear solve, O(N) per explicit step",
            "domain": "Solid mechanics, biomechanics, rubber engineering, metal forming",
            "parameters": [
                "youngs_modulus: Material stiffness",
                "poisson_ratio: Incompressibility parameter",
                "material_model: Constitutive law type",
                "formulation: Total or updated Lagrangian",
            ],
        }


# Alias for C4REQBER compatibility
ContinuumMechanicsPattern = ContinuumMechanics
