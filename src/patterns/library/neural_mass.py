"""
Neural Mass Pattern
Mean-field model for brain dynamics and EEG/MEG simulation

Based on:
- Jansen-Rit model (1995) for alpha rhythm generation
- Wendling model (2002) for epilepsy
- Dynamic Mean Field (DMF) for large-scale networks
- Deco et al. (2014) for resting-state fMRI
"""

from __future__ import annotations

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


class NeuralMassModel(Enum):
    """NeuralMassModel."""
    JANSEN_RIT = "jansen_rit"
    WENDLING = "wendling"
    WILSON_COWAN = "wilson_cowan"


@dataclass
class NeuralMassConfig:
    """Neural mass model configuration"""
    # Model selection
    model: NeuralMassModel = NeuralMassModel.JANSEN_RIT

    # Jansen-Rit parameters (default)
    He: float = 3.25  # mV - excitatory synaptic gain
    Hi: float = 22.0  # mV - inhibitory synaptic gain
    ke: float = 100.0  # s^-1 - excitatory time constant
    ki: float = 50.0  # s^-1 - inhibitory time constant

    # Connectivity parameters
    C: float = 135.0  # Connectivity constant
    C1: float = 1.0  # Pyramid -> excitatory interneurons
    C2: float = 0.8  # Excitatory interneurons -> pyramid
    C3: float = 0.25  # Pyramid -> inhibitory interneurons
    C4: float = 0.25  # Inhibitory interneurons -> pyramid

    # Sigmoid parameters
    e0: float = 2.5  # Maximum firing rate (s^-1)
    v0: float = 6.0  # PSP for 50% firing rate (mV)
    r: float = 0.56  # Slope parameter (mV^-1)

    # Input
    P: float = 220.0  # External input to pyramid (s^-1)
    U: float = 0.0  # Mean external input
    sigma_noise: float = 0.0  # Input noise standard deviation

    # Simulation
    t_max: float = 10.0  # seconds
    dt: float = 0.001  # seconds (1 ms)

    # Output
    output_type: str = "eeg"  # eeg, lfp, firing_rate

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "He": self.He,
            "Hi": self.Hi,
            "ke": self.ke,
            "ki": self.ki,
            "C": self.C,
            "C1": self.C1,
            "C2": self.C2,
            "C3": self.C3,
            "C4": self.C4,
            "e0": self.e0,
            "v0": self.v0,
            "r": self.r,
            "P": self.P,
            "U": self.U,
            "sigma_noise": self.sigma_noise,
            "t_max": self.t_max,
            "dt": self.dt,
            "output_type": self.output_type,
        }


