"""
Core System Dynamics simulation pattern implementation
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import numpy as np

from ...core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)
from . import analysis, models, solver
from . import results as results_module
from .types import Flow, Stock, SystemDynamicsConfig


logger = logging.getLogger(__name__)

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

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.time_history: np.ndarray | None = None
        self.state_history: np.ndarray | None = None
        self.stocks: dict[str, Stock] = {}
        self.flows: list[Flow] = []
        self.events_detected: list[dict[str, Any]] = []

    @classmethod
    def can_simulate(cls, hypothesis: Hypothesis) -> bool:
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
        self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None
    ) -> SimulationResult:
        """Execute System Dynamics simulation"""
        start_time = datetime.now()
        simulation_id = f"sd_{start_time.timestamp()}"

        logger.info(f"Starting System Dynamics simulation {simulation_id}")

        # Parse configuration
        sd_config = self._parse_config(config)  # type: ignore[arg-type]

        if sd_config.random_seed:
            self.rng = np.random.default_rng(sd_config.random_seed)

        try:
            # Build model from hypothesis
            self._build_model(hypothesis)  # type: ignore[arg-type]

            # Run main simulation
            solution, stock_names = await solver.run_simulation(
                sd_config, self.stocks, self.flows, self.events_detected
            )
            self.time_history = solution.t
            self.state_history = solution.y

            # Sensitivity analysis
            sensitivity_results = {}
            if sd_config.sensitivity_analysis:
                sensitivity_results = await analysis.run_sensitivity_analysis(
                    sd_config, self.stocks, self.flows, self.events_detected, self.rng
                )

            # Stability analysis
            stability_results = {}
            if sd_config.stability_analysis:
                stability_results = analysis.analyze_stability(
                    sd_config, self.stocks, self.flows, self.time_history, self.state_history
                )

            # Chaos detection
            chaos_metrics = {}
            if sd_config.detect_chaos:
                chaos_metrics = analysis.detect_chaos(sd_config, self.state_history, self.rng)

            # Compile results
            compiled_results = results_module.compile_results(
                solution, stock_names, sensitivity_results, stability_results,
                chaos_metrics, self.events_detected, sd_config
            )

            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=compiled_results["metrics"],
                logs=compiled_results["logs"],
                confidence_score=results_module.calculate_confidence(compiled_results, sd_config),
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

    def _parse_config(self, config: dict[str, Any]) -> SystemDynamicsConfig:
        """Parse configuration dict[str, Any]"""
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
            self.flows = models.build_logistic_model(self.stocks, params)
        elif model_type == "predator_prey":
            self.flows = models.build_predator_prey_model(self.stocks, params)
        elif model_type == "epidemic":
            self.flows = models.build_epidemic_model(self.stocks, params)
        elif model_type == "custom":
            self.flows = models.build_custom_model(self.stocks, params)
        else:
            self.flows = models.build_generic_model(self.stocks, params)

    def estimate_resources(self, hypothesis: Hypothesis | None = None) -> dict[str, Any]:
        """Estimate resources."""
        if hypothesis is None:
            return {}
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

    def _create_ode_function(self) -> Any:
        from .models import create_ode_function
        return create_ode_function(self.stocks, self.flows)

    async def _run_simulation(self, config: SystemDynamicsConfig) -> Any:
        solution, stock_names = await solver.run_simulation(
            config, self.stocks, self.flows, self.events_detected
        )
        self.time_history = solution.t
        self.state_history = solution.y
        return solution

    async def _run_sensitivity_analysis(self, config: SystemDynamicsConfig) -> dict[str, Any]:
        return await analysis.run_sensitivity_analysis(
            config, self.stocks, self.flows, self.events_detected, self.rng
        )

    def _analyze_stability(self, config: SystemDynamicsConfig) -> dict[str, Any]:
        return analysis.analyze_stability(
            config, self.stocks, self.flows, self.time_history, self.state_history
        )

    def _detect_chaos(self, config: SystemDynamicsConfig) -> dict[str, Any]:
        return analysis.detect_chaos(config, self.state_history, self.rng)

    def _estimate_phase_volume_expansion(self) -> float:
        if self.state_history is None or self.state_history.shape[1] < 10:
            return 0.0
        return analysis._estimate_phase_volume_expansion(self.state_history)

    def _compile_results(self, solution: Any, sensitivity: dict[str, Any],
                         stability: dict[str, Any], chaos: dict[str, Any],
                         config: SystemDynamicsConfig) -> dict[str, Any]:
        stock_names = list(self.stocks.keys())
        return results_module.compile_results(
            solution, stock_names, sensitivity, stability,
            chaos, self.events_detected, config
        )

    def _calculate_confidence(self, results: dict[str, Any], config: SystemDynamicsConfig) -> float:
        return results_module.calculate_confidence(results, config)
