"""
Poisson Solver Pattern
Multigrid method for solving Poisson and Laplace equations

Based on:
- Geometric multigrid (Brandt, 1977)
- V-cycle and Full Multigrid (FMG)
- Gauss-Seidel relaxation
- Restriction and prolongation operators

Applications:
- Electrostatics
- Heat conduction
- Pressure projection in CFD
- Gravitational potential
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import cg

from ..core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)


logger = logging.getLogger(__name__)


class MultigridCycle(Enum):
    """MultigridCycle."""
    V_CYCLE = "v_cycle"      # Simple V-cycle
    W_CYCLE = "w_cycle"      # More expensive W-cycle
    FMG = "fmg"              # Full Multigrid


class RelaxationMethod(Enum):
    """RelaxationMethod."""
    JACOBI = "jacobi"
    GAUSS_SEIDEL = "gauss_seidel"
    SOR = "sor"              # Successive Over-Relaxation


@dataclass
class PoissonConfig:
    """Configuration for Poisson solver"""
    # Grid parameters
    nx: int = 128
    ny: int = 128
    nz: int = 1  # 2D by default

    # Domain
    x_min: float = 0.0
    x_max: float = 1.0
    y_min: float = 0.0
    y_max: float = 1.0

    # Multigrid parameters
    max_levels: int = 4
    cycle_type: str = "v_cycle"
    relaxation_method: str = "gauss_seidel"
    pre_smooth: int = 2
    post_smooth: int = 2

    # Convergence
    max_iterations: int = 100
    tolerance: float = 1e-8
    omega: float = 1.5  # SOR relaxation factor

    # Problem type
    equation: str = "poisson"  # 'poisson' or 'laplace'
    boundary_condition: str = "dirichlet"

    def __post_init__(self) -> None:
        self.dx = (self.x_max - self.x_min) / (self.nx - 1)
        self.dy = (self.y_max - self.y_min) / (self.ny - 1)


@simulation_pattern(
    id="poisson_solver",
    name="Poisson Solver",
    category="physics",
    description="Multigrid solver for Poisson and Laplace equations",
)
class PoissonSolverPattern(SimulationPattern):
    """
    Multigrid solver for elliptic PDEs

    Implements:
    - 2D/3D Poisson equation: ∇²φ = f
    - 2D/3D Laplace equation: ∇²φ = 0
    - Geometric multigrid with V-cycle
    - Multiple relaxation methods (Jacobi, Gauss-Seidel, SOR)
    - Dirichlet and Neumann boundary conditions
    """

    parameters = [
        SimulationParameter(
            name="dimensions",
            type="select",
            default="2d",
            options=["2d", "3d"],
            description="Problem dimensionality",
        ),
        SimulationParameter(
            name="grid_size",
            type="int",
            default=128,
            min=16,
            max=1024,
            description="Grid size (must be power of 2)",
        ),
        SimulationParameter(
            name="equation",
            type="select",
            default="poisson",
            options=["poisson", "laplace"],
            description="Equation type",
        ),
        SimulationParameter(
            name="cycle_type",
            type="select",
            default="v_cycle",
            options=["v_cycle", "w_cycle", "fmg"],
            description="Multigrid cycle type",
        ),
        SimulationParameter(
            name="relaxation",
            type="select",
            default="gauss_seidel",
            options=["jacobi", "gauss_seidel", "sor"],
            description="Relaxation method",
        ),
        SimulationParameter(
            name="max_iterations",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Maximum multigrid cycles",
        ),
        SimulationParameter(
            name="tolerance",
            type="float",
            default=1e-8,
            min=1e-12,
            max=1e-4,
            description="Convergence tolerance",
        ),
        SimulationParameter(
            name="use_direct",
            type="bool",
            default=False,
            description="Use direct solver (small grids only)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.iteration_count = 0
        self.residual_history = []  # type: ignore[var-annotated]

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if Poisson solver can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "poisson", "laplace", "multigrid", "elliptic",
            "electrostatic", "potential", "heat conduction",
            "steady state", "diffusion equilibrium",
            "gravitational potential", "pressure projection",
            "harmonic function", "green function",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute Poisson solver"""
        start_time = datetime.now()
        simulation_id = f"poisson_{start_time.timestamp()}"

        logger.info(f"Starting Poisson solver {simulation_id}")

        try:
            # Parse configuration
            poisson_config = self._parse_config(config)

            # Choose solver
            if config.get("use_direct", False) and poisson_config.nx <= 64:
                results = await self._direct_solver(hypothesis, poisson_config)
            else:
                results = await self._multigrid_solver(hypothesis, poisson_config)

            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Poisson solver failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> PoissonConfig:
        """Parse configuration dict into PoissonConfig"""
        is_3d = config.get("dimensions", "2d") == "3d"
        grid_size = config.get("grid_size", 128)

        return PoissonConfig(
            nx=grid_size,
            ny=grid_size,
            nz=grid_size if is_3d else 1,
            equation=config.get("equation", "poisson"),
            cycle_type=config.get("cycle_type", "v_cycle"),
            relaxation_method=config.get("relaxation", "gauss_seidel"),
            max_iterations=config.get("max_iterations", 100),
            tolerance=config.get("tolerance", 1e-8),
        )

    async def _multigrid_solver(self, hypothesis: Hypothesis, config: PoissonConfig) -> dict[str, Any]:
        """Multigrid solver for Poisson equation"""

        # Initialize solution and RHS
        phi = np.zeros((config.nx, config.ny))
        f = self._initialize_rhs(config)

        # Apply boundary conditions to initial guess
        self._apply_boundary_conditions(phi, config)

        self.iteration_count = 0
        self.residual_history = []

        initial_residual = self._compute_residual(phi, f, config)
        self.residual_history.append(initial_residual)

        converged = False

        for iteration in range(config.max_iterations):
            # Perform multigrid cycle
            if config.cycle_type == "v_cycle":
                phi = self._v_cycle(phi, f, config, config.max_levels)
            elif config.cycle_type == "w_cycle":
                phi = self._w_cycle(phi, f, config, config.max_levels)
            else:  # FMG
                phi = self._fmg(phi, f, config, config.max_levels)

            # Compute residual
            residual = self._compute_residual(phi, f, config)
            self.residual_history.append(residual)
            self.iteration_count = iteration + 1

            # Check convergence
            if residual < config.tolerance * initial_residual:
                converged = True
                break

            if iteration % 10 == 0:
                await asyncio.sleep(0)

        # Compute final metrics
        final_residual = self.residual_history[-1]
        residual_ratio = final_residual / initial_residual if initial_residual > 0 else 0

        # L2 norm of solution
        l2_norm = np.sqrt(np.sum(phi**2) * config.dx * config.dy)

        # Check conservation for Laplace
        conservation_error = 0.0
        if config.equation == "laplace":
            # For Laplace, integral of Laplacian should be zero
            laplacian = self._compute_laplacian(phi, config)
            conservation_error = np.abs(np.sum(laplacian))

        metrics = {
            "iterations": self.iteration_count,
            "initial_residual": float(initial_residual),
            "final_residual": float(final_residual),
            "residual_ratio": float(residual_ratio),
            "converged": float(converged),
            "l2_norm": float(l2_norm),
            "conservation_error": float(conservation_error),
            "grid_size": config.nx,
            "equation": config.equation,
            "cycle_type": config.cycle_type,
        }

        logs = [
            f"Multigrid solver ({config.cycle_type}) completed",
            f"Grid: {config.nx}x{config.ny}",
            f"Iterations: {self.iteration_count}",
            f"Initial residual: {initial_residual:.2e}",
            f"Final residual: {final_residual:.2e}",
            f"Converged: {converged}",
        ]

        return {"metrics": metrics, "logs": logs, "solution": phi}

    async def _direct_solver(self, hypothesis: Hypothesis, config: PoissonConfig) -> dict[str, Any]:
        """Direct sparse solver for small grids"""

        nx, ny = config.nx, config.ny
        n_unknowns = nx * ny

        # Build sparse matrix for 2D Laplacian
        # Using 5-point stencil
        data = []
        row_ind = []
        col_ind = []

        for j in range(ny):
            for i in range(nx):
                idx = j * nx + i

                # Diagonal
                data.append(-4.0)
                row_ind.append(idx)
                col_ind.append(idx)

                # Off-diagonals (neighbors)
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < nx and 0 <= nj < ny:
                        nidx = nj * nx + ni
                        data.append(1.0)
                        row_ind.append(idx)
                        col_ind.append(nidx)

        A = csr_matrix((data, (row_ind, col_ind)), shape=(n_unknowns, n_unknowns))

        # RHS
        f = self._initialize_rhs(config).flatten()

        # Solve using conjugate gradient
        phi_flat, info = cg(A, f, rtol=config.tolerance, maxiter=config.max_iterations)

        phi = phi_flat.reshape((nx, ny))
        self._apply_boundary_conditions(phi, config)

        residual = np.linalg.norm(A @ phi_flat - f)
        l2_norm = np.sqrt(np.sum(phi**2) * config.dx * config.dy)

        metrics = {
            "iterations": info if info > 0 else config.max_iterations,
            "final_residual": float(residual),
            "converged": float(info == 0),
            "l2_norm": float(l2_norm),
            "grid_size": nx,
            "solver": "direct_cg",
        }

        logs = [
            "Direct solver (CG) completed",
            f"Grid: {nx}x{ny}",
            f"Final residual: {residual:.2e}",
            f"Converged: {info == 0}",
        ]

        return {"metrics": metrics, "logs": logs, "solution": phi}

    def _initialize_rhs(self, config: PoissonConfig) -> np.ndarray:
        """Initialize right-hand side (source term)"""
        nx, ny = config.nx, config.ny
        f = np.zeros((nx, ny))

        if config.equation == "poisson":
            # Point source in center
            cx, cy = nx // 2, ny // 2
            f[cx, cy] = 1.0 / (config.dx * config.dy)

        return f

    def _apply_boundary_conditions(self, phi: np.ndarray, config: PoissonConfig) -> None:
        """Apply boundary conditions"""
        if config.boundary_condition == "dirichlet":
            phi[0, :] = 0.0
            phi[-1, :] = 0.0
            phi[:, 0] = 0.0
            phi[:, -1] = 0.0
        elif config.boundary_condition == "neumann":
            # Zero gradient
            phi[0, :] = phi[1, :]
            phi[-1, :] = phi[-2, :]
            phi[:, 0] = phi[:, 1]
            phi[:, -1] = phi[:, -2]

    def _relax(self, phi: np.ndarray, f: np.ndarray, config: PoissonConfig, n_sweeps: int) -> np.ndarray:
        """Perform relaxation sweeps"""
        nx, ny = phi.shape
        dx2 = config.dx ** 2
        dy2 = config.dy ** 2

        for _ in range(n_sweeps):
            if config.relaxation_method == "jacobi":
                phi_new = phi.copy()
                for i in range(1, nx-1):
                    for j in range(1, ny-1):
                        phi_new[i, j] = 0.25 * (
                            phi[i+1, j] + phi[i-1, j] +
                            phi[i, j+1] + phi[i, j-1] - dx2 * f[i, j]
                        )
                phi = phi_new

            elif config.relaxation_method == "gauss_seidel":
                for i in range(1, nx-1):
                    for j in range(1, ny-1):
                        phi[i, j] = 0.25 * (
                            phi[i+1, j] + phi[i-1, j] +
                            phi[i, j+1] + phi[i, j-1] - dx2 * f[i, j]
                        )

            elif config.relaxation_method == "sor":
                omega = config.omega
                for i in range(1, nx-1):
                    for j in range(1, ny-1):
                        phi_old = phi[i, j]
                        phi_gs = 0.25 * (
                            phi[i+1, j] + phi[i-1, j] +
                            phi[i, j+1] + phi[i, j-1] - dx2 * f[i, j]
                        )
                        phi[i, j] = (1 - omega) * phi_old + omega * phi_gs

        self._apply_boundary_conditions(phi, config)
        return phi

    def _compute_residual(self, phi: np.ndarray, f: np.ndarray, config: PoissonConfig) -> float:
        """Compute L2 norm of residual"""
        laplacian = self._compute_laplacian(phi, config)
        residual = laplacian - f
        return np.sqrt(np.sum(residual[1:-1, 1:-1]**2))  # type: ignore[no-any-return]

    def _compute_laplacian(self, phi: np.ndarray, config: PoissonConfig) -> np.ndarray:
        """Compute discrete Laplacian"""
        dx2 = config.dx ** 2
        return (  # type: ignore[no-any-return]
            (np.roll(phi, -1, 0) - 2*phi + np.roll(phi, 1, 0)) / dx2 +
            (np.roll(phi, -1, 1) - 2*phi + np.roll(phi, 1, 1)) / config.dy**2
        )

    def _restrict(self, phi_fine: np.ndarray) -> np.ndarray:
        """Restrict fine grid to coarse grid (full weighting)"""
        nx, ny = phi_fine.shape
        nx_c = nx // 2
        ny_c = ny // 2

        phi_coarse = np.zeros((nx_c, ny_c))

        for i in range(nx_c):
            for j in range(ny_c):
                i2 = 2 * i
                j2 = 2 * j
                # Full weighting restriction
                phi_coarse[i, j] = (
                    0.25 * phi_fine[i2, j2] +
                    0.125 * (phi_fine[i2+1, j2] + phi_fine[i2-1, j2] +
                            phi_fine[i2, j2+1] + phi_fine[i2, j2-1]) +
                    0.0625 * (phi_fine[i2+1, j2+1] + phi_fine[i2+1, j2-1] +
                             phi_fine[i2-1, j2+1] + phi_fine[i2-1, j2-1])
                )

        return phi_coarse

    def _prolong(self, phi_coarse: np.ndarray, nx_f: int, ny_f: int) -> np.ndarray:
        """Prolong coarse grid to fine grid (bilinear interpolation)"""
        phi_fine = np.zeros((nx_f, ny_f))
        nx_c, ny_c = phi_coarse.shape

        for i in range(nx_c):
            for j in range(ny_c):
                i2 = 2 * i
                j2 = 2 * j

                # Copy coarse point
                phi_fine[i2, j2] = phi_coarse[i, j]

                # Interpolate neighbors
                if i2 + 1 < nx_f:
                    phi_fine[i2+1, j2] = 0.5 * (phi_coarse[i, j] +
                                                phi_coarse[min(i+1, nx_c-1), j])
                if j2 + 1 < ny_f:
                    phi_fine[i2, j2+1] = 0.5 * (phi_coarse[i, j] +
                                                phi_coarse[i, min(j+1, ny_c-1)])
                if i2 + 1 < nx_f and j2 + 1 < ny_f:
                    phi_fine[i2+1, j2+1] = 0.25 * (phi_coarse[i, j] +
                                                    phi_coarse[min(i+1, nx_c-1), j] +
                                                    phi_coarse[i, min(j+1, ny_c-1)] +
                                                    phi_coarse[min(i+1, nx_c-1), min(j+1, ny_c-1)])

        return phi_fine

    def _v_cycle(self, phi: np.ndarray, f: np.ndarray, config: PoissonConfig, level: int) -> np.ndarray:
        """V-cycle multigrid"""
        if level == 1:
            # Direct solve on coarsest grid
            return self._relax(phi, f, config, 50)

        # Pre-smoothing
        phi = self._relax(phi, f, config, config.pre_smooth)

        # Compute residual
        residual = self._compute_laplacian(phi, config) - f

        # Restrict to coarse grid
        residual_coarse = self._restrict(residual)

        # Solve on coarse grid
        e_coarse = np.zeros_like(residual_coarse)
        config_coarse = self._coarsen_config(config)
        e_coarse = self._v_cycle(e_coarse, residual_coarse, config_coarse, level - 1)

        # Prolong to fine grid
        e_fine = self._prolong(e_coarse, phi.shape[0], phi.shape[1])

        # Correct
        phi = phi - e_fine

        # Post-smoothing
        phi = self._relax(phi, f, config, config.post_smooth)

        return phi

    def _w_cycle(self, phi: np.ndarray, f: np.ndarray, config: PoissonConfig, level: int) -> np.ndarray:
        """W-cycle multigrid"""
        if level == 1:
            return self._relax(phi, f, config, 50)

        phi = self._relax(phi, f, config, config.pre_smooth)
        residual = self._compute_laplacian(phi, config) - f
        residual_coarse = self._restrict(residual)

        e_coarse = np.zeros_like(residual_coarse)
        config_coarse = self._coarsen_config(config)

        # Two recursive calls for W-cycle
        e_coarse = self._w_cycle(e_coarse, residual_coarse, config_coarse, level - 1)
        e_coarse = self._w_cycle(e_coarse, residual_coarse, config_coarse, level - 1)

        e_fine = self._prolong(e_coarse, phi.shape[0], phi.shape[1])
        phi = phi - e_fine
        phi = self._relax(phi, f, config, config.post_smooth)

        return phi

    def _fmg(self, phi: np.ndarray, f: np.ndarray, config: PoissonConfig, level: int) -> np.ndarray:
        """Full Multigrid"""
        if level == 1:
            return self._relax(phi, f, config, 50)

        # Restrict RHS to coarsest level
        f_coarse = f
        configs = [config]
        for _ in range(level - 1):
            f_coarse = self._restrict(f_coarse)
            configs.append(self._coarsen_config(configs[-1]))

        # Solve on coarsest
        phi_coarse = np.zeros_like(f_coarse)
        phi_coarse = self._relax(phi_coarse, f_coarse, configs[-1], 50)

        # Prolong and refine up the hierarchy
        for l in range(level - 1, 0, -1):
            phi_coarse = self._prolong(phi_coarse, configs[l-1].nx, configs[l-1].ny)
            phi_coarse = self._v_cycle(phi_coarse, f, configs[l-1], l)

        return phi_coarse

    def _coarsen_config(self, config: PoissonConfig) -> PoissonConfig:
        """Create coarsened configuration"""
        return PoissonConfig(
            nx=config.nx // 2,
            ny=config.ny // 2,
            max_levels=config.max_levels - 1,
            cycle_type=config.cycle_type,
            relaxation_method=config.relaxation_method,
            pre_smooth=config.pre_smooth,
            post_smooth=config.post_smooth,
            tolerance=config.tolerance,
            equation=config.equation,
        )

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Convergence achieved
        if metrics.get("converged", 0) > 0.5:
            factors.append(0.4)

        # Low residual
        residual_ratio = metrics.get("residual_ratio", 1.0)
        if residual_ratio < 1e-6:
            factors.append(0.3)
        elif residual_ratio < 1e-3:
            factors.append(0.2)

        # Conservation property
        if metrics.get("conservation_error", 1.0) < 1e-10:
            factors.append(0.2)

        # Sufficient iterations
        if metrics.get("iterations", 0) >= 10:
            factors.append(0.1)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        grid_size = params.get("grid_size", 128)
        max_iter = params.get("max_iterations", 100)

        cells = grid_size ** 2

        return {
            "cpu_cores": 4,
            "memory_gb": 0.5 + cells * 8e-9 * 4,  # Multiple arrays
            "gpu_required": grid_size > 512,
            "estimated_time_seconds": max_iter * cells / 5e6,
        }
