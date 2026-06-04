"""
Neural Network Simulation Pattern
Spiking neural network for neuroscience research

Based on:
- Leaky Integrate-and-Fire (LIF) neurons
- Hodgkin-Huxley (simplified)
- Synaptic dynamics
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

from ..core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)


logger = logging.getLogger(__name__)


class NeuronModel(Enum):
    """NeuronModel."""
    LIF = "leaky_integrate_fire"
    IZHikevich = "izhikevich"
    HH = "hodgkin_huxley"


@dataclass
class Neuron:
    """Single neuron state"""
    neuron_id: int
    v: float = -70.0  # Membrane potential (mV)
    u: float = 0.0    # Recovery variable (for Izhikevich)
    fired: bool = False
    spike_times: list[float] = field(default_factory=list)


@simulation_pattern(
    id="neural_network",
    name="Neural Network Simulation",
    category="neuroscience",
    description="Spiking neural network for brain dynamics simulation",
)
class NeuralNetworkPattern(SimulationPattern):
    """
    Neural network simulation for neuroscience

    Implements:
    - Leaky Integrate-and-Fire (LIF) neurons
    - Izhikevich model ( bursting, chattering)
    - Synaptic connections
    - Population dynamics
    """

    parameters = [
        SimulationParameter(
            name="num_neurons",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Number of neurons",
        ),
        SimulationParameter(
            name="neuron_model",
            type="select",
            default="leaky_integrate_fire",
            options=["leaky_integrate_fire", "izhikevich"],
            description="Neuron dynamics model",
        ),
        SimulationParameter(
            name="connection_prob",
            type="float",
            default=0.1,
            min=0.0,
            max=1.0,
            description="Connection probability",
        ),
        SimulationParameter(
            name="simulation_time",
            type="float",
            default=1000.0,
            min=100.0,
            max=10000.0,
            description="Simulation time (ms)",
        ),
        SimulationParameter(
            name="dt",
            type="float",
            default=0.1,
            min=0.01,
            max=1.0,
            description="Time step (ms)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.neurons: list[Neuron] = []
        self.connections: list[tuple[int, int, float]] = []  # (pre, post, weight)
        self.spike_history: list[tuple[float, int]] = []  # (time, neuron_id)

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if neural network can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "neuron", "neural", "brain", "spiking",
            "synapse", "firing rate", "oscillation",
            "eeg", "population", "neuroscience",
            "integrate and fire", "hodgkin-huxley",
            "bursting", "synchronization",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute neural network simulation"""
        start_time = datetime.now()
        simulation_id = f"nn_{start_time.timestamp()}"

        logger.info(f"Starting neural network simulation {simulation_id}")

        model_type = config.get("neuron_model", "leaky_integrate_fire")

        try:
            if model_type == "leaky_integrate_fire":
                results = await self._lif_simulation(hypothesis, config)
            else:
                results = await self._izhikevich_simulation(hypothesis, config)

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
            logger.exception("Neural network simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    async def _lif_simulation(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Leaky Integrate-and-Fire neuron simulation"""

        params = hypothesis.parameters
        N = config.get("num_neurons", 100)
        T = config.get("simulation_time", 1000.0)
        dt = config.get("dt", 0.1)
        p_conn = config.get("connection_prob", 0.1)

        # LIF parameters
        tau_m = 20.0  # Membrane time constant (ms)
        V_rest = -70.0  # Resting potential (mV)
        V_reset = -70.0  # Reset potential (mV)
        V_thresh = -55.0  # Threshold (mV)
        R = 10.0  # Membrane resistance (MΩ)

        # Initialize neurons
        self.neurons = [Neuron(i, v=V_rest + np.random.randn()*5) for i in range(N)]

        # Create random connections
        self.connections = []
        for i in range(N):
            for j in range(N):
                if i != j and np.random.random() < p_conn:
                    weight = np.random.randn() * 0.5 + 0.1  # Excitatory bias
                    self.connections.append((i, j, weight))

        # Simulation
        n_steps = int(T / dt)
        spike_times: Any = [[] for _ in range(N)]

        for step in range(n_steps):
            t = step * dt

            # External input (noisy)
            I_ext = 2.0 + np.random.randn(N) * 0.5

            # Update each neuron
            for i, neuron in enumerate(self.neurons):
                if neuron.fired:
                    neuron.v = V_reset
                    neuron.fired = False

                # Synaptic input
                I_syn = 0.0
                for pre, post, w in self.connections:
                    if post == i and self.neurons[pre].fired:
                        I_syn += w * 5.0  # EPSC/IPSC

                # LIF equation: dV/dt = (-(V - V_rest) + R*I) / tau_m
                dV = (-(neuron.v - V_rest) + R * (I_ext[i] + I_syn)) / tau_m
                neuron.v += dV * dt

                # Check for spike
                if neuron.v >= V_thresh:
                    neuron.fired = True
                    neuron.spike_times.append(t)
                    spike_times[i].append(t)
                    self.spike_history.append((t, i))

            # Yield control periodically
            if step % 1000 == 0:
                await asyncio.sleep(0)

        # Calculate metrics
        firing_rates = [len(st) / (T/1000) for st in spike_times]  # Hz
        avg_firing_rate = np.mean(firing_rates)

        # Coefficient of variation (regularity)
        cv_values = []
        for st in spike_times:
            if len(st) > 2:
                isi = np.diff(st)
                cv_values.append(np.std(isi) / np.mean(isi))
        avg_cv = np.mean(cv_values) if cv_values else 0

        # Synchronization
        if len(self.spike_history) > 10:
            spike_times_all = [t for t, _ in self.spike_history]
            # Simple sync measure: variance of spike count in time bins
            bins = np.arange(0, T, 10)  # 10ms bins
            counts, _ = np.histogram(spike_times_all, bins)
            sync_index = np.var(counts) / np.mean(counts) if np.mean(counts) > 0 else 0
        else:
            sync_index = 0

        metrics = {
            "num_neurons": N,
            "num_connections": len(self.connections),
            "avg_firing_rate_hz": float(avg_firing_rate),
            "max_firing_rate_hz": float(np.max(firing_rates)) if firing_rates else 0,
            "total_spikes": sum(len(st) for st in spike_times),
            "coefficient_of_variation": float(avg_cv),
            "synchronization_index": float(sync_index),
            "simulation_time_ms": T,
        }

        logs = [
            f"LIF neural network: {N} neurons, {len(self.connections)} connections",
            f"Average firing rate: {avg_firing_rate:.2f} Hz",
            f"Total spikes: {metrics['total_spikes']}",
            f"Synchronization index: {sync_index:.3f}",
        ]

        return {"metrics": metrics, "logs": logs}

    async def _izhikevich_simulation(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Izhikevich neuron model (more biologically realistic)"""

        N = config.get("num_neurons", 100)
        T = config.get("simulation_time", 1000.0)
        dt = config.get("dt", 0.1)

        # Izhikevich parameters (regular spiking)
        a = 0.02
        b = 0.2
        c = -65.0
        d = 8.0

        # State variables
        v = np.ones(N) * -65.0  # Membrane potential
        u = np.ones(N) * -13.0  # Recovery variable

        spike_count = 0

        for step in range(int(T / dt)):
            # Input current
            I = 5.0 + np.random.randn(N) * 2.0

            # Check for spikes
            fired = v >= 30.0
            if np.any(fired):
                v[fired] = c
                u[fired] = u[fired] + d
                spike_count += np.sum(fired)  # type: ignore[assignment]

            # Izhikevich equations
            dv = (0.04 * v**2 + 5 * v + 140 - u + I)
            du = a * (b * v - u)

            v += dv * dt
            u += du * dt

            if step % 1000 == 0:
                await asyncio.sleep(0)

        metrics = {
            "num_neurons": N,
            "total_spikes": int(spike_count),
            "avg_firing_rate_hz": float(spike_count / (N * T/1000)),
            "neuron_model": "izhikevich",
        }

        logs = [
            f"Izhikevich neural network: {N} neurons",
            f"Total spikes: {spike_count}",
            f"Average firing rate: {metrics['avg_firing_rate_hz']:.2f} Hz",
        ]

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Reasonable firing rates
        rate = metrics.get("avg_firing_rate_hz", 0)
        if 0.1 < rate < 100:
            factors.append(0.3)

        # Sufficient spikes
        if metrics.get("total_spikes", 0) > 10:
            factors.append(0.2)

        # Reasonable CV
        cv = metrics.get("coefficient_of_variation", 1)
        if 0.5 < cv < 2.0:
            factors.append(0.2)

        # Network structure
        if metrics.get("num_connections", 0) > 0:
            factors.append(0.2)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("num_neurons", 100)
        T = params.get("simulation_time", 1000.0)
        dt = params.get("dt", 0.1)

        n_steps = int(T / dt)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + N * 1e-4,
            "gpu_required": False,
            "estimated_time_seconds": N * n_steps / 1e6,
        }
