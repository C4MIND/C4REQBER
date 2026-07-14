"""
Circuit Simulation Pattern[str]
Main pattern class for SPICE-based circuit simulation.
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
from .config import AnalysisType, CircuitConfig, ComponentType
from .core import CircuitBuilder, CircuitSimulator


logger = logging.getLogger(__name__)

@simulation_pattern(
    id="circuit_simulation",
    name="Circuit Simulation",
    category="physical",
    description="SPICE-based electrical circuit simulation",
)
class CircuitSimulationPattern(SimulationPattern):
    """
    Circuit simulation pattern using SPICE

    Implements:
    - DC, AC, Transient, and Noise analyses
    - Component-level Monte Carlo
    - Corner case analysis
    - Sensitivity analysis
    - Multi-objective optimization
    """

    parameters = [
        SimulationParameter(
            name="analysis_type",
            type="select",
            default="transient",
            options=["dc", "ac", "transient", "operating_point", "noise"],
            description="Type of circuit analysis",
        ),
        SimulationParameter(
            name="t_stop",
            type="float",
            default=1e-3,
            min=1e-9,
            max=1.0,
            description="Transient stop time (seconds)",
        ),
        SimulationParameter(
            name="t_step",
            type="float",
            default=1e-6,
            min=1e-12,
            max=1e-3,
            description="Transient time step (seconds)",
        ),
        SimulationParameter(
            name="f_start",
            type="float",
            default=1.0,
            min=0.01,
            max=1e12,
            description="AC analysis start frequency (Hz)",
        ),
        SimulationParameter(
            name="f_stop",
            type="float",
            default=1e6,
            min=0.01,
            max=1e12,
            description="AC analysis stop frequency (Hz)",
        ),
        SimulationParameter(
            name="monte_carlo_runs",
            type="int",
            default=0,
            min=0,
            max=1000,
            description="Number of Monte Carlo runs (0 to disable)",
        ),
        SimulationParameter(
            name="tolerance",
            type="float",
            default=0.05,
            min=0.0,
            max=0.5,
            description="Component tolerance for Monte Carlo",
        ),
        SimulationParameter(
            name="temperature",
            type="float",
            default=27.0,
            min=-40.0,
            max=150.0,
            description="Operating temperature (Celsius)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.components = []  # type: ignore[var-annotated]
        self.results: dict[str, np.ndarray] = {}
        self.builder = CircuitBuilder()
        self.simulator = CircuitSimulator(self.rng)

    @classmethod
    def can_simulate(cls, hypothesis: Hypothesis) -> bool:
        """
        Circuit simulation can simulate hypotheses with:
        - Electrical/electronic circuits
        - Signal processing
        - Power systems
        - Sensor systems
        """
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        circuit_keywords = [
            "circuit", "electrical", "electronic", "voltage", "current",
            "resistor", "capacitor", "inductor", "transistor", "amplifier",
            "filter", "oscillator", "power supply", "sensor", "adc",
            "dac", "op-amp", "spice", "impedance", "frequency response",
            "gain", "bandwidth", "noise",
        ]

        return any(kw in title or kw in desc for kw in circuit_keywords)

    async def run(
        self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None
    ) -> SimulationResult:
        """Execute circuit simulation"""
        start_time = datetime.now()
        simulation_id = f"ckt_{start_time.timestamp()}"

        logger.info(f"Starting Circuit simulation {simulation_id}")

        circuit_config = self._parse_config(config)  # type: ignore[arg-type]

        if circuit_config.random_seed:
            self.rng = np.random.default_rng(circuit_config.random_seed)

        try:
            has_pyspice = self._check_pyspice()

            # Build circuit
            self.components = self.builder.build_from_params(hypothesis.parameters)  # type: ignore[union-attr]
            self.simulator = CircuitSimulator(self.rng)
            self.simulator.components = self.components

            # Run simulation
            if has_pyspice:
                results = await self.simulator.run_pyspice(circuit_config)
            else:
                results = await self.simulator.run_fallback(circuit_config)

            # Monte Carlo if requested
            if circuit_config.monte_carlo_runs > 0:
                mc_results = await self.simulator.run_monte_carlo(circuit_config)
                results["metrics"].update(mc_results)

            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results, circuit_config),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Circuit simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _check_pyspice(self) -> bool:
        """Check if PySpice is available"""
        try:
            import PySpice
            return True
        except ImportError:
            logger.warning("PySpice not available, using fallback implementation")
            return False

    def _parse_config(self, config: dict[str, Any]) -> CircuitConfig:
        """Parse configuration dict[str, Any]"""
        analysis_type = AnalysisType(config.get("analysis_type", "transient"))

        return CircuitConfig(
            analysis_type=analysis_type,
            t_start=config.get("t_start", 0.0),
            t_stop=config.get("t_stop", 1e-3),
            t_step=config.get("t_step", 1e-6),
            f_start=config.get("f_start", 1.0),
            f_stop=config.get("f_stop", 1e6),
            n_points=config.get("n_points", 100),
            v_start=config.get("v_start", 0.0),
            v_stop=config.get("v_stop", 5.0),
            v_step=config.get("v_step", 0.1),
            source_name=config.get("source_name", "V1"),
            monte_carlo_runs=config.get("monte_carlo_runs", 0),
            tolerance=config.get("tolerance", 0.05),
            temperature=config.get("temperature", 27.0),
            random_seed=config.get("random_seed"),
        )

    def _calculate_confidence(
        self, results: dict[str, Any], config: CircuitConfig
    ) -> float:
        """Calculate confidence score"""
        factors = []

        # 1. Has PySpice (more accurate)
        try:
            import PySpice
            factors.append(0.2)
        except ImportError:
            pass

        # 2. Monte Carlo performed
        if config.monte_carlo_runs > 10:
            factors.append(0.2)

        # 3. Valid circuit topology
        if len(self.components) >= 2:
            factors.append(0.2)

        # 4. Has calculated metrics
        if results["metrics"]:
            factors.append(0.2)

        # 5. Reasonable component values
        all_positive = all(c.value > 0 for c in self.components if c.component_type != ComponentType.VOLTAGE_SOURCE)
        if all_positive:
            factors.append(0.1)

        # 6. Temperature specified
        if config.temperature != 27.0:
            factors.append(0.1)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis | None = None) -> dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters  # type: ignore[union-attr]
        n_components = len(params.get("components", []))
        mc_runs = params.get("monte_carlo_runs", 0)

        base_time = n_components * 0.1
        mc_time = mc_runs * 0.5 if mc_runs > 0 else 0

        return {
            "cpu_cores": 2,
            "memory_gb": 1.0 + n_components / 100,
            "gpu_required": False,
            "estimated_time_seconds": base_time + mc_time,
        }
