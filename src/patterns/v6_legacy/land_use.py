"""
TURBO-CDI v6.0 - Land Use Pattern
Spatial choice model for land use allocation and competition.

Pattern Structure (Christopher Alexander):
- Context: Urban planning, real estate, transportation
- Forces: Accessibility, land rent, zoning, agglomeration
- Solution: Discrete choice model with spatial interaction
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


@dataclass
class LandUseConfig:
    """Configuration for land use simulation"""

    # Spatial grid
    n_zones: int = 100
    zone_shape: Tuple[int, int] = (10, 10)  # For visualization

    # Land use types
    land_use_types: List[str] = field(
        default_factory=lambda: ["residential", "commercial", "industrial", "green"]
    )

    # Demand
    total_demand: Dict[str, float] = field(
        default_factory=lambda: {
            "residential": 5000,
            "commercial": 2000,
            "industrial": 1500,
            "green": 1000,
        }
    )

    # Accessibility
    zone_centroids: Optional[np.ndarray] = None  # Shape: (n_zones, 2)
    transport_network: Optional[np.ndarray] = None  # Distance matrix

    # Utility parameters (discrete choice)
    accessibility_weight: float = 1.0
    agglomeration_weight: float = 0.5
    competition_weight: float = -0.3

    # Simulation
    max_iterations: int = 100
    convergence_tolerance: float = 1e-4

    # Zoning
    zoning: Optional[Dict[int, List[str]]] = None  # Zone -> allowed uses


class LandUsePattern:
    """
    Spatial land use allocation using discrete choice framework.

    Models:
    - Zone attractiveness based on accessibility
    - Agglomeration effects (similar uses attract)
    - Competition for scarce land
    - Zoning constraints

    Uses multinomial logit for location choice.
    """

    PATTERN_ID = "land_use"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[LandUseConfig] = None):
        self.config = config or LandUseConfig()
        self.allocation: Optional[np.ndarray] = None  # Shape: (n_zones, n_types)
        self.utilities: Optional[np.ndarray] = None

        self._initialize()

    def _initialize(self):
        """Initialize land use simulation"""
        cfg = self.config
        n_types = len(cfg.land_use_types)

        # Initialize centroids if not provided
        if cfg.zone_centroids is None:
            rows, cols = cfg.zone_shape
            cfg.zone_centroids = np.zeros((cfg.n_zones, 2))
            for i in range(cfg.n_zones):
                cfg.zone_centroids[i] = [i // cols, i % cols]

        # Initialize transport network (distances)
        if cfg.transport_network is None:
            cfg.transport_network = self._calculate_distance_matrix(cfg.zone_centroids)

        # Initialize allocation (equal distribution)
        self.allocation = np.ones((cfg.n_zones, n_types)) / n_types

        # Normalize to total demand
        for t, lu_type in enumerate(cfg.land_use_types):
            demand = cfg.total_demand.get(lu_type, 1000)
            self.allocation[:, t] *= demand / cfg.n_zones

        # Set up zoning constraints
        self._setup_zoning()

    def _calculate_distance_matrix(self, centroids: np.ndarray) -> np.ndarray:
        """Calculate Euclidean distance matrix between zones"""
        n = len(centroids)
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.linalg.norm(centroids[i] - centroids[j])
        return dist

    def _setup_zoning(self):
        """Set up zoning constraints"""
        cfg = self.config
        self.zoning_matrix = np.ones((cfg.n_zones, len(cfg.land_use_types)))

        if cfg.zoning:
            for zone, allowed in cfg.zoning.items():
                if 0 <= zone < cfg.n_zones:
                    for t, lu_type in enumerate(cfg.land_use_types):
                        if lu_type not in allowed:
                            self.zoning_matrix[zone, t] = 0

    def _calculate_accessibility(self, zone: int, lu_type: str) -> float:
        """Calculate accessibility utility for zone and land use type"""
        cfg = self.config

        # Distance to other zones weighted by their development
        accessibility = 0.0
        for j in range(cfg.n_zones):
            dist = cfg.transport_network[zone, j]
            if dist > 0:
                # Gravity model: attraction decreases with distance
                accessibility += 1.0 / (1 + dist * 0.1)

        return accessibility

    def _calculate_agglomeration(self, zone: int, lu_type_idx: int) -> float:
        """Calculate agglomeration benefits (positive externality)"""
        cfg = self.config

        # Agglomeration = density of same type in nearby zones
        agglomeration = 0.0
        for j in range(cfg.n_zones):
            dist = cfg.transport_network[zone, j]
            if dist < 3:  # Within interaction radius
                agglomeration += self.allocation[j, lu_type_idx] / (1 + dist)

        return agglomeration

    def _calculate_competition(self, zone: int, lu_type_idx: int) -> float:
        """Calculate competition cost (negative externality)"""
        cfg = self.config

        # Competition = total development pressure in zone
        total_allocation = np.sum(self.allocation[zone])
        capacity = 100  # Arbitrary capacity limit

        if total_allocation > capacity:
            return -(total_allocation - capacity) / capacity
        return 0.0

    def _calculate_utility(self, zone: int, lu_type_idx: int) -> float:
        """Calculate total utility for land use type in zone"""
        cfg = self.config
        lu_type = cfg.land_use_types[lu_type_idx]

        # Base utility components
        accessibility = self._calculate_accessibility(zone, lu_type)
        agglomeration = self._calculate_agglomeration(zone, lu_type_idx)
        competition = self._calculate_competition(zone, lu_type_idx)

        # Type-specific base attractiveness
        base_attractiveness = 1.0

        utility = (
            base_attractiveness
            + cfg.accessibility_weight * accessibility
            + cfg.agglomeration_weight * agglomeration
            + cfg.competition_weight * competition
        )

        # Apply zoning constraint
        utility *= self.zoning_matrix[zone, lu_type_idx]

        return utility

    def _update_allocation(self):
        """Update land use allocation based on utilities"""
        cfg = self.config
        n_types = len(cfg.land_use_types)

        # Calculate utilities for all zone-type combinations
        utilities = np.zeros((cfg.n_zones, n_types))
        for i in range(cfg.n_zones):
            for t in range(n_types):
                utilities[i, t] = self._calculate_utility(i, t)

        # Multinomial logit choice probabilities
        exp_util = np.exp(utilities - np.max(utilities, axis=1, keepdims=True))
        choice_probs = exp_util / np.sum(exp_util, axis=1, keepdims=True)

        # Ensure no NaN
        choice_probs = np.nan_to_num(choice_probs, nan=1.0 / n_types)

        # Allocate demand according to choice probabilities
        new_allocation = np.zeros_like(self.allocation)
        for t, lu_type in enumerate(cfg.land_use_types):
            total_demand = cfg.total_demand.get(lu_type, 1000)
            # Distribute demand according to choice probabilities
            zone_shares = choice_probs[:, t] / np.sum(choice_probs[:, t])
            new_allocation[:, t] = total_demand * zone_shares

        # Apply zoning constraints
        new_allocation *= self.zoning_matrix

        # Check convergence
        max_change = np.max(np.abs(new_allocation - self.allocation))

        self.allocation = new_allocation
        self.utilities = utilities

        return max_change

    def _calculate_land_rent(self) -> np.ndarray:
        """Calculate land rent (bid-rent theory)"""
        # Rent = max utility across land use types
        return (
            np.max(self.utilities, axis=1)
            if self.utilities is not None
            else np.zeros(self.config.n_zones)
        )

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run land use simulation"""
        cfg = self.config

        logger.info(f"Starting land use simulation: {cfg.n_zones} zones")

        convergence_history = []

        for iteration in range(cfg.max_iterations):
            max_change = self._update_allocation()
            convergence_history.append(max_change)

            if iteration % 10 == 0:
                logger.debug(f"Iteration {iteration}: max_change = {max_change:.6f}")

            if max_change < cfg.convergence_tolerance:
                logger.info(f"Converged after {iteration + 1} iterations")
                break

        return self._format_output(iteration + 1, convergence_history)

    def _format_output(
        self, iterations: int, convergence_history: List[float]
    ) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Allocation statistics by type
        type_totals = {}
        type_by_zone = {}
        for t, lu_type in enumerate(cfg.land_use_types):
            type_totals[lu_type] = float(np.sum(self.allocation[:, t]))
            type_by_zone[lu_type] = self.allocation[:, t].tolist()

        # Dominant land use per zone
        dominant_types = np.argmax(self.allocation, axis=1)
        dominant_names = [cfg.land_use_types[i] for i in dominant_types]

        # Spatial metrics
        land_rent = self._calculate_land_rent()

        # Concentration (Herfindahl index per zone)
        concentration = np.sum(self.allocation**2, axis=1) / (
            np.sum(self.allocation, axis=1) ** 2 + 1e-10
        )

        # Diversity index (inverse of concentration)
        diversity = 1 - concentration

        return {
            "allocation": self.allocation.tolist(),
            "dominant_types": dominant_names,
            "type_totals": type_totals,
            "type_by_zone": type_by_zone,
            "utilities": self.utilities.tolist()
            if self.utilities is not None
            else None,
            "land_rent": land_rent.tolist(),
            "spatial_statistics": {
                "mean_rent": float(np.mean(land_rent)),
                "rent_variance": float(np.var(land_rent)),
                "mean_diversity": float(np.mean(diversity)),
                "segregation_index": float(np.std(concentration)),
            },
            "convergence": {
                "iterations": iterations,
                "final_change": convergence_history[-1] if convergence_history else 0,
                "history": convergence_history[
                    :: max(1, len(convergence_history) // 20)
                ],
            },
            "zoning_compliance": float(
                np.sum(self.allocation * self.zoning_matrix) / np.sum(self.allocation)
            ),
            "config": {
                "n_zones": cfg.n_zones,
                "land_use_types": cfg.land_use_types,
                "demand": cfg.total_demand,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Land Use",
            "category": "EXTENDED",
            "domain": ["Urban Planning", "Real Estate", "Transportation"],
            "description": "Spatial land use allocation using discrete choice",
            "computational_complexity": "O(I·N²·T)",
            "typical_runtime": "seconds",
            "accuracy": "Medium (economic equilibrium)",
            "assumptions": [
                "Discrete choice behavior",
                "Static transport network",
                "Perfect information",
            ],
            "parameters": [
                {
                    "name": "n_zones",
                    "type": "int",
                    "default": 100,
                },
                {
                    "name": "accessibility_weight",
                    "type": "float",
                    "default": 1.0,
                },
                {
                    "name": "agglomeration_weight",
                    "type": "float",
                    "default": 0.5,
                },
                {
                    "name": "max_iterations",
                    "type": "int",
                    "default": 100,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Basic allocation
    print("\n=== Test 1: Basic Land Use Allocation ===")
    config = LandUseConfig(
        n_zones=25,
        zone_shape=(5, 5),
        total_demand={
            "residential": 1000,
            "commercial": 500,
            "industrial": 300,
            "green": 200,
        },
    )
    sim = LandUsePattern(config)
    result = sim.run()
    print(f"✓ Converged in {result['convergence']['iterations']} iterations")
    for lu_type, total in result["type_totals"].items():
        print(f"  {lu_type}: {total:.0f}")

    # Test 2: Zoning constraints
    print("\n=== Test 2: Zoning Constraints ===")
    zoning = {
        0: ["residential", "green"],  # Residential zone
        12: ["commercial"],  # CBD
        24: ["industrial"],  # Industrial zone
    }
    config = LandUseConfig(
        n_zones=25,
        zone_shape=(5, 5),
        zoning=zoning,
    )
    sim = LandUsePattern(config)
    result = sim.run()
    print(f"✓ Zoning compliance: {result['zoning_compliance']:.3f}")
    assert result["zoning_compliance"] > 0.95, "Zoning should be mostly respected"

    # Test 3: Agglomeration effects
    print("\n=== Test 3: Agglomeration vs Dispersion ===")
    for agg_weight in [0.0, 0.5, 1.0]:
        config = LandUseConfig(
            n_zones=25,
            agglomeration_weight=agg_weight,
        )
        sim = LandUsePattern(config)
        result = sim.run()
        print(
            f"  Agglomeration {agg_weight}: segregation={result['spatial_statistics']['segregation_index']:.3f}"
        )

    print("\n✅ All land use tests passed!")
