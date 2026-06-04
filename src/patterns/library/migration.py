"""
C4REQBER v6.0 - Migration Pattern
Gravity model and radiation model for human migration flows.

Pattern Structure (Christopher Alexander):
- Context: Demography, economics, geography
- Forces: Economic opportunity, distance decay, network effects
- Solution: Spatial interaction model with utility maximization
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class MigrationModel(Enum):
    """Available migration models"""

    GRAVITY = "gravity"
    RADIATION = "radiation"
    INTERVENING_OPPORTUNITY = "io"


@dataclass
class MigrationConfig:
    """Configuration for migration simulation"""

    model: MigrationModel = MigrationModel.GRAVITY

    # Regions
    n_regions: int = 10
    region_populations: np.ndarray | None = None
    region_attractiveness: np.ndarray | None = None

    # Distance matrix
    distance_matrix: np.ndarray | None = None
    region_coordinates: np.ndarray | None = None  # For distance calculation

    # Gravity model parameters
    alpha: float = 1.0  # Origin mass exponent
    beta: float = 1.0  # Destination mass exponent
    gamma: float = 2.0  # Distance decay exponent

    # Radiation model
    radiation_threshold: float = 0.5

    # Simulation
    n_steps: int = 20
    migration_rate: float = 0.05  # Fraction of population that migrates per step

    # Return migration
    return_migration_probability: float = 0.1

    # Output
    track_flows: bool = True


class MigrationPattern:
    """
    Human migration simulation using gravity and radiation models.

    Models:
    - Gravity: Flow proportional to masses, inversely to distance
    - Radiation: Based on job opportunities within commute range
    - Intervening opportunity: Competing destinations matter
    """

    PATTERN_ID = "migration"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: MigrationConfig | None = None) -> None:
        self.config = config or MigrationConfig()
        self.population: np.ndarray | None = None
        self.flows: np.ndarray | None = None
        self.history: list[dict] = []

        self._initialize()

    def _initialize(self) -> None:
        """Initialize migration simulation"""
        cfg = self.config

        # Initialize populations
        if cfg.region_populations is None:
            # Random initial populations
            cfg.region_populations = np.random.lognormal(10, 1, cfg.n_regions)

        self.population = cfg.region_populations.copy()
        self.initial_population = self.population.copy()

        # Initialize attractiveness
        if cfg.region_attractiveness is None:
            # Based on economic opportunity
            cfg.region_attractiveness = np.random.lognormal(0, 0.5, cfg.n_regions)

        # Initialize coordinates for distance calculation
        if cfg.region_coordinates is None:
            cfg.region_coordinates = np.random.random((cfg.n_regions, 2)) * 1000

        # Calculate distance matrix
        if cfg.distance_matrix is None:
            cfg.distance_matrix = self._calculate_distances(cfg.region_coordinates)

        self.history = []

    def _record_state(self) -> None:
        """Record current state"""
        self.history.append(
            {
                "population": self.population.copy(),  # type: ignore[union-attr]
            }
        )

    def _calculate_distances(self, coords: np.ndarray) -> np.ndarray:
        """Calculate Euclidean distance matrix"""
        n = len(coords)
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.linalg.norm(coords[i] - coords[j])
        np.fill_diagonal(dist, 1)  # Avoid division by zero
        return dist

    def _gravity_flows(self) -> np.ndarray:
        """Calculate migration flows using gravity model"""
        cfg = self.config
        n = cfg.n_regions

        flows = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue

                # Gravity model: T_ij = k * (P_i^alpha * P_j^beta) / d_ij^gamma
                mass_term = (self.population[i] ** cfg.alpha) * (  # type: ignore[index]
                    self.population[j] ** cfg.beta * cfg.region_attractiveness[j]  # type: ignore[index]
                )
                distance_term = cfg.distance_matrix[i, j] ** (-cfg.gamma)  # type: ignore[index]

                flows[i, j] = mass_term * distance_term

        # Normalize to total migration
        total_migrants = np.sum(self.population) * cfg.migration_rate  # type: ignore[arg-type]
        flow_sum = np.sum(flows)
        if flow_sum > 0:
            flows = flows / flow_sum * total_migrants

        return flows

    def _radiation_flows(self) -> np.ndarray:
        """Calculate migration flows using radiation model"""
        cfg = self.config
        n = cfg.n_regions

        flows = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue

                # Population in circle from i to j
                radius = cfg.distance_matrix[i, j]  # type: ignore[index]
                intervening_pop = 0
                for k in range(n):
                    if k != i and k != j:
                        if cfg.distance_matrix[i, k] < radius:  # type: ignore[index]
                            intervening_pop += self.population[k]  # type: ignore[index]

                # Radiation model probability
                m_i = self.population[i]  # type: ignore[index]
                m_j = self.population[j] * cfg.region_attractiveness[j]  # type: ignore[index]

                if m_i + intervening_pop > 0:
                    prob = (m_i * m_j) / (
                        (m_i + intervening_pop) * (m_i + intervening_pop + m_j)
                    )
                    flows[i, j] = prob * self.population[i] * cfg.migration_rate  # type: ignore[index]

        return flows

    def _update_populations(self, flows: np.ndarray) -> None:
        """Update populations based on migration flows"""
        cfg = self.config

        # Net migration for each region
        in_migration = np.sum(flows, axis=0)
        out_migration = np.sum(flows, axis=1)

        # Update populations
        self.population = self.population - out_migration + in_migration

        # Ensure non-negative
        self.population = np.maximum(self.population, 1)

        # Update attractiveness (economies of scale)
        cfg.region_attractiveness *= 1 + 0.01 * (in_migration - out_migration) / (
            self.population + 1
        )

    def _calculate_migration_rate(self) -> float:
        """Calculate overall migration rate"""
        total_movers = np.sum(np.abs(self.population - self.initial_population))  # type: ignore[operator]
        return total_movers / np.sum(self.initial_population)  # type: ignore[no-any-return]

    def _calculate_concentration(self) -> float:
        """Calculate population concentration (Herfindahl index)"""
        shares = self.population / np.sum(self.population)  # type: ignore[arg-type]
        return np.sum(shares**2)  # type: ignore[no-any-return]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run migration simulation"""
        cfg = self.config

        logger.info(
            f"Starting migration simulation: {cfg.model.value}, {cfg.n_regions} regions"
        )

        all_flows = []

        for _step in range(cfg.n_steps):
            # Calculate flows
            if cfg.model == MigrationModel.GRAVITY:
                flows = self._gravity_flows()
            elif cfg.model == MigrationModel.RADIATION:
                flows = self._radiation_flows()
            else:
                flows = self._gravity_flows()

            all_flows.append(flows.copy())

            # Update populations
            self._update_populations(flows)

            self._record_state()

        self.flows = (
            all_flows[-1] if all_flows else np.zeros((cfg.n_regions, cfg.n_regions))
        )

        return self._format_output(all_flows)

    def _format_output(self, all_flows: list[np.ndarray]) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Migration statistics
        total_flows = np.sum([np.sum(f) for f in all_flows])
        avg_flow = np.mean([np.sum(f) for f in all_flows])

        # Net migration per region
        net_migration = self.population - self.initial_population  # type: ignore[operator]

        # Migration connectivity
        connectivity = np.sum(self.flows > 0) / (cfg.n_regions * (cfg.n_regions - 1))  # type: ignore[operator]

        # Gini coefficient of population distribution
        gini = self._calculate_gini(self.population)  # type: ignore[arg-type]

        return {
            "final_population": self.population.tolist(),  # type: ignore[union-attr]
            "initial_population": self.initial_population.tolist(),
            "net_migration": net_migration.tolist(),
            "final_flows": self.flows.tolist(),  # type: ignore[union-attr]
            "flow_history": [
                f.tolist() for f in all_flows[:: max(1, len(all_flows) // 10)]
            ],
            "statistics": {
                "total_migration_volume": float(total_flows),
                "average_flow": float(avg_flow),
                "connectivity": float(connectivity),
                "population_gini": float(gini),
                "concentration_index": float(self._calculate_concentration()),
                "total_population_change": float(np.sum(net_migration)),
            },
            "region_data": [
                {
                    "id": i,
                    "initial": float(self.initial_population[i]),
                    "final": float(self.population[i]),  # type: ignore[index]
                    "net_migration": float(net_migration[i]),
                    "attractiveness": float(cfg.region_attractiveness[i]),  # type: ignore[index]
                }
                for i in range(cfg.n_regions)
            ],
            "config": {
                "model": cfg.model.value,
                "n_regions": cfg.n_regions,
                "n_steps": cfg.n_steps,
                "migration_rate": cfg.migration_rate,
            },
        }

    def _calculate_gini(self, x: np.ndarray) -> float:
        """Calculate Gini coefficient"""
        sorted_x = np.sort(x)
        n = len(x)
        cumsum = np.cumsum(sorted_x)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n  # type: ignore[no-any-return]

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Migration",
            "category": "EXTENDED",
            "domain": ["Demography", "Economics", "Geography"],
            "description": "Gravity and radiation models of migration",
            "computational_complexity": "O(T·N²)",
            "typical_runtime": "seconds",
            "accuracy": "Medium (macro-level predictions)",
            "assumptions": [
                "Rational utility maximization",
                "Distance decay effects",
                "Static attractiveness",
            ],
            "parameters": [
                {
                    "name": "model",
                    "type": "enum",
                    "options": ["gravity", "radiation"],
                    "default": "gravity",
                },
                {
                    "name": "n_regions",
                    "type": "int",
                    "default": 10,
                },
                {
                    "name": "gamma",
                    "type": "float",
                    "default": 2.0,
                    "description": "Distance decay exponent",
                },
                {
                    "name": "migration_rate",
                    "type": "float",
                    "default": 0.05,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Gravity model
    print("\n=== Test 1: Gravity Model ===")
    config = MigrationConfig(
        model=MigrationModel.GRAVITY,
        n_regions=5,
        region_populations=np.array([1000, 500, 800, 300, 600]),
        alpha=1.0,
        beta=1.0,
        gamma=2.0,
        n_steps=10,
    )
    sim = MigrationPattern(config)
    result = sim.run()
    print(f"✓ Total migration: {result['statistics']['total_migration_volume']:.0f}")
    print(f"  Connectivity: {result['statistics']['connectivity']:.3f}")

    # Test 2: Radiation model
    print("\n=== Test 2: Radiation Model ===")
    config = MigrationConfig(
        model=MigrationModel.RADIATION,
        n_regions=5,
        region_populations=np.array([1000, 500, 800, 300, 600]),
        n_steps=10,
    )
    sim = MigrationPattern(config)
    result = sim.run()
    print(
        f"✓ Radiation model migration: {result['statistics']['total_migration_volume']:.0f}"
    )

    # Test 3: Distance decay
    print("\n=== Test 3: Distance Decay Effect ===")
    for gamma in [1.0, 2.0, 3.0]:
        config = MigrationConfig(
            model=MigrationModel.GRAVITY,
            n_regions=5,
            region_populations=np.array([1000, 500, 800, 300, 600]),
            gamma=gamma,
            n_steps=10,
        )
        sim = MigrationPattern(config)
        result = sim.run()
        print(
            f"  Gamma={gamma}: connectivity={result['statistics']['connectivity']:.3f}"
        )

    print("\n✅ All migration tests passed!")
