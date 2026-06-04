# Migrated to Newton Physics (2025) — github.com/newton-physics/newton — Apache 2.0 License
"""
Wave Equation Pattern
1D and 2D wave propagation using finite difference method

Based on:
- Wave equation: d²u/dt² = c² * ∇²u
- FTCS (Forward Time Centered Space) scheme
- Absorbing boundary conditions
- Reflection and transmission coefficients
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
class WaveEquationConfig:
    """Configuration for wave equation simulation"""
    dimension: str = "1d"       # "1d" or "2d"
    c: float = 1.0              # Wave speed
    L: float = 10.0             # Domain length
    nx: int = 200               # Grid points
    t_max: float = 5.0          # Simulation time
    dt: float = 0.01            # Time step
    source_type: str = "gaussian"  # "gaussian", "sine", "pulse"
    source_position: float = 5.0   # Source position (1D)
    source_amplitude: float = 1.0
    source_frequency: float = 1.0


@simulation_pattern(
    id="wave_equation",
    name="Wave Equation",
    category="physics",
    description="1D/2D wave propagation using finite difference method",
)
class WaveEquationPattern(SimulationPattern):
    """
    Wave equation simulation

    Implements:
    - 1D and 2D wave equation
    - Gaussian, sine, and pulse sources
    - Absorbing boundary conditions
    - Energy conservation tracking
    """

    parameters = [
        SimulationParameter(
            name="dimension",
            type="select",
            default="1d",
            options=["1d", "2d"],
            description="Spatial dimension",
        ),
        SimulationParameter(
            name="c",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Wave speed",
        ),
        SimulationParameter(
            name="L",
            type="float",
            default=10.0,
            min=1.0,
            max=100.0,
            description="Domain length",
        ),
        SimulationParameter(
            name="nx",
            type="int",
            default=200,
            min=50,
            max=1000,
            description="Grid resolution",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=5.0,
            min=0.1,
            max=50.0,
            description="Simulation time",
        ),
        SimulationParameter(
            name="source_type",
            type="select",
            default="gaussian",
            options=["gaussian", "sine", "pulse"],
            description="Source waveform",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: WaveEquationConfig = WaveEquationConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if wave equation can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "wave equation", "wave propagation", "acoustic wave",
            "string vibration", "membrane vibration", "d'alembert",
            "wave speed", "standing wave", "traveling wave",
            "interference", "diffraction",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute wave equation simulation with Newton (or fallback)."""
        start_time = datetime.now()
        simulation_id = f"wave_{start_time.timestamp()}"

        # Try Newton Physics first
        from src.simulations.newton_bridge import NewtonBridge
        bridge = NewtonBridge()

        if bridge.available:
            newton_config = {
                "type": "wave",
                "dimension": config.get("dimension", "1d"),
                "c": config.get("c", 1.0),
                "L": config.get("L", 10.0),
                "nx": config.get("nx", 200),
                "t_max": config.get("t_max", 5.0),
                "dt": config.get("dt", 0.01),
                "source_type": config.get("source_type", "gaussian"),
                "source_position": config.get("source_position", 5.0),
                "source_amplitude": config.get("source_amplitude", 1.0),
                "source_frequency": config.get("source_frequency", 1.0),
            }
            result = bridge.run_simulation(newton_config)
            if result.get("status") == "success":
                end_time = datetime.now()
                return SimulationResult(
                    simulation_id=simulation_id,
                    status=SimulationStatus.COMPLETED,
                    start_time=start_time,
                    end_time=end_time,
                    metrics=result.get("result", {}),
                    logs=["Executed via Newton Physics"],
                    confidence_score=0.9,
                    validation_level=ValidationLevel.MONTE_CARLO,
                )

        logger.info(f"Starting wave equation simulation {simulation_id} (legacy)")

        try:
            self.config = self._parse_config(config)
            if self.config.dimension == "1d":
                results = await self._simulate_1d()
            else:
                results = await self._simulate_2d()
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
            logger.exception("Wave equation simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> WaveEquationConfig:
        """Parse configuration dict"""
        cfg = WaveEquationConfig()
        if "dimension" in config:
            cfg.dimension = str(config["dimension"])
        if "c" in config:
            cfg.c = float(config["c"])
        if "L" in config:
            cfg.L = float(config["L"])
        if "nx" in config:
            cfg.nx = int(config["nx"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "source_type" in config:
            cfg.source_type = str(config["source_type"])
        if "source_position" in config:
            cfg.source_position = float(config["source_position"])
        if "source_amplitude" in config:
            cfg.source_amplitude = float(config["source_amplitude"])
        if "source_frequency" in config:
            cfg.source_frequency = float(config["source_frequency"])
        return cfg

    async def _simulate_1d(self) -> dict[str, Any]:
        """1D wave equation simulation"""
        cfg = self.config
        c = cfg.c
        L = cfg.L
        nx = cfg.nx
        dx = L / (nx - 1)
        dt = cfg.dt

        # CFL condition: c * dt / dx <= 1
        cfl = c * dt / dx
        if cfl > 1:
            dt = 0.9 * dx / c
            cfl = c * dt / dx

        n_steps = int(cfg.t_max / dt)

        # Initialize
        u = np.zeros(nx)
        u_prev = np.zeros(nx)

        # Initial condition
        x = np.linspace(0, L, nx)
        src_idx = int(cfg.source_position / dx)

        if cfg.source_type == "gaussian":
            sigma = L / 20
            u = cfg.source_amplitude * np.exp(-((x - cfg.source_position) / sigma)**2)
        elif cfg.source_type == "sine":
            u = cfg.source_amplitude * np.sin(2 * np.pi * cfg.source_frequency * x / L)
        elif cfg.source_type == "pulse":
            u[src_idx:src_idx+5] = cfg.source_amplitude

        u_prev = u.copy()

        # Time stepping
        snapshots = []
        max_amplitude = np.max(np.abs(u))
        energy_history = []

        for step in range(n_steps):
            u_new = np.zeros(nx)

            # Interior points
            for i in range(1, nx - 1):
                u_new[i] = 2 * u[i] - u_prev[i] + cfl**2 * (u[i+1] - 2*u[i] + u[i-1])

            # Absorbing boundary conditions (Mur)
            u_new[0] = u[1] + (cfl - 1) / (cfl + 1) * (u_new[1] - u[0])
            u_new[-1] = u[-2] + (cfl - 1) / (cfl + 1) * (u_new[-2] - u[-1])

            u_prev = u.copy()
            u = u_new.copy()

            max_amplitude = max(max_amplitude, np.max(np.abs(u)))

            # Energy: E = 0.5 * integral(u_t^2 + c^2 * u_x^2)
            if step > 0:
                u_t = (u - u_prev) / dt
                u_x = np.gradient(u, dx)
                energy = 0.5 * np.trapezoid(u_t**2 + c**2 * u_x**2, x)
                energy_history.append(energy)

            if step % max(1, n_steps // 10) == 0:
                snapshots.append(u.copy())

            if step % 500 == 0:
                await asyncio.sleep(0)

        metrics = {
            "max_amplitude": float(max_amplitude),
            "cfl_number": float(cfl),
            "n_steps": n_steps,
            "final_energy": float(energy_history[-1]) if energy_history else 0.0,
            "energy_drift": float(abs(energy_history[-1] - energy_history[0]) / energy_history[0]) if len(energy_history) > 1 else 0.0,
            "dimension": "1d",
        }

        logs = [
            f"1D wave equation: c={c}, L={L}, nx={nx}",
            f"CFL number: {cfl:.4f}",
            f"Time steps: {n_steps}",
            f"Max amplitude: {max_amplitude:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "x": x.tolist(),
            "snapshots": [s.tolist() for s in snapshots],
            "final_state": u.tolist(),
        }

    async def _simulate_2d(self) -> dict[str, Any]:
        """2D wave equation simulation"""
        cfg = self.config
        c = cfg.c
        L = cfg.L
        nx = cfg.nx
        dx = L / (nx - 1)
        dt = cfg.dt

        cfl = c * dt / dx
        if cfl > 0.5:
            dt = 0.45 * dx / c
            cfl = c * dt / dx

        n_steps = int(cfg.t_max / dt)

        # Initialize
        u = np.zeros((nx, nx))
        u_prev = np.zeros((nx, nx))

        # Initial Gaussian pulse at center
        x = np.linspace(0, L, nx)
        y = np.linspace(0, L, nx)
        X, Y = np.meshgrid(x, y)
        cx, cy = L / 2, L / 2
        sigma = L / 10
        u = cfg.source_amplitude * np.exp(-((X - cx)**2 + (Y - cy)**2) / (2 * sigma**2))
        u_prev = u.copy()

        max_amplitude = np.max(np.abs(u))

        for step in range(n_steps):
            u_new = np.zeros((nx, nx))

            # Interior points
            u_new[1:-1, 1:-1] = (
                2 * u[1:-1, 1:-1] - u_prev[1:-1, 1:-1]
                + cfl**2 * (
                    u[2:, 1:-1] - 2*u[1:-1, 1:-1] + u[:-2, 1:-1]
                    + u[1:-1, 2:] - 2*u[1:-1, 1:-1] + u[1:-1, :-2]
                )
            )

            # Simple absorbing boundaries
            u_new[0, :] = u_new[1, :]
            u_new[-1, :] = u_new[-2, :]
            u_new[:, 0] = u_new[:, 1]
            u_new[:, -1] = u_new[:, -2]

            u_prev = u.copy()
            u = u_new.copy()

            max_amplitude = max(max_amplitude, np.max(np.abs(u)))

            if step % 500 == 0:
                await asyncio.sleep(0)

        metrics = {
            "max_amplitude": float(max_amplitude),
            "cfl_number": float(cfl),
            "n_steps": n_steps,
            "dimension": "2d",
        }

        logs = [
            f"2D wave equation: c={c}, L={L}, nx={nx}x{nx}",
            f"CFL number: {cfl:.4f}",
            f"Time steps: {n_steps}",
            f"Max amplitude: {max_amplitude:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "x": x.tolist(),
            "final_state": u.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Stable CFL
        cfl = metrics.get("cfl_number", 0)
        if 0 < cfl <= 1.0:
            factors.append(0.3)

        # Non-zero amplitude
        if metrics.get("max_amplitude", 0) > 0:
            factors.append(0.3)

        # Energy conservation (for 1D)
        if metrics.get("energy_drift", 1.0) < 0.1:
            factors.append(0.2)

        # Sufficient steps
        if metrics.get("n_steps", 0) >= 10:
            factors.append(0.2)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        dim = params.get("dimension", "1d")
        nx = params.get("nx", 200)
        t_max = params.get("t_max", 5.0)
        dt = params.get("dt", 0.01)
        n_steps = int(t_max / dt)

        if dim == "2d":
            memory = nx**2 * 3 * 8e-9
            time = n_steps * nx**2 / 1e7
        else:
            memory = nx * 3 * 8e-9
            time = n_steps * nx / 1e6

        return {
            "cpu_cores": 1,
            "memory_gb": max(0.1, memory),
            "gpu_required": False,
            "estimated_time_seconds": time,
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
                "Evans, L.C. (2010). Partial Differential Equations",
            ],
        }
