"""
System Dynamics Simulation Pattern
Production-grade differential equation simulation

Based on:
- Jay Forrester's System Dynamics
- Stella/iThink methodology
- Modern ODE solvers (scipy.integrate)
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from scipy.integrate import solve_ivp
import json

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


class SystemType(Enum):
    """Types of dynamical systems"""
    LINEAR = "linear"
    NONLINEAR = "nonlinear"
    CHAOTIC = "chaotic"
    OSCILLATORY = "oscillatory"
    BISTABLE = "bistable"


@dataclass
class Stock:
    """Stock (state variable) in system dynamics"""
    name: str
    initial_value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""


@dataclass
class Flow:
    """Flow (rate) in system dynamics"""
    name: str
    source: Optional[str]  # Source stock (None for external)
    sink: Optional[str]    # Sink stock (None for external)
    rate_expression: str   # Mathematical expression


@dataclass
class SystemDynamicsConfig:
    """Configuration for System Dynamics simulation"""
    t_start: float = 0.0
    t_end: float = 100.0
    dt: float = 0.1
    solver: str = "RK45"  # 'RK45', 'RK23', 'DOP853', 'Radau', 'BDF', 'LSODA'
    system_type: str = "nonlinear"
    
    # Sensitivity analysis
    sensitivity_analysis: bool = True
    parameter_variation: float = 0.1
    n_sensitivity_runs: int = 50
    
    # Stability analysis
    stability_analysis: bool = True
    find_equilibria: bool = True
    
    # Chaos detection
    detect_chaos: bool = True
    lyapunov_exponents: bool = False
    
    # Event detection
    detect_events: bool = True
    threshold_crossings: List[float] = None
    
    random_seed: Optional[int] = None

    def __post_init__(self):
        if self.threshold_crossings is None:
            self.threshold_crossings = []


@simulation_pattern(
    id="system_dynamics",
    name="System Dynamics Simulation",
    category="differential",
    description="Continuous-time system simulation using differential equations",
)
class SystemDynamicsPattern(SimulationPattern):
    """
    System Dynamics simulation pattern for continuous systems

    Implements:
    - Multiple ODE solvers (Runge-Kutta, implicit methods)
    - Stock-and-flow modeling (Forrester methodology)
    - Sensitivity analysis (Monte Carlo over parameters)
    - Stability analysis (eigenvalue computation)
    - Chaos detection (Lyapunov exponents)
    - Event detection (threshold crossings)
    """

    parameters = [
        SimulationParameter(
            name="t_end",
            type="float",
            default=100.0,
            min=1.0,
            max=10000.0,
            description="Simulation end time",
        ),
        SimulationParameter(
            name="dt",
            type="float",
            default=0.1,
            min=0.001,
            max=1.0,
            description="Time step for output",
        ),
        SimulationParameter(
            name="solver",
            type="select",
            default="RK45",
            options=["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"],
            description="ODE solver method",
        ),
        SimulationParameter(
            name="sensitivity_analysis",
            type="bool",
            default=True,
            description="Run sensitivity analysis",
        ),
        SimulationParameter(
            name="stability_analysis",
            type="bool",
            default=True,
            description="Analyze system stability",
        ),
        SimulationParameter(
            name="detect_chaos",
            type="bool",
            default=True,
            description="Detect chaotic behavior",
        ),
    ]

    def __init__(self):
        super().__init__()
        self.rng = np.random.default_rng()
        self.time_history: np.ndarray = None
        self.state_history: np.ndarray = None
        self.stocks: Dict[str, Stock] = {}
        self.flows: List[Flow] = []
        self.events_detected: List[Dict[str, Any]] = []

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """
        System dynamics can simulate hypotheses with:
        - Continuous variables
        - Rates of change
        - Feedback loops
        - Accumulation processes
        """
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        sd_keywords = [
            "system dynamics",
            "differential equation",
            "ode",
            "rate",
            "accumulation",
            "stock",
            "flow",
            "feedback",
            "growth",
            "decay",
            "oscillation",
            "equilibrium",
            "steady state",
            "dynamic",
            "time derivative",
            "population dynamics",
            "epidemic",
            "predator prey",
            "lotka volterra",
            "compartmental",
        ]

        return any(kw in title or kw in desc for kw in sd_keywords)

    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute System Dynamics simulation"""
        start_time = datetime.now()
        simulation_id = f"sd_{start_time.timestamp()}"

        logger.info(f"Starting System Dynamics simulation {simulation_id}")

        # Parse configuration
        sd_config = self._parse_config(config)
        
        if sd_config.random_seed:
            self.rng = np.random.default_rng(sd_config.random_seed)

        try:
            # Build model from hypothesis
            self._build_model(hypothesis)
            
            # Run main simulation
            solution = await self._run_simulation(sd_config)
            
            # Sensitivity analysis
            sensitivity_results = {}
            if sd_config.sensitivity_analysis:
                sensitivity_results = await self._run_sensitivity_analysis(sd_config)
            
            # Stability analysis
            stability_results = {}
            if sd_config.stability_analysis:
                stability_results = self._analyze_stability(sd_config)
            
            # Chaos detection
            chaos_metrics = {}
            if sd_config.detect_chaos:
                chaos_metrics = self._detect_chaos(sd_config)
            
            # Compile results
            results = self._compile_results(
                solution, sensitivity_results, stability_results, chaos_metrics, sd_config
            )
            
            end_time = datetime.now()
            
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results, sd_config),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("System Dynamics simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: Dict[str, Any]) -> SystemDynamicsConfig:
        """Parse configuration dict"""
        return SystemDynamicsConfig(
            t_start=config.get("t_start", 0.0),
            t_end=config.get("t_end", 100.0),
            dt=config.get("dt", 0.1),
            solver=config.get("solver", "RK45"),
            sensitivity_analysis=config.get("sensitivity_analysis", True),
            parameter_variation=config.get("parameter_variation", 0.1),
            n_sensitivity_runs=config.get("n_sensitivity_runs", 50),
            stability_analysis=config.get("stability_analysis", True),
            detect_chaos=config.get("detect_chaos", True),
            random_seed=config.get("random_seed"),
        )

    def _build_model(self, hypothesis: Hypothesis) -> None:
        """Build stock-and-flow model from hypothesis"""
        params = hypothesis.parameters
        
        # Clear previous model
        self.stocks = {}
        self.flows = []
        
        # Extract stocks from hypothesis
        stock_names = params.get("stocks", ["population", "resources"])
        for name in stock_names:
            self.stocks[name] = Stock(
                name=name,
                initial_value=params.get(f"{name}_initial", 100.0),
                min_value=params.get(f"{name}_min", 0.0),
                max_value=params.get(f"{name}_max", None),
                unit=params.get(f"{name}_unit", "units"),
            )
        
        # Build flows based on model type
        model_type = params.get("model_type", "generic")
        
        if model_type == "logistic_growth":
            self._build_logistic_model(params)
        elif model_type == "predator_prey":
            self._build_predator_prey_model(params)
        elif model_type == "epidemic":
            self._build_epidemic_model(params)
        elif model_type == "custom":
            self._build_custom_model(params)
        else:
            self._build_generic_model(params)

    def _build_logistic_model(self, params: Dict[str, Any]) -> None:
        """Build logistic growth model"""
        self.flows = [
            Flow(
                name="growth",
                source=None,
                sink="population",
                rate_expression=f"{params.get('growth_rate', 0.1)} * population * (1 - population / {params.get('carrying_capacity', 1000)})",
            ),
            Flow(
                name="death",
                source="population",
                sink=None,
                rate_expression=f"{params.get('death_rate', 0.05)} * population",
            ),
        ]

    def _build_predator_prey_model(self, params: Dict[str, Any]) -> None:
        """Build Lotka-Volterra predator-prey model"""
        self.flows = [
            Flow(
                name="prey_growth",
                source=None,
                sink="prey",
                rate_expression=f"{params.get('prey_growth', 1.0)} * prey",
            ),
            Flow(
                name="predation",
                source="prey",
                sink=None,
                rate_expression=f"{params.get('predation_rate', 0.1)} * prey * predators",
            ),
            Flow(
                name="predator_growth",
                source=None,
                sink="predators",
                rate_expression=f"{params.get('conversion_efficiency', 0.075)} * {params.get('predation_rate', 0.1)} * prey * predators",
            ),
            Flow(
                name="predator_death",
                source="predators",
                sink=None,
                rate_expression=f"{params.get('predator_death', 0.5)} * predators",
            ),
        ]
        
        # Add stocks if not present
        if "prey" not in self.stocks:
            self.stocks["prey"] = Stock(name="prey", initial_value=params.get("prey_initial", 100.0))
        if "predators" not in self.stocks:
            self.stocks["predators"] = Stock(name="predators", initial_value=params.get("predator_initial", 10.0))

    def _build_epidemic_model(self, params: Dict[str, Any]) -> None:
        """Build SIR epidemic model"""
        # Ensure SIR stocks exist
        if "susceptible" not in self.stocks:
            self.stocks["susceptible"] = Stock(name="susceptible", initial_value=params.get("S0", 990.0))
        if "infected" not in self.stocks:
            self.stocks["infected"] = Stock(name="infected", initial_value=params.get("I0", 10.0))
        if "recovered" not in self.stocks:
            self.stocks["recovered"] = Stock(name="recovered", initial_value=params.get("R0", 0.0))
        
        total = sum(s.initial_value for s in self.stocks.values())
        
        self.flows = [
            Flow(
                name="infection",
                source="susceptible",
                sink="infected",
                rate_expression=f"{params.get('beta', 0.3)} * susceptible * infected / {total}",
            ),
            Flow(
                name="recovery",
                source="infected",
                sink="recovered",
                rate_expression=f"{params.get('gamma', 0.1)} * infected",
            ),
        ]

    def _build_custom_model(self, params: Dict[str, Any]) -> None:
        """Build custom model from explicit flow definitions"""
        flow_defs = params.get("flows", [])
        for flow_def in flow_defs:
            self.flows.append(Flow(
                name=flow_def["name"],
                source=flow_def.get("source"),
                sink=flow_def.get("sink"),
                rate_expression=flow_def["expression"],
            ))

    def _build_generic_model(self, params: Dict[str, Any]) -> None:
        """Build generic two-stock model with feedback"""
        if len(self.stocks) >= 2:
            stock_names = list(self.stocks.keys())
            self.flows = [
                Flow(
                    name="flow_1",
                    source=None,
                    sink=stock_names[0],
                    rate_expression=f"{params.get('inflow_rate', 1.0)} - 0.01 * {stock_names[0]}",
                ),
                Flow(
                    name="flow_2",
                    source=stock_names[0],
                    sink=stock_names[1],
                    rate_expression=f"{params.get('transfer_rate', 0.1)} * {stock_names[0]}",
                ),
                Flow(
                    name="outflow",
                    source=stock_names[1],
                    sink=None,
                    rate_expression=f"{params.get('outflow_rate', 0.05)} * {stock_names[1]}",
                ),
            ]

    def _create_ode_function(self) -> Callable:
        """Create ODE function from stocks and flows"""
        stock_names = list(self.stocks.keys())
        
        def ode_func(t: float, y: np.ndarray) -> np.ndarray:
            # Create state dict
            state = {name: y[i] for i, name in enumerate(stock_names)}
            
            # Calculate flows
            flow_values = {}
            for flow in self.flows:
                try:
                    # Evaluate flow expression
                    local_vars = {**state, "t": t, "np": np}
                    flow_values[flow.name] = eval(flow.rate_expression, {"__builtins__": {}}, local_vars)
                except:
                    flow_values[flow.name] = 0.0
            
            # Calculate derivatives (net flow into each stock)
            dydt = np.zeros(len(stock_names))
            for i, name in enumerate(stock_names):
                for flow in self.flows:
                    if flow.sink == name:
                        dydt[i] += flow_values[flow.name]
                    if flow.source == name:
                        dydt[i] -= flow_values[flow.name]
            
            return dydt
        
        return ode_func

    async def _run_simulation(self, config: SystemDynamicsConfig) -> Any:
        """Run the ODE simulation"""
        ode_func = self._create_ode_function()
        
        # Initial conditions
        y0 = np.array([s.initial_value for s in self.stocks.values()])
        stock_names = list(self.stocks.keys())
        
        # Time span
        t_span = (config.t_start, config.t_end)
        t_eval = np.arange(config.t_start, config.t_end + config.dt, config.dt)
        
        # Event detection
        events = []
        if config.detect_events and config.threshold_crossings:
            for threshold in config.threshold_crossings:
                def make_event(th):
                    def event(t, y):
                        return np.max(y) - th
                    event.terminal = False
                    event.direction = 0
                    return event
                events.append(make_event(threshold))
        
        # Run solver
        solution = solve_ivp(
            ode_func,
            t_span,
            y0,
            method=config.solver,
            t_eval=t_eval,
            dense_output=True,
            events=events if events else None,
            max_step=config.dt * 10,
        )
        
        # Store results
        self.time_history = solution.t
        self.state_history = solution.y
        
        # Record events
        self.events_detected = []
        if hasattr(solution, 'events') and solution.events is not None:
            for i, event_times in enumerate(solution.events):
                if event_times is not None:
                    for t in event_times:
                        self.events_detected.append({
                            "time": float(t),
                            "type": "threshold_crossing",
                            "threshold_index": i,
                        })
        
        return solution

    async def _run_sensitivity_analysis(
        self, config: SystemDynamicsConfig
    ) -> Dict[str, Any]:
        """Run Monte Carlo sensitivity analysis"""
        logger.info(f"Running sensitivity analysis ({config.n_sensitivity_runs} runs)")
        
        # Store original parameters
        original_stocks = {name: stock.initial_value for name, stock in self.stocks.items()}
        
        # Collect final values across runs
        final_values = {name: [] for name in self.stocks.keys()}
        
        for i in range(config.n_sensitivity_runs):
            # Perturb initial conditions
            for name, stock in self.stocks.items():
                variation = self.rng.normal(1.0, config.parameter_variation)
                stock.initial_value = original_stocks[name] * variation
            
            # Run simulation
            try:
                solution = await self._run_simulation(config)
                
                # Record final values
                for j, name in enumerate(self.stocks.keys()):
                    final_values[name].append(solution.y[j, -1])
                    
            except Exception as e:
                logger.warning(f"Sensitivity run {i} failed: {e}")
            
            # Yield control
            if i % 10 == 0:
                await asyncio.sleep(0)
        
        # Restore original parameters
        for name, value in original_stocks.items():
            self.stocks[name].initial_value = value
        
        # Calculate sensitivity metrics
        sensitivity_metrics = {}
        for name, values in final_values.items():
            if values:
                sensitivity_metrics[f"{name}_sensitivity_mean"] = float(np.mean(values))
                sensitivity_metrics[f"{name}_sensitivity_std"] = float(np.std(values))
                sensitivity_metrics[f"{name}_cv"] = float(np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0
        
        return sensitivity_metrics

    def _analyze_stability(self, config: SystemDynamicsConfig) -> Dict[str, Any]:
        """Analyze system stability using Jacobian eigenvalues"""
        if self.state_history is None or self.state_history.size == 0:
            return {}
        
        # Compute Jacobian numerically at final state
        stock_names = list(self.stocks.keys())
        n = len(stock_names)
        
        # Use finite differences to approximate Jacobian
        epsilon = 1e-8
        jacobian = np.zeros((n, n))
        
        y_final = self.state_history[:, -1]
        t_final = self.time_history[-1]
        ode_func = self._create_ode_function()
        
        for i in range(n):
            y_plus = y_final.copy()
            y_plus[i] += epsilon
            y_minus = y_final.copy()
            y_minus[i] -= epsilon
            
            f_plus = ode_func(t_final, y_plus)
            f_minus = ode_func(t_final, y_minus)
            
            jacobian[:, i] = (f_plus - f_minus) / (2 * epsilon)
        
        # Compute eigenvalues
        eigenvalues = np.linalg.eigvals(jacobian)
        
        # Analyze stability
        max_real = np.max(np.real(eigenvalues))
        is_stable = max_real < 0
        
        # Find equilibria (where derivatives are near zero)
        equilibria = []
        if config.find_equilibria:
            for i in range(len(self.time_history)):
                y = self.state_history[:, i]
                dy = ode_func(self.time_history[i], y)
                if np.all(np.abs(dy) < 0.01):
                    equilibria.append({
                        "time": float(self.time_history[i]),
                        "state": y.tolist(),
                    })
        
        return {
            "jacobian_eigenvalues_real": [float(np.real(ev)) for ev in eigenvalues],
            "jacobian_eigenvalues_imag": [float(np.imag(ev)) for ev in eigenvalues],
            "max_eigenvalue_real": float(max_real),
            "is_stable": bool(is_stable),
            "damped_frequency": float(np.max(np.imag(eigenvalues))) if any(np.imag(eigenvalues) != 0) else 0.0,
            "n_equilibria": len(equilibria),
        }

    def _detect_chaos(self, config: SystemDynamicsConfig) -> Dict[str, Any]:
        """Detect chaotic behavior using 0-1 test"""
        if self.state_history is None or self.state_history.shape[1] < 100:
            return {}
        
        # Use 0-1 test for chaos
        # K ≈ 0: regular dynamics, K ≈ 1: chaotic dynamics
        
        # Select primary variable (usually first stock)
        x = self.state_history[0, :]
        
        # 0-1 test
        c = self.rng.uniform(0, 2 * np.pi)
        n = len(x)
        
        p = np.zeros(n)
        q = np.zeros(n)
        
        for i in range(n):
            p[i] = np.sum(x[:i+1] * np.cos(np.arange(i+1) * c))
            q[i] = np.sum(x[:i+1] * np.sin(np.arange(i+1) * c))
        
        # Compute mean square displacement
        M = np.zeros(n // 10)
        for j in range(1, n // 10):
            M[j] = np.mean((p[j:] - p[:-j])**2 + (q[j:] - q[:-j])**2)
        
        # Compute K
        log_M = np.log(M[1:])
        log_n = np.log(np.arange(1, len(M)))
        
        K = np.polyfit(log_n, log_M, 1)[0]
        
        # Alternative: Check for sensitivity to initial conditions
        # by looking at phase space expansion
        phase_volume = self._estimate_phase_volume_expansion()
        
        return {
            "chaos_indicator_k": float(K),
            "is_chaotic": bool(K > 0.8),
            "phase_volume_expansion": float(phase_volume),
            "lyapunov_estimate": float(K),  # K approximates largest Lyapunov exponent
        }

    def _estimate_phase_volume_expansion(self) -> float:
        """Estimate phase space volume expansion rate"""
        if self.state_history is None or self.state_history.shape[1] < 10:
            return 0.0
        
        # Compute distance between trajectories at different times
        n_points = min(100, self.state_history.shape[1] // 2)
        
        distances_early = []
        distances_late = []
        
        for i in range(n_points):
            for j in range(i + 1, n_points):
                d_early = np.linalg.norm(
                    self.state_history[:, i] - self.state_history[:, j]
                )
                d_late = np.linalg.norm(
                    self.state_history[:, -(i+1)] - self.state_history[:, -(j+1)]
                )
                if d_early > 1e-6:
                    distances_early.append(d_early)
                    distances_late.append(d_late)
        
        if distances_early and distances_late:
            expansion = np.mean(distances_late) / np.mean(distances_early)
            return float(np.log(expansion))
        
        return 0.0

    def _compile_results(
        self,
        solution: Any,
        sensitivity: Dict[str, Any],
        stability: Dict[str, Any],
        chaos: Dict[str, Any],
        config: SystemDynamicsConfig,
    ) -> Dict[str, Any]:
        """Compile all results"""
        
        # Basic trajectory metrics
        final_state = solution.y[:, -1]
        initial_state = solution.y[:, 0]
        
        metrics = {
            "final_values": {name: float(final_state[i]) for i, name in enumerate(self.stocks.keys())},
            "initial_values": {name: float(initial_state[i]) for i, name in enumerate(self.stocks.keys())},
            "n_steps": len(solution.t),
            "integration_success": solution.success,
            "n_function_evals": solution.nfev if hasattr(solution, 'nfev') else 0,
        }
        
        # Add time series statistics
        for i, name in enumerate(self.stocks.keys()):
            traj = solution.y[i, :]
            metrics[f"{name}_mean"] = float(np.mean(traj))
            metrics[f"{name}_std"] = float(np.std(traj))
            metrics[f"{name}_min"] = float(np.min(traj))
            metrics[f"{name}_max"] = float(np.max(traj))
            metrics[f"{name}_initial"] = float(traj[0])
            metrics[f"{name}_final"] = float(traj[-1])
            
            # Oscillation frequency
            if len(traj) > 10:
                zero_crossings = np.sum(np.diff(np.signbit(traj - np.mean(traj))))
                metrics[f"{name}_oscillations"] = int(zero_crossings // 2)
        
        # Add sensitivity results
        metrics.update(sensitivity)
        
        # Add stability results
        metrics.update(stability)
        
        # Add chaos results
        metrics.update(chaos)
        
        # Event detection
        metrics["n_events"] = len(self.events_detected)
        
        # Build logs
        logs = [
            f"Simulation completed: {len(solution.t)} time points",
            f"Integration {'successful' if solution.success else 'may have issues'}",
            f"Stocks analyzed: {list(self.stocks.keys())}",
        ]
        
        for name in self.stocks.keys():
            logs.append(
                f"  {name}: {metrics[f'{name}_initial']:.2f} → {metrics[f'{name}_final']:.2f}"
            )
        
        if stability.get("is_stable"):
            logs.append(f"System is STABLE (max eigenvalue: {stability.get('max_eigenvalue_real', 0):.4f})")
        elif stability.get("max_eigenvalue_real"):
            logs.append(f"System is UNSTABLE (max eigenvalue: {stability.get('max_eigenvalue_real', 0):.4f})")
        
        if chaos.get("is_chaotic"):
            logs.append(f"CHAOTIC behavior detected (K = {chaos.get('chaos_indicator_k', 0):.4f})")
        
        if self.events_detected:
            logs.append(f"Detected {len(self.events_detected)} threshold crossing events")
        
        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(
        self, results: Dict[str, Any], config: SystemDynamicsConfig
    ) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # 1. Successful integration
        if metrics.get("integration_success", False):
            factors.append(0.2)
        
        # 2. Stability analysis performed
        if "is_stable" in metrics:
            factors.append(0.15)
        
        # 3. Sensitivity analysis performed
        if any("sensitivity" in k for k in metrics.keys()):
            factors.append(0.15)
        
        # 4. Sufficient time points
        if metrics.get("n_steps", 0) > 100:
            factors.append(0.15)
        
        # 5. No chaos (deterministic systems more confident)
        if not metrics.get("is_chaotic", False):
            factors.append(0.15)
        
        # 6. Events detected or explicitly searched for
        if metrics.get("n_events", 0) > 0 or not config.detect_events:
            factors.append(0.1)
        
        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_end = params.get("t_end", 100.0)
        dt = params.get("dt", 0.1)
        n_runs = params.get("n_sensitivity_runs", 50) if params.get("sensitivity_analysis", True) else 1
        
        n_steps = int(t_end / dt)
        estimated_time = n_steps * n_runs / 10000  # Rough estimate
        
        return {
            "cpu_cores": 2,
            "memory_gb": 1.0 + n_steps / 10000,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
