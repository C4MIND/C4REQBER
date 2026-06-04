"""
Hodgkin-Huxley Pattern
Biophysically detailed neuron action potential model

Based on:
- Hodgkin & Huxley (1952) Nobel Prize-winning model
- Voltage-gated Na+ and K+ ion channels
- Membrane capacitance and leak currents
- Propagating action potentials
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

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


class StimulusType(Enum):
    """StimulusType."""
    STEP = "step"
    RAMP = "ramp"
    PULSE = "pulse"
    SINUSOIDAL = "sinusoidal"


@dataclass
class HHConfig:
    """Hodgkin-Huxley model configuration"""
    # Membrane parameters
    C_m: float = 1.0  # Membrane capacitance (uF/cm^2)
    g_Na: float = 120.0  # Max Na+ conductance (mS/cm^2)
    g_K: float = 36.0  # Max K+ conductance (mS/cm^2)
    g_L: float = 0.3  # Leak conductance (mS/cm^2)
    E_Na: float = 50.0  # Na+ reversal potential (mV)
    E_K: float = -77.0  # K+ reversal potential (mV)
    E_L: float = -54.387  # Leak reversal potential (mV)

    # Simulation parameters
    t_max: float = 50.0  # Simulation time (ms)
    dt: float = 0.01  # Time step (ms)
    I_inj: float = 10.0  # Injected current (uA/cm^2)
    stim_start: float = 5.0  # Stimulus start (ms)
    stim_end: float = 30.0  # Stimulus end (ms)
    stim_type: StimulusType = StimulusType.STEP

    # Initial conditions
    V0: float = -65.0  # Initial membrane potential (mV)

    def to_dict(self) -> dict[str, Any]:
        return {
            "C_m": self.C_m,
            "g_Na": self.g_Na,
            "g_K": self.g_K,
            "g_L": self.g_L,
            "E_Na": self.E_Na,
            "E_K": self.E_K,
            "E_L": self.E_L,
            "t_max": self.t_max,
            "dt": self.dt,
            "I_inj": self.I_inj,
            "stim_start": self.stim_start,
            "stim_end": self.stim_end,
            "stim_type": self.stim_type.value,
            "V0": self.V0,
        }


@simulation_pattern(
    id="hodgkin_huxley",
    name="Hodgkin-Huxley Neuron Model",
    category="neuroscience",
    description="Biophysically detailed action potential simulation using voltage-gated ion channels",
)
class HodgkinHuxleyPattern(SimulationPattern):
    """
    Hodgkin-Huxley neuron model for action potential generation

    Implements the Nobel Prize-winning model (1952) that describes
    how action potentials in neurons are initiated and propagated
    through voltage-gated sodium and potassium ion channels.

    Key features:
    - Voltage-gated Na+ channels (activation m, inactivation h)
    - Voltage-gated K+ channels (activation n)
    - Membrane capacitance and leak currents
    - Multiple stimulus types (step, ramp, pulse, sinusoidal)
    """

    parameters = [
        SimulationParameter(
            name="C_m",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Membrane capacitance (uF/cm^2)",
        ),
        SimulationParameter(
            name="g_Na",
            type="float",
            default=120.0,
            min=0.0,
            max=500.0,
            description="Max Na+ conductance (mS/cm^2)",
        ),
        SimulationParameter(
            name="g_K",
            type="float",
            default=36.0,
            min=0.0,
            max=200.0,
            description="Max K+ conductance (mS/cm^2)",
        ),
        SimulationParameter(
            name="I_inj",
            type="float",
            default=10.0,
            min=-50.0,
            max=100.0,
            description="Injected current amplitude (uA/cm^2)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=50.0,
            min=10.0,
            max=500.0,
            description="Simulation duration (ms)",
        ),
        SimulationParameter(
            name="stim_type",
            type="select",
            default="step",
            options=["step", "ramp", "pulse", "sinusoidal"],
            description="Stimulus waveform type",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: HHConfig = HHConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if HH model can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "hodgkin", "huxley", "action potential", "spike",
            "ion channel", "voltage-gated", "membrane potential",
            "sodium", "potassium", "conductance", "neuron",
            "biophysical", "excitable", "axon", "squid giant",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute Hodgkin-Huxley simulation"""
        start_time = datetime.now()
        simulation_id = f"hh_{start_time.timestamp()}"

        logger.info(f"Starting Hodgkin-Huxley simulation {simulation_id}")

        try:
            # Parse configuration
            self.config = self._parse_config(config)

            # Run simulation
            results = await self._simulate_hh()

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
            logger.exception("Hodgkin-Huxley simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> HHConfig:
        """Parse configuration dictionary into HHConfig"""
        cfg = HHConfig()

        if "C_m" in config:
            cfg.C_m = float(config["C_m"])
        if "g_Na" in config:
            cfg.g_Na = float(config["g_Na"])
        if "g_K" in config:
            cfg.g_K = float(config["g_K"])
        if "g_L" in config:
            cfg.g_L = float(config["g_L"])
        if "E_Na" in config:
            cfg.E_Na = float(config["E_Na"])
        if "E_K" in config:
            cfg.E_K = float(config["E_K"])
        if "E_L" in config:
            cfg.E_L = float(config["E_L"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "I_inj" in config:
            cfg.I_inj = float(config["I_inj"])
        if "stim_start" in config:
            cfg.stim_start = float(config["stim_start"])
        if "stim_end" in config:
            cfg.stim_end = float(config["stim_end"])
        if "stim_type" in config:
            cfg.stim_type = StimulusType(config["stim_type"])
        if "V0" in config:
            cfg.V0 = float(config["V0"])

        return cfg

    async def _simulate_hh(self) -> dict[str, Any]:
        """Run the Hodgkin-Huxley simulation"""

        cfg = self.config

        # Time array
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        # Initial conditions: [V, m, h, n]
        # Initial gating variables at steady state for V0
        m0 = self._alpha_m(cfg.V0) / (self._alpha_m(cfg.V0) + self._beta_m(cfg.V0))
        h0 = self._alpha_h(cfg.V0) / (self._alpha_h(cfg.V0) + self._beta_h(cfg.V0))
        n0 = self._alpha_n(cfg.V0) / (self._alpha_n(cfg.V0) + self._beta_n(cfg.V0))

        y0 = [cfg.V0, m0, h0, n0]

        # Solve ODE system
        solution = solve_ivp(
            self._hh_equations,
            t_span,
            y0,
            t_eval=t_eval,
            method='RK45',
            dense_output=True,
        )

        # Extract results
        t = solution.t
        V = solution.y[0]
        m = solution.y[1]
        h = solution.y[2]
        n = solution.y[3]

        # Calculate ionic currents
        I_Na = cfg.g_Na * m**3 * h * (V - cfg.E_Na)
        I_K = cfg.g_K * n**4 * (V - cfg.E_K)
        I_L = cfg.g_L * (V - cfg.E_L)

        # Find action potentials (spikes)
        spike_threshold = -20.0  # mV
        spike_times = self._detect_spikes(t, V, spike_threshold)

        # Calculate metrics
        metrics = self._calculate_metrics(t, V, m, h, n, I_Na, I_K, spike_times)

        logs = [
            "Hodgkin-Huxley simulation completed",
            f"Parameters: C_m={cfg.C_m}, g_Na={cfg.g_Na}, g_K={cfg.g_K}",
            f"Stimulus: {cfg.I_inj} uA/cm^2 ({cfg.stim_type.value})",
            f"Action potentials detected: {len(spike_times)}",
            f"Spike frequency: {metrics['spike_frequency']:.2f} Hz",
            f"Max depolarization: {metrics['max_V']:.2f} mV",
            f"Resting potential: {metrics['resting_V']:.2f} mV",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "voltage": V.tolist(),
            "m_gate": m.tolist(),
            "h_gate": h.tolist(),
            "n_gate": n.tolist(),
            "I_Na": I_Na.tolist(),
            "I_K": I_K.tolist(),
            "spike_times": spike_times,
        }

    def _hh_equations(self, t: float, y: list[float]) -> list[float]:
        """Hodgkin-Huxley differential equations"""
        V, m, h, n = y
        cfg = self.config

        # Stimulus current
        I_stim = self._get_stimulus(t)

        # Gating variable derivatives
        dm_dt = self._alpha_m(V) * (1 - m) - self._beta_m(V) * m
        dh_dt = self._alpha_h(V) * (1 - h) - self._beta_h(V) * h
        dn_dt = self._alpha_n(V) * (1 - n) - self._beta_n(V) * n

        # Ionic currents
        I_Na = cfg.g_Na * m**3 * h * (V - cfg.E_Na)
        I_K = cfg.g_K * n**4 * (V - cfg.E_K)
        I_L = cfg.g_L * (V - cfg.E_L)

        # Membrane potential derivative: C_m * dV/dt = I_stim - I_ionic
        dV_dt = (I_stim - I_Na - I_K - I_L) / cfg.C_m

        return [dV_dt, dm_dt, dh_dt, dn_dt]

    def _get_stimulus(self, t: float) -> float:
        """Get stimulus current at time t"""
        cfg = self.config

        if t < cfg.stim_start or t >= cfg.stim_end:
            return 0.0

        if cfg.stim_type == StimulusType.STEP:
            return cfg.I_inj
        elif cfg.stim_type == StimulusType.RAMP:
            ramp_factor = (t - cfg.stim_start) / (cfg.stim_end - cfg.stim_start)
            return cfg.I_inj * ramp_factor
        elif cfg.stim_type == StimulusType.PULSE:
            # Short pulse at start
            if t < cfg.stim_start + 1.0:
                return cfg.I_inj
            return 0.0
        elif cfg.stim_type == StimulusType.SINUSOIDAL:
            freq = 0.5  # kHz
            return cfg.I_inj * np.sin(2 * np.pi * freq * (t - cfg.stim_start))  # type: ignore[no-any-return]

        return 0.0  # type: ignore[unreachable]

    # Gating variable rate functions (original HH formulas)
    def _alpha_m(self, V: float) -> float:
        """Na+ activation forward rate"""
        x = (V + 40.0) / 10.0
        if abs(x) < 1e-9:
            return 1.0  # lim x→0 x/(1-e^{-x}) = 1, so alpha_m = 0.1 * 10 * 1 = 1.0
        return 0.1 * 10.0 * x / (1.0 - np.exp(-x))  # type: ignore[no-any-return]

    def _beta_m(self, V: float) -> float:
        """Na+ activation backward rate"""
        return 4.0 * np.exp(-(V + 65.0) / 18.0)  # type: ignore[no-any-return]

    def _alpha_h(self, V: float) -> float:
        """Na+ inactivation forward rate"""
        return 0.07 * np.exp(-(V + 65.0) / 20.0)  # type: ignore[no-any-return]

    def _beta_h(self, V: float) -> float:
        """Na+ inactivation backward rate"""
        return 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))  # type: ignore[no-any-return]

    def _alpha_n(self, V: float) -> float:
        """K+ activation forward rate"""
        x = (V + 55.0) / 10.0
        if abs(x) < 1e-9:
            return 0.1  # lim x→0 x/(1-e^{-x}) = 1, so alpha_n = 0.01 * 10 * 1 = 0.1
        return 0.01 * 10.0 * x / (1.0 - np.exp(-x))  # type: ignore[no-any-return]

    def _beta_n(self, V: float) -> float:
        """K+ activation backward rate"""
        return 0.125 * np.exp(-(V + 65.0) / 80.0)  # type: ignore[no-any-return]

    def _detect_spikes(self, t: np.ndarray, V: np.ndarray, threshold: float) -> list[float]:
        """Detect action potential spike times"""
        spike_times = []
        for i in range(1, len(V)):
            if V[i] > threshold and V[i-1] <= threshold:
                # Linear interpolation for more accurate spike time
                if V[i] != V[i-1]:
                    t_spike = t[i-1] + (threshold - V[i-1]) * (t[i] - t[i-1]) / (V[i] - V[i-1])
                else:
                    t_spike = t[i]
                spike_times.append(float(t_spike))
        return spike_times

    def _calculate_metrics(
        self, t: np.ndarray, V: np.ndarray, m: np.ndarray,
        h: np.ndarray, n: np.ndarray, I_Na: np.ndarray, I_K: np.ndarray,
        spike_times: list[float]
    ) -> dict[str, float]:
        """Calculate simulation metrics"""

        cfg = self.config
        stim_duration = cfg.stim_end - cfg.stim_start

        # Basic voltage metrics
        resting_V = float(np.mean(V[:100]))  # First 1 ms (approx)
        max_V = float(np.max(V))
        min_V = float(np.min(V))

        # Spike metrics
        num_spikes = len(spike_times)
        spike_frequency = num_spikes / (stim_duration / 1000.0) if stim_duration > 0 else 0  # Hz

        # ISI statistics
        if num_spikes > 1:
            isis = np.diff(spike_times)
            mean_isi = float(np.mean(isis))
            cv_isi = float(np.std(isis) / np.mean(isis)) if np.mean(isis) > 0 else 0
        else:
            mean_isi = 0.0
            cv_isi = 0.0

        # AP amplitude (from resting to peak)
        ap_amplitude = max_V - resting_V

        # Threshold (approximate - where m starts rapid increase)
        threshold_idx = np.where(np.diff(m) > 0.01)[0]
        threshold_V = float(V[threshold_idx[0]]) if len(threshold_idx) > 0 else -55.0

        # Max conductances
        max_g_Na = float(np.max(cfg.g_Na * m**3 * h))
        max_g_K = float(np.max(cfg.g_K * n**4))

        # Current integrals
        total_Na_current = float(np.trapezoid(I_Na, t))
        total_K_current = float(np.trapezoid(I_K, t))

        return {
            "resting_V": resting_V,
            "max_V": max_V,
            "min_V": min_V,
            "ap_amplitude": ap_amplitude,
            "threshold_V": threshold_V,
            "num_spikes": num_spikes,
            "spike_frequency": spike_frequency,
            "mean_isi_ms": mean_isi,
            "cv_isi": cv_isi,
            "max_g_Na": max_g_Na,
            "max_g_K": max_g_K,
            "total_Na_charge": total_Na_current,
            "total_K_charge": total_K_current,
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score based on physiological plausibility"""
        metrics = results["metrics"]
        factors = []

        # Resting potential in physiological range
        resting = metrics.get("resting_V", -65.0)
        if -80 < resting < -50:
            factors.append(0.25)

        # Action potential amplitude reasonable
        ap_amp = metrics.get("ap_amplitude", 0)
        if 80 < ap_amp < 120:
            factors.append(0.25)

        # Spike frequency in physiological range
        freq = metrics.get("spike_frequency", 0)
        if 0 <= freq < 200:  # Up to 200 Hz is reasonable
            factors.append(0.25)

        # Conductance ratios reasonable
        g_Na = self.config.g_Na
        g_K = self.config.g_K
        if 2 < g_Na / g_K < 5:  # Typical ratio
            factors.append(0.25)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 50.0)
        dt = params.get("dt", 0.01)

        n_steps = int(t_max / dt)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": n_steps / 1e5,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": cls.id,
            "name": cls.name,  # type: ignore[attr-defined]
            "category": cls.category,  # type: ignore[attr-defined]
            "description": cls.description,  # type: ignore[attr-defined]
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
                "Hodgkin, A.L. & Huxley, A.F. (1952). A quantitative description of membrane current",
            ],
        }
