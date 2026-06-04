"""
C4REQBER v6.0 - Crystal Growth Pattern
Phase-field model for simulating microstructure evolution during solidification.

Pattern Structure (Christopher Alexander):
- Context: Materials processing, alloy design, crystal engineering
- Forces: Interface tracking, anisotropy, thermal diffusion
- Solution: Phase-field method with implicit interface representation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class CrystalSymmetry(Enum):
    """Crystal symmetry types"""

    ISOTROPIC = "isotropic"
    CUBIC = "cubic"
    HEXAGONAL = "hexagonal"
    TETRAGONAL = "tetragonal"


class NucleationModel(Enum):
    """Nucleation models"""

    HOMOGENEOUS = "homogeneous"
    HETEROGENEOUS = "heterogeneous"
    PREDEFINED = "predefined"


@dataclass
class CrystalGrowthConfig:
    """Configuration for crystal growth simulation"""

    # Grid parameters
    nx: int = 128  # Grid points in x
    ny: int = 128  # Grid points in y
    dx: float = 0.5  # Grid spacing (μm)

    # Time parameters
    dt: float = 0.001  # Time step
    n_steps: int = 5000  # Number of steps
    output_interval: int = 500

    # Phase-field parameters
    epsilon: float = 0.5  # Interface width parameter
    tau: float = 0.0003  # Relaxation time
    m: float = 0.02  # Mobility

    # Thermal parameters
    T_melt: float = 1000.0  # Melting temperature (K)
    T_initial: float = 950.0  # Initial undercooled temperature (K)
    alpha: float = 1.0  # Thermal diffusivity
    latent_heat: float = 1.0  # Latent heat release

    # Anisotropy
    symmetry: CrystalSymmetry = CrystalSymmetry.CUBIC
    anisotropy_strength: float = 0.05  # Anisotropy coefficient (0-0.1)
    anisotropy_mode: int = 4  # Number of anisotropy modes

    # Nucleation
    nucleation_model: NucleationModel = NucleationModel.HETEROGENEOUS
    n_nuclei: int = 5  # Number of initial nuclei
    nucleation_radius: float = 2.0  # Initial nucleus radius

    # Noise for side-branching
    thermal_noise: bool = True
    noise_amplitude: float = 0.01


class CrystalGrowthPattern:
    """
    Phase-field model for dendritic crystal growth.

    Implements the Allen-Cahn / Cahn-Hilliard type phase-field equation:
    τ(∂φ/∂t) = ε²∇²φ + φ(1-φ²) - λ(1-φ²)²(T - Tm)

    with anisotropic surface energy and thermal diffusion.
    """

    PATTERN_ID = "crystal_growth"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: CrystalGrowthConfig | None = None) -> None:
        self.config = config or CrystalGrowthConfig()

        # Fields
        self.phi: np.ndarray | None = None  # Phase field (liquid=-1, solid=+1)
        self.T: np.ndarray | None = None  # Temperature field

        # History
        self.phi_history: list[np.ndarray] = []
        self.T_history: list[np.ndarray] = []
        self.time_history: list[float] = []

        self._initialize_system()

    def _initialize_system(self) -> None:
        """Initialize phase and temperature fields"""
        cfg = self.config

        # Initialize phase field (liquid = -1)
        self.phi = -np.ones((cfg.ny, cfg.nx))

        # Initialize temperature (uniform undercooling)
        self.T = np.ones((cfg.ny, cfg.nx)) * cfg.T_initial

        # Create initial nuclei
        self._create_nuclei()

    def _create_nuclei(self) -> None:
        """Create initial solid nuclei"""
        cfg = self.config

        # Random or predefined nucleation sites
        np.random.seed(42)

        for _ in range(cfg.n_nuclei):
            if cfg.nucleation_model == NucleationModel.HETEROGENEOUS:
                # Place near edges or corners for interesting growth
                if np.random.rand() > 0.5:
                    x = np.random.choice([5, cfg.nx - 5])
                    y = np.random.randint(10, cfg.ny - 10)
                else:
                    x = np.random.randint(10, cfg.nx - 10)
                    y = np.random.choice([5, cfg.ny - 5])
            else:
                x = np.random.randint(20, cfg.nx - 20)
                y = np.random.randint(20, cfg.ny - 20)

            # Create circular nucleus
            Y, X = np.ogrid[: cfg.ny, : cfg.nx]
            r = np.sqrt((X - x) ** 2 + (Y - y) ** 2) * cfg.dx

            # Smooth interface using tanh profile
            self.phi[r <= cfg.nucleation_radius] = np.tanh(  # type: ignore[index]
                (cfg.nucleation_radius - r[r <= cfg.nucleation_radius]) / cfg.epsilon
            )

    def _anisotropy_function(self, theta: np.ndarray) -> np.ndarray:
        """Calculate anisotropy factor based on orientation"""
        cfg = self.config

        if cfg.symmetry == CrystalSymmetry.ISOTROPIC:
            return np.ones_like(theta)

        elif cfg.symmetry == CrystalSymmetry.CUBIC:
            # 4-fold symmetry
            return 1.0 + cfg.anisotropy_strength * np.cos(cfg.anisotropy_mode * theta)  # type: ignore[no-any-return]

        elif cfg.symmetry == CrystalSymmetry.HEXAGONAL:
            # 6-fold symmetry
            return 1.0 + cfg.anisotropy_strength * np.cos(6 * theta)  # type: ignore[no-any-return]

        elif cfg.symmetry == CrystalSymmetry.TETRAGONAL:
            # 4-fold with different strength
            return 1.0 + cfg.anisotropy_strength * np.cos(4 * theta)  # type: ignore[no-any-return]

        return np.ones_like(theta)  # type: ignore[unreachable]

    def _gradient(self, field: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Calculate gradient of field (central differences)"""
        cfg = self.config

        # Periodic boundaries
        dx = cfg.dx

        # x-derivative
        dfdx = np.zeros_like(field)
        dfdx[:, 1:-1] = (field[:, 2:] - field[:, :-2]) / (2 * dx)
        dfdx[:, 0] = (field[:, 1] - field[:, -1]) / (2 * dx)
        dfdx[:, -1] = (field[:, 0] - field[:, -2]) / (2 * dx)

        # y-derivative
        dfdy = np.zeros_like(field)
        dfdy[1:-1, :] = (field[2:, :] - field[:-2, :]) / (2 * dx)
        dfdy[0, :] = (field[1, :] - field[-1, :]) / (2 * dx)
        dfdy[-1, :] = (field[0, :] - field[-2, :]) / (2 * dx)

        return dfdx, dfdy

    def _laplacian(self, field: np.ndarray) -> np.ndarray:
        """Calculate Laplacian with periodic boundaries"""
        cfg = self.config
        dx2 = cfg.dx**2

        lapl = np.zeros_like(field)

        # Interior
        lapl[1:-1, 1:-1] = (
            field[:-2, 1:-1]
            + field[2:, 1:-1]
            + field[1:-1, :-2]
            + field[1:-1, 2:]
            - 4 * field[1:-1, 1:-1]
        ) / dx2

        # Periodic boundaries
        # Top/Bottom
        lapl[0, 1:-1] = (
            field[-1, 1:-1]
            + field[1, 1:-1]
            + field[0, :-2]
            + field[0, 2:]
            - 4 * field[0, 1:-1]
        ) / dx2
        lapl[-1, 1:-1] = (
            field[-2, 1:-1]
            + field[0, 1:-1]
            + field[-1, :-2]
            + field[-1, 2:]
            - 4 * field[-1, 1:-1]
        ) / dx2

        # Left/Right
        lapl[:, 0] = (
            field[:, -1]
            + field[:, 1]
            + np.roll(field[:, 0], 1, axis=0)
            + np.roll(field[:, 0], -1, axis=0)
            - 4 * field[:, 0]
        ) / dx2
        lapl[:, -1] = (
            field[:, -2]
            + field[:, 0]
            + np.roll(field[:, -1], 1, axis=0)
            + np.roll(field[:, -1], -1, axis=0)
            - 4 * field[:, -1]
        ) / dx2

        return lapl

    def _anisotropic_laplacian(self, phi: np.ndarray) -> np.ndarray:
        """Calculate anisotropic Laplacian for phase field"""
        cfg = self.config

        # Calculate gradient
        phi_x, phi_y = self._gradient(phi)

        # Calculate local normal angle
        theta = np.arctan2(phi_y, phi_x)

        # Anisotropy factor
        a = self._anisotropy_function(theta)
        a_prime = np.zeros_like(a)

        # Derivative of anisotropy (for cubic symmetry)
        if cfg.symmetry == CrystalSymmetry.CUBIC:
            a_prime = (
                -cfg.anisotropy_strength
                * cfg.anisotropy_mode
                * np.sin(cfg.anisotropy_mode * theta)
            )

        # Anisotropic term
        aniso_term = a * a * self._laplacian(phi)

        # Additional curvature term from anisotropy derivative
        if cfg.anisotropy_strength > 0:
            aniso_term += (
                a
                * a_prime
                * (phi_x * self._gradient(phi_x)[1] - phi_y * self._gradient(phi_y)[0])
                / cfg.dx
            )

        return aniso_term  # type: ignore[no-any-return]

    def _phase_field_rhs(self) -> np.ndarray:
        """Calculate right-hand side of phase-field equation"""
        cfg = self.config

        phi = self.phi
        T = self.T

        # Double-well potential derivative: φ(1-φ²)
        f_phi = phi * (1 - phi**2)  # type: ignore[operator]

        # Thermal driving force: -λ(1-φ²)²(T - Tm)
        lambda_pf = 0.9  # Coupling constant
        thermal_force = -lambda_pf * (1 - phi**2) ** 2 * (T - cfg.T_melt) / cfg.T_melt  # type: ignore[operator]

        # Anisotropic diffusion term
        diffusion = cfg.epsilon**2 * self._anisotropic_laplacian(phi)  # type: ignore[arg-type]

        # Total RHS
        rhs = (diffusion + f_phi + thermal_force) / cfg.tau

        # Add thermal noise for side-branching
        if cfg.thermal_noise:
            interface_mask = np.abs(phi) < 0.9  # type: ignore  # Only at interface
            noise = cfg.noise_amplitude * np.random.randn(*phi.shape) * interface_mask  # type: ignore[union-attr]
            rhs += noise

        return rhs  # type: ignore[no-any-return]

    def _thermal_rhs(self) -> np.ndarray:
        """Calculate right-hand side of thermal diffusion equation"""
        cfg = self.config

        # Thermal diffusion
        diffusion = cfg.alpha * self._laplacian(self.T)  # type: ignore[arg-type]

        # Latent heat release at interface
        # H = L * ∂φ/∂t (approximate)
        phi_old = self.phi.copy()  # type: ignore[union-attr]
        phi_rhs = self._phase_field_rhs()
        latent_heat = cfg.latent_heat * phi_rhs * cfg.tau

        return diffusion + latent_heat

    def _step(self) -> None:
        """Advance simulation by one time step (explicit Euler)"""
        cfg = self.config

        # Update phase field
        phi_rhs = self._phase_field_rhs()
        self.phi += cfg.dt * phi_rhs  # type: ignore[operator]

        # Clip phase field to physical range
        self.phi = np.clip(self.phi, -1, 1)

        # Update temperature
        T_rhs = self._thermal_rhs()
        self.T += cfg.dt * T_rhs  # type: ignore[operator]

    def _compute_interface_length(self) -> float:
        """Compute total interface length"""
        cfg = self.config

        # Interface is where |phi| < threshold
        threshold = 0.5
        interface = np.abs(self.phi) < threshold  # type: ignore[arg-type]

        # Count interface pixels and multiply by grid spacing
        length = np.sum(interface) * cfg.dx

        return float(length)

    def _compute_solid_fraction(self) -> float:
        """Compute solid fraction (phi > 0)"""
        return float(np.sum(self.phi > 0) / self.phi.size)  # type: ignore[operator, union-attr]

    def _compute_tip_velocity(self) -> float:
        """Estimate dendrite tip velocity"""
        # Find maximum extent of solid phase
        solid_mask = self.phi > 0  # type: ignore[operator]
        if np.any(solid_mask):
            # Find centroid and max radius
            y, x = np.where(solid_mask)
            if len(x) > 0:
                centroid_x = np.mean(x)
                centroid_y = np.mean(y)
                distances = np.sqrt((x - centroid_x) ** 2 + (y - centroid_y) ** 2)
                return float(np.max(distances) * self.config.dx)
        return 0.0

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run crystal growth simulation"""
        cfg = self.config

        logger.info(
            f"Starting crystal growth: {cfg.symmetry.value}, "
            f"steps={cfg.n_steps}, grid={cfg.nx}x{cfg.ny}"
        )

        for step in range(cfg.n_steps):
            self._step()

            # Store output
            if step % cfg.output_interval == 0:
                self.phi_history.append(self.phi.copy())  # type: ignore[union-attr]
                self.T_history.append(self.T.copy())  # type: ignore[union-attr]
                self.time_history.append(step * cfg.dt)

                solid_frac = self._compute_solid_fraction()
                logger.debug(f"Step {step}, Solid fraction: {solid_frac:.3f}")

        # Store final state
        self.phi_history.append(self.phi.copy())  # type: ignore[union-attr]
        self.T_history.append(self.T.copy())  # type: ignore[union-attr]
        self.time_history.append(cfg.n_steps * cfg.dt)

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Calculate growth metrics
        final_solid_fraction = self._compute_solid_fraction()
        final_interface_length = self._compute_interface_length()

        return {
            "symmetry": cfg.symmetry.value,
            "anisotropy": cfg.anisotropy_strength,
            "final_solid_fraction": final_solid_fraction,
            "final_interface_length": final_interface_length,
            "nucleation_model": cfg.nucleation_model.value,
            "n_nuclei": cfg.n_nuclei,
            "grid_size": [cfg.nx, cfg.ny],
            "time_history": self.time_history,
            "phi_history": [p.tolist() for p in self.phi_history],
            "T_history": [T.tolist() for T in self.T_history],
            "final_phi": self.phi.tolist(),  # type: ignore[union-attr]
            "final_temperature": self.T.tolist(),  # type: ignore[union-attr]
            "mean_temperature": float(np.mean(self.T)),  # type: ignore[arg-type]
            "min_temperature": float(np.min(self.T)),  # type: ignore[arg-type]
            "max_temperature": float(np.max(self.T)),  # type: ignore[arg-type]
            "config": {
                "epsilon": cfg.epsilon,
                "tau": cfg.tau,
                "dt": cfg.dt,
                "T_melt": cfg.T_melt,
                "T_initial": cfg.T_initial,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Crystal Growth",
            "category": "ON_DEMAND",
            "domain": ["Materials Science", "Metallurgy", "Condensed Matter Physics"],
            "description": "Phase-field model for dendritic crystal growth",
            "computational_complexity": "O(N²) per time step",
            "typical_runtime": "minutes to hours",
            "accuracy": "High (diffuse interface approximation)",
            "assumptions": [
                "Diffuse interface approximation",
                "Isotropic or weakly anisotropic surface energy",
                "Constant material properties",
                "Local equilibrium at interface",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 128,
                    "description": "Grid points in x",
                },
                {
                    "name": "ny",
                    "type": "int",
                    "default": 128,
                    "description": "Grid points in y",
                },
                {
                    "name": "n_steps",
                    "type": "int",
                    "default": 5000,
                    "description": "Number of time steps",
                },
                {
                    "name": "symmetry",
                    "type": "enum",
                    "options": ["isotropic", "cubic", "hexagonal", "tetragonal"],
                    "default": "cubic",
                },
                {
                    "name": "anisotropy_strength",
                    "type": "float",
                    "default": 0.05,
                    "description": "Surface energy anisotropy",
                },
                {
                    "name": "T_initial",
                    "type": "float",
                    "default": 950.0,
                    "description": "Initial temperature (undercooled)",
                },
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================


def test_phase_field_range() -> None:
    """Test that phase field stays within [-1, 1]"""
    config = CrystalGrowthConfig(nx=32, ny=32, n_steps=100, anisotropy_strength=0.0)

    growth = CrystalGrowthPattern(config)
    result = growth.run()

    final_phi = np.array(result["final_phi"])
    assert np.all(final_phi >= -1.0), "Phase field below -1"
    assert np.all(final_phi <= 1.0), "Phase field above 1"
    print("✓ Phase field range test passed")


def test_solid_growth() -> None:
    """Test that solid phase grows from nuclei"""
    config = CrystalGrowthConfig(
        nx=64,
        ny=64,
        n_steps=500,
        T_initial=900.0,  # More undercooling for faster growth
        anisotropy_strength=0.0,
        n_nuclei=1,
        nucleation_model=NucleationModel.PREDEFINED,
    )

    growth = CrystalGrowthPattern(config)
    result = growth.run()

    # Solid fraction should increase
    assert result["final_solid_fraction"] > 0.01, (
        f"No solid growth detected: fraction={result['final_solid_fraction']}"
    )
    print("✓ Solid growth test passed")


def test_anisotropy_effect() -> None:
    """Test that anisotropy affects crystal shape"""
    np.random.seed(42)

    # Isotropic growth
    config_iso = CrystalGrowthConfig(
        nx=64,
        ny=64,
        n_steps=300,
        symmetry=CrystalSymmetry.ISOTROPIC,
        anisotropy_strength=0.0,
    )
    growth_iso = CrystalGrowthPattern(config_iso)
    result_iso = growth_iso.run()

    # Anisotropic growth
    config_aniso = CrystalGrowthConfig(
        nx=64,
        ny=64,
        n_steps=300,
        symmetry=CrystalSymmetry.CUBIC,
        anisotropy_strength=0.1,
    )
    growth_aniso = CrystalGrowthPattern(config_aniso)
    result_aniso = growth_aniso.run()

    # Anisotropic should have different interface shape
    # (measured by interface length to area ratio)
    def shape_factor(result: Any) -> Any:
        """Shape factor."""
        phi = np.array(result["final_phi"])
        solid_area = np.sum(phi > 0)
        interface = np.sum(np.abs(phi) < 0.5)
        return interface / solid_area if solid_area > 0 else 0

    shape_iso = shape_factor(result_iso)
    shape_aniso = shape_factor(result_aniso)

    assert shape_iso != shape_aniso, "Anisotropy did not affect crystal shape"
    print("✓ Anisotropy effect test passed")


def test_temperature_coupling() -> None:
    """Test that latent heat raises temperature"""
    config = CrystalGrowthConfig(
        nx=48,
        ny=48,
        n_steps=200,
        T_initial=950.0,
        latent_heat=5.0,  # High latent heat for noticeable effect
        n_nuclei=3,
    )

    growth = CrystalGrowthPattern(config)
    result = growth.run()

    # Temperature should rise due to latent heat
    assert result["max_temperature"] > config.T_initial, (
        "Latent heat did not raise temperature"
    )
    print("✓ Temperature coupling test passed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run tests
    test_phase_field_range()
    test_solid_growth()
    test_anisotropy_effect()
    test_temperature_coupling()

    # Demo run
    print("\n--- Demo Run ---")
    config = CrystalGrowthConfig(
        nx=64,
        ny=64,
        n_steps=1000,
        symmetry=CrystalSymmetry.CUBIC,
        anisotropy_strength=0.05,
    )

    growth = CrystalGrowthPattern(config)
    result = growth.run()

    print(f"Symmetry: {result['symmetry']}")
    print(f"Final solid fraction: {result['final_solid_fraction']:.3f}")
    print(f"Interface length: {result['final_interface_length']:.2f} μm")
    print(
        f"Temperature range: {result['min_temperature']:.1f} - {result['max_temperature']:.1f} K"
    )
