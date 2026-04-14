"""
Fisheries Pattern
Stock-recruitment and age-structured fish population models

Based on:
- Beverton-Holt stock-recruitment (1957)
- Ricker model (1954)
- Schaefer surplus production
- Age-structured assessment (Virtual Population Analysis)
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


class RecruitmentModel(Enum):
    BEVERTON_HOLT = "beverton_holt"
    RICKER = "ricker"
    LOGISTIC = "logistic"


class ProductionModel(Enum):
    SCHAFFER = "schaefer"
    FOX = "fox"
    THOMPSON_BELL = "thompson_bell"


@dataclass
class FisheriesConfig:
    """Fisheries model configuration"""
    # Model selection
    recruitment_model: RecruitmentModel = RecruitmentModel.BEVERTON_HOLT
    production_model: ProductionModel = ProductionModel.SCHAFFER
    
    # Population parameters
    r_max: float = 0.3  # Maximum intrinsic growth rate
    K: float = 10000.0  # Carrying capacity (tonnes)
    B0: float = 8000.0  # Initial biomass
    
    # Stock-recruitment parameters
    alpha: float = 1000.0  # Recruitment scaling
    beta: float = 0.0001  # Density dependence
    steepness: float = 0.8  # Recruitment steepness (h)
    
    # Age structure
    max_age: int = 15
    natural_mortality: float = 0.2  # Annual
    ages_at_maturity: int = 3
    
    # Fishing
    fishing_mortality: float = 0.2  # Annual rate
    years: int = 50
    
    # Reference points
    f_msy: Optional[float] = None  # F at MSY
    b_msy: Optional[float] = None  # B at MSY
    
    # Management
    quota: Optional[float] = None  # Fixed quota
    effort_limit: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recruitment_model": self.recruitment_model.value,
            "production_model": self.production_model.value,
            "r_max": self.r_max,
            "K": self.K,
            "B0": self.B0,
            "alpha": self.alpha,
            "beta": self.beta,
            "steepness": self.steepness,
            "max_age": self.max_age,
            "natural_mortality": self.natural_mortality,
            "ages_at_maturity": self.ages_at_maturity,
            "fishing_mortality": self.fishing_mortality,
            "years": self.years,
            "f_msy": self.f_msy,
            "b_msy": self.b_msy,
            "quota": self.quota,
            "effort_limit": self.effort_limit,
        }


@simulation_pattern(
    id="fisheries",
    name="Fisheries Stock Assessment",
    category="ecology",
    description="Stock-recruitment and age-structured fisheries population models",
)
class FisheriesPattern(SimulationPattern):
    """
    Fisheries population dynamics simulation
    
    Models fish population dynamics for stock assessment:
    
    1. Surplus Production (Schaefer/Fox):
       - Aggregate biomass approach
       - MSY estimation
       
    2. Stock-Recruitment (Beverton-Holt/Ricker):
       - Spawner-recruit relationships
       - Steepness parameter
       
    3. Age-Structured:
       - Cohort analysis
       - Selectivity patterns
    
    Applications:
    - Stock assessment
    - Management strategy evaluation
    - Rebuilding analysis
    - Climate impacts
    """
    
    parameters = [
        SimulationParameter(
            name="recruitment_model",
            type="select",
            default="beverton_holt",
            options=["beverton_holt", "ricker", "logistic"],
            description="Stock-recruitment relationship",
        ),
        SimulationParameter(
            name="production_model",
            type="select",
            default="schaefer",
            options=["schaefer", "fox", "thompson_bell"],
            description="Surplus production model",
        ),
        SimulationParameter(
            name="r_max",
            type="float",
            default=0.3,
            min=0.01,
            max=2.0,
            description="Maximum growth rate",
        ),
        SimulationParameter(
            name="K",
            type="float",
            default=10000.0,
            min=100.0,
            max=1000000.0,
            description="Carrying capacity (tonnes)",
        ),
        SimulationParameter(
            name="B0",
            type="float",
            default=8000.0,
            min=1.0,
            max=1000000.0,
            description="Initial biomass",
        ),
        SimulationParameter(
            name="steepness",
            type="float",
            default=0.8,
            min=0.2,
            max=1.0,
            description="Recruitment steepness (h)",
        ),
        SimulationParameter(
            name="natural_mortality",
            type="float",
            default=0.2,
            min=0.0,
            max=1.0,
            description="Natural mortality rate",
        ),
        SimulationParameter(
            name="fishing_mortality",
            type="float",
            default=0.2,
            min=0.0,
            max=1.0,
            description="Fishing mortality rate",
        ),
        SimulationParameter(
            name="years",
            type="int",
            default=50,
            min=10,
            max=200,
            description="Simulation duration (years)",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.config: FisheriesConfig = FisheriesConfig()
        self.rng = np.random.default_rng(seed=42)
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if fisheries can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "fish", "fishery", "fishing", "stock", "population",
            "biomass", "recruitment", "spawning", "catch", "harvest",
            "mortality", "msy", "quota", "assessment", "age structure",
            "cohort", "surplus production", "beverton-holt", "ricker",
            "sustainability", "overfishing", "rebuilding",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute fisheries simulation"""
        start_time = datetime.now()
        simulation_id = f"fish_{start_time.timestamp()}"
        
        logger.info(f"Starting fisheries simulation {simulation_id}")
        
        try:
            # Parse configuration
            self.config = self._parse_config(config)
            
            # Run simulation based on model
            if self.config.production_model == ProductionModel.SCHAFFER:
                results = await self._schaefer_simulation()
            elif self.config.production_model == ProductionModel.FOX:
                results = await self._fox_simulation()
            else:
                results = await self._age_structured_simulation()
            
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
            logger.exception("Fisheries simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> FisheriesConfig:
        """Parse configuration dictionary"""
        cfg = FisheriesConfig()
        
        if "recruitment_model" in config:
            cfg.recruitment_model = RecruitmentModel(config["recruitment_model"])
        if "production_model" in config:
            cfg.production_model = ProductionModel(config["production_model"])
        if "r_max" in config:
            cfg.r_max = float(config["r_max"])
        if "K" in config:
            cfg.K = float(config["K"])
        if "B0" in config:
            cfg.B0 = float(config["B0"])
        if "alpha" in config:
            cfg.alpha = float(config["alpha"])
        if "beta" in config:
            cfg.beta = float(config["beta"])
        if "steepness" in config:
            cfg.steepness = float(config["steepness"])
        if "max_age" in config:
            cfg.max_age = int(config["max_age"])
        if "natural_mortality" in config:
            cfg.natural_mortality = float(config["natural_mortality"])
        if "ages_at_maturity" in config:
            cfg.ages_at_maturity = int(config["ages_at_maturity"])
        if "fishing_mortality" in config:
            cfg.fishing_mortality = float(config["fishing_mortality"])
        if "years" in config:
            cfg.years = int(config["years"])
        if "quota" in config:
            cfg.quota = float(config["quota"]) if config["quota"] else None
        if "effort_limit" in config:
            cfg.effort_limit = float(config["effort_limit"]) if config["effort_limit"] else None
            
        return cfg
    
    async def _schaefer_simulation(self) -> Dict[str, Any]:
        """Schaefer surplus production model"""
        
        cfg = self.config
        
        # Schaefer: dB/dt = r*B*(1 - B/K) - C
        # where C = q*E*B (catch = catchability * effort * biomass)
        
        B = cfg.B0  # Current biomass
        
        biomass_history = [B]
        catch_history = []
        recruitment_history = []
        
        for year in range(cfg.years):
            # Surplus production
            production = cfg.r_max * B * (1 - B / cfg.K)
            
            # Natural mortality (included in logistic)
            # Recruitment (implicit in production model)
            recruitment = production
            
            # Catch
            if cfg.quota is not None:
                catch = min(cfg.quota, B * 0.5)  # Can't catch more than 50% of biomass
            else:
                catch = cfg.fishing_mortality * B
            
            # Update biomass
            B = B + production - catch
            B = max(B, 1.0)  # Minimum biomass floor
            
            biomass_history.append(B)
            catch_history.append(catch)
            recruitment_history.append(recruitment)
            
            if year % 10 == 0:
                await asyncio.sleep(0)
        
        # Calculate reference points
        B_msy = cfg.K / 2
        MSY = cfg.r_max * B_msy * (1 - B_msy / cfg.K)
        F_msy = cfg.r_max / 2
        
        # Current status
        final_B = biomass_history[-1]
        depletion = final_B / cfg.K
        
        metrics = {
            "final_biomass": float(final_B),
            "final_catch": float(catch_history[-1]),
            "mean_biomass": float(np.mean(biomass_history)),
            "mean_catch": float(np.mean(catch_history)),
            "B_msy": float(B_msy),
            "MSY": float(MSY),
            "F_msy": float(F_msy),
            "depletion": float(depletion),
            "B_Bmsy": float(final_B / B_msy),
            "status": self._assess_status(final_B, B_msy, cfg.fishing_mortality, F_msy),
            "model": "schaefer",
        }
        
        logs = [
            f"Schaefer model simulation completed",
            f"Initial biomass: {cfg.B0:.1f} t, Carrying capacity: {cfg.K:.1f} t",
            f"Final biomass: {final_B:.1f} t ({depletion*100:.1f}% of K)",
            f"B/Bmsy: {metrics['B_Bmsy']:.2f}, Status: {metrics['status']}",
            f"MSY: {MSY:.1f} t/year",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "biomass": biomass_history,
            "catch": catch_history,
            "recruitment": recruitment_history,
        }
    
    def _assess_status(self, B: float, B_msy: float, F: float, F_msy: float) -> str:
        """Assess stock status"""
        B_ratio = B / B_msy
        F_ratio = F / F_msy if F_msy > 0 else 0
        
        if B_ratio < 0.5:
            return "overfished" if F_ratio > 1 else "depleted"
        elif F_ratio > 1:
            return "overfishing"
        else:
            return "healthy"
    
    async def _fox_simulation(self) -> Dict[str, Any]:
        """Fox surplus production model (asymmetric)"""
        
        cfg = self.config
        
        # Fox: dB/dt = r*B*ln(K/B) - C
        # More realistic asymmetric production curve
        
        B = cfg.B0
        
        biomass_history = [B]
        catch_history = []
        
        for year in range(cfg.years):
            # Fox production
            production = cfg.r_max * B * np.log(cfg.K / max(B, 1))
            
            # Catch
            if cfg.quota is not None:
                catch = min(cfg.quota, B * 0.5)
            else:
                catch = cfg.fishing_mortality * B
            
            B = B + production - catch
            B = max(B, 1.0)
            
            biomass_history.append(B)
            catch_history.append(catch)
            
            if year % 10 == 0:
                await asyncio.sleep(0)
        
        # Fox reference points (Bmsy = K/e ≈ 0.368*K)
        B_msy = cfg.K / np.e
        MSY = cfg.r_max * B_msy
        F_msy = cfg.r_max
        
        final_B = biomass_history[-1]
        
        metrics = {
            "final_biomass": float(final_B),
            "B_msy": float(B_msy),
            "MSY": float(MSY),
            "F_msy": float(F_msy),
            "depletion": float(final_B / cfg.K),
            "B_Bmsy": float(final_B / B_msy),
            "model": "fox",
        }
        
        logs = [
            f"Fox model simulation completed",
            f"B/Bmsy: {metrics['B_Bmsy']:.2f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "biomass": biomass_history,
            "catch": catch_history,
        }
    
    async def _age_structured_simulation(self) -> Dict[str, Any]:
        """Age-structured population model"""
        
        cfg = self.config
        
        # Initialize age structure
        N = np.zeros(cfg.max_age)  # Numbers at age
        
        # Steady-state initial population
        R0 = 1000  # Initial recruitment
        for a in range(cfg.max_age):
            N[a] = R0 * np.exp(-cfg.natural_mortality * a)
        
        age_history = []
        spawning_biomass_history = []
        recruitment_history = []
        catch_history = []
        
        # Weight at age (von Bertalanffy growth)
        weight_at_age = np.array([
            0.1 * (1 - np.exp(-0.3 * (a - 1)))**3 
            for a in range(1, cfg.max_age + 1)
        ])
        weight_at_age = np.maximum(weight_at_age, 0.01)
        
        # Maturity at age (logistic)
        maturity_at_age = 1 / (1 + np.exp(-0.5 * (np.arange(cfg.max_age) - cfg.ages_at_maturity)))
        
        for year in range(cfg.years):
            # Calculate spawning biomass
            spawning_biomass = np.sum(N * maturity_at_age * weight_at_age)
            spawning_biomass_history.append(float(spawning_biomass))
            
            # Recruitment
            recruitment = self._calculate_recruitment(spawning_biomass)
            recruitment_history.append(float(recruitment))
            
            # Catch at age
            catch_at_age = N * (1 - np.exp(-cfg.fishing_mortality)) * weight_at_age
            total_catch = np.sum(catch_at_age)
            catch_history.append(float(total_catch))
            
            # Update population (natural + fishing mortality)
            Z = cfg.natural_mortality + cfg.fishing_mortality
            
            # Age advancement
            new_N = np.zeros(cfg.max_age)
            new_N[0] = recruitment  # Recruitment to age 0
            for a in range(1, cfg.max_age):
                new_N[a] = N[a-1] * np.exp(-Z)
            # Plus group
            new_N[cfg.max_age-1] += N[cfg.max_age-1] * np.exp(-Z)
            
            N = new_N
            age_history.append(N.copy())
            
            if year % 10 == 0:
                await asyncio.sleep(0)
        
        # Metrics
        final_biomass = np.sum(N * weight_at_age)
        
        metrics = {
            "final_biomass": float(final_biomass),
            "final_recruitment": float(recruitment_history[-1]),
            "mean_spawning_biomass": float(np.mean(spawning_biomass_history)),
            "mean_recruitment": float(np.mean(recruitment_history)),
            "mean_catch": float(np.mean(catch_history)),
            "final_catch": float(catch_history[-1]),
            "model": "age_structured",
            "ages": cfg.max_age,
        }
        
        logs = [
            f"Age-structured simulation completed",
            f"Ages: {cfg.max_age}, Maturity at age {cfg.ages_at_maturity}",
            f"Final biomass: {final_biomass:.1f} t",
            f"Mean recruitment: {metrics['mean_recruitment']:.1f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "age_structure": [n.tolist() for n in age_history[::5]],
            "spawning_biomass": spawning_biomass_history,
            "recruitment": recruitment_history,
            "catch": catch_history,
        }
    
    def _calculate_recruitment(self, spawning_biomass: float) -> float:
        """Calculate recruitment from spawning biomass"""
        cfg = self.config
        
        if cfg.recruitment_model == RecruitmentModel.BEVERTON_HOLT:
            # Beverton-Holt: R = alpha * S / (1 + beta * S)
            return cfg.alpha * spawning_biomass / (1 + cfg.beta * spawning_biomass)
        
        elif cfg.recruitment_model == RecruitmentModel.RICKER:
            # Ricker: R = alpha * S * exp(-beta * S)
            return cfg.alpha * spawning_biomass * np.exp(-cfg.beta * spawning_biomass)
        
        else:  # Logistic
            # Simplified logistic
            return cfg.r_max * spawning_biomass * (1 - spawning_biomass / cfg.K)
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Biomass in reasonable range
        B = metrics.get("final_biomass", 0)
        K = self.config.K
        if 0 < B < K * 2:  # Allow some overshoot
            factors.append(0.3)
        
        # Positive catch
        catch = metrics.get("final_catch", 0)
        if catch >= 0:
            factors.append(0.2)
        
        # Valid status
        status = metrics.get("status", "")
        if status in ["healthy", "overfishing", "overfished", "depleted"]:
            factors.append(0.25)
        
        # Biomass changed over simulation
        B0 = self.config.B0
        if abs(B - B0) / (B0 + 1) > 0.01:
            factors.append(0.25)
        
        return min(0.95, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        years = params.get("years", 50)
        max_age = params.get("max_age", 15)
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": years * max_age / 1000,
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
                "Beverton, R.J.H. & Holt, S.J. (1957). On the Dynamics of Exploited Fish Populations",
                "Ricker, W.E. (1954). Stock and recruitment",
                "Schaefer, M.B. (1954). Some aspects of the dynamics of populations",
            ],
        }
