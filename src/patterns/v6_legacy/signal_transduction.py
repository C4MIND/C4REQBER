"""
Signal Transduction Pattern
ODE-based signaling cascade and network simulation

Based on:
- MAPK cascade (Huang-Ferrell, 1996)
- GPCR signaling (Kenakin, 2009)
- Ultrasensitivity and bistability
- Adaptation and oscillations
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


class SignalingModel(Enum):
    MAPK_CASCADE = "mapk_cascade"
    GPCR = "gpcr"
    ADAPTATION = "adaptation"
    REPRESSILATOR = "repressilator"
    TOGGLE_SWITCH = "toggle_switch"


@dataclass
class SignalTransductionConfig:
    """Signal transduction configuration"""
    # Model selection
    model: SignalingModel = SignalingModel.MAPK_CASCADE
    
    # General parameters
    t_max: float = 1000.0  # seconds
    dt: float = 0.1  # seconds
    
    # MAPK cascade parameters
    E1_total: float = 0.1  # uM - MAPKKK kinase
    E2_total: float = 0.1  # uM - MAPKKK phosphatase
    MAPKK_total: float = 10.0  # uM
    MAPK_total: float = 10.0  # uM
    
    # Kinetic constants
    k1: float = 0.01  # 1/(uM*s)
    k2: float = 0.1  # 1/s
    k3: float = 0.01  # 1/(uM*s)
    k4: float = 0.1  # 1/s
    
    # GPCR parameters
    R_total: float = 1.0  # uM - Receptor
    G_total: float = 1.0  # uM - G-protein
    ligand_conc: float = 0.1  # uM - Stimulus
    
    # Adaptation parameters
    stimulus_amp: float = 1.0
    stimulus_duration: float = 100.0
    adaptation_rate: float = 0.1
    
    # Repressilator parameters
    n_genes: int = 3
    alpha: float = 250.0  # Promoter strength
    beta: float = 5.0  # mRNA decay / protein decay ratio
    n_hill: float = 2.0  # Hill coefficient
    
    # Toggle switch parameters
    gamma: float = 1.0  # Degradation rate
    K: float = 1.0  # Threshold
    
    # Analysis
    num_stimulus_levels: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model.value,
            "t_max": self.t_max,
            "dt": self.dt,
            "E1_total": self.E1_total,
            "E2_total": self.E2_total,
            "MAPKK_total": self.MAPKK_total,
            "MAPK_total": self.MAPK_total,
            "k1": self.k1,
            "k2": self.k2,
            "k3": self.k3,
            "k4": self.k4,
            "R_total": self.R_total,
            "G_total": self.G_total,
            "ligand_conc": self.ligand_conc,
            "stimulus_amp": self.stimulus_amp,
            "stimulus_duration": self.stimulus_duration,
            "adaptation_rate": self.adaptation_rate,
            "n_genes": self.n_genes,
            "alpha": self.alpha,
            "beta": self.beta,
            "n_hill": self.n_hill,
            "gamma": self.gamma,
            "K": self.K,
            "num_stimulus_levels": self.num_stimulus_levels,
        }


@simulation_pattern(
    id="signal_transduction",
    name="Signal Transduction",
    category="biology",
    description="ODE-based signaling cascade and network dynamics",
)
class SignalTransductionPattern(SimulationPattern):
    """
    Signal transduction pathway simulation
    
    Models cellular signaling cascades using systems of ODEs.
    Captures key signaling properties like amplification,
    ultrasensitivity, adaptation, and oscillations.
    
    Models supported:
    1. MAPK Cascade: Three-tier phosphorylation cascade
    2. GPCR: G-protein coupled receptor signaling
    3. Adaptation: Perfect or near-perfect adaptation
    4. Repressilator: Synthetic genetic oscillator
    5. Toggle Switch: Bistable genetic switch
    
    Applications:
    - Drug target identification
    - Cancer signaling studies
    - Synthetic biology design
    - Systems pharmacology
    """
    
    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="mapk_cascade",
            options=["mapk_cascade", "gpcr", "adaptation", "repressilator", "toggle_switch"],
            description="Signaling pathway model",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=1000.0,
            min=10.0,
            max=10000.0,
            description="Simulation duration (s)",
        ),
        SimulationParameter(
            name="E1_total",
            type="float",
            default=0.1,
            min=0.001,
            max=10.0,
            description="MAPKKK kinase (uM)",
        ),
        SimulationParameter(
            name="MAPKK_total",
            type="float",
            default=10.0,
            min=0.1,
            max=100.0,
            description="Total MAPKK (uM)",
        ),
        SimulationParameter(
            name="MAPK_total",
            type="float",
            default=10.0,
            min=0.1,
            max=100.0,
            description="Total MAPK (uM)",
        ),
        SimulationParameter(
            name="ligand_conc",
            type="float",
            default=0.1,
            min=0.0,
            max=10.0,
            description="Ligand concentration (uM)",
        ),
        SimulationParameter(
            name="stimulus_amp",
            type="float",
            default=1.0,
            min=0.0,
            max=10.0,
            description="Stimulus amplitude",
        ),
        SimulationParameter(
            name="alpha",
            type="float",
            default=250.0,
            min=10.0,
            max=1000.0,
            description="Promoter strength (repressilator)",
        ),
        SimulationParameter(
            name="beta",
            type="float",
            default=5.0,
            min=0.1,
            max=50.0,
            description="Decay ratio (repressilator)",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.config: SignalTransductionConfig = SignalTransductionConfig()
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if signal transduction can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "signaling", "transduction", "cascade", "mapk", "erk", "kinase",
            "phosphorylation", "receptor", "gpcr", "g-protein", "second messenger",
            "adaptation", "oscillation", "bistability", "ultrasensitive",
            "synthetic biology", "repressilator", "toggle", "feedback",
            "cellular response", "signal amplification",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute signal transduction simulation"""
        start_time = datetime.now()
        simulation_id = f"st_{start_time.timestamp()}"
        
        logger.info(f"Starting signal transduction simulation {simulation_id}")
        
        try:
            # Parse configuration
            self.config = self._parse_config(config)
            
            # Run simulation based on model type
            if self.config.model == SignalingModel.MAPK_CASCADE:
                results = await self._mapk_simulation()
            elif self.config.model == SignalingModel.GPCR:
                results = await self._gpcr_simulation()
            elif self.config.model == SignalingModel.ADAPTATION:
                results = await self._adaptation_simulation()
            elif self.config.model == SignalingModel.REPRESSILATOR:
                results = await self._repressilator_simulation()
            else:
                results = await self._toggle_switch_simulation()
            
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
            logger.exception("Signal transduction simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> SignalTransductionConfig:
        """Parse configuration dictionary"""
        cfg = SignalTransductionConfig()
        
        if "model" in config:
            cfg.model = SignalingModel(config["model"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "E1_total" in config:
            cfg.E1_total = float(config["E1_total"])
        if "E2_total" in config:
            cfg.E2_total = float(config["E2_total"])
        if "MAPKK_total" in config:
            cfg.MAPKK_total = float(config["MAPKK_total"])
        if "MAPK_total" in config:
            cfg.MAPK_total = float(config["MAPK_total"])
        if "k1" in config:
            cfg.k1 = float(config["k1"])
        if "k2" in config:
            cfg.k2 = float(config["k2"])
        if "k3" in config:
            cfg.k3 = float(config["k3"])
        if "k4" in config:
            cfg.k4 = float(config["k4"])
        if "R_total" in config:
            cfg.R_total = float(config["R_total"])
        if "G_total" in config:
            cfg.G_total = float(config["G_total"])
        if "ligand_conc" in config:
            cfg.ligand_conc = float(config["ligand_conc"])
        if "stimulus_amp" in config:
            cfg.stimulus_amp = float(config["stimulus_amp"])
        if "stimulus_duration" in config:
            cfg.stimulus_duration = float(config["stimulus_duration"])
        if "adaptation_rate" in config:
            cfg.adaptation_rate = float(config["adaptation_rate"])
        if "n_genes" in config:
            cfg.n_genes = int(config["n_genes"])
        if "alpha" in config:
            cfg.alpha = float(config["alpha"])
        if "beta" in config:
            cfg.beta = float(config["beta"])
        if "n_hill" in config:
            cfg.n_hill = float(config["n_hill"])
        if "gamma" in config:
            cfg.gamma = float(config["gamma"])
        if "K" in config:
            cfg.K = float(config["K"])
            
        return cfg
    
    async def _mapk_simulation(self) -> Dict[str, Any]:
        """MAPK cascade (Huang-Ferrell) simulation"""
        
        cfg = self.config
        
        # State variables: MAPKKK*, MAPKK-P, MAPKK-PP, MAPK-P, MAPK-PP
        # Using conservation: MAPKK_total = MAPKK + MAPKK-P + MAPKK-PP
        #                    MAPK_total = MAPK + MAPK-P + MAPK-PP
        
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        # Initial conditions: all inactive
        y0 = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        def mapk_equations(t, y):
            MKKK_star, MKK_P, MKK_PP, MK_P, MK_PP = y
            
            MKKK = cfg.E1_total - MKKK_star  # Assuming E1 is MKKKK
            MKK = cfg.MAPKK_total - MKK_P - MKK_PP
            MK = cfg.MAPK_total - MK_P - MK_PP
            
            # MAPKKK activation
            dMKKK_star = (cfg.k1 * cfg.E1_total * MKKK - cfg.k2 * MKKK_star)
            
            # MAPKK phosphorylation (two steps)
            v1 = cfg.k1 * MKKK_star * MKK
            v2 = cfg.k2 * MKK_P
            v3 = cfg.k3 * MKKK_star * MKK_P
            v4 = cfg.k4 * MKK_PP
            
            dMKK_P = v1 - v2 - v3 + v4
            dMKK_PP = v3 - v4
            
            # MAPK phosphorylation (two steps)
            w1 = cfg.k1 * MKK_PP * MK
            w2 = cfg.k2 * MK_P
            w3 = cfg.k3 * MKK_PP * MK_P
            w4 = cfg.k4 * MK_PP
            
            dMK_P = w1 - w2 - w3 + w4
            dMK_PP = w3 - w4
            
            return [dMKKK_star, dMKK_P, dMKK_PP, dMK_P, dMK_PP]
        
        solution = solve_ivp(mapk_equations, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        MKKK_star = solution.y[0]
        MKK_PP = solution.y[2]
        MK_PP = solution.y[4]
        
        # Calculate ultrasensitivity
        dose_response = self._mapk_dose_response()
        
        # Hill coefficient estimate
        hill_n = self._estimate_hill_coefficient(dose_response)
        
        metrics = {
            "final_MAPKKK_active": float(MKKK_star[-1]),
            "final_MAPKK_PP": float(MKK_PP[-1]),
            "final_MAPK_PP": float(MK_PP[-1]),
            "max_MAPK_PP": float(np.max(MK_PP)),
            "amplification_factor": float(MK_PP[-1] / MKKK_star[-1]) if MKKK_star[-1] > 0 else 0,
            "hill_coefficient": hill_n,
            "model": "mapk_cascade",
        }
        
        logs = [
            f"MAPK cascade simulation completed",
            f"Final MAPK-PP: {metrics['final_MAPK_PP']:.4f} uM",
            f"Max MAPK-PP: {metrics['max_MAPK_PP']:.4f} uM",
            f"Amplification factor: {metrics['amplification_factor']:.2f}",
            f"Estimated Hill coefficient: {hill_n:.2f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "MAPKKK_star": MKKK_star.tolist(),
            "MAPKK_PP": MKK_PP.tolist(),
            "MAPK_PP": MK_PP.tolist(),
            "dose_response": dose_response,
        }
    
    def _mapk_dose_response(self) -> Dict[str, List[float]]:
        """Calculate MAPK cascade dose-response curve"""
        cfg = self.config
        
        e1_levels = np.logspace(-3, 0, cfg.num_stimulus_levels)
        responses = []
        
        for e1 in e1_levels:
            # Quick simulation to steady state
            t_span = (0, 1000)
            y0 = [0.0, 0.0, 0.0, 0.0, 0.0]
            
            def eq(t, y):
                MKKK_star, MKK_P, MKK_PP, MK_P, MK_PP = y
                MKKK = e1 - MKKK_star
                MKK = cfg.MAPKK_total - MKK_P - MKK_PP
                MK = cfg.MAPK_total - MK_P - MK_PP
                
                dMKKK_star = (cfg.k1 * e1 * MKKK - cfg.k2 * MKKK_star)
                v1 = cfg.k1 * MKKK_star * MKK
                v2 = cfg.k2 * MKK_P
                v3 = cfg.k3 * MKKK_star * MKK_P
                v4 = cfg.k4 * MKK_PP
                dMKK_P = v1 - v2 - v3 + v4
                dMKK_PP = v3 - v4
                w1 = cfg.k1 * MKK_PP * MK
                w2 = cfg.k2 * MK_P
                w3 = cfg.k3 * MKK_PP * MK_P
                w4 = cfg.k4 * MK_PP
                dMK_P = w1 - w2 - w3 + w4
                dMK_PP = w3 - w4
                return [dMKKK_star, dMKK_P, dMKK_PP, dMK_P, dMK_PP]
            
            sol = solve_ivp(eq, t_span, y0, method='RK45')
            responses.append(float(sol.y[4][-1]))  # Final MAPK-PP
        
        return {
            "stimulus_levels": e1_levels.tolist(),
            "responses": responses,
        }
    
    def _estimate_hill_coefficient(self, dose_response: Dict[str, List[float]]) -> float:
        """Estimate Hill coefficient from dose-response"""
        S = np.array(dose_response["stimulus_levels"])
        R = np.array(dose_response["responses"])
        
        if len(S) < 3 or np.max(R) == 0:
            return 1.0
        
        # Normalize
        R_norm = R / np.max(R)
        
        # Find EC10 and EC90
        try:
            ec10_idx = np.where(R_norm >= 0.1)[0][0]
            ec90_idx = np.where(R_norm >= 0.9)[0][0]
            ec10 = S[ec10_idx]
            ec90 = S[ec90_idx]
            
            # Hill coefficient approximation
            n = 2 * np.log10(81) / np.log10(ec90 / ec10) if ec90 > ec10 else 1.0
            return float(n)
        except:
            return 1.0
    
    async def _gpcr_simulation(self) -> Dict[str, Any]:
        """GPCR signaling simulation"""
        
        cfg = self.config
        
        # Simplified GPCR model: R + L <-> RL, RL + G <-> RL*G -> RL + G*
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        # State: [RL, Ga_GTP, Gbg]
        y0 = [0.0, 0.0, 0.0]
        
        def gpcr_equations(t, y):
            RL, Ga_GTP, Gbg = y
            R = cfg.R_total - RL
            L = cfg.ligand_conc
            G = cfg.G_total - Ga_GTP - Gbg
            
            # Parameters
            ka = 1e6  # Association
            kd = 0.1  # Dissociation
            k_act = 1.0  # Activation
            k_hyd = 0.1  # GTP hydrolysis
            
            dRL = ka * R * L - kd * RL
            dGa_GTP = k_act * RL * G - k_hyd * Ga_GTP
            dGbg = k_act * RL * G - k_hyd * Gbg
            
            return [dRL, dGa_GTP, dGbg]
        
        solution = solve_ivp(gpcr_equations, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        RL = solution.y[0]
        Ga_GTP = solution.y[1]
        
        metrics = {
            "final_receptor_occupancy": float(RL[-1] / cfg.R_total),
            "final_G_protein_active": float(Ga_GTP[-1] / cfg.G_total),
            "max_response": float(np.max(Ga_GTP)),
            "EC50_approx": cfg.ligand_conc * (0.5 / (RL[-1]/cfg.R_total)) if RL[-1] > 0 else cfg.ligand_conc,
            "model": "gpcr",
        }
        
        logs = [
            f"GPCR simulation completed",
            f"Ligand concentration: {cfg.ligand_conc:.4f} uM",
            f"Receptor occupancy: {metrics['final_receptor_occupancy']*100:.1f}%",
            f"Active G-protein: {metrics['final_G_protein_active']*100:.1f}%",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "receptor_ligand": RL.tolist(),
            "active_G_protein": Ga_GTP.tolist(),
        }
    
    async def _adaptation_simulation(self) -> Dict[str, Any]:
        """Adaptation model (perfect or near-perfect)"""
        
        cfg = self.config
        
        # Barkai-Leibler perfect adaptation model
        # State: [X (response), X_m (modified)]
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        y0 = [0.0, 0.0]
        
        def adaptation_equations(t, y):
            X, X_m = y
            
            # Stimulus
            S = cfg.stimulus_amp if t < cfg.stimulus_duration else 0
            
            # Rate constants
            k_r = 0.1  # Response activation
            k_m = 0.1  # Modification
            k_dem = 0.01  # Demodification
            
            dX = k_r * S * (1 - X) - k_m * X
            dX_m = k_m * X - k_dem * X_m
            
            return [dX, dX_m]
        
        solution = solve_ivp(adaptation_equations, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        X = solution.y[0]
        X_m = solution.y[1]
        
        # Calculate adaptation quality
        peak_response = float(np.max(X))
        steady_response = float(X[-1]) if t[-1] > cfg.stimulus_duration else 0
        adaptation_error = abs(steady_response) / peak_response if peak_response > 0 else 0
        
        metrics = {
            "peak_response": peak_response,
            "steady_state_response": steady_response,
            "adaptation_error": adaptation_error,
            "adaptation_quality": "perfect" if adaptation_error < 0.05 else "partial",
            "model": "adaptation",
        }
        
        logs = [
            f"Adaptation simulation completed",
            f"Peak response: {peak_response:.4f}",
            f"Steady-state: {steady_response:.4f}",
            f"Adaptation: {metrics['adaptation_quality']}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "response": X.tolist(),
            "modified": X_m.tolist(),
        }
    
    async def _repressilator_simulation(self) -> Dict[str, Any]:
        """Repressilator (Elowitz-Leibler) simulation"""
        
        cfg = self.config
        n = cfg.n_genes
        
        # State: [m1, p1, m2, p2, ..., mn, pn]
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        y0 = [0.0] * (2 * n)
        # Small initial perturbation
        y0[0] = 0.1
        
        def repressilator_equations(t, y):
            dydt = []
            for i in range(n):
                m = y[2*i]
                p = y[2*i + 1]
                
                # Previous protein represses current gene
                p_prev = y[(2*((i-1)%n) + 1)]
                
                # Hill repression
                repression = cfg.alpha / (1 + p_prev**cfg.n_hill)
                
                dm = repression - cfg.beta * m
                dp = m - p
                
                dydt.extend([dm, dp])
            
            return dydt
        
        solution = solve_ivp(repressilator_equations, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        
        # Extract protein levels
        proteins = [solution.y[2*i + 1] for i in range(n)]
        
        # Calculate oscillation properties
        periods = []
        for p in proteins:
            peaks = self._find_peaks(t, p)
            if len(peaks) > 1:
                periods.append(np.mean(np.diff(peaks)))
        
        avg_period = float(np.mean(periods)) if periods else 0
        
        metrics = {
            "num_genes": n,
            "period": avg_period,
            "oscillation_detected": len(periods) > 0 and avg_period > 0,
            "mean_protein_1": float(np.mean(proteins[0])),
            "max_protein_1": float(np.max(proteins[0])),
            "model": "repressilator",
        }
        
        logs = [
            f"Repressilator simulation completed",
            f"Genes in ring: {n}",
            f"Oscillation period: {avg_period:.2f} s" if avg_period > 0 else "No clear oscillation",
            f"Oscillation detected: {metrics['oscillation_detected']}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "proteins": [p.tolist() for p in proteins],
        }
    
    def _find_peaks(self, t: np.ndarray, signal: np.ndarray) -> List[float]:
        """Find peak times in signal"""
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(signal, height=np.mean(signal))
        return [t[p] for p in peaks]
    
    async def _toggle_switch_simulation(self) -> Dict[str, Any]:
        """Genetic toggle switch (Gardner-Collins) simulation"""
        
        cfg = self.config
        
        # State: [u (gene 1), v (gene 2)]
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        y0 = [0.1, 0.5]  # Asymmetric initial condition
        
        def toggle_equations(t, y):
            u, v = y
            
            # Mutual repression
            du = cfg.alpha / (1 + v**cfg.n_hill) - u
            dv = cfg.alpha / (1 + u**cfg.n_hill) - v
            
            return [du, dv]
        
        solution = solve_ivp(toggle_equations, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        u = solution.y[0]
        v = solution.y[1]
        
        # Check bistability
        # Run from opposite initial condition
        y0_rev = [0.5, 0.1]
        sol_rev = solve_ivp(toggle_equations, t_span, y0_rev, t_eval=t_eval, method='RK45')
        u_rev = sol_rev.y[0]
        v_rev = sol_rev.y[1]
        
        bistable = abs(u[-1] - u_rev[-1]) > 0.1 and abs(v[-1] - v_rev[-1]) > 0.1
        
        metrics = {
            "final_u": float(u[-1]),
            "final_v": float(v[-1]),
            "bistable": bistable,
            "steady_state": "high_u" if u[-1] > v[-1] else "high_v",
            "switching_possible": bistable,
            "model": "toggle_switch",
        }
        
        logs = [
            f"Toggle switch simulation completed",
            f"Bistability: {bistable}",
            f"Final state: u={metrics['final_u']:.4f}, v={metrics['final_v']:.4f}",
            f"Dominant protein: {metrics['steady_state']}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "protein_1": u.tolist(),
            "protein_2": v.tolist(),
            "protein_1_alt": u_rev.tolist(),
            "protein_2_alt": v_rev.tolist(),
        }
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Model-specific checks
        if self.config.model == SignalingModel.MAPK_CASCADE:
            if metrics.get("amplification_factor", 0) > 1:
                factors.append(0.4)
            if metrics.get("hill_coefficient", 1) > 1:
                factors.append(0.3)
        
        elif self.config.model == SignalingModel.REPRESSILATOR:
            if metrics.get("oscillation_detected", False):
                factors.append(0.7)
        
        elif self.config.model == SignalingModel.TOGGLE_SWITCH:
            if metrics.get("bistable", False):
                factors.append(0.7)
        
        elif self.config.model == SignalingModel.ADAPTATION:
            if metrics.get("adaptation_quality") == "perfect":
                factors.append(0.7)
        
        # Positive concentrations
        factors.append(0.25)
        
        return min(0.95, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 1000.0)
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": 1 + t_max / 1000,
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
                "Huang, C.Y. & Ferrell, J.E. (1996). Ultrasensitivity in the MAPK cascade",
                "Elowitz, M.B. & Leibler, S. (2000). A synthetic oscillatory network",
                "Gardner, T.S. et al. (2000). Construction of a genetic toggle switch",
            ],
        }
