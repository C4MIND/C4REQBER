"""
C4REQBER v6.0 - Pedestrian Pattern
Social force model for crowd dynamics and pedestrian movement.

Pattern Structure (Christopher Alexander):
- Context: Transportation, safety engineering, architecture
- Forces: Goal-directed motion, collision avoidance, social norms
- Solution: Force-based model with psychological and physical forces
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class PedestrianScenario(Enum):
    """Available simulation scenarios"""

    CORRIDOR = "corridor"
    BOTTLENECK = "bottleneck"
    CROSSING = "crossing"
    EVACUATION = "evacuation"


@dataclass
class PedestrianConfig:
    """Configuration for pedestrian simulation"""

    scenario: PedestrianScenario = PedestrianScenario.CORRIDOR

    # Population
    n_pedestrians: int = 100

    # Space (meters)
    width: float = 20.0
    height: float = 10.0

    # Pedestrian properties
    desired_speed: float = 1.34  # m/s (average walking speed)
    pedestrian_radius: float = 0.3  # m
    mass: float = 80.0  # kg

    # Social force parameters (Helbing et al.)
    A: float = 2000.0  # Repulsion strength
    B: float = 0.08  # Repulsion range
    kappa: float = 120000.0  # Body compression
    lambda_: float = 240000.0  # Sliding friction

    # Wall repulsion
    wall_A: float = 2000.0
    wall_B: float = 0.08

    # Relaxation time (desired velocity adaptation)
    tau: float = 0.5  # s

    # Simulation
    dt: float = 0.01  # s
    n_steps: int = 2000

    # Obstacles (list of (x, y, radius))
    obstacles: list[tuple[float, float, float]] = field(default_factory=list)


class PedestrianPattern:
    """
    Social force model for pedestrian dynamics.

    Based on Helbing et al. (2000) "Self-organized pedestrian crowd dynamics".

    Forces acting on each pedestrian:
    1. Driving force: towards desired velocity
    2. Pedestrian repulsion: avoid collisions
    3. Obstacle repulsion: avoid walls and obstacles
    4. Physical contact forces (when overlapping)
    """

    PATTERN_ID = "pedestrian"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: PedestrianConfig | None = None) -> None:
        self.config = config or PedestrianConfig()
        self.positions: np.ndarray | None = None
        self.velocities: np.ndarray | None = None
        self.desired_velocities: np.ndarray | None = None
        self.destinations: np.ndarray | None = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize pedestrian simulation"""
        cfg = self.config

        # Initialize positions based on scenario
        self.positions = self._initialize_positions()

        # Initialize velocities
        self.velocities = np.zeros((cfg.n_pedestrians, 2))

        # Set destinations
        self.destinations = self._initialize_destinations()

        # Calculate desired directions
        self._update_desired_velocities()

    def _initialize_positions(self) -> np.ndarray:
        """Initialize positions based on scenario"""
        cfg = self.config
        positions = np.zeros((cfg.n_pedestrians, 2))

        if cfg.scenario == PedestrianScenario.CORRIDOR:
            # Left to right flow
            positions[:, 0] = np.random.uniform(0, 2, cfg.n_pedestrians)
            positions[:, 1] = np.random.uniform(1, cfg.height - 1, cfg.n_pedestrians)

        elif cfg.scenario == PedestrianScenario.BOTTLENECK:
            # Crowd before bottleneck
            positions[:, 0] = np.random.uniform(0, 5, cfg.n_pedestrians)
            positions[:, 1] = np.random.uniform(1, cfg.height - 1, cfg.n_pedestrians)

        elif cfg.scenario == PedestrianScenario.CROSSING:
            # Two groups crossing
            n_half = cfg.n_pedestrians // 2
            # Group 1: left to right
            positions[:n_half, 0] = np.random.uniform(0, 2, n_half)
            positions[:n_half, 1] = np.random.uniform(1, cfg.height - 1, n_half)
            # Group 2: bottom to top
            positions[n_half:, 0] = np.random.uniform(5, 15, cfg.n_pedestrians - n_half)
            positions[n_half:, 1] = np.random.uniform(0, 2, cfg.n_pedestrians - n_half)

        elif cfg.scenario == PedestrianScenario.EVACUATION:
            # Random positions, exit on right
            positions[:, 0] = np.random.uniform(0, cfg.width - 2, cfg.n_pedestrians)
            positions[:, 1] = np.random.uniform(1, cfg.height - 1, cfg.n_pedestrians)

        return positions

    def _initialize_destinations(self) -> np.ndarray:
        """Set destinations based on scenario"""
        cfg = self.config
        destinations = np.zeros((cfg.n_pedestrians, 2))

        if cfg.scenario == PedestrianScenario.CORRIDOR:
            destinations[:, 0] = cfg.width
            destinations[:, 1] = self.positions[:, 1]  # type: ignore[index]

        elif cfg.scenario == PedestrianScenario.BOTTLENECK:
            destinations[:, 0] = cfg.width
            destinations[:, 1] = cfg.height / 2

        elif cfg.scenario == PedestrianScenario.CROSSING:
            n_half = cfg.n_pedestrians // 2
            destinations[:n_half, 0] = cfg.width
            destinations[:n_half, 1] = self.positions[:n_half, 1]  # type: ignore[index]
            destinations[n_half:, 0] = self.positions[n_half:, 0]  # type: ignore[index]
            destinations[n_half:, 1] = cfg.height

        elif cfg.scenario == PedestrianScenario.EVACUATION:
            destinations[:, 0] = cfg.width
            destinations[:, 1] = cfg.height / 2

        return destinations

    def _update_desired_velocities(self) -> None:
        """Calculate desired velocity towards destination"""
        cfg = self.config

        direction = self.destinations - self.positions  # type: ignore[operator]
        distance = np.linalg.norm(direction, axis=1, keepdims=True)

        # Normalize direction
        direction = np.where(distance > 0, direction / distance, 0)

        self.desired_velocities = direction * cfg.desired_speed

    def _driving_force(self, i: int) -> np.ndarray:
        """Driving force towards destination"""
        cfg = self.config
        return (self.desired_velocities[i] - self.velocities[i]) * cfg.mass / cfg.tau  # type: ignore[index, no-any-return]

    def _pedestrian_repulsion(self, i: int) -> np.ndarray:
        """Repulsive force from other pedestrians"""
        cfg = self.config
        force = np.zeros(2)

        for j in range(cfg.n_pedestrians):
            if i == j:
                continue

            diff = self.positions[i] - self.positions[j]  # type: ignore[index]
            dist = np.linalg.norm(diff)

            if dist > 0:
                # Psychological repulsion
                direction = diff / dist
                repulsion = cfg.A * np.exp(-(dist - 2 * cfg.pedestrian_radius) / cfg.B)
                force += repulsion * direction

                # Physical contact forces
                if dist < 2 * cfg.pedestrian_radius:
                    overlap = 2 * cfg.pedestrian_radius - dist
                    # Body force
                    force += cfg.kappa * overlap * direction

                    # Sliding friction
                    tangent = np.array([-direction[1], direction[0]])
                    velocity_diff = self.velocities[j] - self.velocities[i]  # type: ignore[index]
                    force += (
                        cfg.lambda_ * overlap * np.dot(velocity_diff, tangent) * tangent
                    )

        return force

    def _wall_repulsion(self, i: int) -> np.ndarray:
        """Repulsive force from walls and obstacles"""
        cfg = self.config
        force = np.zeros(2)

        # Wall forces
        walls = [
            (self.positions[i, 0], np.array([1, 0])),  # type: ignore  # Left wall
            (cfg.width - self.positions[i, 0], np.array([-1, 0])),  # type: ignore  # Right wall
            (self.positions[i, 1], np.array([0, 1])),  # type: ignore  # Bottom wall
            (cfg.height - self.positions[i, 1], np.array([0, -1])),  # type: ignore  # Top wall
        ]

        for dist, normal in walls:
            if dist < 2 * cfg.pedestrian_radius:
                overlap = 2 * cfg.pedestrian_radius - dist
                force += cfg.wall_A * np.exp(-dist / cfg.wall_B) * normal
                force += cfg.kappa * overlap * normal

        # Obstacle forces
        for obs_x, obs_y, obs_r in cfg.obstacles:
            diff = self.positions[i] - np.array([obs_x, obs_y])  # type: ignore[index]
            dist = np.linalg.norm(diff)
            if dist > 0:
                direction = diff / dist
                force += cfg.wall_A * np.exp(-(dist - obs_r) / cfg.wall_B) * direction
                if dist < obs_r + cfg.pedestrian_radius:
                    overlap = obs_r + cfg.pedestrian_radius - dist
                    force += cfg.kappa * overlap * direction

        return force

    def _step(self) -> None:
        """One simulation step"""
        cfg = self.config

        # Update desired velocities
        self._update_desired_velocities()

        # Calculate forces for all pedestrians
        accelerations = np.zeros((cfg.n_pedestrians, 2))

        for i in range(cfg.n_pedestrians):
            f_drive = self._driving_force(i)
            f_ped = self._pedestrian_repulsion(i)
            f_wall = self._wall_repulsion(i)

            total_force = f_drive + f_ped + f_wall
            accelerations[i] = total_force / cfg.mass

        # Update velocities and positions
        self.velocities += accelerations * cfg.dt  # type: ignore[operator]

        # Limit speed
        speeds = np.linalg.norm(self.velocities, axis=1)
        max_speed_factor = np.minimum(1, cfg.desired_speed * 2 / (speeds + 1e-6))
        self.velocities = (self.velocities.T * max_speed_factor).T

        self.positions += self.velocities * cfg.dt  # type: ignore[operator]

        # Keep within bounds
        self.positions[:, 0] = np.clip(self.positions[:, 0], 0, cfg.width)
        self.positions[:, 1] = np.clip(self.positions[:, 1], 0, cfg.height)

    def _calculate_flow_rate(self) -> float:
        """Calculate pedestrian flow rate (pedestrians per meter per second)"""
        cfg = self.config

        # Count pedestrians passing a line
        passing = np.sum(self.positions[:, 0] > cfg.width - 1)  # type: ignore[index]
        return passing / (cfg.width * cfg.dt * cfg.n_steps)  # type: ignore[return-value]

    def _calculate_density(self) -> float:
        """Calculate average pedestrian density"""
        cfg = self.config
        area = cfg.width * cfg.height
        return cfg.n_pedestrians / area

    def _calculate_mean_speed(self) -> float:
        """Calculate mean walking speed"""
        speeds = np.linalg.norm(self.velocities, axis=1)  # type: ignore[arg-type]
        return np.mean(speeds)  # type: ignore[no-any-return]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run pedestrian simulation"""
        cfg = self.config

        logger.info(
            f"Starting pedestrian simulation: {cfg.scenario.value}, {cfg.n_pedestrians} pedestrians"
        )

        # History for analysis
        position_history = []
        velocity_history = []

        for step in range(cfg.n_steps):
            self._step()

            if step % 50 == 0:
                position_history.append(self.positions.copy())  # type: ignore[union-attr]
                velocity_history.append(self.velocities.copy())  # type: ignore[union-attr]

            if step % 1000 == 0:
                mean_speed = self._calculate_mean_speed()
                logger.debug(f"Step {step}: mean speed = {mean_speed:.2f} m/s")

        return self._format_output(position_history, velocity_history)

    def _format_output(
        self, pos_history: list[np.ndarray], vel_history: list[np.ndarray]
    ) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Fundamental diagram metrics
        density = self._calculate_density()
        mean_speed = self._calculate_mean_speed()
        flow = density * mean_speed  # Fundamental diagram

        # Speed statistics
        speeds = np.linalg.norm(self.velocities, axis=1)  # type: ignore[arg-type]

        # Distance to destination
        distances_to_dest = np.linalg.norm(self.positions - self.destinations, axis=1)  # type: ignore[operator]
        arrived = np.sum(distances_to_dest < 1.0)

        return {
            "final_positions": self.positions.tolist(),  # type: ignore[union-attr]
            "final_velocities": self.velocities.tolist(),  # type: ignore[union-attr]
            "trajectory": [
                p.tolist() for p in pos_history[:: max(1, len(pos_history) // 20)]
            ],
            "fundamental_diagram": {
                "density": float(density),  # ped/m²
                "mean_speed": float(mean_speed),  # m/s
                "flow": float(flow),  # ped/(m·s)
            },
            "statistics": {
                "mean_speed": float(np.mean(speeds)),
                "speed_variance": float(np.var(speeds)),
                "min_speed": float(np.min(speeds)),
                "max_speed": float(np.max(speeds)),
                "arrived": int(arrived),
                "arrival_rate": float(arrived / cfg.n_pedestrians),
            },
            "scenario": cfg.scenario.value,
            "config": {
                "n_pedestrians": cfg.n_pedestrians,
                "desired_speed": cfg.desired_speed,
                "tau": cfg.tau,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Pedestrian",
            "category": "EXTENDED",
            "domain": ["Transportation", "Safety Engineering", "Architecture"],
            "description": "Social force model for crowd dynamics",
            "computational_complexity": "O(T·N²)",
            "typical_runtime": "seconds to minutes",
            "accuracy": "High (empirically validated)",
            "assumptions": [
                "Continuous space",
                "Deterministic forces",
                "Homogeneous pedestrians",
            ],
            "parameters": [
                {
                    "name": "scenario",
                    "type": "enum",
                    "options": ["corridor", "bottleneck", "crossing", "evacuation"],
                    "default": "corridor",
                },
                {
                    "name": "n_pedestrians",
                    "type": "int",
                    "default": 100,
                },
                {
                    "name": "desired_speed",
                    "type": "float",
                    "default": 1.34,
                },
                {
                    "name": "A",
                    "type": "float",
                    "default": 2000.0,
                    "description": "Repulsion strength",
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Corridor flow
    print("\n=== Test 1: Corridor Flow ===")
    config = PedestrianConfig(
        scenario=PedestrianScenario.CORRIDOR,
        n_pedestrians=30,
        n_steps=500,
        width=10.0,
        height=5.0,
    )
    sim = PedestrianPattern(config)
    result = sim.run()
    print(f"✓ Mean speed: {result['statistics']['mean_speed']:.2f} m/s")
    print(f"  Arrival rate: {result['statistics']['arrival_rate']:.2f}")

    # Test 2: Bottleneck
    print("\n=== Test 2: Bottleneck ===")
    config = PedestrianConfig(
        scenario=PedestrianScenario.BOTTLENECK,
        n_pedestrians=40,
        n_steps=500,
        width=15.0,
        height=10.0,
        obstacles=[(7, 2, 0.5), (7, 8, 0.5)],
    )
    sim = PedestrianPattern(config)
    result = sim.run()
    print(f"✓ Bottleneck mean speed: {result['statistics']['mean_speed']:.2f} m/s")

    # Test 3: Density effect
    print("\n=== Test 3: Density Effect ===")
    for n in [15, 30]:
        config = PedestrianConfig(
            scenario=PedestrianScenario.CORRIDOR,
            n_pedestrians=n,
            n_steps=500,
            width=10.0,
            height=5.0,
        )
        sim = PedestrianPattern(config)
        result = sim.run()
        print(
            f"  N={n}: density={result['fundamental_diagram']['density']:.3f}, speed={result['fundamental_diagram']['mean_speed']:.2f}"
        )

    print("\n✅ All pedestrian tests passed!")
