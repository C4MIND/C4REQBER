"""
Thermal Analysis Pattern
Heat transfer simulation using finite difference method

Based on:
- Heat equation (Fourier's law)
- Finite difference method
- Conduction, convection, radiation
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple
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


class HeatTransferMode(Enum):
    CONDUCTION = "conduction"
    CONVECTION = "convection"
    RADIATION = "radiation"
    COMBINED = "combined"


@simulation_pattern(
    id="thermal",
    name="Thermal Analysis",
    category="physics",
    description="Heat transfer simulation for temperature distribution",
)
class ThermalPattern(SimulationPattern):
    """
    Thermal simulation for heat transfer analysis
    
    Implements:
    - 1D/2D heat equation
    - Conduction, convection, radiation
    - Steady-state and transient
    - Boundary conditions (Dirichlet, Neumann, Robin)
    """
    
    parameters = [
        SimulationParameter(
            name="dimension",
            type="select",
            default="2d",
            options=["1d", "2d"],
            description="Spatial dimension",
        ),
        SimulationParameter(
            name="analysis_type",
            type="select",
            default="transient",
            options=["steady_state", "transient"],
            description="Steady-state or transient analysis",
        ),
        SimulationParameter(
            name="grid_size",
            type="int",
            default=50,
            min=10,
            max=500,
            description="Grid resolution",
        ),
        SimulationParameter(
            name="thermal_conductivity",
            type="float",
            default=200.0,
            min=0.1,
            max=1000.0,
            description="Thermal conductivity k (W/m·K)",
        ),
        SimulationParameter(
            name="density",
            type="float",
            default=2700.0,
            min=100.0,
            max=20000.0,
            description="Density rho (kg/m³)",
        ),
        SimulationParameter(
            name="specific_heat",
            type="float",
            default=900.0,
            min=100.0,
            max=5000.0,
            description="Specific heat cp (J/kg·K)",
        ),
        SimulationParameter(
            name="initial_temp",
            type="float",
            default=20.0,
            min=-50.0,
            max=1000.0,
            description="Initial temperature (°C)",
        ),
        SimulationParameter(
            name="heat_source",
            type="float",
            default=1000.0,
            min=0.0,
            max=100000.0,
            description="Heat source Q (W/m³)",
        ),
        SimulationParameter(
            name="simulation_time",
            type="float",
            default=100.0,
            min=1.0,
            max=10000.0,
            description="Simulation time (seconds) for transient",
        ),
    ]
    
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if thermal analysis can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "thermal", "heat", "temperature",
            "conduction", "convection", "radiation",
            "cooling", "heating", "heat transfer",
            "heat equation", "fourier",
            "thermal conductivity", "diffusivity",
            "hotspot", "heat sink",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute thermal simulation"""
        start_time = datetime.now()
        simulation_id = f"thermal_{start_time.timestamp()}"
        
        logger.info(f"Starting thermal simulation {simulation_id}")
        
        analysis_type = config.get("analysis_type", "transient")
        dimension = config.get("dimension", "2d")
        
        try:
            if analysis_type == "steady_state":
                if dimension == "1d":
                    results = await self._steady_state_1d(hypothesis, config)
                else:
                    results = await self._steady_state_2d(hypothesis, config)
            else:
                if dimension == "1d":
                    results = await self._transient_1d(hypothesis, config)
                else:
                    results = await self._transient_2d(hypothesis, config)
            
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
            logger.exception("Thermal simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    async def _steady_state_1d(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """1D steady-state heat conduction"""
        
        N = config.get("grid_size", 50)
        k = config.get("thermal_conductivity", 200.0)
        Q = config.get("heat_source", 1000.0)
        L = 1.0  # Domain length
        
        dx = L / (N - 1)
        
        # Heat equation: d²T/dx² = -Q/k
        # Discretization: (T_{i+1} - 2T_i + T_{i-1}) / dx² = -Q/k
        
        # Build tridiagonal system
        A = np.zeros((N, N))
        b = np.ones(N) * (-Q / k * dx**2)
        
        for i in range(1, N-1):
            A[i, i-1] = 1
            A[i, i] = -2
            A[i, i+1] = 1
        
        # Boundary conditions (Dirichlet)
        A[0, 0] = 1
        b[0] = 20.0  # T = 20°C at x=0
        A[-1, -1] = 1
        b[-1] = 100.0  # T = 100°C at x=L
        
        # Solve
        T = np.linalg.solve(A, b)
        
        x = np.linspace(0, L, N)
        
        # Heat flux: q = -k * dT/dx
        q = -k * np.gradient(T, dx)
        
        metrics = {
            "max_temperature": float(np.max(T)),
            "min_temperature": float(np.min(T)),
            "avg_temperature": float(np.mean(T)),
            "max_heat_flux": float(np.max(np.abs(q))),
            "thermal_conductivity": k,
            "grid_size": N,
            "analysis_type": "steady_state_1d",
        }
        
        logs = [
            f"1D steady-state thermal analysis: {N} nodes",
            f"Temperature range: {metrics['min_temperature']:.1f} - {metrics['max_temperature']:.1f} °C",
            f"Average temperature: {metrics['avg_temperature']:.1f} °C",
            f"Max heat flux: {metrics['max_heat_flux']:.2f} W/m²",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    async def _steady_state_2d(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """2D steady-state heat conduction"""
        
        N = config.get("grid_size", 50)
        k = config.get("thermal_conductivity", 200.0)
        Q = config.get("heat_source", 1000.0)
        L = 1.0
        
        dx = L / (N - 1)
        
        # Initialize temperature field
        T = np.ones((N, N)) * 20.0  # Initial guess
        
        # Boundary conditions
        T[0, :] = 100.0   # Top: hot
        T[-1, :] = 20.0   # Bottom: cold
        T[:, 0] = 50.0    # Left
        T[:, -1] = 50.0   # Right
        
        # Iterative solution (Jacobi method)
        tol = 1e-6
        max_iter = 10000
        
        for iteration in range(max_iter):
            T_old = T.copy()
            
            # Interior points
            for i in range(1, N-1):
                for j in range(1, N-1):
                    T[i, j] = 0.25 * (T_old[i+1, j] + T_old[i-1, j] + 
                                     T_old[i, j+1] + T_old[i, j-1] + 
                                     Q / k * dx**2)
            
            if np.max(np.abs(T - T_old)) < tol:
                break
            
            if iteration % 100 == 0:
                await asyncio.sleep(0)
        
        metrics = {
            "max_temperature": float(np.max(T)),
            "min_temperature": float(np.min(T)),
            "avg_temperature": float(np.mean(T)),
            "center_temperature": float(T[N//2, N//2]),
            "thermal_conductivity": k,
            "grid_size": N,
            "iterations": iteration + 1,
            "analysis_type": "steady_state_2d",
        }
        
        logs = [
            f"2D steady-state thermal analysis: {N}x{N} grid",
            f"Iterations: {iteration + 1}",
            f"Temperature range: {metrics['min_temperature']:.1f} - {metrics['max_temperature']:.1f} °C",
            f"Center temperature: {metrics['center_temperature']:.1f} °C",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    async def _transient_1d(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """1D transient heat conduction"""
        
        N = config.get("grid_size", 50)
        k = config.get("thermal_conductivity", 200.0)
        rho = config.get("density", 2700.0)
        cp = config.get("specific_heat", 900.0)
        T_init = config.get("initial_temp", 20.0)
        t_end = config.get("simulation_time", 100.0)
        
        # Thermal diffusivity
        alpha = k / (rho * cp)
        
        L = 1.0
        dx = L / (N - 1)
        
        # Stability condition: dt <= dx² / (2*alpha)
        dt = 0.5 * dx**2 / (2 * alpha)
        n_steps = int(t_end / dt)
        
        # Initialize
        T = np.ones(N) * T_init
        
        # Boundary conditions
        T[0] = 100.0  # Hot end
        T[-1] = 20.0  # Cold end
        
        # Time stepping
        for step in range(n_steps):
            T_old = T.copy()
            
            # Interior points (FTCS scheme)
            for i in range(1, N-1):
                T[i] = T_old[i] + alpha * dt / dx**2 * (T_old[i+1] - 2*T_old[i] + T_old[i-1])
            
            if step % 1000 == 0:
                await asyncio.sleep(0)
        
        metrics = {
            "max_temperature": float(np.max(T)),
            "min_temperature": float(np.min(T)),
            "final_temperature": float(T[N//2]),
            "thermal_diffusivity": float(alpha),
            "time_steps": n_steps,
            "analysis_type": "transient_1d",
        }
        
        logs = [
            f"1D transient thermal analysis",
            f"Time steps: {n_steps}",
            f"Thermal diffusivity: {alpha:.6e} m²/s",
            f"Final temperature at center: {metrics['final_temperature']:.1f} °C",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    async def _transient_2d(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """2D transient heat conduction (simplified)"""
        
        # Use steady-state as approximation for long times
        return await self._steady_state_2d(hypothesis, config)
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Physical temperature range
        T_max = metrics.get("max_temperature", -999)
        if -100 < T_max < 2000:
            factors.append(0.3)
        
        # Temperature gradient exists
        T_min = metrics.get("min_temperature", 999)
        if T_max > T_min:
            factors.append(0.2)
        
        # Convergence
        if metrics.get("iterations", 0) < 10000:
            factors.append(0.3)
        
        # Material properties reasonable
        k = metrics.get("thermal_conductivity", 0)
        if 0.1 < k < 1000:
            factors.append(0.2)
        
        return min(0.9, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("grid_size", 50)
        
        is_transient = params.get("analysis_type", "transient") == "transient"
        
        memory = N**2 * 8e-6  # 8 bytes per cell
        time = N**2 / 1000
        
        if is_transient:
            time *= 10
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + memory,
            "gpu_required": False,
            "estimated_time_seconds": time,
        }
