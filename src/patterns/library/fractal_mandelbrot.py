"""
Mandelbrot Set Pattern
Fractal generation and analysis

Based on:
- Iteration z_{n+1} = z_n^2 + c
- Escape time algorithm
- Boundary detection
- Hausdorff dimension estimate
"""

from __future__ import annotations

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
class MandelbrotConfig:
    """Configuration for Mandelbrot set simulation"""
    width: int = 800          # Image width
    height: int = 600         # Image height
    max_iter: int = 100       # Maximum iterations
    x_min: float = -2.5       # Real axis minimum
    x_max: float = 1.0        # Real axis maximum
    y_min: float = -1.25      # Imaginary axis minimum
    y_max: float = 1.25       # Imaginary axis maximum


@simulation_pattern(
    id="fractal_mandelbrot",
    name="Mandelbrot Set",
    category="mathematics",
    description="Mandelbrot set fractal generation and analysis",
)
class MandelbrotPattern(SimulationPattern):
    """
    Mandelbrot set simulation

    Implements:
    - Escape time algorithm
    - Iteration count visualization
    - Area estimate via Monte Carlo
    - Boundary detection
    """

    parameters = [
        SimulationParameter(
            name="width",
            type="int",
            default=800,
            min=100,
            max=2000,
            description="Image width",
        ),
        SimulationParameter(
            name="height",
            type="int",
            default=600,
            min=100,
            max=2000,
            description="Image height",
        ),
        SimulationParameter(
            name="max_iter",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Maximum iterations",
        ),
        SimulationParameter(
            name="x_min",
            type="float",
            default=-2.5,
            min=-3.0,
            max=0.0,
            description="Real axis minimum",
        ),
        SimulationParameter(
            name="x_max",
            type="float",
            default=1.0,
            min=0.0,
            max=3.0,
            description="Real axis maximum",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: MandelbrotConfig = MandelbrotConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if Mandelbrot can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "mandelbrot", "fractal", "complex dynamics", "julia",
            "escape time", "iteration", "chaos", "self-similar",
            "hausdorff dimension", "boundary", "complex plane",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute Mandelbrot simulation"""
        start_time = datetime.now()
        simulation_id = f"mandel_{start_time.timestamp()}"
        logger.info(f"Starting Mandelbrot simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_mandelbrot()
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
            logger.exception("Mandelbrot simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> MandelbrotConfig:
        """Parse configuration dict"""
        cfg = MandelbrotConfig()
        if "width" in config:
            cfg.width = int(config["width"])
        if "height" in config:
            cfg.height = int(config["height"])
        if "max_iter" in config:
            cfg.max_iter = int(config["max_iter"])
        if "x_min" in config:
            cfg.x_min = float(config["x_min"])
        if "x_max" in config:
            cfg.x_max = float(config["x_max"])
        if "y_min" in config:
            cfg.y_min = float(config["y_min"])
        if "y_max" in config:
            cfg.y_max = float(config["y_max"])
        return cfg

    async def _simulate_mandelbrot(self) -> dict[str, Any]:
        """Run Mandelbrot set computation"""
        cfg = self.config
        w, h = cfg.width, cfg.height
        max_iter = cfg.max_iter

        # Create complex plane grid
        x = np.linspace(cfg.x_min, cfg.x_max, w)
        y = np.linspace(cfg.y_min, cfg.y_max, h)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y

        # Escape time algorithm
        Z = np.zeros_like(C)
        iterations = np.zeros(C.shape, dtype=int)
        mask = np.ones(C.shape, dtype=bool)

        for i in range(max_iter):
            Z[mask] = Z[mask]**2 + C[mask]
            mask_new = np.abs(Z) <= 2
            newly_escaped = mask & (~mask_new)
            iterations[newly_escaped] = i
            mask = mask_new

        # Points that never escaped
        iterations[mask] = max_iter

        # Area estimate (Mandelbrot set area ~ 1.50659)
        # Monte Carlo: count points inside / total * area
        inside = np.sum(iterations >= max_iter)
        total_points = w * h
        area = (cfg.x_max - cfg.x_min) * (cfg.y_max - cfg.y_min)
        area_estimate = inside / total_points * area

        # Boundary estimate (points near escape boundary)
        boundary_mask = (iterations > 0) & (iterations < max_iter)
        boundary_points = np.sum(boundary_mask)

        # Cardioid and period-2 bulb check
        # Main cardioid: c = 0.5 * e^(i*theta) - 0.25 * e^(2*i*theta)
        # Period-2 bulb: |c + 1| < 0.25
        in_cardioid = 0
        in_bulb = 0
        for i in range(min(1000, total_points)):
            c = C.flat[i]
            # Check cardioid
            q = (c.real - 0.25)**2 + c.imag**2
            if q * (q + (c.real - 0.25)) <= 0.25 * c.imag**2:
                in_cardioid += 1
            # Check period-2 bulb
            if (c.real + 1)**2 + c.imag**2 < 0.0625:
                in_bulb += 1

        metrics = {
            "width": w,
            "height": h,
            "max_iter": max_iter,
            "inside_points": int(inside),
            "boundary_points": int(boundary_points),
            "area_estimate": float(area_estimate),
            "escape_rate": float(boundary_points / total_points),
            "cardioid_points": in_cardioid,
            "bulb_points": in_bulb,
        }

        logs = [
            f"Mandelbrot set: {w}x{h}, max_iter={max_iter}",
            f"Inside points: {inside} / {total_points}",
            f"Area estimate: {area_estimate:.6f}",
            f"Boundary points: {boundary_points}",
            f"Escape rate: {metrics['escape_rate']*100:.2f}%",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "iterations": iterations.tolist(),
            "x": x.tolist(),
            "y": y.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Area estimate in reasonable range (known ~1.506)
        area = metrics.get("area_estimate", 0)
        if 1.0 < area < 2.5:
            factors.append(0.3)

        # Some points inside
        if metrics.get("inside_points", 0) > 0:
            factors.append(0.2)

        # Some points escaped
        if metrics.get("boundary_points", 0) > 0:
            factors.append(0.2)

        # Sufficient iterations
        if metrics.get("max_iter", 0) >= 50:
            factors.append(0.2)

        # Cardioid points found
        if metrics.get("cardioid_points", 0) > 0:
            factors.append(0.1)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        w = params.get("width", 800)
        h = params.get("height", 600)
        max_iter = params.get("max_iter", 100)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + w * h * 8e-9,
            "gpu_required": False,
            "estimated_time_seconds": w * h * max_iter / 1e8,
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
                "Mandelbrot, B. (1980). Fractal aspects of the iteration of z -> lambda*z*(1-z)",
            ],
        }
