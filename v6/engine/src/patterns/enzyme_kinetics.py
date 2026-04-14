"""
Enzyme Kinetics Pattern
Michaelis-Menten and advanced enzyme kinetics models

Based on:
- Michaelis-Menten (1913) - Classic enzyme kinetics
- Briggs-Haldane (1925) - Steady-state approximation
- Hill equation - Cooperative binding
- Monod-Wyman-Changeux - Allosteric regulation
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from scipy.integrate import solve_ivp

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


class KineticModel(Enum):
    MICHAELIS_MENTEN = "michaelis_menten"
    BRIGGS_HALDANE = "briggs_haldane"
    COMPETITIVE_INHIBITION = "competitive_inhibition"
    HILL = "hill"
    MWC = "mwc"  # Monod-Wyman-Changeux


@dataclass
class EnzymeKineticsConfig:
    """Enzyme kinetics configuration"""
    # Model selection
    model: KineticModel = KineticModel.MICHAELIS_MENTEN
    
    # Michaelis-Menten parameters
    Vmax: float = 100.0  # Maximum reaction rate (uM/s)
    Km: float = 50.0  # Michaelis constant (uM)
    
    # Enzyme and substrate
    E0: float = 1.0  # Initial enzyme concentration (uM)
    S0: float = 100.0  # Initial substrate concentration (uM)
    P0: float = 0.0  # Initial product concentration (uM)
    ES0: float = 0.0  # Initial enzyme-substrate complex (uM)
    
    # Briggs-Haldane individual rate constants
    k1: float = 100.0  # E + S -> ES (1/uM/s)
    k_1: float = 50.0  # ES -> E + S (1/s)
    k2: float = 50.0  # ES -> E + P (1/s)
    
    # Inhibition
    I0: float = 0.0  # Inhibitor concentration (uM)
    Ki: float = 10.0  # Inhibition constant (uM)
    
    # Hill equation
    n: float = 1.0  # Hill coefficient
    Kd: float = 50.0  # Dissociation constant
    
    # MWC parameters
    L: float = 1000.0  # Allosteric constant (T/R ratio)
    c: float = 0.01  # Non-exclusive binding factor
    
    # Simulation
    t_max: float = 100.0  # seconds
    dt: float = 0.01  # seconds
    
    # Multiple substrate concentrations for curve
    substrate_range: Tuple[float, float] = (1.0, 1000.0)  # (min, max) uM
    num_points: int = 20  # Number of substrate concentrations
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model.value,
            "Vmax": self.Vmax,
            "Km": self.Km,
            "E0": self.E0,
            "S0": self.S0,
            "P0": self.P0,
            "ES0": self.ES0,
            "k1": self.k1,
            "k_1": self.k_1,
            "k2": self.k2,
            "I0": self.I0,
            "Ki": self.Ki,
            "n": self.n,
            "Kd": self.Kd,
            "L": self.L,
            "c": self.c,
            "t_max": self.t_max,
            "dt": self.dt,
            "substrate_range": self.substrate_range,
            "num_points": self.num_points,
        }


@simulation_pattern(
    id="enzyme_kinetics",
    name="Enzyme Kinetics",
    category="biology",
    description="Michaelis-Menten and advanced enzyme kinetics simulation",
)
class EnzymeKineticsPattern(SimulationPattern):
    """
    Enzyme kinetics simulation for biochemical reactions
    
    Models enzyme-catalyzed reactions with various kinetic formalisms:
    
    1. Michaelis-Menten: Classic steady-state approximation
    2. Briggs-Haldane: Individual rate constants
    3. Competitive Inhibition: Reversible inhibitor binding
    4. Hill Equation: Cooperative binding (sigmoid kinetics)
    5. MWC: Allosteric regulation model
    
    Applications:
    - Drug metabolism (CYP450 enzymes)
    - Metabolic pathway modeling
    - Enzyme inhibitor screening
    - Bioprocess optimization
    """
    
    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="michaelis_menten",
            options=["michaelis_menten", "briggs_haldane", "competitive_inhibition", "hill", "mwc"],
            description="Kinetic model type",
        ),
        SimulationParameter(
            name="Vmax",
            type="float",
            default=100.0,
            min=0.1,
            max=10000.0,
            description="Maximum reaction rate (uM/s)",
        ),
        SimulationParameter(
            name="Km",
            type="float",
            default=50.0,
            min=0.1,
            max=10000.0,
            description="Michaelis constant (uM)",
        ),
        SimulationParameter(
            name="E0",
            type="float",
            default=1.0,
            min=0.01,
            max=1000.0,
            description="Enzyme concentration (uM)",
        ),
        SimulationParameter(
            name="S0",
            type="float",
            default=100.0,
            min=0.0,
            max=10000.0,
            description="Substrate concentration (uM)",
        ),
        SimulationParameter(
            name="I0",
            type="float",
            default=0.0,
            min=0.0,
            max=10000.0,
            description="Inhibitor concentration (uM)",
        ),
        SimulationParameter(
            name="Ki",
            type="float",
            default=10.0,
            min=0.1,
            max=10000.0,
            description="Inhibition constant (uM)",
        ),
        SimulationParameter(
            name="n",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Hill coefficient",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=100.0,
            min=1.0,
            max=1000.0,
            description="Simulation duration (s)",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.config: EnzymeKineticsConfig = EnzymeKineticsConfig()
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if enzyme kinetics can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "enzyme", "kinetics", "michaelis", "menten", "substrate",
            "product", "catalysis", "inhibition", "reaction rate",
            "km", "vmax", "hill", "cooperative", "allosteric",
            "metabolism", "biochemical", "pathway", "cyp",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute enzyme kinetics simulation"""
        start_time = datetime.now()
        simulation_id = f"ek_{start_time.timestamp()}"
        
        logger.info(f"Starting enzyme kinetics simulation {simulation_id}")
        
        try:
            # Parse configuration
            self.config = self._parse_config(config)
            
            # Run simulation based on model type
            if self.config.model == KineticModel.MICHAELIS_MENTEN:
                results = await self._michaelis_menten_simulation()
            elif self.config.model == KineticModel.BRIGGS_HALDANE:
                results = await self._briggs_haldane_simulation()
            elif self.config.model == KineticModel.COMPETITIVE_INHIBITION:
                results = await self._competitive_inhibition_simulation()
            elif self.config.model == KineticModel.HILL:
                results = await self._hill_simulation()
            else:
                results = await self._mwc_simulation()
            
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
            logger.exception("Enzyme kinetics simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> EnzymeKineticsConfig:
        """Parse configuration dictionary"""
        cfg = EnzymeKineticsConfig()
        
        if "model" in config:
            cfg.model = KineticModel(config["model"])
        if "Vmax" in config:
            cfg.Vmax = float(config["Vmax"])
        if "Km" in config:
            cfg.Km = float(config["Km"])
        if "E0" in config:
            cfg.E0 = float(config["E0"])
        if "S0" in config:
            cfg.S0 = float(config["S0"])
        if "P0" in config:
            cfg.P0 = float(config["P0"])
        if "ES0" in config:
            cfg.ES0 = float(config["ES0"])
        if "k1" in config:
            cfg.k1 = float(config["k1"])
        if "k_1" in config:
            cfg.k_1 = float(config["k_1"])
        if "k2" in config:
            cfg.k2 = float(config["k2"])
        if "I0" in config:
            cfg.I0 = float(config["I0"])
        if "Ki" in config:
            cfg.Ki = float(config["Ki"])
        if "n" in config:
            cfg.n = float(config["n"])
        if "Kd" in config:
            cfg.Kd = float(config["Kd"])
        if "L" in config:
            cfg.L = float(config["L"])
        if "c" in config:
            cfg.c = float(config["c"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "num_points" in config:
            cfg.num_points = int(config["num_points"])
            
        return cfg
    
    async def _michaelis_menten_simulation(self) -> Dict[str, Any]:
        """Michaelis-Menten kinetics simulation"""
        
        cfg = self.config
        
        # Time course simulation
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        # Initial conditions
        y0 = [cfg.S0, cfg.P0]
        
        def mm_kinetics(t, y):
            S, P = y
            # Michaelis-Menten rate equation
            v = cfg.Vmax * S / (cfg.Km + S)
            dSdt = -v
            dPdt = v
            return [dSdt, dPdt]
        
        solution = solve_ivp(mm_kinetics, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        S = solution.y[0]
        P = solution.y[1]
        
        # Calculate reaction velocity at each point
        v = cfg.Vmax * S / (cfg.Km + S)
        
        # Generate saturation curve (v vs [S])
        S_range = np.logspace(np.log10(cfg.substrate_range[0]), 
                               np.log10(cfg.substrate_range[1]), cfg.num_points)
        v_curve = cfg.Vmax * S_range / (cfg.Km + S_range)
        
        # Lineweaver-Burk data
        inv_S = 1 / S_range
        inv_v = 1 / v_curve
        
        # Calculate metrics
        metrics = self._calculate_mm_metrics(t, S, P, v, S_range, v_curve)
        
        logs = [
            f"Michaelis-Menten simulation completed",
            f"Parameters: Vmax={cfg.Vmax:.2f} uM/s, Km={cfg.Km:.2f} uM",
            f"Initial substrate: {cfg.S0:.2f} uM",
            f"Final product: {P[-1]:.2f} uM",
            f"Initial velocity: {v[0]:.4f} uM/s",
            f"Km from fit: {metrics['fitted_Km']:.2f} uM",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "velocity": v.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v": v_curve.tolist(),
            "lineweaver_S": inv_S.tolist(),
            "lineweaver_v": inv_v.tolist(),
        }
    
    async def _briggs_haldane_simulation(self) -> Dict[str, Any]:
        """Briggs-Haldane (explicit intermediate) simulation"""
        
        cfg = self.config
        
        # Full mechanism: E + S <-> ES -> E + P
        # State variables: [S, ES, P, E]
        # E is determined by conservation: E = E0 - ES
        
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        # Initial conditions [S, ES, P]
        y0 = [cfg.S0, cfg.ES0, cfg.P0]
        
        def bh_kinetics(t, y):
            S, ES, P = y
            E = cfg.E0 - ES  # Enzyme conservation
            
            # Rate equations
            dSdt = -cfg.k1 * E * S + cfg.k_1 * ES
            dESdt = cfg.k1 * E * S - cfg.k_1 * ES - cfg.k2 * ES
            dPdt = cfg.k2 * ES
            
            return [dSdt, dESdt, dPdt]
        
        solution = solve_ivp(bh_kinetics, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        S = solution.y[0]
        ES = solution.y[1]
        P = solution.y[2]
        E = cfg.E0 - ES
        
        # Calculate apparent Km and Vmax
        # Vmax = k2 * E0
        # Km = (k_1 + k2) / k1
        apparent_Vmax = cfg.k2 * cfg.E0
        apparent_Km = (cfg.k_1 + cfg.k2) / cfg.k1
        
        metrics = {
            "apparent_Vmax": apparent_Vmax,
            "apparent_Km": apparent_Km,
            "k1": cfg.k1,
            "k_1": cfg.k_1,
            "k2": cfg.k2,
            "final_product": float(P[-1]),
            "final_substrate": float(S[-1]),
            "max_ES": float(np.max(ES)),
            "model": "briggs_haldane",
        }
        
        logs = [
            f"Briggs-Haldane simulation completed",
            f"Rate constants: k1={cfg.k1}, k-1={cfg.k_1}, k2={cfg.k2}",
            f"Apparent Vmax: {apparent_Vmax:.2f} uM/s",
            f"Apparent Km: {apparent_Km:.2f} uM",
            f"Max ES complex: {metrics['max_ES']:.4f} uM",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "enzyme_substrate": ES.tolist(),
            "free_enzyme": E.tolist(),
            "product": P.tolist(),
        }
    
    async def _competitive_inhibition_simulation(self) -> Dict[str, Any]:
        """Competitive inhibition simulation"""
        
        cfg = self.config
        
        # Inhibitor competes with substrate for active site
        # E + I <-> EI (inactive)
        # Reduced apparent Vmax or increased Km depending on model
        
        # Modified Michaelis-Menten with inhibition
        def inhibited_rate(S, I):
            # Competitive inhibition increases apparent Km
            alpha = 1 + I / cfg.Ki
            Km_app = cfg.Km * alpha
            return cfg.Vmax * S / (Km_app + S)
        
        # Time course
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.P0]
        
        def inhibited_kinetics(t, y):
            S, P = y
            v = inhibited_rate(S, cfg.I0)
            return [-v, v]
        
        solution = solve_ivp(inhibited_kinetics, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        S = solution.y[0]
        P = solution.y[1]
        v = np.array([inhibited_rate(s, cfg.I0) for s in S])
        
        # Generate curves without and with inhibitor
        S_range = np.linspace(cfg.substrate_range[0], cfg.substrate_range[1], cfg.num_points)
        v_no_inhibitor = cfg.Vmax * S_range / (cfg.Km + S_range)
        v_with_inhibitor = [inhibited_rate(s, cfg.I0) for s in S_range]
        
        alpha = 1 + cfg.I0 / cfg.Ki
        Km_app = cfg.Km * alpha
        
        metrics = {
            "Vmax": cfg.Vmax,
            "Km": cfg.Km,
            "Km_apparent": Km_app,
            "inhibition_factor": alpha,
            "I0": cfg.I0,
            "Ki": cfg.Ki,
            "percent_inhibition": (1 - v[-1] / (cfg.Vmax * S[-1] / (cfg.Km + S[-1]))) * 100,
            "model": "competitive_inhibition",
        }
        
        logs = [
            f"Competitive inhibition simulation completed",
            f"[I] = {cfg.I0:.2f} uM, Ki = {cfg.Ki:.2f} uM",
            f"Apparent Km: {Km_app:.2f} uM (factor: {alpha:.2f})",
            f"Vmax unchanged: {cfg.Vmax:.2f} uM/s",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "velocity": v.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v_control": v_no_inhibitor.tolist(),
            "saturation_v_inhibited": v_with_inhibitor,
        }
    
    async def _hill_simulation(self) -> Dict[str, Any]:
        """Hill equation (cooperative binding) simulation"""
        
        cfg = self.config
        
        # Hill equation: v = Vmax * [S]^n / (Kd^n + [S]^n)
        # n > 1: positive cooperativity
        # n < 1: negative cooperativity
        # n = 1: no cooperativity (reduces to MM)
        
        def hill_rate(S):
            return cfg.Vmax * S**cfg.n / (cfg.Kd**cfg.n + S**cfg.n)
        
        # Time course
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.P0]
        
        def hill_kinetics(t, y):
            S, P = y
            v = hill_rate(S)
            return [-v, v]
        
        solution = solve_ivp(hill_kinetics, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        S = solution.y[0]
        P = solution.y[1]
        
        # Saturation curve
        S_range = np.logspace(np.log10(cfg.substrate_range[0]), 
                               np.log10(cfg.substrate_range[1]), cfg.num_points)
        v_curve = [hill_rate(s) for s in S_range]
        
        # Calculate EC50 (concentration at half Vmax)
        EC50 = cfg.Kd
        
        # Hill plot (logit transformation)
        Y = np.array(v_curve) / cfg.Vmax
        log_S = np.log10(S_range[Y > 0.01])  # Avoid log(0)
        logit_Y = np.log10(Y[Y > 0.01] / (1 - Y[Y > 0.01]))
        
        # Slope of Hill plot gives Hill coefficient
        if len(log_S) > 2:
            hill_slope = np.polyfit(log_S, logit_Y, 1)[0]
        else:
            hill_slope = cfg.n
        
        metrics = {
            "Vmax": cfg.Vmax,
            "n": cfg.n,
            "Kd": cfg.Kd,
            "EC50": EC50,
            "hill_slope_fitted": hill_slope,
            "cooperativity": "positive" if cfg.n > 1 else ("negative" if cfg.n < 1 else "none"),
            "final_product": float(P[-1]),
            "model": "hill",
        }
        
        logs = [
            f"Hill equation simulation completed",
            f"Hill coefficient n = {cfg.n:.2f}",
            f"Kd = {cfg.Kd:.2f} uM, EC50 = {EC50:.2f} uM",
            f"Cooperativity: {metrics['cooperativity']}",
            f"Fitted Hill slope: {hill_slope:.2f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v": v_curve,
            "hill_plot_x": log_S.tolist(),
            "hill_plot_y": logit_Y.tolist(),
        }
    
    async def _mwc_simulation(self) -> Dict[str, Any]:
        """Monod-Wyman-Changeux allosteric model"""
        
        cfg = self.config
        
        # MWC model for allosteric enzymes
        # T (tense) and R (relaxed) states in equilibrium
        # Substrate binds preferentially to R state
        
        def mwc_fraction_active(S):
            # Fraction of enzyme in R state with substrate bound
            L = cfg.L
            c = cfg.c
            n = cfg.n  # Number of subunits
            
            alpha = S / cfg.Kd  # Normalized substrate concentration
            
            # Fraction of active (R) form
            Y = (alpha * (1 + alpha)**(n-1) + L * c * alpha * (1 + c * alpha)**(n-1)) / \
                ((1 + alpha)**n + L * (1 + c * alpha)**n)
            
            return Y
        
        # Saturation curve
        S_range = np.logspace(np.log10(cfg.substrate_range[0]), 
                               np.log10(cfg.substrate_range[1]), cfg.num_points)
        fraction_active = [mwc_fraction_active(s) for s in S_range]
        v_curve = [cfg.Vmax * f for f in fraction_active]
        
        # Time course (simplified)
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.P0]
        
        def mwc_kinetics(t, y):
            S, P = y
            f = mwc_fraction_active(S)
            v = cfg.Vmax * f
            return [-v, v]
        
        solution = solve_ivp(mwc_kinetics, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        S = solution.y[0]
        P = solution.y[1]
        
        metrics = {
            "Vmax": cfg.Vmax,
            "L": cfg.L,
            "c": cfg.c,
            "n": cfg.n,
            "Kd": cfg.Kd,
            "T0_R0_ratio": cfg.L,
            "final_product": float(P[-1]),
            "model": "mwc",
        }
        
        logs = [
            f"MWC allosteric model simulation completed",
            f"Allosteric constant L = {cfg.L:.2f}",
            f"Non-exclusive binding c = {cfg.c:.4f}",
            f"T0/R0 ratio: {cfg.L:.2f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v": v_curve,
            "fraction_active": fraction_active,
        }
    
    def _calculate_mm_metrics(
        self, t: np.ndarray, S: np.ndarray, P: np.ndarray,
        v: np.ndarray, S_range: np.ndarray, v_curve: np.ndarray
    ) -> Dict[str, float]:
        """Calculate Michaelis-Menten metrics"""
        
        # Fit Km and Vmax from data
        # Use double-reciprocal (Lineweaver-Burk) for estimation
        inv_S = 1 / S_range[S_range > 0]
        inv_v = 1 / np.array(v_curve)[S_range > 0]
        
        # Linear regression on Lineweaver-Burk plot
        if len(inv_S) > 2:
            slope, intercept = np.polyfit(inv_S, inv_v, 1)
            fitted_Vmax = 1 / intercept if intercept > 0 else self.config.Vmax
            fitted_Km = slope / intercept if intercept > 0 else self.config.Km
        else:
            fitted_Vmax = self.config.Vmax
            fitted_Km = self.config.Km
        
        # Initial velocity
        v0 = float(v[0]) if len(v) > 0 else 0
        
        # Final concentrations
        S_final = float(S[-1]) if len(S) > 0 else 0
        P_final = float(P[-1]) if len(P) > 0 else 0
        
        # Reaction extent
        extent = (self.config.S0 - S_final) / self.config.S0 if self.config.S0 > 0 else 0
        
        # Catalytic efficiency (kcat/Km approximation)
        # Assuming [E] = 1 uM, kcat ≈ Vmax
        catalytic_efficiency = fitted_Vmax / fitted_Km if fitted_Km > 0 else 0
        
        return {
            "fitted_Vmax": fitted_Vmax,
            "fitted_Km": fitted_Km,
            "input_Vmax": self.config.Vmax,
            "input_Km": self.config.Km,
            "initial_velocity": v0,
            "final_substrate": S_final,
            "final_product": P_final,
            "reaction_extent": extent,
            "catalytic_efficiency": catalytic_efficiency,
            "model": "michaelis_menten",
        }
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Reaction proceeded
        extent = metrics.get("reaction_extent", 0)
        if 0.01 < extent < 1.0:
            factors.append(0.3)
        
        # Fitted parameters reasonable
        fitted_km = metrics.get("fitted_Km", 0)
        if 0.1 < fitted_km < 10000:
            factors.append(0.25)
        
        # Positive concentrations
        if metrics.get("final_product", 0) >= 0:
            factors.append(0.25)
        
        # Model-specific checks
        if self.config.model == KineticModel.MICHAELIS_MENTEN:
            # Check if fitted matches input reasonably
            input_km = metrics.get("input_Km", 0)
            if abs(fitted_km - input_km) / (input_km + 1) < 0.5:
                factors.append(0.2)
        
        return min(0.95, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 100.0)
        num_points = params.get("num_points", 20)
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": 1 + t_max / 100 + num_points / 10,
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
                "Michaelis, L. & Menten, M. (1913). Die Kinetik der Invertinwirkung",
                "Briggs, G.E. & Haldane, J.B.S. (1925). A note on the kinetics of enzyme action",
                "Monod, J. et al. (1965). On the nature of allosteric transitions",
            ],
        }
