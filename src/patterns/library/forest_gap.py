"""
Forest Gap Pattern
Cellular automaton model of forest dynamics

Based on:
- Shugart (1984) JABOWA/FORET gap models
- Caswell-Etter (1993) cellular automaton approach
- Drossel-Schwabl forest fire model extensions
- Neutral theory of biodiversity
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
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


class GapState(Enum):
    """GapState."""
    EMPTY = 0
    JUVENILE = 1
    MATURE = 2
    OLD_GROWTH = 3
    DISTURBED = 4  # Gap opening


@dataclass
class ForestGapConfig:
    """Forest gap model configuration"""
    # Grid
    grid_size: int = 50  # N x N grid
    num_species: int = 3  # Number of tree species

    # Disturbance
    disturbance_rate: float = 0.01  # Probability per cell per year
    gap_expansion_prob: float = 0.3  # Probability gap expands to neighbor

    # Succession rates (per year)
    recruitment_rate: float = 0.1  # Empty -> Juvenile
    maturation_rate: float = 0.05  # Juvenile -> Mature
    aging_rate: float = 0.02  # Mature -> Old Growth
    mortality_rates: dict[str, float] = field(default_factory=lambda: {
        "juvenile": 0.05,
        "mature": 0.02,
        "old_growth": 0.05,
    })

    # Competition
    competition_factor: float = 0.1
    shading_effect: float = 0.3

    # Simulation
    years: int = 500
    record_interval: int = 10

    # Initial conditions
    initial_cover: float = 0.7  # Fraction of grid with trees

    def to_dict(self) -> dict[str, Any]:
        return {
            "grid_size": self.grid_size,
            "num_species": self.num_species,
            "disturbance_rate": self.disturbance_rate,
            "gap_expansion_prob": self.gap_expansion_prob,
            "recruitment_rate": self.recruitment_rate,
            "maturation_rate": self.maturation_rate,
            "aging_rate": self.aging_rate,
            "mortality_rates": self.mortality_rates,
            "competition_factor": self.competition_factor,
            "shading_effect": self.shading_effect,
            "years": self.years,
            "record_interval": self.record_interval,
            "initial_cover": self.initial_cover,
        }


@simulation_pattern(
    id="forest_gap",
    name="Forest Gap Dynamics",
    category="ecology",
    description="Cellular automaton model of forest gap dynamics and succession",
)
class ForestGapPattern(SimulationPattern):
    """
    Forest gap dynamics simulation using cellular automata

    Models forest dynamics through gap formation and succession:
    - Disturbance creates gaps
    - Colonization by pioneer species
    - Succession to mature forest
    - Competition and shading

    Applications:
    - Forest management
    - Biodiversity studies
    - Climate change impacts
    - Natural disturbance regimes
    """

    parameters = [
        SimulationParameter(
            name="grid_size",
            type="int",
            default=50,
            min=10,
            max=200,
            description="Grid size (N x N)",
        ),
        SimulationParameter(
            name="num_species",
            type="int",
            default=3,
            min=1,
            max=10,
            description="Number of tree species",
        ),
        SimulationParameter(
            name="disturbance_rate",
            type="float",
            default=0.01,
            min=0.0,
            max=0.5,
            description="Annual disturbance probability",
        ),
        SimulationParameter(
            name="gap_expansion_prob",
            type="float",
            default=0.3,
            min=0.0,
            max=1.0,
            description="Gap expansion probability",
        ),
        SimulationParameter(
            name="recruitment_rate",
            type="float",
            default=0.1,
            min=0.0,
            max=1.0,
            description="Recruitment rate (gap colonization)",
        ),
        SimulationParameter(
            name="maturation_rate",
            type="float",
            default=0.05,
            min=0.0,
            max=1.0,
            description="Maturation rate",
        ),
        SimulationParameter(
            name="years",
            type="int",
            default=500,
            min=50,
            max=5000,
            description="Simulation duration (years)",
        ),
        SimulationParameter(
            name="initial_cover",
            type="float",
            default=0.7,
            min=0.0,
            max=1.0,
            description="Initial forest cover",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: ForestGapConfig = ForestGapConfig()
        self.rng = np.random.default_rng(seed=42)
        self.grid: np.ndarray | None = None
        self.species_grid: np.ndarray | None = None
        self.age_grid: np.ndarray | None = None

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if forest gap can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "forest", "gap", "succession", "disturbance", "tree",
            "canopy", "regeneration", "biodiversity", "ecosystem",
            "cellular automaton", "patch dynamics", "stand dynamics",
            "old growth", "pioneer", "climax", "recruitment",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute forest gap simulation"""
        start_time = datetime.now()
        simulation_id = f"fg_{start_time.timestamp()}"

        logger.info(f"Starting forest gap simulation {simulation_id}")

        try:
            # Parse configuration
            self.config = self._parse_config(config)

            # Initialize grid
            self._initialize_grid()

            # Run simulation
            results = await self._simulate()

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
            logger.exception("Forest gap simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> ForestGapConfig:
        """Parse configuration dictionary"""
        cfg = ForestGapConfig()

        if "grid_size" in config:
            cfg.grid_size = int(config["grid_size"])
        if "num_species" in config:
            cfg.num_species = int(config["num_species"])
        if "disturbance_rate" in config:
            cfg.disturbance_rate = float(config["disturbance_rate"])
        if "gap_expansion_prob" in config:
            cfg.gap_expansion_prob = float(config["gap_expansion_prob"])
        if "recruitment_rate" in config:
            cfg.recruitment_rate = float(config["recruitment_rate"])
        if "maturation_rate" in config:
            cfg.maturation_rate = float(config["maturation_rate"])
        if "aging_rate" in config:
            cfg.aging_rate = float(config["aging_rate"])
        if "competition_factor" in config:
            cfg.competition_factor = float(config["competition_factor"])
        if "shading_effect" in config:
            cfg.shading_effect = float(config["shading_effect"])
        if "years" in config:
            cfg.years = int(config["years"])
        if "record_interval" in config:
            cfg.record_interval = int(config["record_interval"])
        if "initial_cover" in config:
            cfg.initial_cover = float(config["initial_cover"])

        return cfg

    def _initialize_grid(self) -> None:
        """Initialize forest grid"""
        cfg = self.config
        N = cfg.grid_size

        # State grid: 0=empty, 1=juvenile, 2=mature, 3=old_growth
        self.grid = np.zeros((N, N), dtype=int)
        self.species_grid = np.zeros((N, N), dtype=int)
        self.age_grid = np.zeros((N, N), dtype=int)

        # Random initial forest cover
        forest_mask = self.rng.random((N, N)) < cfg.initial_cover

        # Assign random ages/stages
        self.grid[forest_mask] = self.rng.integers(1, 4, np.sum(forest_mask))  # type: ignore[call-overload]
        self.species_grid[forest_mask] = self.rng.integers(0, cfg.num_species, np.sum(forest_mask))  # type: ignore[call-overload]
        self.age_grid[forest_mask] = self.rng.integers(0, 100, np.sum(forest_mask))  # type: ignore[call-overload]

    async def _simulate(self) -> dict[str, Any]:
        """Run forest gap simulation"""

        cfg = self.config
        N = cfg.grid_size

        # Storage
        snapshots = []
        cover_history = []
        species_richness_history = []
        gap_fraction_history = []
        age_distribution_history = []

        for year in range(cfg.years):
            # 1. Disturbance (gap formation)
            self._apply_disturbance()

            # 2. Succession dynamics
            self._apply_succession()

            # 3. Record state
            if year % cfg.record_interval == 0:
                snapshots.append(self.grid.copy())  # type: ignore[union-attr]

                # Calculate metrics
                cover = np.sum(self.grid > 0) / (N * N)  # type: ignore[operator]
                cover_history.append(float(cover))

                # Species richness
                present_species = np.unique(self.species_grid[self.grid > 0])  # type: ignore[index, operator]
                species_richness_history.append(len(present_species))

                # Gap fraction (empty cells + recent disturbances)
                gap_frac = np.sum(self.grid == 0) / (N * N)
                gap_fraction_history.append(float(gap_frac))

                # Age distribution
                ages = self.age_grid[self.grid > 0]  # type: ignore[index, operator]
                age_distribution_history.append({
                    "mean": float(np.mean(ages)) if len(ages) > 0 else 0,
                    "std": float(np.std(ages)) if len(ages) > 0 else 0,
                })

            if year % 100 == 0:
                await asyncio.sleep(0)

        # Final analysis
        metrics = self._calculate_metrics(
            cover_history, species_richness_history,
            gap_fraction_history, snapshots
        )

        logs = [
            "Forest gap simulation completed",
            f"Grid: {N}x{N}, Years: {cfg.years}",
            f"Species: {cfg.num_species}",
            f"Final cover: {metrics['final_cover']*100:.1f}%",
            f"Mean gap fraction: {metrics['mean_gap_fraction']*100:.1f}%",
            f"Species richness: {metrics['final_species_richness']}/{cfg.num_species}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "cover_history": cover_history,
            "species_richness": species_richness_history,
            "gap_fraction": gap_fraction_history,
            "final_grid": self.grid.tolist(),  # type: ignore[union-attr]
            "final_species": self.species_grid.tolist(),  # type: ignore[union-attr]
            "snapshots": [s.tolist() for s in snapshots[::len(snapshots)//10]] if len(snapshots) >= 10 else [s.tolist() for s in snapshots],
        }

    def _apply_disturbance(self) -> None:
        """Apply stochastic disturbance (gap formation)"""
        cfg = self.config
        N = cfg.grid_size

        # Random disturbances
        disturbance_mask = self.rng.random((N, N)) < cfg.disturbance_rate

        # Larger disturbance events (windthrows, fires)
        if self.rng.random() < 0.1:  # 10% chance per year
            # Create large disturbance patch
            center = (self.rng.integers(0, N), self.rng.integers(0, N))
            size = self.rng.integers(3, 10)
            for i in range(max(0, center[0]-size), min(N, center[0]+size)):
                for j in range(max(0, center[1]-size), min(N, center[1]+size)):
                    if (i-center[0])**2 + (j-center[1])**2 < size**2:
                        if self.rng.random() < 0.7:
                            disturbance_mask[i, j] = True

        # Apply disturbance
        self.grid[disturbance_mask] = 0  # type: ignore  # Empty
        self.species_grid[disturbance_mask] = -1  # type: ignore  # No species
        self.age_grid[disturbance_mask] = 0  # type: ignore[index]

        # Gap expansion (neighbor effect)
        for _ in range(3):  # Multiple expansion attempts
            for i in range(N):
                for j in range(N):
                    if self.grid[i, j] == 0:  # type: ignore  # If gap exists
                        # Try to expand to neighbors
                        neighbors = [
                            ((i-1)%N, j), ((i+1)%N, j),
                            (i, (j-1)%N), (i, (j+1)%N)
                        ]
                        for ni, nj in neighbors:
                            if self.grid[ni, nj] > 0 and self.rng.random() < cfg.gap_expansion_prob:  # type: ignore[index]
                                self.grid[ni, nj] = 0  # type: ignore[index]
                                self.species_grid[ni, nj] = -1  # type: ignore[index]
                                self.age_grid[ni, nj] = 0  # type: ignore[index]

    def _apply_succession(self) -> None:
        """Apply succession dynamics"""
        cfg = self.config
        N = cfg.grid_size

        # Process cells in random order
        cells = [(i, j) for i in range(N) for j in range(N)]
        self.rng.shuffle(cells)

        for i, j in cells:
            # Age increment
            if self.grid[i, j] > 0:  # type: ignore[index]
                self.age_grid[i, j] += 1  # type: ignore[index]

            # State transitions
            if self.grid[i, j] == 0:  # type: ignore  # Empty -> Juvenile (recruitment)
                # Check for seed source (any mature/old neighbor)
                has_seed = self._has_mature_neighbor(i, j)
                rate = cfg.recruitment_rate * (2 if has_seed else 1)
                if self.rng.random() < rate:
                    self.grid[i, j] = 1  # type: ignore  # Juvenile
                    self.species_grid[i, j] = self._choose_species(i, j)  # type: ignore[index]
                    self.age_grid[i, j] = 0  # type: ignore[index]

            elif self.grid[i, j] == 1:  # type: ignore  # Juvenile
                # Mortality
                if self.rng.random() < cfg.mortality_rates["juvenile"]:
                    self.grid[i, j] = 0  # type: ignore[index]
                    continue

                # Maturation
                if self.rng.random() < cfg.maturation_rate:
                    self.grid[i, j] = 2  # type: ignore  # Mature

            elif self.grid[i, j] == 2:  # type: ignore  # Mature
                # Mortality
                if self.rng.random() < cfg.mortality_rates["mature"]:
                    self.grid[i, j] = 0  # type: ignore[index]
                    continue

                # Aging
                if self.rng.random() < cfg.aging_rate:
                    self.grid[i, j] = 3  # type: ignore  # Old growth

            elif self.grid[i, j] == 3:  # type: ignore  # Old growth
                # Higher mortality
                if self.rng.random() < cfg.mortality_rates["old_growth"]:
                    self.grid[i, j] = 0  # type: ignore[index]

    def _has_mature_neighbor(self, i: int, j: int) -> bool:
        """Check if cell has mature neighbor"""
        N = self.config.grid_size
        neighbors = [
            ((i-1)%N, j), ((i+1)%N, j),
            (i, (j-1)%N), (i, (j+1)%N)
        ]
        for ni, nj in neighbors:
            if self.grid[ni, nj] >= 2:  # type: ignore  # Mature or old growth
                return True
        return False

    def _choose_species(self, i: int, j: int) -> int:
        """Choose species for recruitment based on neighbors"""
        N = self.config.grid_size
        neighbors = [
            ((i-1)%N, j), ((i+1)%N, j),
            (i, (j-1)%N), (i, (j+1)%N)
        ]

        # Collect neighbor species
        neighbor_species = []
        for ni, nj in neighbors:
            if self.species_grid[ni, nj] >= 0:  # type: ignore[index]
                neighbor_species.append(self.species_grid[ni, nj])  # type: ignore[index]

        if neighbor_species and self.rng.random() < 0.8:
            # 80% chance to recruit from neighbor species
            return self.rng.choice(neighbor_species)  # type: ignore[no-any-return]
        else:
            # Random species (dispersal from outside)
            return self.rng.integers(0, self.config.num_species)

    def _calculate_metrics(
        self, cover_history: list[float],
        species_richness: list[int],
        gap_fraction: list[float],
        snapshots: list[np.ndarray]
    ) -> dict[str, float]:
        """Calculate forest metrics"""

        cfg = self.config

        # Basic metrics
        final_cover = cover_history[-1] if cover_history else 0
        mean_cover = np.mean(cover_history) if cover_history else 0
        final_richness = species_richness[-1] if species_richness else 0
        mean_gap = np.mean(gap_fraction) if gap_fraction else 0

        # Cover stability (last 20% of simulation)
        if len(cover_history) > 10:
            recent_cover = cover_history[-len(cover_history)//5:]
            cover_stability = 1 - np.std(recent_cover) / (np.mean(recent_cover) + 0.001)
        else:
            cover_stability = 0  # type: ignore[assignment]

        # Stage distribution
        stage_counts = np.bincount(self.grid.flatten(), minlength=4)  # type: ignore[union-attr]
        total = np.sum(stage_counts)

        if total > 0:
            stage_distribution = {
                "empty": float(stage_counts[0] / total),
                "juvenile": float(stage_counts[1] / total),
                "mature": float(stage_counts[2] / total),
                "old_growth": float(stage_counts[3] / total),
            }
        else:
            stage_distribution = {"empty": 1, "juvenile": 0, "mature": 0, "old_growth": 0}

        # Shannon diversity index
        if final_richness > 0:
            species_counts = np.bincount(
                self.species_grid[self.grid > 0].flatten(),  # type: ignore[index, operator]
                minlength=cfg.num_species
            )
            proportions = species_counts / np.sum(species_counts)
            shannon = -np.sum(proportions * np.log(proportions + 1e-10))
        else:
            shannon = 0

        # Spatial metrics from final snapshot
        if snapshots:
            final_snap = snapshots[-1]
            # Calculate patch sizes
            gaps = (final_snap == 0).astype(int)
            # Simple connected component analysis
            gap_clusters = self._count_clusters(gaps)
        else:
            gap_clusters = 0

        return {
            "final_cover": final_cover,
            "mean_cover": mean_cover,  # type: ignore[dict-item]
            "final_species_richness": final_richness,
            "mean_species_richness": float(np.mean(species_richness)) if species_richness else 0,
            "mean_gap_fraction": mean_gap,  # type: ignore[dict-item]
            "cover_stability": float(cover_stability),
            "shannon_diversity": float(shannon),
            "stage_distribution": stage_distribution,  # type: ignore[dict-item]
            "num_gap_clusters": gap_clusters,
            "years_simulated": cfg.years,
        }

    def _count_clusters(self, binary_grid: np.ndarray) -> int:
        """Count connected components (simple version)"""
        from scipy import ndimage
        labeled, num_features = ndimage.label(binary_grid)
        return int(num_features)

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Valid cover range
        cover = metrics.get("final_cover", 0)
        if 0.1 < cover < 1.0:
            factors.append(0.3)

        # Reasonable species richness
        richness = metrics.get("final_species_richness", 0)
        if 0 < richness <= self.config.num_species:
            factors.append(0.25)

        # Positive Shannon diversity
        if metrics.get("shannon_diversity", 0) > 0:
            factors.append(0.25)

        # Stable dynamics
        if metrics.get("cover_stability", 0) > 0.5:
            factors.append(0.2)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("grid_size", 50)
        years = params.get("years", 500)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + N * N * years * 1e-7,
            "gpu_required": False,
            "estimated_time_seconds": N * N * years / 1e6,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": cls.id,
            "name": cls.name,  # type: ignore[attr-defined]
            "category": cls.category,  # type: ignore[attr-defined]
            "description": cls.description,  # type: ignore[attr-defined]
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "default": p.default,
                    "min": p.min,
                    "max": p.max,
                    "options": p.options,
                    "description": p.description,
                }
                for p in cls.parameters
            ],
            "references": [
                "Shugart, H.H. (1984). A Theory of Forest Dynamics",
                "Caswell, H. & Etter, R.J. (1993). Ecological interactions in patchy environments",
                "Hubbell, S.P. (2001). The Unified Neutral Theory of Biodiversity",
            ],
        }
