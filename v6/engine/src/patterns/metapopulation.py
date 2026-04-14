"""
Metapopulation Pattern
Levins model and spatially explicit population dynamics

Based on:
- Levins (1969) classic metapopulation model
- Hanski (1999) incidence function model
- Spatially realistic models
- Patch occupancy dynamics
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from ..core import (
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    Hypothesis,
    SimulationParameter,
    ValidationLevel,
    simulation_pattern,
)

logger = logging.getLogger(__name__)


class MetapopulationModel(Enum):
    LEVINS = "levins"
    LEVINS_Hanski = "levins_hanski"  # With rescue effect
    INCIDENCE_FUNCTION = "incidence_function"
    SPATIAL = "spatial"


@dataclass
class Patch:
    """Single patch in metapopulation"""
    id: int
    area: float  # Patch area (quality proxy)
    x: float  # X coordinate
    y: float  # Y coordinate
    occupied: bool = False
    
    def distance_to(self, other: 'Patch') -> float:
        """Calculate distance to another patch"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class MetapopulationConfig:
    """Metapopulation model configuration"""
    # Model selection
    model: MetapopulationModel = MetapopulationModel.LEVINS
    
    # Classic Levins parameters
    c: float = 0.1  # Colonization rate
    e: float = 0.05  # Extinction rate
    
    # Spatial parameters
    num_patches: int = 20
    landscape_size: float = 100.0  # km
    
    # Patch characteristics
    area_mean: float = 10.0  # ha
    area_cv: float = 0.5  # Coefficient of variation
    
    # Hanski parameters
    alpha: float = 1.0  # Dispersal parameter (1/mean dispersal distance)
    xi: float = 1.0  # Scaling of extinction with area
    
    # Correlation (rescue effect)
    rescue_effect: bool = False
    correlation: float = 0.0  # Spatial correlation in extinction
    
    # Simulation
    years: int = 100
    initial_occupancy: float = 0.5
    
    # Stochasticity
    demographic_stochasticity: bool = True
    environmental_stochasticity: bool = False
    env_sigma: float = 0.1  # Environmental variation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model.value,
            "c": self.c,
            "e": self.e,
            "num_patches": self.num_patches,
            "landscape_size": self.landscape_size,
            "area_mean": self.area_mean,
            "area_cv": self.area_cv,
            "alpha": self.alpha,
            "xi": self.xi,
            "rescue_effect": self.rescue_effect,
            "correlation": self.correlation,
            "years": self.years,
            "initial_occupancy": self.initial_occupancy,
            "demographic_stochasticity": self.demographic_stochasticity,
            "environmental_stochasticity": self.environmental_stochasticity,
            "env_sigma": self.env_sigma,
        }


