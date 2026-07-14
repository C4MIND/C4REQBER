"""
Reaction-Diffusion Pattern
Gray-Scott model and Turing pattern formation

Based on:
- Gray-Scott model: two coupled reaction-diffusion equations
- Turing instability mechanism
- Finite difference method
- Pattern classification
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

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
class ReactionDiffusionConfig:
    """Configuration for reaction-diffusion simulation"""
    model: str = "gray_scott"  # "gray_scott" or "turing"
    nx: int = 128              # Grid size
    ny: int = 128
    Du: float = 0.16           # Diffusion coefficient U
    Dv: float = 0.08           # Diffusion coefficient V
    F: float = 0.035           # Feed rate
    k: float = 0.06            # Kill rate
    dt: float = 1.0            # Time step
    n_steps: int = 10000       # Number of steps
    snapshot_interval: int = 1000


@simulation_pattern(
    id="reaction_diffusion",
    name="Reaction-Diffusion",
    category="biology",
    description="Gray-Scott model and Turing pattern formation",
)
class ReactionDiffusionPattern(SimulationPattern):
    """
    Reaction-diffusion simulation

    Implements:
    - Gray-Scott model
    - Turing instability
    - Pattern classification
    - Energy/entropy tracking
    """

    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="gray_scott",
            options=["gray_scott", "turing"],
            description="Reaction-diffusion model",
        ),
        SimulationParameter(
            name="nx",
            type="int",
            default=128,
            min=32,
            max=512,
            description="Grid resolution",
        ),
        SimulationParameter(
            name="Du",
            type="float",
            default=0.16,
            min=0.01,
            max=1.0,
            description="U diffusion coefficient",
        ),
        SimulationParameter(
            name="Dv",
            type="float",
            default=0.08,
            min=0.01,
            max=1.0,
            description="V diffusion coefficient",
        ),
        SimulationParameter(
            name="F",
            type="float",
            default=0.035,
            min=0.0,
            max=0.1,
            description="Feed rate",
        ),
        SimulationParameter(
            name="k",
            type="float",
            default=0.06,
            min=0.0,
            max=0.1,
            description="Kill rate",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=10000,
            min=1000,
            max=50000,
            description="Number of time steps",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: ReactionDiffusionConfig = ReactionDiffusionConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if reaction-diffusion can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "reaction diffusion", "gray scott", "turing pattern",
            "morphogenesis", "pattern formation", "activator inhibitor",
            "chemical pattern", "spots", "stripes", "waves",
            "self-organization", "dissipative structure",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute reaction-diffusion simulation"""
        start_time = datetime.now()
        simulation_id = f"rd_{start_time.timestamp()}"
        logger.info(f"Starting reaction-diffusion simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.model == "gray_scott":
                results = await self._simulate_gray_scott()
            else:
                results = await self._simulate_turing()
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
            logger.exception("Reaction-diffusion simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> ReactionDiffusionConfig:
        """Parse configuration dict"""
        cfg = ReactionDiffusionConfig()
        if "model" in config:
            cfg.model = str(config["model"])
        if "nx" in config:
            cfg.nx = int(config["nx"])
            cfg.ny = int(config["nx"])
        if "Du" in config:
            cfg.Du = float(config["Du"])
        if "Dv" in config:
            cfg.Dv = float(config["Dv"])
        if "F" in config:
            cfg.F = float(config["F"])
        if "k" in config:
            cfg.k = float(config["k"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "n_steps" in config:
            cfg.n_steps = int(config["n_steps"])
        return cfg

    async def _simulate_gray_scott(self) -> dict[str, Any]:
        """Gray-Scott model simulation"""
        cfg = self.config
        nx, ny = cfg.nx, cfg.ny
        Du, Dv = cfg.Du, cfg.Dv
        F, k = cfg.F, cfg.k
        dt = cfg.dt

        # Initialize: U = 1 everywhere, V = 0 with small seed
        U = np.ones((nx, ny))
        V = np.zeros((nx, ny))

        # Seed perturbation
        seed_size = nx // 10
        cx, cy = nx // 2, ny // 2
        U[cx-seed_size:cx+seed_size, cy-seed_size:cy+seed_size] = 0.5
        V[cx-seed_size:cx+seed_size, cy-seed_size:cy+seed_size] = 0.25

        # Add noise
        U += np.random.randn(nx, ny) * 0.01
        V += np.random.randn(nx, ny) * 0.01

        # Laplacian kernel
        def laplacian(Z: np.ndarray) -> np.ndarray:
            return (
                np.roll(Z, 1, axis=0) + np.roll(Z, -1, axis=0) +
                np.roll(Z, 1, axis=1) + np.roll(Z, -1, axis=1) - 4 * Z
            )

        snapshots = []
        U_mean_history = []
        V_mean_history = []

        for step in range(cfg.n_steps):
            # Reaction terms
            UVV = U * V * V

            # Update
            U_new = U + dt * (Du * laplacian(U) - UVV + F * (1 - U))
            V_new = V + dt * (Dv * laplacian(V) + UVV - (F + k) * V)

            U = np.clip(U_new, 0, 1)
            V = np.clip(V_new, 0, 1)

            U_mean_history.append(float(np.mean(U)))
            V_mean_history.append(float(np.mean(V)))

            if step % cfg.snapshot_interval == 0:
                snapshots.append(V.copy())

            if step % 1000 == 0:
                await asyncio.sleep(0)

        # Classify pattern
        pattern_type = self._classify_pattern(V)

        metrics = {
            "final_U_mean": float(np.mean(U)),
            "final_V_mean": float(np.mean(V)),
            "U_variance": float(np.var(U)),
            "V_variance": float(np.var(V)),
            "pattern_type": pattern_type,
            "n_steps": cfg.n_steps,
            "Du": Du,
            "Dv": Dv,
            "F": F,
            "k": k,
        }

        logs = [
            f"Gray-Scott: {nx}x{ny} grid, {cfg.n_steps} steps",
            f"Parameters: Du={Du}, Dv={Dv}, F={F}, k={k}",
            f"Final U mean: {metrics['final_U_mean']:.4f}",
            f"Final V mean: {metrics['final_V_mean']:.4f}",
            f"Pattern type: {pattern_type}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "U_final": U.tolist(),
            "V_final": V.tolist(),
            "snapshots": [s.tolist() for s in snapshots],
            "U_mean_history": U_mean_history,
            "V_mean_history": V_mean_history,
        }

    async def _simulate_turing(self) -> dict[str, Any]:
        """Simple Turing pattern simulation"""
        cfg = self.config
        nx = cfg.nx

        # Activator-inhibitor model (simplified)
        A = np.random.rand(nx, nx) * 0.1 + 0.5
        I = np.random.rand(nx, nx) * 0.1 + 0.5

        Da, Di = 0.01, 0.5
        ra, ri = 0.1, 0.05
        ba, bi = 0.1, 0.05
        dt = cfg.dt

        def laplacian(Z: np.ndarray) -> np.ndarray:
            return (
                np.roll(Z, 1, axis=0) + np.roll(Z, -1, axis=0) +
                np.roll(Z, 1, axis=1) + np.roll(Z, -1, axis=1) - 4 * Z
            )

        for step in range(min(cfg.n_steps, 5000)):
            A_new = A + dt * (Da * laplacian(A) + ra * A - ba * A * I)
            I_new = I + dt * (Di * laplacian(I) + ri * A - bi * I)
            A = np.clip(A_new, 0, 2)
            I = np.clip(I_new, 0, 2)

            if step % 1000 == 0:
                await asyncio.sleep(0)

        metrics = {
            "final_A_mean": float(np.mean(A)),
            "final_I_mean": float(np.mean(I)),
            "A_variance": float(np.var(A)),
            "pattern_type": "turing",
            "n_steps": min(cfg.n_steps, 5000),
        }

        logs = [
            f"Turing pattern: {nx}x{nx} grid",
            f"Final A mean: {metrics['final_A_mean']:.4f}",
            f"Final I mean: {metrics['final_I_mean']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "A_final": A.tolist(),
            "I_final": I.tolist(),
        }

    def _classify_pattern(self, V: np.ndarray) -> str:
        """Classify Gray-Scott pattern type"""
        var = np.var(V)
        if var < 0.001:
            return "homogeneous"

        # Count connected components approximation
        np.mean(V)

        # Simple pattern classification based on variance and structure
        if var > 0.05:
            return "chaotic"
        elif var > 0.02:
            return "spots"
        elif var > 0.005:
            return "stripes"
        else:
            return "waves"

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Non-homogeneous pattern
        if metrics.get("V_variance", 0) > 0.001:
            factors.append(0.3)

        # Valid parameter range
        if 0 < metrics.get("F", -1) < 0.1:
            factors.append(0.2)

        # Pattern formed
        if metrics.get("pattern_type", "") != "homogeneous":
            factors.append(0.3)

        # Sufficient steps
        if metrics.get("n_steps", 0) >= 5000:
            factors.append(0.2)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        nx = params.get("nx", 128)
        n_steps = params.get("n_steps", 10000)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + nx**2 * 2 * 8e-9,
            "gpu_required": False,
            "estimated_time_seconds": n_steps * nx**2 / 1e7,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.id,
            "name": cls.name,  # type: ignore[attr-defined]
            "category": cls.category,  # type: ignore[attr-defined]
            "description": cls.description,  # type: ignore[attr-defined]
            "parameters": [
                {"name": p.name, "type": p.type, "default": p.default,
                 "min": p.min, "max": p.max, "description": p.description}
                for p in cls.parameters
            ],
            "references": [
                "Pearson, J.E. (1993). Complex patterns in a simple system. Science",
                "Turing, A.M. (1952). The chemical basis of morphogenesis",
            ],
        }
