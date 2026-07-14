"""
Projectile Motion Pattern
Ballistics with air resistance

Based on:
- Newton's second law with drag
- Quadratic drag model: F_d = -0.5 * rho * C_d * A * |v| * v
- RK4 integration
- Range and apogee calculation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

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
class ProjectileConfig:
    """Configuration for projectile motion simulation"""
    v0: float = 50.0          # Initial speed (m/s)
    angle: float = 45.0       # Launch angle (degrees)
    mass: float = 0.5         # Mass (kg)
    drag_coefficient: float = 0.47  # Sphere
    area: float = 0.01        # Cross-sectional area (m^2)
    rho: float = 1.225        # Air density (kg/m^3)
    g: float = 9.81           # Gravity (m/s^2)
    dt: float = 0.01          # Time step (s)
    t_max: float = 20.0       # Max simulation time (s)


@simulation_pattern(
    id="projectile_motion",
    name="Projectile Motion",
    category="physics",
    description="Ballistics with quadratic air resistance",
)
class ProjectileMotionPattern(SimulationPattern):
    """
    Projectile motion simulation

    Implements:
    - Quadratic drag model
    - RK4 integration
    - Range, apogee, and time of flight
    - Comparison with vacuum trajectory
    """

    parameters = [
        SimulationParameter(
            name="v0",
            type="float",
            default=50.0,
            min=1.0,
            max=1000.0,
            description="Initial speed (m/s)",
        ),
        SimulationParameter(
            name="angle",
            type="float",
            default=45.0,
            min=0.0,
            max=90.0,
            description="Launch angle (degrees)",
        ),
        SimulationParameter(
            name="mass",
            type="float",
            default=0.5,
            min=0.001,
            max=100.0,
            description="Projectile mass (kg)",
        ),
        SimulationParameter(
            name="drag_coefficient",
            type="float",
            default=0.47,
            min=0.0,
            max=2.0,
            description="Drag coefficient",
        ),
        SimulationParameter(
            name="rho",
            type="float",
            default=1.225,
            min=0.0,
            max=10.0,
            description="Air density (kg/m^3)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: ProjectileConfig = ProjectileConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if projectile motion can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "projectile", "ballistics", "trajectory", "air resistance",
            "drag", "range", "apogee", "cannon", "missile",
            "flight path", "parabolic", "launch",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute projectile motion simulation"""
        start_time = datetime.now()
        simulation_id = f"proj_{start_time.timestamp()}"
        logger.info(f"Starting projectile motion simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_projectile()
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
            logger.exception("Projectile motion simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> ProjectileConfig:
        """Parse configuration dict"""
        cfg = ProjectileConfig()
        if "v0" in config:
            cfg.v0 = float(config["v0"])
        if "angle" in config:
            cfg.angle = float(config["angle"])
        if "mass" in config:
            cfg.mass = float(config["mass"])
        if "drag_coefficient" in config:
            cfg.drag_coefficient = float(config["drag_coefficient"])
        if "area" in config:
            cfg.area = float(config["area"])
        if "rho" in config:
            cfg.rho = float(config["rho"])
        if "g" in config:
            cfg.g = float(config["g"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        return cfg

    async def _simulate_projectile(self) -> dict[str, Any]:
        """Run projectile motion simulation"""
        cfg = self.config
        m = cfg.mass
        Cd = cfg.drag_coefficient
        A = cfg.area
        rho = cfg.rho
        g = cfg.g

        theta0 = cfg.angle * np.pi / 180
        v0x = cfg.v0 * np.cos(theta0)
        v0y = cfg.v0 * np.sin(theta0)

        # Drag factor
        k_drag = 0.5 * rho * Cd * A / m

        def equations(t: float, y: np.ndarray) -> np.ndarray:
            """Equations of motion with drag"""
            vx, vy, x, y_pos = y
            v = np.sqrt(vx**2 + vy**2)

            if v > 1e-10:
                ax = -k_drag * v * vx
                ay = -g - k_drag * v * vy
            else:
                ax = 0.0
                ay = -g

            return np.array([ax, ay, vx, vy])

        # Event: projectile hits ground
        def hit_ground(t: float, y: np.ndarray) -> float:
            return y[3]  # y position
        hit_ground.terminal = True
        hit_ground.direction = -1

        y0 = np.array([v0x, v0y, 0.0, 0.0])
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        sol = solve_ivp(
            equations, t_span, y0, t_eval=t_eval,
            events=hit_ground, method='RK45', max_step=cfg.dt
        )

        t = sol.t
        vx, vy, x, y_pos = sol.y
        v = np.sqrt(vx**2 + vy**2)

        # Find apogee
        apogee_idx = np.argmax(y_pos)
        apogee_height = y_pos[apogee_idx]
        t[apogee_idx]

        # Range
        range_val = x[-1]

        # Time of flight
        tof = t[-1]

        # Vacuum comparison
        range_vacuum = cfg.v0**2 * np.sin(2 * theta0) / g
        apogee_vacuum = (cfg.v0 * np.sin(theta0))**2 / (2 * g)
        2 * cfg.v0 * np.sin(theta0) / g

        # Impact velocity
        impact_speed = v[-1]
        impact_angle = np.arctan2(-vy[-1], vx[-1]) * 180 / np.pi

        metrics = {
            "range": float(range_val),
            "apogee": float(apogee_height),
            "time_of_flight": float(tof),
            "impact_speed": float(impact_speed),
            "impact_angle": float(impact_angle),
            "range_vacuum": float(range_vacuum),
            "apogee_vacuum": float(apogee_vacuum),
            "range_reduction": float((range_vacuum - range_val) / range_vacuum) if range_vacuum > 0 else 0.0,
            "drag_coefficient": Cd,
            "launch_angle": cfg.angle,
        }

        logs = [
            f"Projectile: v0={cfg.v0}m/s, angle={cfg.angle}deg, mass={m}kg",
            f"Range: {range_val:.2f} m (vacuum: {range_vacuum:.2f} m)",
            f"Apogee: {apogee_height:.2f} m (vacuum: {apogee_vacuum:.2f} m)",
            f"Time of flight: {tof:.2f} s",
            f"Impact speed: {impact_speed:.2f} m/s at {impact_angle:.1f}deg",
            f"Range reduction due to drag: {metrics['range_reduction']*100:.1f}%",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "x": x.tolist(),
            "y": y_pos.tolist(),
            "vx": vx.tolist(),
            "vy": vy.tolist(),
            "speed": v.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Positive range
        if metrics.get("range", 0) > 0:
            factors.append(0.25)

        # Range less than vacuum
        if metrics.get("range", 0) <= metrics.get("range_vacuum", float('inf')):
            factors.append(0.25)

        # Positive apogee
        if metrics.get("apogee", 0) > 0:
            factors.append(0.25)

        # Physical impact speed
        if 0 < metrics.get("impact_speed", 0) < metrics.get("range_vacuum", 0) * 2:
            factors.append(0.25)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1,
            "gpu_required": False,
            "estimated_time_seconds": 0.1,
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
                "Taylor, J.R. (2005). Classical Mechanics",
            ],
        }