@simulation_pattern(
    id="metapopulation",
    name="Metapopulation Dynamics",
    category="ecology",
    description="Levins metapopulation and spatially explicit population models",
)
class MetapopulationPattern(SimulationPattern):
    """
    Metapopulation dynamics simulation
    
    Models populations in fragmented landscapes:
    
    1. Classic Levins: p* = 1 - e/c
    2. Levins-Hanski: With rescue effect
    3. Incidence Function: Patch-specific extinction/colonization
    4. Spatial: Individual-based patch dynamics
    
    Applications:
    - Conservation planning
    - Reserve design
    - Fragmentation effects
    - Climate change range shifts
    """
    
    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="levins",
            options=["levins", "levins_hanski", "incidence_function", "spatial"],
            description="Metapopulation model",
        ),
        SimulationParameter(
            name="c",
            type="float",
            default=0.1,
            min=0.001,
            max=1.0,
            description="Colonization rate",
        ),
        SimulationParameter(
            name="e",
            type="float",
            default=0.05,
            min=0.001,
            max=1.0,
            description="Extinction rate",
        ),
        SimulationParameter(
            name="num_patches",
            type="int",
            default=20,
            min=2,
            max=1000,
            description="Number of habitat patches",
        ),
        SimulationParameter(
            name="alpha",
            type="float",
            default=1.0,
            min=0.01,
            max=10.0,
            description="Dispersal parameter (1/distance)",
        ),
        SimulationParameter(
            name="xi",
            type="float",
            default=1.0,
            min=0.1,
            max=2.0,
            description="Extinction-area scaling",
        ),
        SimulationParameter(
            name="years",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Simulation duration (years)",
        ),
        SimulationParameter(
            name="initial_occupancy",
            type="float",
            default=0.5,
            min=0.0,
            max=1.0,
            description="Initial patch occupancy",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.config: MetapopulationConfig = MetapopulationConfig()
        self.rng = np.random.default_rng(seed=42)
        self.patches: List[Patch] = []
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if metapopulation can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "metapopulation", "fragmentation", "patch", "habitat", "occupancy",
            "colonization", "extinction", "rescue", "dispersal", "connectivity",
            "landscape", "reserve", "corridor", "isolation", "connectance",
            "levins", "hanski", "incidence function", "turnover",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute metapopulation simulation"""
        start_time = datetime.now()
        simulation_id = f"meta_{start_time.timestamp()}"
        
        logger.info(f"Starting metapopulation simulation {simulation_id}")
        
        try:
            # Parse configuration
            self.config = self._parse_config(config)
            
            # Generate landscape
            self._generate_landscape()
            
            # Run simulation based on model
            if self.config.model == MetapopulationModel.LEVINS:
                results = await self._levins_simulation()
            elif self.config.model == MetapopulationModel.LEVINS_Hanski:
                results = await self._levins_hanski_simulation()
            elif self.config.model == MetapopulationModel.INCIDENCE_FUNCTION:
                results = await self._incidence_function_simulation()
            else:
                results = await self._spatial_simulation()
            
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
            logger.exception("Metapopulation simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> MetapopulationConfig:
        """Parse configuration dictionary"""
        cfg = MetapopulationConfig()
        
        if "model" in config:
            cfg.model = MetapopulationModel(config["model"])
        if "c" in config:
            cfg.c = float(config["c"])
        if "e" in config:
            cfg.e = float(config["e"])
        if "num_patches" in config:
            cfg.num_patches = int(config["num_patches"])
        if "landscape_size" in config:
            cfg.landscape_size = float(config["landscape_size"])
        if "area_mean" in config:
            cfg.area_mean = float(config["area_mean"])
        if "area_cv" in config:
            cfg.area_cv = float(config["area_cv"])
        if "alpha" in config:
            cfg.alpha = float(config["alpha"])
        if "xi" in config:
            cfg.xi = float(config["xi"])
        if "rescue_effect" in config:
            cfg.rescue_effect = bool(config["rescue_effect"])
        if "correlation" in config:
            cfg.correlation = float(config["correlation"])
        if "years" in config:
            cfg.years = int(config["years"])
        if "initial_occupancy" in config:
            cfg.initial_occupancy = float(config["initial_occupancy"])
        if "demographic_stochasticity" in config:
            cfg.demographic_stochasticity = bool(config["demographic_stochasticity"])
        if "environmental_stochasticity" in config:
            cfg.environmental_stochasticity = bool(config["environmental_stochasticity"])
        if "env_sigma" in config:
            cfg.env_sigma = float(config["env_sigma"])
            
        return cfg
    
    def _generate_landscape(self):
        """Generate patch landscape"""
        cfg = self.config
        
        # Generate random patch locations and areas
        self.patches = []
        for i in range(cfg.num_patches):
            area = self.rng.lognormal(
                np.log(cfg.area_mean), 
                cfg.area_cv
            )
            x = self.rng.uniform(0, cfg.landscape_size)
            y = self.rng.uniform(0, cfg.landscape_size)
            occupied = self.rng.random() < cfg.initial_occupancy
            
            self.patches.append(Patch(i, area, x, y, occupied))
    
    async def _levins_simulation(self) -> Dict[str, Any]:
        """Classic Levins model (analytical)"""
        
        cfg = self.config
        
        # Levins differential equation: dp/dt = cp(1-p) - ep
        # where p = fraction of patches occupied
        
        p = cfg.initial_occupancy
        
        occupancy_history = [p]
        colonization_events = 0
        extinction_events = 0
        
        for year in range(cfg.years):
            # Deterministic change
            dp = cfg.c * p * (1 - p) - cfg.e * p
            
            if cfg.demographic_stochasticity:
                # Add noise
                noise = self.rng.normal(0, 0.01)
                dp += noise
            
            p = max(0, min(1, p + dp))
            
            # Track events
            if dp > 0.001:
                colonization_events += 1
            elif dp < -0.001:
                extinction_events += 1
            
            occupancy_history.append(p)
            
            if year % 10 == 0:
                await asyncio.sleep(0)
        
        # Equilibrium
        p_star = 1 - cfg.e / cfg.c if cfg.c > cfg.e else 0
        
        # Metapopulation capacity
        lambda_M = cfg.c / cfg.e
        
        metrics = {
            "final_occupancy": float(p),
            "mean_occupancy": float(np.mean(occupancy_history)),
            "equilibrium_occupancy": float(p_star),
            "metapopulation_capacity": float(lambda_M),
            "colonization_events": colonization_events,
            "extinction_events": extinction_events,
            "persistence": p > 0.01,
            "c_e_ratio": cfg.c / cfg.e,
            "model": "levins",
        }
        
        logs = [
            f"Levins metapopulation simulation completed",
            f"Patches: {cfg.num_patches}, c={cfg.c}, e={cfg.e}",
            f"Final occupancy: {p*100:.1f}%",
            f"Equilibrium p*: {p_star*100:.1f}%",
            f"Metapopulation capacity (lambda): {lambda_M:.2f}",
            f"Persistent: {metrics['persistence']}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "occupancy": occupancy_history,
        }
    
    async def _levins_hanski_simulation(self) -> Dict[str, Any]:
        """Levins-Hanski model with rescue effect"""
        
        cfg = self.config
        
        # With rescue effect: extinction rate decreases with connectivity
        # e' = e * (1 - connectivity)
        
        p = cfg.initial_occupancy
        
        occupancy_history = [p]
        effective_extinction_rates = []
        
        for year in range(cfg.years):
            # Connectivity increases with occupancy
            connectivity = p
            
            # Rescue effect reduces extinction
            if cfg.rescue_effect:
                e_effective = cfg.e * (1 - 0.5 * connectivity)  # Rescue reduces extinction by up to 50%
            else:
                e_effective = cfg.e
            
            effective_extinction_rates.append(float(e_effective))
            
            # Modified dynamics
            dp = cfg.c * p * (1 - p) - e_effective * p
            
            if cfg.demographic_stochasticity:
                dp += self.rng.normal(0, 0.01)
            
            p = max(0, min(1, p + dp))
            occupancy_history.append(p)
            
            if year % 10 == 0:
                await asyncio.sleep(0)
        
        # Equilibrium with rescue
        if cfg.rescue_effect:
            # Approximate equilibrium
            p_star = max(0, (cfg.c - cfg.e) / (cfg.c - 0.5 * cfg.e)) if cfg.c > cfg.e else 0
        else:
            p_star = 1 - cfg.e / cfg.c if cfg.c > cfg.e else 0
        
        metrics = {
            "final_occupancy": float(p),
            "mean_occupancy": float(np.mean(occupancy_history)),
            "equilibrium_occupancy": float(p_star),
            "mean_effective_extinction": float(np.mean(effective_extinction_rates)),
            "rescue_effect": cfg.rescue_effect,
            "persistence": p > 0.01,
            "model": "levins_hanski",
        }
        
        logs = [
            f"Levins-Hanski simulation completed",
            f"Rescue effect: {cfg.rescue_effect}",
            f"Mean effective extinction: {metrics['mean_effective_extinction']:.4f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "occupancy": occupancy_history,
            "effective_extinction": effective_extinction_rates,
        }
    
    async def _incidence_function_simulation(self) -> Dict[str, Any]:
        """Incidence function model (patch-specific)"""
        
        cfg = self.config
        
        # Each patch has specific colonization and extinction probabilities
        # Based on area and connectivity
        
        # Calculate connectivity for each patch
        connectivity = []
        for patch in self.patches:
            conn = 0
            for other in self.patches:
                if other.id != patch.id and other.occupied:
                    dist = patch.distance_to(other)
                    conn += other.area * np.exp(-cfg.alpha * dist)
            connectivity.append(conn)
        
        # Track patch occupancy
        patch_occupancy = [[p.occupied] for p in self.patches]
        
        for year in range(cfg.years):
            # Update connectivity based on current occupancy
            for i, patch in enumerate(self.patches):
                conn = 0
                for j, other in enumerate(self.patches):
                    if i != j and patch_occupancy[j][-1]:
                        dist = patch.distance_to(other)
                        conn += other.area * np.exp(-cfg.alpha * dist)
                connectivity[i] = conn
            
            # Colonization and extinction for each patch
            for i, patch in enumerate(self.patches):
                occupied = patch_occupancy[i][-1]
                
                # Colonization probability
                C = connectivity[i] / (connectivity[i] + cfg.c)
                
                # Extinction probability (decreases with area)
                E = cfg.e / (patch.area ** cfg.xi)
                
                if cfg.environmental_stochasticity:
                    E *= np.exp(self.rng.normal(0, cfg.env_sigma))
                
                if not occupied:
                    # Try to colonize
                    if self.rng.random() < C:
                        occupied = True
                else:
                    # Check extinction
                    if self.rng.random() < E:
                        occupied = False
                
                patch_occupancy[i].append(occupied)
            
            if year % 10 == 0:
                await asyncio.sleep(0)
        
        # Calculate metrics
        final_occupancy = [p[-1] for p in patch_occupancy]
        occupancy_rates = []
        for i in range(len(patch_occupancy[0])):
            rate = sum(p[i] for p in patch_occupancy) / len(self.patches)
            occupancy_rates.append(rate)
        
        # Incidence vs area relationship
        areas = [p.area for p in self.patches]
        incidences = [sum(p) / len(p) for p in patch_occupancy]
        
        # Correlation between area and occupancy
        area_incidence_corr = np.corrcoef(areas, incidences)[0, 1] if len(areas) > 2 else 0
        
        metrics = {
            "final_occupancy_rate": float(occupancy_rates[-1]),
            "mean_occupancy_rate": float(np.mean(occupancy_rates)),
            "num_patches": cfg.num_patches,
            "num_occupied_final": sum(final_occupancy),
            "area_occupancy_correlation": float(area_incidence_corr),
            "persistence": occupancy_rates[-1] > 0.01,
            "model": "incidence_function",
        }
        
        logs = [
            f"Incidence function simulation completed",
            f"Patches: {cfg.num_patches}, Occupied: {metrics['num_occupied_final']}",
            f"Final occupancy rate: {metrics['final_occupancy_rate']*100:.1f}%",
            f"Area-occupancy correlation: {area_incidence_corr:.3f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "occupancy_rates": occupancy_rates,
            "patch_occupancy": [[bool(o) for o in p] for p in patch_occupancy],
            "patch_areas": areas,
            "patch_incidences": incidences,
        }
    
    async def _spatial_simulation(self) -> Dict[str, Any]:
        """Individual-based spatial simulation"""
        
        cfg = self.config
        
        # Simulate individual dispersal events
        # Track population size in each patch
        
        # Initialize populations
        patch_populations = []
        for patch in self.patches:
            if patch.occupied:
                N = int(patch.area * 10)  # 10 individuals per ha
            else:
                N = 0
            patch_populations.append([N])
        
        for year in range(cfg.years):
            new_populations = []
            
            for i, patch in enumerate(self.patches):
                N = patch_populations[i][-1]
                
                if N > 0:
                    # Local dynamics (logistic)
                    K = int(patch.area * 20)  # Carrying capacity
                    births = self.rng.poisson(N * 0.5 * (1 - N/K))
                    deaths = self.rng.poisson(N * 0.3)
                    N = max(0, N + births - deaths)
                
                # Immigration
                for j, source in enumerate(self.patches):
                    if i != j and patch_populations[j][-1] > 0:
                        dist = patch.distance_to(source)
                        prob = np.exp(-cfg.alpha * dist) * 0.1
                        immigrants = self.rng.poisson(patch_populations[j][-1] * prob)
                        N += immigrants
                
                new_populations.append(N)
            
            for i, N in enumerate(new_populations):
                patch_populations[i].append(N)
            
            if year % 10 == 0:
                await asyncio.sleep(0)
        
        # Metrics
        total_population = [sum(p[i] for p in patch_populations) for i in range(len(patch_populations[0]))]
        occupied_patches = [sum(1 for p in patch_populations if p[i] > 0) for i in range(len(patch_populations[0]))]
        
        metrics = {
            "final_total_population": total_population[-1],
            "mean_total_population": float(np.mean(total_population)),
            "final_occupied_patches": occupied_patches[-1],
            "mean_occupied_patches": float(np.mean(occupied_patches)),
            "model": "spatial",
        }
        
        logs = [
            f"Spatial metapopulation simulation completed",
            f"Final population: {metrics['final_total_population']}",
            f"Patches occupied: {metrics['final_occupied_patches']}/{cfg.num_patches}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "total_population": total_population,
            "occupied_patches": occupied_patches,
        }
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Valid occupancy
        occ = metrics.get("final_occupancy", metrics.get("final_occupancy_rate", 0))
        if 0 <= occ <= 1:
            factors.append(0.3)
        
        # Persistence determinable
        if "persistence" in metrics:
            factors.append(0.25)
        
        # Model-specific
        if self.config.model == MetapopulationModel.LEVINS:
            c_e_ratio = metrics.get("c_e_ratio", 0)
            if c_e_ratio > 0:
                factors.append(0.25)
        
        elif self.config.model == MetapopulationModel.INCIDENCE_FUNCTION:
            if "area_occupancy_correlation" in metrics:
                factors.append(0.25)
        
        # Patch count reasonable
        if self.config.num_patches >= 2:
            factors.append(0.2)
        
        return min(0.95, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_patches = params.get("num_patches", 20)
        years = params.get("years", 100)
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + n_patches * years * 1e-5,
            "gpu_required": False,
            "estimated_time_seconds": n_patches * n_patches * years / 1e6,
        }
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": cls.id,
            "name": cls.name,
            "category": cls.category,
            "description": cls.description,
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
                "Levins, R. (1969). Some demographic and genetic consequences of environmental heterogeneity",
                "Hanski, I. (1999). Metapopulation Ecology",
                "Hanski, I. (1994). A practical model of metapopulation dynamics",
            ],
        }
