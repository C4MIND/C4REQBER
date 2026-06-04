"""
Spatial Ecology Pattern
Reaction-diffusion equations for spatial population dynamics

Based on:
- Fisher-KPP equation (1937)
- Turing pattern formation (1952)
- Lotka-Volterra diffusion
- Invasion waves
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
from scipy.ndimage import laplace

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


@dataclass
class SpatialEcologyConfig:
    """Configuration for spatial ecology simulation"""
    grid_size: int = 100
    dx: float = 1.0
    dt: float = 0.01
    n_steps: int = 5000

    # Model type
    model_type: str = "fisher_kpp"  # fisher_kpp, turing, competition, invasion

    # Species parameters
    n_species: int = 1
    growth_rates: list[float] = field(default_factory=lambda: [1.0])
    carrying_capacities: list[float] = field(default_factory=lambda: [1.0])
    diffusion_coeffs: list[float] = field(default_factory=lambda: [0.1])

    # Interaction (for multi-species)
    interaction_matrix: np.ndarray | None = None

    # Turing pattern parameters
    activator_diffusion: float = 0.01
    inhibitor_diffusion: float = 0.5

    record_interval: int = 100
    random_seed: int | None = None


@simulation_pattern(
    id="spatial_ecology",
    name="Spatial Ecology",
    category="biology",
    description="Reaction-diffusion equations for spatial population dynamics",
)
class SpatialEcologyPattern(SimulationPattern):
    """
    Spatial ecology simulation for population waves and patterns

    Implements:
    - Fisher-KPP equation (invasion waves)
    - Turing pattern formation
    - Competition-diffusion systems
    - Wave speed calculation
    - Pattern wavelength analysis
    """

    parameters = [
        SimulationParameter(
            name="grid_size",
            type="int",
            default=100,
            min=50,
            max=500,
            description="Grid resolution (N×N)",
        ),
        SimulationParameter(
            name="model_type",
            type="select",
            default="fisher_kpp",
            options=["fisher_kpp", "turing", "competition", "invasion"],
            description="Type of spatial model",
        ),
        SimulationParameter(
            name="n_species",
            type="int",
            default=1,
            min=1,
            max=3,
            description="Number of species",
        ),
        SimulationParameter(
            name="D",
            type="float",
            default=0.1,
            min=0.001,
            max=1.0,
            description="Diffusion coefficient",
        ),
        SimulationParameter(
            name="r",
            type="float",
            default=1.0,
            min=0.1,
            max=5.0,
            description="Intrinsic growth rate",
        ),
        SimulationParameter(
            name="K",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Carrying capacity",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=5000,
            min=1000,
            max=50000,
            description="Number of simulation steps",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.config: SpatialEcologyConfig | None = None
        self.fields: list[np.ndarray] = []
        self.history: list[dict[str, Any]] = []

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "spatial ecology", "reaction diffusion", "turing pattern",
            "invasion wave", "fisher equation", "kpp equation",
            "population wave", "spatial spread", "range expansion",
            "patch dynamics", "metapopulation", "dispersal",
            "pattern formation", "morphogenesis", "activator inhibitor",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute spatial ecology simulation"""
        start_time = datetime.now()
        simulation_id = f"spatial_eco_{start_time.timestamp()}"

        logger.info(f"Starting Spatial Ecology simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.random_seed:
                self.rng = np.random.default_rng(self.config.random_seed)

            results = await self._simulate(hypothesis)

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=datetime.now(),
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Spatial Ecology simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> SpatialEcologyConfig:
        """Parse configuration"""
        n_species = config.get("n_species", 1)
        model_type = config.get("model_type", "fisher_kpp")

        if model_type == "turing":
            n_species = 2  # Turing requires 2 species

        return SpatialEcologyConfig(
            grid_size=config.get("grid_size", 100),
            dx=config.get("dx", 1.0),
            dt=config.get("dt", 0.01),
            n_steps=config.get("n_steps", 5000),
            model_type=model_type,
            n_species=n_species,
            growth_rates=config.get("growth_rates", [config.get("r", 1.0)] * n_species),
            carrying_capacities=config.get("carrying_capacities", [config.get("K", 1.0)] * n_species),
            diffusion_coeffs=config.get("diffusion_coeffs", [config.get("D", 0.1)] * n_species),
            activator_diffusion=config.get("activator_diffusion", 0.01),
            inhibitor_diffusion=config.get("inhibitor_diffusion", 0.5),
            record_interval=config.get("record_interval", 100),
            random_seed=config.get("random_seed"),
        )

    async def _simulate(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run spatial simulation"""
        N = self.config.grid_size  # type: ignore[union-attr]
        dx = self.config.dx  # type: ignore[union-attr]
        dt = self.config.dt  # type: ignore[union-attr]
        n_species = self.config.n_species  # type: ignore[union-attr]

        # Turing requires at least 2 species (activator + inhibitor)
        if self.config.model_type == "turing":  # type: ignore[union-attr]
            n_species = max(n_species, 2)

        # Ensure coefficient lists have enough elements
        cfg = self.config  # type: ignore[assignment]
        while len(cfg.diffusion_coeffs) < n_species:  # type: ignore[union-attr]
            cfg.diffusion_coeffs.append(0.1)  # type: ignore[union-attr]
        while len(cfg.growth_rates) < n_species:  # type: ignore[union-attr]
            cfg.growth_rates.append(1.0)  # type: ignore[union-attr]
        while len(cfg.carrying_capacities) < n_species:  # type: ignore[union-attr]
            cfg.carrying_capacities.append(1.0)  # type: ignore[union-attr]

        # Initialize fields
        self.fields = []
        for i in range(n_species):
            if self.config.model_type == "fisher_kpp" and i == 0:  # type: ignore[union-attr]
                # Initial invasion: small population at center
                field = np.zeros((N, N))
                center = N // 2
                field[center-2:center+3, center-2:center+3] = 0.5
            elif self.config.model_type == "turing":  # type: ignore[union-attr]
                # Turing: small random perturbations
                if i == 0:  # Activator
                    field = np.ones((N, N)) + 0.1 * self.rng.standard_normal((N, N))
                else:  # Inhibitor
                    field = np.ones((N, N)) + 0.1 * self.rng.standard_normal((N, N))
            else:
                # Random initial conditions
                field = self.rng.random((N, N))

            self.fields.append(field)

        self.history = []

        # Run simulation
        for step in range(self.config.n_steps):  # type: ignore[union-attr]
            if self.config.model_type == "fisher_kpp":  # type: ignore[union-attr]
                self._step_fisher_kpp(dx, dt)
            elif self.config.model_type == "turing":  # type: ignore[union-attr]
                self._step_turing(dx, dt)
            elif self.config.model_type == "competition":  # type: ignore[union-attr]
                self._step_competition(dx, dt)
            else:  # invasion
                self._step_invasion(dx, dt)

            # Record
            if step % self.config.record_interval == 0:  # type: ignore[union-attr]
                self._record(step * dt)

            if step % 500 == 0:
                await asyncio.sleep(0)

        return self._analyze_results()

    def _step_fisher_kpp(self, dx: float, dt: float) -> None:
        """Fisher-KPP equation: ∂u/∂t = D∇²u + ru(1-u/K)"""
        u = self.fields[0]
        D = self.config.diffusion_coeffs[0]  # type: ignore[index, union-attr]
        r = self.config.growth_rates[0]  # type: ignore[index, union-attr]
        K = self.config.carrying_capacities[0]  # type: ignore[index, union-attr]

        # Diffusion term (Laplacian)
        laplacian_u = laplace(u) / (dx ** 2)

        # Reaction term (logistic growth)
        reaction = r * u * (1 - u / K)

        # Update
        self.fields[0] = u + dt * (D * laplacian_u + reaction)
        self.fields[0] = np.clip(self.fields[0], 0, None)

    def _step_turing(self, dx: float, dt: float) -> None:
        """Turing pattern formation"""
        A = self.fields[0]  # Activator
        I = self.fields[1]  # Inhibitor

        Da = self.config.activator_diffusion  # type: ignore[union-attr]
        Di = self.config.inhibitor_diffusion  # type: ignore[union-attr]

        # Gray-Scott like model
        laplacian_A = laplace(A) / (dx ** 2)
        laplacian_I = laplace(I) / (dx ** 2)

        # Reaction terms
        reaction_A = A - A**3 - I + 0.1
        reaction_I = (A - I) * 0.5

        self.fields[0] = A + dt * (Da * laplacian_A + reaction_A)
        self.fields[1] = I + dt * (Di * laplacian_I + reaction_I)

    def _step_competition(self, dx: float, dt: float) -> None:
        """Competition-diffusion system"""
        new_fields = []

        for i, u in enumerate(self.fields):
            D = self.config.diffusion_coeffs[i]  # type: ignore[index, union-attr]
            r = self.config.growth_rates[i]  # type: ignore[index, union-attr]
            K = self.config.carrying_capacities[i]  # type: ignore[index, union-attr]

            laplacian_u = laplace(u) / (dx ** 2)

            # Competition term
            competition = u / K
            for j, other in enumerate(self.fields):
                if i != j:
                    competition += 0.5 * other / K

            reaction = r * u * (1 - competition)
            new_fields.append(u + dt * (D * laplacian_u + reaction))

        self.fields = [np.clip(f, 0, None) for f in new_fields]

    def _step_invasion(self, dx: float, dt: float) -> None:
        """Invasion with Allee effect"""
        u = self.fields[0]
        D = self.config.diffusion_coeffs[0]  # type: ignore[index, union-attr]
        r = self.config.growth_rates[0]  # type: ignore[index, union-attr]
        K = self.config.carrying_capacities[0]  # type: ignore[index, union-attr]

        laplacian_u = laplace(u) / (dx ** 2)

        # Allee effect: growth is reduced at low densities
        allee_threshold = 0.2 * K
        allee_factor = np.where(u > allee_threshold, 1.0, u / allee_threshold)

        reaction = r * u * (1 - u / K) * allee_factor

        self.fields[0] = u + dt * (D * laplacian_u + reaction)
        self.fields[0] = np.clip(self.fields[0], 0, None)

    def _record(self, t: float) -> None:
        """Record simulation state"""
        u = self.fields[0]

        # Total population
        total = np.sum(u)
        mean = np.mean(u)
        max_val = np.max(u)

        # Spatial spread (for invasion)
        if self.config.model_type in ["fisher_kpp", "invasion"]:  # type: ignore[union-attr]
            # Find radius where density > threshold
            N = self.config.grid_size  # type: ignore[union-attr]
            center = N // 2
            threshold = 0.01 * self.config.carrying_capacities[0]  # type: ignore[index, union-attr]

            mask = u > threshold
            if np.any(mask):
                y, x = np.where(mask)
                distances = np.sqrt((x - center)**2 + (y - center)**2)
                spread_radius = np.max(distances) * self.config.dx  # type: ignore[union-attr]
            else:
                spread_radius = 0
        else:
            spread_radius = 0

        # Pattern metrics (for Turing)
        if self.config.model_type == "turing":  # type: ignore[union-attr]
            # Estimate wavelength from FFT
            fft = np.fft.fft2(u - np.mean(u))
            power = np.abs(fft)**2
            # Find dominant frequency
            peak_idx = np.unravel_index(np.argmax(power), power.shape)
            wavelength = self.config.grid_size / max(peak_idx[0], 1)  # type: ignore[operator, union-attr]
        else:
            wavelength = 0

        self.history.append({
            "time": t,
            "total": float(total),
            "mean": float(mean),
            "max": float(max_val),
            "spread_radius": float(spread_radius),
            "wavelength": float(wavelength),
        })

    def _analyze_results(self) -> dict[str, Any]:
        """Analyze simulation results"""
        if not self.history:
            return {"metrics": {}, "logs": ["No simulation data"]}

        initial = self.history[0]
        final = self.history[-1]

        metrics = {
            "initial_total": initial["total"],
            "final_total": final["total"],
            "initial_mean": initial["mean"],
            "final_mean": final["mean"],
            "max_density": final["max"],
        }

        logs = [
            f"Spatial Ecology ({self.config.model_type}): {self.config.grid_size}×{self.config.grid_size}",  # type: ignore[union-attr]
            f"Initial total: {metrics['initial_total']:.2f}",
            f"Final total: {metrics['final_total']:.2f}",
            f"Max density: {metrics['max_density']:.4f}",
        ]

        # Wave speed calculation (Fisher-KPP)
        if self.config.model_type in ["fisher_kpp", "invasion"]:  # type: ignore[union-attr]
            times = np.array([h["time"] for h in self.history])
            radii = np.array([h["spread_radius"] for h in self.history])

            if len(times) > 10 and np.any(radii > 0):
                # Linear fit to find wave speed
                valid = radii > 0
                if np.sum(valid) > 5:
                    coeffs = np.polyfit(times[valid], radii[valid], 1)
                    wave_speed = float(coeffs[0])

                    # Theoretical Fisher wave speed: v = 2√(Dr)
                    D = self.config.diffusion_coeffs[0]  # type: ignore[index, union-attr]
                    r = self.config.growth_rates[0]  # type: ignore[index, union-attr]
                    theoretical_speed = 2 * np.sqrt(D * r)

                    metrics["wave_speed"] = wave_speed
                    metrics["theoretical_wave_speed"] = float(theoretical_speed)
                    metrics["wave_speed_error"] = float(abs(wave_speed - theoretical_speed) / theoretical_speed)

                    logs.append(f"Wave speed: {wave_speed:.4f}")
                    logs.append(f"Theoretical speed: {theoretical_speed:.4f}")

        # Turing pattern analysis
        if self.config.model_type == "turing":  # type: ignore[union-attr]
            wavelengths = [h["wavelength"] for h in self.history if h["wavelength"] > 0]
            if wavelengths:
                avg_wavelength = np.mean(wavelengths)
                metrics["pattern_wavelength"] = float(avg_wavelength)
                logs.append(f"Pattern wavelength: {avg_wavelength:.2f}")

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        if self.config.n_steps >= 5000:  # type: ignore[union-attr]
            factors.append(0.3)

        if "wave_speed" in metrics:
            error = metrics.get("wave_speed_error", 1.0)
            if error < 0.2:
                factors.append(0.3)
            elif error < 0.5:
                factors.append(0.2)

        if self.config.model_type == "turing" and "pattern_wavelength" in metrics:  # type: ignore[union-attr]
            factors.append(0.3)

        if metrics.get("final_total", 0) > metrics.get("initial_total", 0):
            factors.append(0.1)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("grid_size", 100)
        n_steps = params.get("n_steps", 5000)

        estimated_time = (N * N * n_steps) / 1e6

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + (N * N * 8) / 1e6,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
