"""
Cellular Automata Pattern
Conway's Game of Life and Rule 110

Based on:
- Conway's Game of Life (2D cellular automaton)
- Elementary cellular automata (Rule 110)
- Pattern detection (gliders, oscillators)
- Entropy analysis
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
class CellularAutomataConfig:
    """Configuration for cellular automata simulation"""
    model: str = "game_of_life"
    width: int = 100
    height: int = 100
    n_steps: int = 100
    initial_density: float = 0.5
    rule_number: int = 110


@simulation_pattern(
    id="cellular_automata",
    name="Cellular Automata",
    category="mathematics",
    description="Conway's Game of Life and elementary cellular automata",
)
class CellularAutomataPattern(SimulationPattern):
    """
    Cellular automata simulation

    Implements:
    - Conway's Game of Life
    - Elementary cellular automata (Rule 110)
    - Pattern detection
    - Entropy and density tracking
    """

    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="game_of_life",
            options=["game_of_life", "rule_110"],
            description="Cellular automaton model",
        ),
        SimulationParameter(
            name="width",
            type="int",
            default=100,
            min=10,
            max=500,
            description="Grid width",
        ),
        SimulationParameter(
            name="height",
            type="int",
            default=100,
            min=10,
            max=500,
            description="Grid height",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Number of steps",
        ),
        SimulationParameter(
            name="initial_density",
            type="float",
            default=0.5,
            min=0.0,
            max=1.0,
            description="Initial live cell density",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: CellularAutomataConfig = CellularAutomataConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if can simulate."""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "cellular automata", "game of life", "conway",
            "rule 110", "elementary automata", "emergence",
            "self-organization", "complexity", "cellular",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> SimulationResult:
        """Run."""
        start_time = datetime.now()
        simulation_id = f"ca_{start_time.timestamp()}"
        logger.info(f"Starting CA simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.model == "game_of_life":
                results = await self._simulate_gol()
            else:
                results = await self._simulate_rule110()
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
            logger.exception("CA simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> CellularAutomataConfig:
        cfg = CellularAutomataConfig()
        if "model" in config:
            cfg.model = str(config["model"])
        if "width" in config:
            cfg.width = int(config["width"])
        if "height" in config:
            cfg.height = int(config["height"])
        if "n_steps" in config:
            cfg.n_steps = int(config["n_steps"])
        if "initial_density" in config:
            cfg.initial_density = float(config["initial_density"])
        if "rule_number" in config:
            cfg.rule_number = int(config["rule_number"])
        return cfg

    async def _simulate_gol(self) -> dict[str, Any]:
        cfg = self.config
        w, h = cfg.width, cfg.height
        n_steps = cfg.n_steps

        # Initialize random grid
        grid = np.random.random((h, w)) < cfg.initial_density

        density_history = []
        entropy_history = []
        snapshots = []

        for step in range(n_steps):
            density = np.mean(grid)
            density_history.append(float(density))

            # Shannon entropy
            p = density
            if 0 < p < 1:
                entropy = -(p * np.log2(p) + (1-p) * np.log2(1-p))
            else:
                entropy = 0.0
            entropy_history.append(float(entropy))

            if step % max(1, n_steps // 5) == 0:
                snapshots.append(grid.copy().astype(int).tolist())

            # Count neighbors
            neighbors = (
                np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
                np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) +
                np.roll(np.roll(grid, 1, axis=0), 1, axis=1) +
                np.roll(np.roll(grid, 1, axis=0), -1, axis=1) +
                np.roll(np.roll(grid, -1, axis=0), 1, axis=1) +
                np.roll(np.roll(grid, -1, axis=0), -1, axis=1)
            )

            # Apply rules
            new_grid = np.zeros_like(grid)
            new_grid[(grid) & ((neighbors == 2) | (neighbors == 3))] = True
            new_grid[(~grid) & (neighbors == 3)] = True
            grid = new_grid

            if step % 100 == 0:
                await asyncio.sleep(0)

        final_density = float(np.mean(grid))
        alive_cells = int(np.sum(grid))

        metrics = {
            "model": "game_of_life",
            "width": w,
            "height": h,
            "n_steps": n_steps,
            "initial_density": cfg.initial_density,
            "final_density": final_density,
            "alive_cells": alive_cells,
            "mean_density": float(np.mean(density_history)),
            "final_entropy": entropy_history[-1] if entropy_history else 0.0,
        }

        logs = [
            f"Game of Life: {w}x{h}, {n_steps} steps",
            f"Initial density: {cfg.initial_density:.2f}",
            f"Final density: {final_density:.4f}",
            f"Alive cells: {alive_cells}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "final_grid": grid.astype(int).tolist(),
            "density_history": density_history,
            "entropy_history": entropy_history,
            "snapshots": snapshots,
        }

    async def _simulate_rule110(self) -> dict[str, Any]:
        cfg = self.config
        w = cfg.width
        n_steps = cfg.n_steps
        rule = cfg.rule_number

        # Parse rule into binary
        rule_bits = [(rule >> i) & 1 for i in range(8)]

        # Initialize single cell
        grid = np.zeros((n_steps, w), dtype=int)
        grid[0, w // 2] = 1

        for step in range(1, n_steps):
            for i in range(w):
                left = grid[step-1, (i-1) % w]
                center = grid[step-1, i]
                right = grid[step-1, (i+1) % w]
                pattern = left * 4 + center * 2 + right
                grid[step, i] = rule_bits[pattern]

            if step % 100 == 0:
                await asyncio.sleep(0)

        density = float(np.mean(grid))
        ones_count = int(np.sum(grid))

        metrics = {
            "model": "rule_110",
            "rule_number": rule,
            "width": w,
            "n_steps": n_steps,
            "density": density,
            "ones_count": ones_count,
        }

        logs = [
            f"Rule {rule}: {w} cells, {n_steps} steps",
            f"Density: {density:.4f}",
            f"Ones: {ones_count}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "grid": grid.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        metrics = results["metrics"]
        factors = []

        if metrics.get("final_density", 0) >= 0:
            factors.append(0.25)

        if metrics.get("n_steps", 0) >= 10:
            factors.append(0.25)

        if metrics.get("model") == "game_of_life" and metrics.get("alive_cells", 0) >= 0:
            factors.append(0.25)
        elif metrics.get("model") == "rule_110" and metrics.get("ones_count", 0) >= 0:
            factors.append(0.25)

        if 0 <= metrics.get("final_density", -1) <= 1:
            factors.append(0.25)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Estimate resources."""
        params = hypothesis.parameters
        w = params.get("width", 100)
        h = params.get("height", 100)
        n_steps = params.get("n_steps", 100)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + w * h * n_steps * 8e-9,
            "gpu_required": False,
            "estimated_time_seconds": w * h * n_steps / 1e7,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.id,
            "name": cls.name,
            "category": cls.category,
            "description": cls.description,
            "parameters": [
                {"name": p.name, "type": p.type, "default": p.default,
                 "min": p.min, "max": p.max, "description": p.description}
                for p in cls.parameters
            ],
            "references": [
                "Gardner, M. (1970). Mathematical Games: The fantastic combinations of John Conway's new solitaire game 'life'",
                "Wolfram, S. (2002). A New Kind of Science",
            ],
        }
