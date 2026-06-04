"""
Julia Set Pattern
Julia set fractal generation

Based on:
- Iteration z_{n+1} = z_n^2 + c
- Fixed complex parameter c
- Escape time algorithm
- Connectedness test
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
class JuliaConfig:
    """Configuration for Julia set simulation"""
    width: int = 800
    height: int = 600
    max_iter: int = 100
    c_real: float = -0.7      # Real part of c
    c_imag: float = 0.27015   # Imaginary part of c
    x_min: float = -2.0
    x_max: float = 2.0
    y_min: float = -1.5
    y_max: float = 1.5


@simulation_pattern(
    id="fractal_julia",
    name="Julia Set",
    category="mathematics",
    description="Julia set fractal generation for complex parameter c",
)
class JuliaPattern(SimulationPattern):
    """
    Julia set simulation

    Implements:
    - Escape time algorithm
    - Fixed complex parameter c
    - Connectedness analysis
    - Area estimate
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
            name="c_real",
            type="float",
            default=-0.7,
            min=-2.0,
            max=2.0,
            description="Real part of c",
        ),
        SimulationParameter(
            name="c_imag",
            type="float",
            default=0.27015,
            min=-2.0,
            max=2.0,
            description="Imaginary part of c",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: JuliaConfig = JuliaConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if Julia can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "julia set", "fractal", "complex dynamics", "iteration",
            "escape time", "fatou", "self-similar", "complex plane",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute Julia set simulation"""
        start_time = datetime.now()
        simulation_id = f"julia_{start_time.timestamp()}"
        logger.info(f"Starting Julia set simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_julia()
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
            logger.exception("Julia set simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> JuliaConfig:
        """Parse configuration dict"""
        cfg = JuliaConfig()
        if "width" in config:
            cfg.width = int(config["width"])
        if "height" in config:
            cfg.height = int(config["height"])
        if "max_iter" in config:
            cfg.max_iter = int(config["max_iter"])
        if "c_real" in config:
            cfg.c_real = float(config["c_real"])
        if "c_imag" in config:
            cfg.c_imag = float(config["c_imag"])
        if "x_min" in config:
            cfg.x_min = float(config["x_min"])
        if "x_max" in config:
            cfg.x_max = float(config["x_max"])
        if "y_min" in config:
            cfg.y_min = float(config["y_min"])
        if "y_max" in config:
            cfg.y_max = float(config["y_max"])
        return cfg

    async def _simulate_julia(self) -> dict[str, Any]:
        """Run Julia set computation"""
        cfg = self.config
        w, h = cfg.width, cfg.height
        max_iter = cfg.max_iter
        c = cfg.c_real + 1j * cfg.c_imag

        # Create complex plane grid
        x = np.linspace(cfg.x_min, cfg.x_max, w)
        y = np.linspace(cfg.y_min, cfg.y_max, h)
        X, Y = np.meshgrid(x, y)
        Z = X + 1j * Y

        # Escape time algorithm
        iterations = np.zeros(Z.shape, dtype=int)
        mask = np.ones(Z.shape, dtype=bool)

        for i in range(max_iter):
            Z[mask] = Z[mask]**2 + c
            mask_new = np.abs(Z) <= 2
            newly_escaped = mask & (~mask_new)
            iterations[newly_escaped] = i
            mask = mask_new

        iterations[mask] = max_iter

        # Statistics
        inside = np.sum(iterations >= max_iter)
        total_points = w * h
        area = (cfg.x_max - cfg.x_min) * (cfg.y_max - cfg.y_min)
        area_estimate = inside / total_points * area

        boundary_points = np.sum((iterations > 0) & (iterations < max_iter))

        # Connectedness: Julia set is connected iff c is in Mandelbrot set
        # Simple test: iterate z=0 with z_{n+1}=z_n^2+c
        z_test = 0
        connected = True
        for _ in range(max_iter * 2):
            z_test = z_test**2 + c
            if abs(z_test) > 2:
                connected = False
                break

        # Estimate fractal dimension using box counting (simplified)
        # Use boundary points at different resolutions
        dims = []
        for scale in [2, 4, 8]:
            if w // scale > 0 and h // scale > 0:
                coarse = iterations[::scale, ::scale]
                boundary = np.sum((coarse > 0) & (coarse < max_iter))
                if boundary > 0:
                    dims.append(np.log(boundary) / np.log(w // scale))
        fractal_dim = np.mean(dims) if dims else 0.0

        metrics = {
            "width": w,
            "height": h,
            "max_iter": max_iter,
            "c_real": cfg.c_real,
            "c_imag": cfg.c_imag,
            "inside_points": int(inside),
            "boundary_points": int(boundary_points),
            "area_estimate": float(area_estimate),
            "connected": connected,
            "fractal_dimension_estimate": float(fractal_dim),
            "escape_rate": float(boundary_points / total_points),
        }

        logs = [
            f"Julia set: c = {cfg.c_real} + {cfg.c_imag}i",
            f"Grid: {w}x{h}, max_iter={max_iter}",
            f"Inside points: {inside} / {total_points}",
            f"Connected: {connected}",
            f"Fractal dimension estimate: {fractal_dim:.3f}",
            f"Area estimate: {area_estimate:.4f}",
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

        # Non-empty set
        if metrics.get("inside_points", 0) > 0:
            factors.append(0.25)

        # Boundary exists
        if metrics.get("boundary_points", 0) > 0:
            factors.append(0.25)

        # Fractal dimension in reasonable range (1-2 for Julia sets)
        dim = metrics.get("fractal_dimension_estimate", 0)
        if 1.0 < dim < 2.0:
            factors.append(0.25)

        # Sufficient iterations
        if metrics.get("max_iter", 0) >= 50:
            factors.append(0.25)

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
                "Julia, G. (1918). Memoire sur l'iteration des fonctions rationnelles",
            ],
        }
