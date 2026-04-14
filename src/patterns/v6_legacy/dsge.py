"""
DSGE Model Pattern
Dynamic Stochastic General Equilibrium for macroeconomics

Based on:
- Real Business Cycle (RBC) model
- New Keynesian framework
- Linearized equilibrium conditions
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from scipy.linalg import solve

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


@simulation_pattern(
    id="dsge",
    name="DSGE Model",
    category="economics",
    description="Dynamic Stochastic General Equilibrium for macroeconomic policy analysis",
)
class DSGEPattern(SimulationPattern):
    """
    DSGE simulation for macroeconomic analysis
    
    Implements:
    - Real Business Cycle (RBC) model
    - Productivity shocks
    - Consumption-leisure tradeoff
    - Capital accumulation
    - Linearized solution
    """
    
    parameters = [
        SimulationParameter(
            name="model_type",
            type="select",
            default="rbc",
            options=["rbc", "nk"],
            description="DSGE model type",
        ),
        SimulationParameter(
            name="periods",
            type="int",
            default=200,
            min=50,
            max=1000,
            description="Number of simulation periods",
        ),
        SimulationParameter(
            name="shock_std",
            type="float",
            default=0.01,
            min=0.001,
            max=0.1,
            description="Standard deviation of productivity shock",
        ),
        SimulationParameter(
            name="discount_factor",
            type="float",
            default=0.99,
            min=0.9,
            max=0.999,
            description="Household discount factor (beta)",
        ),
        SimulationParameter(
            name="risk_aversion",
            type="float",
            default=2.0,
            min=0.5,
            max=10.0,
            description="Coefficient of relative risk aversion",
        ),
        SimulationParameter(
            name="depreciation",
            type="float",
            default=0.025,
            min=0.01,
            max=0.1,
            description="Capital depreciation rate",
        ),
        SimulationParameter(
            name="capital_share",
            type="float",
            default=0.36,
            min=0.2,
            max=0.5,
            description="Capital share in production (alpha)",
        ),
    ]
    
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if DSGE can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "dsge", "dynamic stochastic", "general equilibrium",
            "macroeconomic", "business cycle", "rbc",
            "productivity shock", "technology shock",
            "consumption", "investment", "output gap",
            "monetary policy", "fiscal policy",
            "new keynesian", "real business cycle",
            "impulse response", "economic fluctuation",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute DSGE simulation"""
        start_time = datetime.now()
        simulation_id = f"dsge_{start_time.timestamp()}"
        
        logger.info(f"Starting DSGE simulation {simulation_id}")
        
        model_type = config.get("model_type", "rbc")
        
        try:
            if model_type == "rbc":
                results = await self._rbc_model(hypothesis, config)
            else:
                results = await self._new_keynesian(hypothesis, config)
            
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
            logger.exception("DSGE simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    async def _rbc_model(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """Real Business Cycle model simulation"""
        
        params = hypothesis.parameters
        T = config.get("periods", 200)
        beta = config.get("discount_factor", 0.99)
        gamma = config.get("risk_aversion", 2.0)
        delta = config.get("depreciation", 0.025)
        alpha = config.get("capital_share", 0.36)
        sigma_z = config.get("shock_std", 0.01)
        
        # Steady state (approximate)
        K_ss = ((1/beta - 1 + delta) / alpha) ** (1/(alpha-1))
        Y_ss = K_ss ** alpha
        C_ss = Y_ss - delta * K_ss
        
        # Log-linearized system matrices (simplified)
        # State: [k_t, z_t] where k=log(K/K_ss), z=productivity
        # Control: [c_t, y_t, i_t]
        
        # Productivity process: z_t = rho*z_{t-1} + eps_t
        rho = 0.95
        
        # Simulate
        np.random.seed(42)
        z = np.zeros(T)  # Productivity
        k = np.zeros(T)  # Capital (log deviation)
        c = np.zeros(T)  # Consumption
        y = np.zeros(T)  # Output
        i = np.zeros(T)  # Investment
        
        # Simplified linear policy functions
        # k_{t+1} = eta_kk * k_t + eta_kz * z_t
        eta_kk = 0.95
        eta_kz = 0.1
        
        # c_t = eta_ck * k_t + eta_cz * z_t
        eta_ck = 0.3
        eta_cz = 0.5
        
        for t in range(T-1):
            # Productivity shock
            if t == 0:
                z[t] = sigma_z * np.random.randn()
            else:
                z[t] = rho * z[t-1] + sigma_z * np.random.randn()
            
            # Controls
            c[t] = eta_ck * k[t] + eta_cz * z[t]
            y[t] = alpha * k[t] + z[t]  # Production function
            i[t] = y[t] - c[t]
            
            # Next period capital
            k[t+1] = eta_kk * k[t] + eta_kz * z[t]
            
            if t % 50 == 0:
                await asyncio.sleep(0)
        
        # Calculate statistics
        y_levels = Y_ss * np.exp(y)
        c_levels = C_ss * np.exp(c)
        
        # Volatility
        y_vol = float(np.std(y)) * 100  # As percentage
        c_vol = float(np.std(c)) * 100
        i_vol = float(np.std(i)) * 100
        
        # Correlations
        cy_corr = float(np.corrcoef(c, y)[0,1]) if len(c) > 1 else 0
        iy_corr = float(np.corrcoef(i, y)[0,1]) if len(i) > 1 else 0
        
        # Impulse response (max deviation after shock)
        irf_y = float(np.max(np.abs(y[:20]))) * 100
        
        metrics = {
            "output_volatility_pct": y_vol,
            "consumption_volatility_pct": c_vol,
            "investment_volatility_pct": i_vol,
            "consumption_output_correlation": cy_corr,
            "investment_output_correlation": iy_corr,
            "impulse_response_max": irf_y,
            "steady_state_output": float(Y_ss),
            "steady_state_consumption": float(C_ss),
            "capital_share": alpha,
            "discount_factor": beta,
            "model_type": "rbc",
        }
        
        logs = [
            f"RBC model simulation: {T} periods",
            f"Output volatility: {y_vol:.2f}%",
            f"Consumption volatility: {c_vol:.2f}%",
            f"C-Y correlation: {cy_corr:.3f}",
            f"Steady state output: {Y_ss:.2f}",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    async def _new_keynesian(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simplified New Keynesian model"""
        
        T = config.get("periods", 200)
        
        # Three equation model (simplified)
        # 1. IS curve: y_t = E[y_{t+1}] - sigma*(i_t - E[pi_{t+1}]) + eps
        # 2. Phillips curve: pi_t = beta*E[pi_{t+1}] + kappa*y_t + u
        # 3. Taylor rule: i_t = phi_pi*pi_t + phi_y*y_t + v
        
        # Parameters
        sigma = 1.0  # Intertemporal elasticity
        kappa = 0.1  # Phillips curve slope
        phi_pi = 1.5  # Taylor rule inflation coefficient
        phi_y = 0.5   # Taylor rule output coefficient
        
        # Simulate
        y = np.zeros(T)  # Output gap
        pi = np.zeros(T)  # Inflation
        i = np.zeros(T)   # Interest rate
        
        np.random.seed(42)
        
        for t in range(T-1):
            # Shocks
            eps_y = 0.01 * np.random.randn()  # Demand shock
            eps_pi = 0.005 * np.random.randn()  # Supply shock
            
            # Taylor rule
            i[t] = phi_pi * pi[t] + phi_y * y[t]
            
            # Phillips curve (simplified)
            pi[t+1] = pi[t] + kappa * y[t] + eps_pi
            
            # IS curve (simplified)
            y[t+1] = y[t] - sigma * (i[t] - pi[t+1]) + eps_y
            
            if t % 50 == 0:
                await asyncio.sleep(0)
        
        metrics = {
            "output_volatility_pct": float(np.std(y)) * 100,
            "inflation_volatility_pct": float(np.std(pi)) * 100,
            "interest_rate_volatility_pct": float(np.std(i)) * 100,
            "avg_output_gap": float(np.mean(y)) * 100,
            "avg_inflation": float(np.mean(pi)) * 100,
            "model_type": "new_keynesian",
        }
        
        logs = [
            "New Keynesian model simulation",
            f"Output gap volatility: {metrics['output_volatility_pct']:.2f}%",
            f"Inflation volatility: {metrics['inflation_volatility_pct']:.2f}%",
            f"Average inflation: {metrics['avg_inflation']:.2f}%",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Reasonable volatility
        y_vol = metrics.get("output_volatility_pct", 0)
        if 0.5 < y_vol < 10:
            factors.append(0.3)
        
        # Consumption smoother than output
        c_vol = metrics.get("consumption_volatility_pct", 0)
        if c_vol < y_vol:
            factors.append(0.2)
        
        # Positive correlations
        cy_corr = metrics.get("consumption_output_correlation", 0)
        if cy_corr > 0:
            factors.append(0.2)
        
        # Model structure
        if "steady_state_output" in metrics:
            factors.append(0.2)
        
        return min(0.9, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        T = params.get("periods", 200)
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": T / 1000,
        }
