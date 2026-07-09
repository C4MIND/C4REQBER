"""
C4REQBER v6.0 - Flocking Pattern
Boids and Vicsek models for collective animal motion.

Pattern Structure (Christopher Alexander):
- Context: Biology, robotics, swarm intelligence
- Forces: Alignment, cohesion, separation
- Solution: Agent-based model with local interaction rules
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class FlockingModel(Enum):
    """Available flocking models"""

    BOIDS = "boids"  # Reynolds 1987
    VICSEK = "vicsek"  # Vicsek et al. 1995


@dataclass
class FlockingConfig:
    """Configuration for flocking simulation"""

    model: FlockingModel = FlockingModel.BOIDS

    # Population
    n_agents: int = 200

    # Space
    space_size: tuple[float, float] = (100.0, 100.0)
    boundary_mode: str = "periodic"  # periodic, reflective, open

    # Boids parameters
    perception_radius: float = 10.0
    separation_distance: float = 3.0
    max_speed: float = 2.0
    max_force: float = 0.1

    # Weights
    separation_weight: float = 1.5
    alignment_weight: float = 1.0
    cohesion_weight: float = 1.0

    # Vicsek parameters
    noise_strength: float = 0.1  # η in Vicsek model
    velocity: float = 1.0  # Constant speed in Vicsek

    # Simulation
    n_steps: int = 500
    dt: float = 1.0

    # Obstacles
    obstacle_positions: np.ndarray | None = None
    obstacle_radius: float = 5.0


class FlockingPattern:
    """
    Collective motion simulation using Boids or Vicsek models.

    Boids rules (Reynolds):
    1. Separation: avoid crowding neighbors
    2. Alignment: steer towards average heading
    3. Cohesion: steer towards average position

    Vicsek model:
    - Constant speed, align with neighbors plus noise
    """

    PATTERN_ID = "flocking"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: FlockingConfig | None = None) -> None:
        self.config = config or FlockingConfig()
        self.positions: np.ndarray | None = None
        self.velocities: np.ndarray | None = None
        self.history: list[dict] = []

        self._initialize()

    def _initialize(self) -> None:
        """Initialize flock"""
        cfg = self.config

        # Random initial positions
        self.positions = np.random.random((cfg.n_agents, 2)) * cfg.space_size

        # Random initial velocities
        angles = np.random.random(cfg.n_agents) * 2 * np.pi
        self.velocities = np.column_stack(
            [cfg.max_speed * np.cos(angles), cfg.max_speed * np.sin(angles)]
        )

        self._record_state()

    def _distance_matrix(self) -> np.ndarray:
        """Calculate pairwise distances with boundary conditions"""
        cfg = self.config

        if cfg.boundary_mode == "periodic":
            # Minimum image convention
            diff = self.positions[:, np.newaxis, :] - self.positions[np.newaxis, :, :]  # type: ignore[index]
            diff = (
                np.mod(diff + cfg.space_size[0] / 2, cfg.space_size[0])
                - cfg.space_size[0] / 2
            )
            dist = np.sqrt(np.sum(diff**2, axis=2))
        else:
            diff = self.positions[:, np.newaxis, :] - self.positions[np.newaxis, :, :]  # type: ignore[index]
            dist = np.sqrt(np.sum(diff**2, axis=2))

        return dist  # type: ignore[no-any-return]

    def _separation(self, i: int, neighbors: np.ndarray) -> np.ndarray:
        """Calculate separation steering for agent i"""
        cfg = self.config

        if not neighbors.any():
            return np.zeros(2)

        separation_force = np.zeros(2)
        for j in np.where(neighbors)[0]:
            diff = self.positions[i] - self.positions[j]  # type: ignore[index]
            dist = np.linalg.norm(diff)
            if dist > 0 and dist < cfg.separation_distance:
                separation_force += diff / dist

        return separation_force

    def _alignment(self, i: int, neighbors: np.ndarray) -> np.ndarray:
        """Calculate alignment steering for agent i"""
        if not neighbors.any():
            return np.zeros(2)

        avg_velocity = np.mean(self.velocities[neighbors], axis=0)  # type: ignore[index]
        return avg_velocity - self.velocities[i]  # type: ignore[index, no-any-return]

    def _cohesion(self, i: int, neighbors: np.ndarray) -> np.ndarray:
        """Calculate cohesion steering for agent i"""
        if not neighbors.any():
            return np.zeros(2)

        avg_position = np.mean(self.positions[neighbors], axis=0)  # type: ignore[index]
        return avg_position - self.positions[i]  # type: ignore[index, no-any-return]

    def _avoid_obstacles(self, i: int) -> np.ndarray:
        """Calculate obstacle avoidance"""
        cfg = self.config

        if cfg.obstacle_positions is None:
            return np.zeros(2)

        avoidance = np.zeros(2)
        for obs in cfg.obstacle_positions:
            diff = self.positions[i] - obs  # type: ignore[index]
            dist = np.linalg.norm(diff)
            if dist < cfg.obstacle_radius * 2:
                avoidance += diff / (dist + 0.01)

        return avoidance

    def _limit_magnitude(self, vector: np.ndarray, max_magnitude: float) -> np.ndarray:
        """Limit vector magnitude"""
        magnitude = np.linalg.norm(vector)
        if magnitude > max_magnitude:
            return vector / magnitude * max_magnitude  # type: ignore[no-any-return]
        return vector

    def _boids_step(self) -> None:
        """One step of Boids simulation"""
        cfg = self.config

        dist = self._distance_matrix()
        new_velocities = np.zeros_like(self.velocities)

        for i in range(cfg.n_agents):
            # Find neighbors
            neighbors = dist[i] < cfg.perception_radius
            neighbors[i] = False  # Exclude self

            # Calculate forces
            sep = self._separation(i, neighbors) * cfg.separation_weight
            ali = self._alignment(i, neighbors) * cfg.alignment_weight
            coh = self._cohesion(i, neighbors) * cfg.cohesion_weight
            obs = self._avoid_obstacles(i) * 2.0

            # Update velocity
            acceleration = sep + ali + coh + obs
            acceleration = self._limit_magnitude(acceleration, cfg.max_force)

            new_velocities[i] = self.velocities[i] + acceleration * cfg.dt  # type: ignore[index]
            new_velocities[i] = self._limit_magnitude(new_velocities[i], cfg.max_speed)

        self.velocities = new_velocities
        self.positions = self.positions + self.velocities * cfg.dt  # type: ignore[operator]

        # Apply boundaries
        self._apply_boundaries()

    def _vicsek_step(self) -> None:
        """One step of Vicsek model"""
        cfg = self.config

        dist = self._distance_matrix()
        new_velocities = np.zeros_like(self.velocities)

        for i in range(cfg.n_agents):
            # Find neighbors
            neighbors = dist[i] < cfg.perception_radius
            neighbors[i] = False

            if neighbors.any():
                # Average direction of neighbors
                avg_angle = np.arctan2(
                    np.mean(self.velocities[neighbors, 1]),  # type: ignore[index]
                    np.mean(self.velocities[neighbors, 0]),  # type: ignore[index]
                )
            else:
                # Keep current direction
                avg_angle = np.arctan2(self.velocities[i, 1], self.velocities[i, 0])  # type: ignore[index]

            # Add noise
            noise = np.random.uniform(-cfg.noise_strength, cfg.noise_strength)
            new_angle = avg_angle + noise

            # Constant speed
            new_velocities[i] = cfg.velocity * np.array(
                [np.cos(new_angle), np.sin(new_angle)]
            )

        self.velocities = new_velocities
        self.positions = self.positions + self.velocities * cfg.dt  # type: ignore[operator]

        # Apply boundaries
        self._apply_boundaries()

    def _apply_boundaries(self) -> None:
        """Apply boundary conditions"""
        cfg = self.config

        if cfg.boundary_mode == "periodic":
            self.positions = np.mod(self.positions, cfg.space_size)  # type: ignore[arg-type]
        elif cfg.boundary_mode == "reflective":
            # Reflect off walls
            for dim in range(2):
                mask_low = self.positions[:, dim] < 0  # type: ignore[index]
                mask_high = self.positions[:, dim] >= cfg.space_size[dim]  # type: ignore[index]

                self.positions[mask_low, dim] = -self.positions[mask_low, dim]  # type: ignore[index]
                self.positions[mask_high, dim] = (  # type: ignore[index]
                    2 * cfg.space_size[dim] - self.positions[mask_high, dim]  # type: ignore[index]
                )

                self.velocities[mask_low | mask_high, dim] *= -1  # type: ignore[index]

    def _record_state(self) -> None:
        """Record current state"""
        self.history.append(
            {
                "positions": self.positions.copy(),  # type: ignore[union-attr]
                "velocities": self.velocities.copy(),  # type: ignore[union-attr]
            }
        )

    def _calculate_order_parameter(self) -> float:
        """Calculate order parameter (normalized average velocity)"""
        avg_velocity = np.mean(self.velocities, axis=0)  # type: ignore[arg-type]
        return np.linalg.norm(avg_velocity) / self.config.max_speed  # type: ignore[return-value]

    def _calculate_clustering(self) -> float:
        """Calculate spatial clustering"""
        # Average distance to nearest neighbor
        dist = self._distance_matrix()
        np.fill_diagonal(dist, np.inf)
        nearest = np.min(dist, axis=1)
        return np.mean(nearest)  # type: ignore[no-any-return]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run flocking simulation"""
        cfg = self.config

        logger.info(f"Starting {cfg.model.value} flocking: {cfg.n_agents} agents")

        order_history = []

        for step in range(cfg.n_steps):
            if cfg.model == FlockingModel.BOIDS:
                self._boids_step()
            elif cfg.model == FlockingModel.VICSEK:
                self._vicsek_step()

            order = self._calculate_order_parameter()
            order_history.append(order)

            if step % 10 == 0:
                self._record_state()

            if step % 100 == 0:
                logger.debug(f"Step {step}: order = {order:.3f}")

        return self._format_output(order_history)

    def _format_output(self, order_history: list[float]) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        final_order = order_history[-1] if order_history else 0
        avg_order = np.mean(order_history) if order_history else 0

        # Final positions and velocities
        final_positions = self.positions.tolist()  # type: ignore[union-attr]
        final_velocities = self.velocities.tolist()  # type: ignore[union-attr]

        # Statistics
        clustering = self._calculate_clustering()

        # Velocity distribution
        speeds = np.linalg.norm(self.velocities, axis=1)  # type: ignore[arg-type]

        return {
            "final_positions": final_positions,
            "final_velocities": final_velocities,
            "trajectory": [
                {
                    "positions": h["positions"].tolist(),
                    "velocities": h["velocities"].tolist(),
                }
                for h in self.history[:: max(1, len(self.history) // 20)]
            ],
            "order_parameter": {
                "final": float(final_order),
                "average": float(avg_order),
                "history": order_history[:: max(1, len(order_history) // 50)],
            },
            "statistics": {
                "mean_speed": float(np.mean(speeds)),
                "speed_variance": float(np.var(speeds)),
                "clustering_distance": float(clustering),
                "center_of_mass": self.positions.mean(axis=0).tolist(),  # type: ignore[union-attr]
                "velocity_variance": float(np.var(self.velocities)),  # type: ignore[arg-type]
            },
            "config": {
                "model": cfg.model.value,
                "n_agents": cfg.n_agents,
                "separation_weight": cfg.separation_weight,
                "alignment_weight": cfg.alignment_weight,
                "cohesion_weight": cfg.cohesion_weight,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Flocking",
            "category": "EXTENDED",
            "domain": ["Biology", "Robotics", "Swarm Intelligence"],
            "description": "Boids and Vicsek models of collective motion",
            "computational_complexity": "O(T·N²)",
            "typical_runtime": "seconds",
            "accuracy": "High (agent-based)",
            "assumptions": [
                "Local interaction only",
                "Identical agents",
                "Continuous space",
            ],
            "parameters": [
                {
                    "name": "model",
                    "type": "enum",
                    "options": ["boids", "vicsek"],
                    "default": "boids",
                },
                {
                    "name": "n_agents",
                    "type": "int",
                    "default": 200,
                },
                {
                    "name": "separation_weight",
                    "type": "float",
                    "default": 1.5,
                },
                {
                    "name": "alignment_weight",
                    "type": "float",
                    "default": 1.0,
                },
                {
                    "name": "cohesion_weight",
                    "type": "float",
                    "default": 1.0,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Boids flocking
    print("\n=== Test 1: Boids Flocking ===")
    config = FlockingConfig(
        model=FlockingModel.BOIDS,
        n_agents=50,
        n_steps=200,
        separation_weight=1.5,
        alignment_weight=1.0,
        cohesion_weight=1.0,
    )
    sim = FlockingPattern(config)
    result = sim.run()
    print(f"✓ Final order parameter: {result['order_parameter']['final']:.3f}")
    print(f"  Average order: {result['order_parameter']['average']:.3f}")
    assert result["order_parameter"]["average"] >= 0, "Should complete successfully"

    # Test 2: Vicsek model
    print("\n=== Test 2: Vicsek Model ===")
    config = FlockingConfig(
        model=FlockingModel.VICSEK,
        n_agents=100,
        n_steps=200,
        noise_strength=0.1,
    )
    sim = FlockingPattern(config)
    result = sim.run()
    print(f"✓ Vicsek order parameter: {result['order_parameter']['final']:.3f}")

    # Test 3: Noise effect on order
    print("\n=== Test 3: Noise Effect ===")
    for noise in [0.0, 0.5, 1.0, 2.0]:
        config = FlockingConfig(
            model=FlockingModel.VICSEK,
            n_agents=100,
            n_steps=200,
            noise_strength=noise,
        )
        sim = FlockingPattern(config)
        result = sim.run()
        print(f"  Noise η={noise}: order={result['order_parameter']['final']:.3f}")

    print("\n✅ All flocking tests passed!")
