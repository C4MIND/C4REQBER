"""
Circuit Simulation Pattern[str] Core
Core simulation logic for circuit simulation.
"""

import asyncio
from typing import Any

import numpy as np

from .config import AnalysisType, CircuitConfig, Component, ComponentType


class CircuitBuilder:
    """Builds circuits from parameters or templates"""

    def __init__(self) -> None:
        self.components: list[Component] = []

    def build_from_params(self, params: dict[str, Any]) -> list[Component]:
        """Build circuit from hypothesis parameters"""
        self.components = []

        # Check for explicit component list[Any]
        if "components" in params:
            for comp_def in params["components"]:
                self.components.append(Component(
                    name=comp_def["name"],
                    component_type=ComponentType[comp_def["type"].upper()],
                    nodes=comp_def.get("nodes", []),
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

        return self.components

    def _build_rc_filter(self, params: dict[str, Any]) -> None:
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

    def _build_rlc_tank(self, params: dict[str, Any]) -> None:
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

    def _build_amplifier(self, params: dict[str, Any]) -> None:
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

    def _build_oscillator(self, params: dict[str, Any]) -> None:
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

    def _build_regulator(self, params: dict[str, Any]) -> None:
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

    def _build_generic_circuit(self, params: dict[str, Any]) -> None:
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

class CircuitSimulator:
    """SPICE-based circuit simulation engine"""

    def __init__(self, rng: Any) -> None:
        self.rng = rng
        self.components: list[Component] = []

    async def run(self, components: list[Component], config: CircuitConfig) -> dict[str, Any]:
        """Main entry point: route between PySpice, fallback, and Monte Carlo"""
        self.components = components

        has_pyspice = False
        try:
            import PySpice
            has_pyspice = True
        except ImportError:
            pass

        if has_pyspice and config.analysis_type != AnalysisType.TRANSIENT:
            try:
                results = await asyncio.to_thread(self.run_pyspice, config)
            except (ImportError, AttributeError, TypeError, ValueError):
                results = await self.run_fallback(config)
        else:
            results = await self.run_fallback(config)

        if config.monte_carlo_runs > 0:
            mc_results = await self.run_monte_carlo(config)
            results["metrics"].update(mc_results)

        return results

    async def run_pyspice(self, config: CircuitConfig) -> dict[str, Any]:
        """Run simulation using PySpice"""
        from PySpice.Spice.Netlist import Circuit
        from PySpice.Unit import u_A, u_F, u_H, u_Hz, u_Ohm, u_s, u_V

        # Create circuit
        circuit = Circuit('C4REQBER Circuit')
        circuit.temp(config.temperature)

        # Add components
        for comp in self.components:
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
                config.source_name,
                config.v_start @ u_V,
                config.v_stop @ u_V,
                config.v_step @ u_V,
            )
        elif config.analysis_type == AnalysisType.OP:
            analysis = simulator.operating_point()

        # Extract results
        return self._extract_results(analysis, config)

    def _extract_results(self, analysis: Any, config: CircuitConfig) -> dict[str, Any]:
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
                magnitude = np.abs(voltage)
                metrics[f"v_{node_name}_mag_max"] = float(np.max(magnitude))

        # Calculate power
        total_power = 0.0
        for comp in self.components:
            if comp.component_type in [ComponentType.RESISTOR, ComponentType.CAPACITOR, ComponentType.INDUCTOR]:
                if len(comp.nodes) >= 2:
                    try:
                        v1 = np.array(analysis[comp.nodes[0]])
                        v2 = np.array(analysis[comp.nodes[1]]) if comp.nodes[1] != "ground" else np.zeros_like(v1)
                        power = np.mean((v1 - v2) ** 2) / comp.value
                        total_power += power
                    except (KeyError, IndexError, TypeError, ValueError):
                        pass

        metrics["total_power"] = total_power

        logs.append(f"Analysis type: {config.analysis_type.value}")
        logs.append(f"Components: {len(self.components)}")
        logs.append(f"Nodes analyzed: {len(analysis.nodes)}")

        return {"metrics": metrics, "logs": logs}

    async def run_fallback(self, config: CircuitConfig) -> dict[str, Any]:
        """Fallback analytical simulation when PySpice unavailable"""
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
            tau = r_vals[0] * c_vals[0]
            fc = 1 / (2 * np.pi * tau)
            metrics["rc_time_constant"] = tau
            metrics["cutoff_frequency"] = fc
            logs.append(f"RC time constant: {tau:.6e} s")
            logs.append(f"Cutoff frequency: {fc:.2f} Hz")

        if l_vals and c_vals:
            f0 = 1 / (2 * np.pi * np.sqrt(l_vals[0] * c_vals[0]))
            metrics["resonant_frequency"] = f0
            logs.append(f"Resonant frequency: {f0:.2f} Hz")

        if r_vals and l_vals and c_vals:
            zeta = r_vals[0] / (2 * np.sqrt(l_vals[0] / c_vals[0]))
            metrics["damping_factor"] = zeta
            metrics["is_underdamped"] = zeta < 1
            logs.append(f"Damping factor: {zeta:.4f}")
            logs.append(f"System is {'underdamped' if zeta < 1 else 'overdamped'}")

        v_sources = [c for c in self.components if c.component_type == ComponentType.VOLTAGE_SOURCE]
        if v_sources and r_vals:
            v = v_sources[0].value
            r_eq = 1 / sum(1/r for r in r_vals) if len(r_vals) > 1 else r_vals[0]
            power = v ** 2 / r_eq
            metrics["estimated_power"] = power
            logs.append(f"Estimated power: {power:.4f} W")

        return {"metrics": metrics, "logs": logs}

    async def run_monte_carlo(self, config: CircuitConfig) -> dict[str, Any]:
        """Run Monte Carlo analysis with component tolerances"""
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

                run_result = await self.run_fallback(config)
                results.append(run_result["metrics"])
            except (ValueError, TypeError, ZeroDivisionError):
                pass

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