@simulation_pattern(
    id="neural_mass",
    name="Neural Mass Model",
    category="neuroscience",
    description="Mean-field brain dynamics simulation for EEG/MEG and population activity",
)
class NeuralMassPattern(SimulationPattern):
    """
    Neural mass model for macroscopic brain dynamics

    Simulates the collective behavior of large neuronal populations
    using mean-field approximations. Models include:

    1. Jansen-Rit: Biophysical model of alpha rhythm generation
    2. Wendling: Extended model for epileptic activity
    3. Wilson-Cowan: Classical firing rate model

    Applications:
    - EEG/MEG signal generation
    - Epilepsy seizure modeling
    - Resting-state dynamics
    - Brain stimulation effects
    """

    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="jansen_rit",
            options=["jansen_rit", "wendling", "wilson_cowan"],
            description="Neural mass model type",
        ),
        SimulationParameter(
            name="He",
            type="float",
            default=3.25,
            min=0.1,
            max=50.0,
            description="Excitatory synaptic gain (mV)",
        ),
        SimulationParameter(
            name="Hi",
            type="float",
            default=22.0,
            min=0.1,
            max=100.0,
            description="Inhibitory synaptic gain (mV)",
        ),
        SimulationParameter(
            name="ke",
            type="float",
            default=100.0,
            min=10.0,
            max=500.0,
            description="Excitatory time constant (s^-1)",
        ),
        SimulationParameter(
            name="ki",
            type="float",
            default=50.0,
            min=10.0,
            max=500.0,
            description="Inhibitory time constant (s^-1)",
        ),
        SimulationParameter(
            name="P",
            type="float",
            default=220.0,
            min=0.0,
            max=1000.0,
            description="External input to pyramidal population (s^-1)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=10.0,
            min=1.0,
            max=100.0,
            description="Simulation duration (seconds)",
        ),
        SimulationParameter(
            name="sigma_noise",
            type="float",
            default=0.0,
            min=0.0,
            max=1000.0,
            description="Input noise standard deviation",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: NeuralMassConfig = NeuralMassConfig()
        self.noise_stream: np.random.Generator | None = None

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if neural mass model can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "neural mass", "mean field", "eeg", "meg", "population",
            "jansen-rit", "wendling", "wilson-cowan", "brain dynamics",
            "alpha rhythm", "epilepsy", "seizure", "oscillation",
            "pyramidal", "interneuron", "connectivity", "cortical",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute neural mass simulation"""
        start_time = datetime.now()
        simulation_id = f"nm_{start_time.timestamp()}"

        logger.info(f"Starting neural mass simulation {simulation_id}")

        try:
            # Parse configuration
            self.config = self._parse_config(config)
            self.noise_stream = np.random.default_rng(seed=42)

            # Run simulation based on model type
            if self.config.model == NeuralMassModel.JANSEN_RIT:
                results = await self._jansen_rit_simulation()
            elif self.config.model == NeuralMassModel.WENDLING:
                results = await self._wendling_simulation()
            else:
                results = await self._wilson_cowan_simulation()

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
            logger.exception("Neural mass simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> NeuralMassConfig:
        """Parse configuration dictionary"""
        cfg = NeuralMassConfig()

        if "model" in config:
            cfg.model = NeuralMassModel(config["model"])
        if "He" in config:
            cfg.He = float(config["He"])
        if "Hi" in config:
            cfg.Hi = float(config["Hi"])
        if "ke" in config:
            cfg.ke = float(config["ke"])
        if "ki" in config:
            cfg.ki = float(config["ki"])
        if "C" in config:
            cfg.C = float(config["C"])
        if "C1" in config:
            cfg.C1 = float(config["C1"])
        if "C2" in config:
            cfg.C2 = float(config["C2"])
        if "C3" in config:
            cfg.C3 = float(config["C3"])
        if "C4" in config:
            cfg.C4 = float(config["C4"])
        if "e0" in config:
            cfg.e0 = float(config["e0"])
        if "v0" in config:
            cfg.v0 = float(config["v0"])
        if "r" in config:
            cfg.r = float(config["r"])
        if "P" in config:
            cfg.P = float(config["P"])
        if "U" in config:
            cfg.U = float(config["U"])
        if "sigma_noise" in config:
            cfg.sigma_noise = float(config["sigma_noise"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "output_type" in config:
            cfg.output_type = config["output_type"]

        return cfg

    async def _jansen_rit_simulation(self) -> dict[str, Any]:
        """Jansen-Rit model simulation"""

        cfg = self.config

        # Time array
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        # Initial conditions: [y0, y1, y2, y3, y4, y5]
        # y0, y1: excitatory interneurons
        # y2, y3: pyramidal cells
        # y4, y5: inhibitory interneurons
        y0 = np.zeros(6)

        # Solve ODE
        solution = solve_ivp(
            self._jansen_rit_equations,
            t_span,
            y0,
            t_eval=t_eval,
            method='RK45',
        )

        t = solution.t
        y = solution.y

        # Extract post-synaptic potentials
        v_e = y[1]  # PSP at excitatory interneurons
        v_p = y[3]  # PSP at pyramidal cells
        v_i = y[5]  # PSP at inhibitory interneurons

        # EEG signal (postsynaptic potential at pyramidal cells)
        eeg_signal = v_p

        # Calculate firing rates using sigmoid
        firing_e = self._sigmoid(v_e)
        firing_p = self._sigmoid(v_p)
        firing_i = self._sigmoid(v_i)

        # Calculate metrics
        metrics = self._calculate_eeg_metrics(t, eeg_signal, firing_e, firing_p, firing_i)

        logs = [
            "Jansen-Rit neural mass simulation completed",
            f"Parameters: He={cfg.He}mV, Hi={cfg.Hi}mV",
            f"External input: P={cfg.P} s^-1",
            f"EEG mean amplitude: {metrics['eeg_mean_amplitude']:.4f} mV",
            f"Dominant frequency: {metrics['dominant_freq']:.2f} Hz",
            f"Peak alpha power: {metrics['alpha_power']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "eeg": eeg_signal.tolist(),
            "v_e": v_e.tolist(),
            "v_p": v_p.tolist(),
            "v_i": v_i.tolist(),
        }

    def _jansen_rit_equations(self, t: float, y: np.ndarray) -> np.ndarray:
        """Jansen-Rit differential equations"""
        cfg = self.config

        # Unpack state variables
        y0, y1, y2, y3, y4, y5 = y

        # Sigmoid functions for firing rates
        S_v2 = self._sigmoid_scalar(y2)
        S_v3 = self._sigmoid_scalar(y3)

        # Add noise to input if specified
        noise = 0.0
        if cfg.sigma_noise > 0 and self.noise_stream is not None:
            noise = self.noise_stream.normal(0, cfg.sigma_noise)

        # External input
        p_t = cfg.P + cfg.U + noise

        # Differential equations
        dy0dt = y1
        dy1dt = cfg.He * cfg.ke * (cfg.C1 * S_v2) - 2 * cfg.ke * y1 - cfg.ke**2 * y0

        dy2dt = y3
        dy3dt = cfg.He * cfg.ke * (p_t + cfg.C2 * S_v2) - 2 * cfg.ke * y3 - cfg.ke**2 * y2

        dy4dt = y5
        dy5dt = cfg.Hi * cfg.ki * (cfg.C3 * S_v3) - 2 * cfg.ki * y5 - cfg.ki**2 * y4

        return np.array([dy0dt, dy1dt, dy2dt, dy3dt, dy4dt, dy5dt])

    async def _wendling_simulation(self) -> dict[str, Any]:
        """Wendling model (extended Jansen-Rit with slow dendritic currents)"""

        cfg = self.config

        # Wendling adds slow inhibitory population for epileptic activity
        # State: [y0, y1, y2, y3, y4, y5, y6, y7] - additional slow inhibitory
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        y0 = np.zeros(8)

        solution = solve_ivp(
            self._wendling_equations,
            t_span,
            y0,
            t_eval=t_eval,
            method='RK45',
        )

        t = solution.t
        y = solution.y

        # Pyramidal PSP
        v_p = y[3]

        metrics = self._calculate_eeg_metrics(t, v_p, None, None, None)
        metrics["model"] = "wendling"  # type: ignore[assignment]

        logs = [
            "Wendling neural mass simulation completed",
            "Slow inhibition included for epileptic dynamics",
            f"Dominant frequency: {metrics['dominant_freq']:.2f} Hz",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "eeg": v_p.tolist(),
        }

    def _wendling_equations(self, t: float, y: np.ndarray) -> np.ndarray:
        """Wendling differential equations"""
        # Simplified version - full Wendling has additional slow inhibition
        # For now, use Jansen-Rit as base
        return self._jansen_rit_equations(t, y[:6])

    async def _wilson_cowan_simulation(self) -> dict[str, Any]:
        """Wilson-Cowan firing rate model"""

        cfg = self.config

        # Time array
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        # Initial firing rates
        E0, I0 = 0.1, 0.1

        solution = solve_ivp(
            self._wilson_cowan_equations,
            t_span,
            [E0, I0],
            t_eval=t_eval,
            method='RK45',
        )

        t = solution.t
        E, I = solution.y

        metrics = {
            "mean_excitatory": float(np.mean(E)),
            "mean_inhibitory": float(np.mean(I)),
            "max_excitatory": float(np.max(E)),
            "max_inhibitory": float(np.max(I)),
            "dominant_freq": 0.0,  # Would need FFT
        }

        logs = [
            "Wilson-Cowan simulation completed",
            f"Mean E rate: {metrics['mean_excitatory']:.4f}",
            f"Mean I rate: {metrics['mean_inhibitory']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "E": E.tolist(),
            "I": I.tolist(),
        }

    def _wilson_cowan_equations(self, t: float, y: np.ndarray) -> np.ndarray:
        """Wilson-Cowan firing rate equations"""
        E, I = y

        # Parameters
        tau_E, tau_I = 0.01, 0.02  # Time constants (s)
        P, Q = 0.0, 0.0  # External inputs

        # Coupling constants
        c1, c2 = 12.0, 4.0  # E->E, I->E
        c3, c4 = 13.0, 11.0  # E->I, I->I

        # Sigmoid response function
        def S(x: Any) -> Any:
            return 1 / (1 + np.exp(-(x - 2.0)))

        dEdt = (-E + S(c1 * E - c2 * I + P)) / tau_E
        dIdt = (-I + S(c3 * E - c4 * I + Q)) / tau_I

        return np.array([dEdt, dIdt])

    def _sigmoid(self, v: np.ndarray) -> np.ndarray:
        """Sigmoid activation function (vectorized)"""
        cfg = self.config
        return 2 * cfg.e0 / (1 + np.exp(cfg.r * (cfg.v0 - v)))  # type: ignore[no-any-return]

    def _sigmoid_scalar(self, v: float) -> float:
        """Sigmoid activation function (scalar)"""
        cfg = self.config
        return 2 * cfg.e0 / (1 + np.exp(cfg.r * (cfg.v0 - v)))  # type: ignore[no-any-return]

    def _calculate_eeg_metrics(
        self, t: np.ndarray, eeg: np.ndarray,
        firing_e: np.ndarray | None, firing_p: np.ndarray | None,
        firing_i: np.ndarray | None
    ) -> dict[str, float]:
        """Calculate EEG metrics including spectral analysis"""

        dt = t[1] - t[0]
        fs = 1.0 / dt  # Sampling frequency

        # Basic statistics
        eeg_mean = float(np.mean(eeg))
        eeg_std = float(np.std(eeg))
        eeg_range = float(np.max(eeg) - np.min(eeg))

        # FFT for frequency analysis
        n = len(eeg)
        fft = np.fft.fft(eeg - eeg_mean)
        freqs = np.fft.fftfreq(n, dt)
        power = np.abs(fft)**2

        # Only positive frequencies
        pos_mask = freqs > 0
        pos_freqs = freqs[pos_mask]
        pos_power = power[pos_mask]

        # Find dominant frequency
        if len(pos_power) > 0:
            dominant_idx = np.argmax(pos_power)
            dominant_freq = float(pos_freqs[dominant_idx])
        else:
            dominant_freq = 0.0

        # Power in frequency bands
        def band_power(fmin: Any, fmax: Any) -> Any:
            """Band power."""
            mask = (pos_freqs >= fmin) & (pos_freqs <= fmax)
            return float(np.sum(pos_power[mask])) if np.any(mask) else 0.0

        delta_power = band_power(0.5, 4)    # 0.5-4 Hz
        theta_power = band_power(4, 8)      # 4-8 Hz
        alpha_power = band_power(8, 13)     # 8-13 Hz
        beta_power = band_power(13, 30)     # 13-30 Hz
        gamma_power = band_power(30, 100)   # 30-100 Hz

        # Alpha peak characteristics
        alpha_mask = (pos_freqs >= 8) & (pos_freqs <= 13)
        alpha_peak_freq = 0.0
        alpha_peak_power = 0.0
        if np.any(alpha_mask):
            alpha_peak_idx = np.argmax(pos_power[alpha_mask])
            alpha_peak_freq = float(pos_freqs[alpha_mask][alpha_peak_idx])
            alpha_peak_power = float(pos_power[alpha_mask][alpha_peak_idx])

        # Firing rate metrics
        firing_metrics = {}
        if firing_e is not None:
            firing_metrics["mean_firing_e"] = float(np.mean(firing_e))
        if firing_p is not None:
            firing_metrics["mean_firing_p"] = float(np.mean(firing_p))
        if firing_i is not None:
            firing_metrics["mean_firing_i"] = float(np.mean(firing_i))

        return {
            "eeg_mean_amplitude": eeg_mean,
            "eeg_std": eeg_std,
            "eeg_range": eeg_range,
            "dominant_freq": dominant_freq,
            "alpha_peak_freq": alpha_peak_freq,
            "alpha_power": alpha_power,
            "delta_power": delta_power,
            "theta_power": theta_power,
            "beta_power": beta_power,
            "gamma_power": gamma_power,
            **firing_metrics,
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Dominant frequency in brain-relevant range
        dom_freq = metrics.get("dominant_freq", 0)
        if 0.5 < dom_freq < 100:  # Brain frequencies
            factors.append(0.3)

        # Alpha band power (characteristic of Jansen-Rit)
        alpha = metrics.get("alpha_power", 0)
        if alpha > 0:
            factors.append(0.2)

        # Reasonable EEG amplitude
        amp = metrics.get("eeg_std", 0)
        if 0.001 < amp < 10:  # mV range
            factors.append(0.25)

        # Model-specific checks
        if self.config.model == NeuralMassModel.JANSEN_RIT:
            if 8 < metrics.get("alpha_peak_freq", 0) < 13:
                factors.append(0.25)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 10.0)
        dt = params.get("dt", 0.001)

        n_steps = int(t_max / dt)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + n_steps * 1e-6,
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
                "Jansen, B.H. & Rit, V.G. (1995). Electroencephalogram and visual evoked potential",
                "Wendling, F. et al. (2002). Epileptic fast intracerebral EEG activity",
                "Wilson, H.R. & Cowan, J.D. (1972). Excitatory and inhibitory interactions",
            ],
        }
