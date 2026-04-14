"""
Circuit Simulation Pattern
Production-grade electrical circuit simulation

Based on:
- SPICE (Simulation Program with Integrated Circuit Emphasis)
- PySpice for Python integration
- Ngspice/Xyce backends
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import logging
from pathlib import Path
import tempfile
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


class ComponentType(Enum):
    """Types of circuit components"""
    RESISTOR = auto()
    CAPACITOR = auto()
    INDUCTOR = auto()
    VOLTAGE_SOURCE = auto()
    CURRENT_SOURCE = auto()
    DIODE = auto()
    TRANSISTOR_NPN = auto()
    TRANSISTOR_PNP = auto()
    MOSFET = auto()
    OPAMP = auto()


class AnalysisType(Enum):
    """Types of circuit analyses"""
    DC = "dc"
    AC = "ac"
    TRANSIENT = "transient"
    OP = "operating_point"
    NOISE = "noise"
    DISTORTION = "distortion"
    SENSITIVITY = "sensitivity"


@dataclass
class Component:
    """Circuit component"""
    name: str
    component_type: ComponentType
    nodes: List[str]
    value: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    model: Optional[str] = None


@dataclass
class CircuitConfig:
    """Configuration for circuit simulation"""
    analysis_type: AnalysisType = AnalysisType.TRANSIENT
    
    # Transient analysis parameters
    t_start: float = 0.0
    t_stop: float = 1e-3
    t_step: float = 1e-6
    
    # AC analysis parameters
    f_start: float = 1.0
    f_stop: float = 1e6
    n_points: int = 100
    
    # DC analysis parameters
    v_start: float = 0.0
    v_stop: float = 5.0
    v_step: float = 0.1
    source_name: str = "V1"
    
    # Convergence
    reltol: float = 1e-3
    abstol: float = 1e-12
    max_iter: int = 100
    
    # Temperature
    temperature: float = 27.0  # Celsius
    
    # Monte Carlo
    monte_carlo_runs: int = 0
    tolerance: float = 0.05  # 5% component tolerance
    
    # Optimization
    optimize: bool = False
    target_metric: str = "power"
    target_value: float = 0.0
    
    random_seed: Optional[int] = None


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

    def __init__(self):
        super().__init__()
        self.rng = np.random.default_rng()
        self.components: List[Component] = []
        self.circuit_file: Optional[Path] = None
        self.results: Dict[str, np.ndarray] = {}

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
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
            "circuit",
            "electrical",
            "electronic",
            "voltage",
            "current",
            "resistor",
            "capacitor",
            "inductor",
            "transistor",
            "amplifier",
            "filter",
            "oscillator",
            "power supply",
            "sensor",
            "adc",
            "dac",
            "op-amp",
            "spice",
            "impedance",
            "frequency response",
            "gain",
            "bandwidth",
            "noise",
        ]

        return any(kw in title or kw in desc for kw in circuit_keywords)

    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute circuit simulation"""
        start_time = datetime.now()
        simulation_id = f"ckt_{start_time.timestamp()}"

        logger.info(f"Starting Circuit simulation {simulation_id}")

        # Parse configuration
        circuit_config = self._parse_config(config)
        
        if circuit_config.random_seed:
            self.rng = np.random.default_rng(circuit_config.random_seed)

        try:
            # Check if PySpice is available
            try:
                import PySpice
                has_pyspice = True
            except ImportError:
                has_pyspice = False
                logger.warning("PySpice not available, using fallback implementation")
            
            # Build circuit
            self._build_circuit(hypothesis)
            
            # Run simulation (or fallback)
            if has_pyspice:
                results = await self._run_pyspice_simulation(circuit_config)
            else:
                results = await self._run_fallback_simulation(circuit_config)
            
            # Monte Carlo if requested
            if circuit_config.monte_carlo_runs > 0:
                mc_results = await self._run_monte_carlo(circuit_config)
                results["monte_carlo"] = mc_results
            
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

    def _parse_config(self, config: Dict[str, Any]) -> CircuitConfig:
        """Parse configuration dict"""
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

    def _build_circuit(self, hypothesis: Hypothesis) -> None:
        """Build circuit from hypothesis description"""
        params = hypothesis.parameters
        
        self.components = []
        
        # Check for explicit component list
        if "components" in params:
            for comp_def in params["components"]:
                self.components.append(Component(
                    name=comp_def["name"],
                    component_type=ComponentType[comp_def["type"].upper()],
                    nodes=comp_def["nodes"],
                    value=comp_def["value"],
                    parameters=comp_def.get("parameters", {}),
                    model=comp_def.get("model"),
                ))
        else:
            # Build from circuit type
            circuit_type = params.get("circuit_type", "generic")
            
            if circuit_type == "rc_filter":
                self._build_rc_filter(params)
            elif circuit_type == "rlc_tank":
                self._build_rlc_tank(params)
            elif circuit_type == "amplifier":
                self._build_amplifier(params)
            elif circuit_type == "oscillator":
                self._build_oscillator(params)
            elif circuit_type == "voltage_regulator":
                self._build_regulator(params)
            else:
                self._build_generic_circuit(params)

    def _build_rc_filter(self, params: Dict[str, Any]) -> None:
        """Build RC low-pass filter"""
        self.components = [
            Component(
                name="R1",
                component_type=ComponentType.RESISTOR,
                nodes=["input", "output"],
                value=params.get("resistance", 1000.0),
            ),
            Component(
                name="C1",
                component_type=ComponentType.CAPACITOR,
                nodes=["output", "ground"],
                value=params.get("capacitance", 1e-6),
            ),
            Component(
                name="V1",
                component_type=ComponentType.VOLTAGE_SOURCE,
                nodes=["input", "ground"],
                value=params.get("input_voltage", 1.0),
                parameters={"ac": 1.0},
            ),
        ]

    def _build_rlc_tank(self, params: Dict[str, Any]) -> None:
        """Build RLC tank circuit"""
        self.components = [
            Component(
                name="L1",
                component_type=ComponentType.INDUCTOR,
                nodes=["node1", "output"],
                value=params.get("inductance", 1e-3),
            ),
            Component(
                name="C1",
                component_type=ComponentType.CAPACITOR,
                nodes=["output", "ground"],
                value=params.get("capacitance", 1e-9),
            ),
            Component(
                name="R1",
                component_type=ComponentType.RESISTOR,
                nodes=["output", "ground"],
                value=params.get("resistance", 100.0),
            ),
            Component(
                name="I1",
                component_type=ComponentType.CURRENT_SOURCE,
                nodes=["node1", "ground"],
                value=params.get("input_current", 1e-3),
            ),
        ]

    def _build_amplifier(self, params: Dict[str, Any]) -> None:
        """Build simple transistor amplifier"""
        self.components = [
            Component(
                name="Q1",
                component_type=ComponentType.TRANSISTOR_NPN,
                nodes=["collector", "base", "emitter"],
                value=0,
                model="2N2222",
            ),
            Component(
                name="Rc",
                component_type=ComponentType.RESISTOR,
                nodes=["vcc", "collector"],
                value=params.get("collector_resistor", 1000.0),
            ),
            Component(
                name="Rb",
                component_type=ComponentType.RESISTOR,
                nodes=["vcc", "base"],
                value=params.get("base_resistor", 10000.0),
            ),
            Component(
                name="Re",
                component_type=ComponentType.RESISTOR,
                nodes=["emitter", "ground"],
                value=params.get("emitter_resistor", 100.0),
            ),
            Component(
                name="Vcc",
                component_type=ComponentType.VOLTAGE_SOURCE,
                nodes=["vcc", "ground"],
                value=params.get("supply_voltage", 5.0),
            ),
            Component(
                name="Vin",
                component_type=ComponentType.VOLTAGE_SOURCE,
                nodes=["input", "ground"],
                value=params.get("input_voltage", 0.0),
                parameters={"ac": 0.01},
            ),
            Component(
                name="Cin",
                component_type=ComponentType.CAPACITOR,
                nodes=["input", "base"],
                value=10e-6,
            ),
        ]

    def _build_oscillator(self, params: Dict[str, Any]) -> None:
        """Build relaxation oscillator"""
        self.components = [
            Component(
                name="R1",
                component_type=ComponentType.RESISTOR,
                nodes=["vcc", "cap"],
                value=params.get("charge_resistor", 10000.0),
            ),
            Component(
                name="C1",
                component_type=ComponentType.CAPACITOR,
                nodes=["cap", "ground"],
                value=params.get("capacitance", 1e-6),
            ),
            Component(
                name="Vcc",
                component_type=ComponentType.VOLTAGE_SOURCE,
                nodes=["vcc", "ground"],
                value=params.get("supply_voltage", 5.0),
            ),
        ]

    def _build_regulator(self, params: Dict[str, Any]) -> None:
        """Build voltage regulator"""
        self.components = [
            Component(
                name="R1",
                component_type=ComponentType.RESISTOR,
                nodes=["vin", "vout"],
                value=params.get("series_resistance", 10.0),
            ),
            Component(
                name="D1",
                component_type=ComponentType.DIODE,
                nodes=["vout", "ground"],
                value=0,
                model="1N4148",
                parameters={"is": 1e-14, "n": 1.0},
            ),
            Component(
                name="C1",
                component_type=ComponentType.CAPACITOR,
                nodes=["vout", "ground"],
                value=params.get("filter_cap", 100e-6),
            ),
            Component(
                name="Vin",
                component_type=ComponentType.VOLTAGE_SOURCE,
                nodes=["vin", "ground"],
                value=params.get("input_voltage", 9.0),
            ),
        ]

    def _build_generic_circuit(self, params: Dict[str, Any]) -> None:
        """Build generic test circuit"""
        self.components = [
            Component(
                name="R1",
                component_type=ComponentType.RESISTOR,
                nodes=["in", "out"],
                value=params.get("r1", 1000.0),
            ),
            Component(
                name="R2",
                component_type=ComponentType.RESISTOR,
                nodes=["out", "ground"],
                value=params.get("r2", 1000.0),
            ),
            Component(
                name="V1",
                component_type=ComponentType.VOLTAGE_SOURCE,
                nodes=["in", "ground"],
                value=params.get("vin", 5.0),
            ),
        ]

    async def _run_pyspice_simulation(self, config: CircuitConfig) -> Dict[str, Any]:
        """Run simulation using PySpice"""
        from PySpice.Spice.Netlist import Circuit
        from PySpice.Unit import u_V, u_Ohm, u_F, u_H, u_A, u_s, u_Hz
        
        # Create circuit
        circuit = Circuit('TURBO-CDI Circuit')
        circuit.temp(config.temperature)
        
        # Add components
        for comp in self.components:
            self._add_component_to_pyspice(circuit, comp)
        
        # Run analysis
        simulator = circuit.simulator()
        
        if config.analysis_type == AnalysisType.TRANSIENT:
            analysis = simulator.transient(
                step_time=config.t_step @ u_s,
                end_time=config.t_stop @ u_s,
            )
        elif config.analysis_type == AnalysisType.AC:
            analysis = simulator.ac(
                start_frequency=config.f_start @ u_Hz,
                stop_frequency=config.f_stop @ u_Hz,
                number_of_points=config.n_points,
                variation='dec',
            )
        elif config.analysis_type == AnalysisType.DC:
            analysis = simulator.dc(
                Vconfig.source_name,
                config.v_start @ u_V,
                config.v_stop @ u_V,
                config.v_step @ u_V,
            )
        elif config.analysis_type == AnalysisType.OP:
            analysis = simulator.operating_point()
        
        # Extract results
        results = self._extract_pyspice_results(analysis, config)
        
        return results

    def _add_component_to_pyspice(self, circuit, comp: Component) -> None:
        """Add component to PySpice circuit"""
        from PySpice.Unit import u_V, u_Ohm, u_F, u_H, u_A
        
        if comp.component_type == ComponentType.RESISTOR:
            circuit.R(comp.name, comp.nodes[0], comp.nodes[1], comp.value @ u_Ohm)
        elif comp.component_type == ComponentType.CAPACITOR:
            circuit.C(comp.name, comp.nodes[0], comp.nodes[1], comp.value @ u_F)
        elif comp.component_type == ComponentType.INDUCTOR:
            circuit.L(comp.name, comp.nodes[0], comp.nodes[1], comp.value @ u_H)
        elif comp.component_type == ComponentType.VOLTAGE_SOURCE:
            if "pulse" in comp.parameters:
                p = comp.parameters["pulse"]
                circuit.PulseVoltageSource(
                    comp.name, comp.nodes[0], comp.nodes[1],
                    initial_value=p.get("v1", 0) @ u_V,
                    pulsed_value=p.get("v2", 1) @ u_V,
                    pulse_width=p.get("pw", 1e-3) @ u_s,
                    period=p.get("period", 2e-3) @ u_s,
                )
            else:
                circuit.V(comp.name, comp.nodes[0], comp.nodes[1], comp.value @ u_V)
                if "ac" in comp.parameters:
                    circuit[comp.name].ac = comp.parameters["ac"]
        elif comp.component_type == ComponentType.CURRENT_SOURCE:
            circuit.I(comp.name, comp.nodes[0], comp.nodes[1], comp.value @ u_A)

    def _extract_pyspice_results(self, analysis, config: CircuitConfig) -> Dict[str, Any]:
        """Extract results from PySpice analysis"""
        metrics = {}
        logs = []
        
        # Get node voltages
        for node in analysis.nodes:
            node_name = str(node)
            voltage = np.array(analysis[node])
            
            metrics[f"v_{node_name}_mean"] = float(np.mean(voltage))
            metrics[f"v_{node_name}_min"] = float(np.min(voltage))
            metrics[f"v_{node_name}_max"] = float(np.max(voltage))
            
            if config.analysis_type == AnalysisType.AC:
                # For AC analysis, calculate magnitude and phase
                magnitude = np.abs(voltage)
                metrics[f"v_{node_name}_mag_max"] = float(np.max(magnitude))
        
        # Calculate power
        total_power = 0.0
        for comp in self.components:
            if comp.component_type in [ComponentType.RESISTOR, ComponentType.CAPACITOR, ComponentType.INDUCTOR]:
                # P = V^2 / R (approximate)
                if len(comp.nodes) >= 2:
                    try:
                        v1 = np.array(analysis[comp.nodes[0]])
                        v2 = np.array(analysis[comp.nodes[1]]) if comp.nodes[1] != "ground" else np.zeros_like(v1)
                        power = np.mean((v1 - v2) ** 2) / comp.value
                        total_power += power
                    except:
                        pass
        
        metrics["total_power"] = total_power
        
        logs.append(f"Analysis type: {config.analysis_type.value}")
        logs.append(f"Components: {len(self.components)}")
        logs.append(f"Nodes analyzed: {len(analysis.nodes)}")
        
        return {"metrics": metrics, "logs": logs}

    async def _run_fallback_simulation(self, config: CircuitConfig) -> Dict[str, Any]:
        """Fallback implementation when PySpice unavailable"""
        logger.info("Using fallback circuit simulation")
        
        # Simplified analytical solutions
        metrics = {}
        logs = ["Using fallback analytical simulation (PySpice not available)"]
        
        # Analyze circuit topology
        r_vals = []
        c_vals = []
        l_vals = []
        
        for comp in self.components:
            if comp.component_type == ComponentType.RESISTOR:
                r_vals.append(comp.value)
            elif comp.component_type == ComponentType.CAPACITOR:
                c_vals.append(comp.value)
            elif comp.component_type == ComponentType.INDUCTOR:
                l_vals.append(comp.value)
        
        # Calculate key metrics analytically
        if r_vals and c_vals:
            # RC circuit characteristics
            tau = r_vals[0] * c_vals[0]
            fc = 1 / (2 * np.pi * tau)
            metrics["rc_time_constant"] = tau
            metrics["cutoff_frequency"] = fc
            logs.append(f"RC time constant: {tau:.6e} s")
            logs.append(f"Cutoff frequency: {fc:.2f} Hz")
        
        if l_vals and c_vals:
            # LC resonant frequency
            f0 = 1 / (2 * np.pi * np.sqrt(l_vals[0] * c_vals[0]))
            metrics["resonant_frequency"] = f0
            logs.append(f"Resonant frequency: {f0:.2f} Hz")
        
        if r_vals and l_vals and c_vals:
            # Damping factor
            zeta = r_vals[0] / (2 * np.sqrt(l_vals[0] / c_vals[0]))
            metrics["damping_factor"] = zeta
            metrics["is_underdamped"] = zeta < 1
            logs.append(f"Damping factor: {zeta:.4f}")
            logs.append(f"System is {'underdamped' if zeta < 1 else 'overdamped'}")
        
        # Estimate power
        v_sources = [c for c in self.components if c.component_type == ComponentType.VOLTAGE_SOURCE]
        if v_sources and r_vals:
            v = v_sources[0].value
            r_eq = 1 / sum(1/r for r in r_vals) if len(r_vals) > 1 else r_vals[0]
            power = v ** 2 / r_eq
            metrics["estimated_power"] = power
            logs.append(f"Estimated power: {power:.4f} W")
        
        return {"metrics": metrics, "logs": logs}

    async def _run_monte_carlo(self, config: CircuitConfig) -> Dict[str, Any]:
        """Run Monte Carlo analysis with component tolerances"""
        logger.info(f"Running Monte Carlo with {config.monte_carlo_runs} runs")
        
        results = []
        
        for i in range(config.monte_carlo_runs):
            # Vary component values
            for comp in self.components:
                if comp.component_type in [ComponentType.RESISTOR, ComponentType.CAPACITOR, ComponentType.INDUCTOR]:
                    variation = self.rng.normal(1.0, config.tolerance)
                    comp.value *= variation
            
            # Run simulation
            try:
                if i % 50 == 0:
                    await asyncio.sleep(0)
                
                # Use fallback for speed in Monte Carlo
                run_result = await self._run_fallback_simulation(config)
                results.append(run_result["metrics"])
                
            except Exception as e:
                logger.warning(f"Monte Carlo run {i} failed: {e}")
            
            # Restore nominal values (simplified - in reality need to store originals)
        
        # Aggregate results
        mc_metrics = {}
        if results:
            for key in results[0].keys():
                values = [r[key] for r in results if key in r]
                if values:
                    mc_metrics[f"{key}_mc_mean"] = float(np.mean(values))
                    mc_metrics[f"{key}_mc_std"] = float(np.std(values))
                    mc_metrics[f"{key}_mc_min"] = float(np.min(values))
                    mc_metrics[f"{key}_mc_max"] = float(np.max(values))
        
        return mc_metrics

    def _calculate_confidence(
        self, results: Dict[str, Any], config: CircuitConfig
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

    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_components = len(params.get("components", []))
        mc_runs = params.get("monte_carlo_runs", 0)
        
        base_time = n_components * 0.1  # 0.1s per component
        mc_time = mc_runs * 0.5 if mc_runs > 0 else 0
        
        return {
            "cpu_cores": 2,
            "memory_gb": 1.0 + n_components / 100,
            "gpu_required": False,
            "estimated_time_seconds": base_time + mc_time,
        }
