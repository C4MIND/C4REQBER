"""
Synaptic Plasticity Pattern
Spike-Timing Dependent Plasticity (STDP) and learning models

Based on:
- STDP: Bi and Poo (1998) - Hebbian learning with timing
- BCM theory: Bienenstock, Cooper, Munro (1982)
- Oja's rule: Principal component learning
- Calcium-based models: Shouval et al. (2002)
"""

import asyncio
import logging
from dataclasses import dataclass
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


class PlasticityRule(Enum):
    """PlasticityRule."""
    STDP = "stdp"
    BCM = "bcm"
    OJA = "oja"
    CALCIUM = "calcium"


@dataclass
class SynapticPlasticityConfig:
    """Synaptic plasticity configuration"""
    # Learning rule
    rule: PlasticityRule = PlasticityRule.STDP

    # STDP parameters
    A_plus: float = 0.01  # LTP amplitude
    A_minus: float = 0.0105  # LTD amplitude
    tau_plus: float = 20.0  # LTP time constant (ms)
    tau_minus: float = 20.0  # LTD time constant (ms)
    w_min: float = 0.0  # Minimum weight
    w_max: float = 1.0  # Maximum weight

    # BCM parameters
    theta_M: float = 0.01  # Modification threshold
    tau_theta: float = 10.0  # Threshold adaptation (s)

    # Oja parameters
    alpha: float = 1.0  # Learning rate
    gamma: float = 0.01  # Decay rate

    # Calcium parameters
    C_pre: float = 1.0  # Presynaptic calcium contribution
    C_post: float = 2.0  # Postsynaptic calcium contribution
    tau_Ca: float = 20.0  # Calcium decay (ms)
    theta_p: float = 1.5  # Potentiation threshold
    theta_d: float = 1.0  # Depression threshold

    # Simulation
    num_pre: int = 100  # Number of presynaptic neurons
    num_post: int = 10  # Number of postsynaptic neurons
    simulation_time: float = 10000.0  # ms
    dt: float = 0.1  # ms
    input_rate: float = 10.0  # Hz - baseline firing rate
    correlation: float = 0.1  # Input correlation

    # Protocol
    protocol: str = "poisson"  # poisson, theta_burst, pairing

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule.value,
            "A_plus": self.A_plus,
            "A_minus": self.A_minus,
            "tau_plus": self.tau_plus,
            "tau_minus": self.tau_minus,
            "w_min": self.w_min,
            "w_max": self.w_max,
            "theta_M": self.theta_M,
            "tau_theta": self.tau_theta,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "C_pre": self.C_pre,
            "C_post": self.C_post,
            "tau_Ca": self.tau_Ca,
            "theta_p": self.theta_p,
            "theta_d": self.theta_d,
            "num_pre": self.num_pre,
            "num_post": self.num_post,
            "simulation_time": self.simulation_time,
            "dt": self.dt,
            "input_rate": self.input_rate,
            "correlation": self.correlation,
            "protocol": self.protocol,
        }


@simulation_pattern(
    id="synaptic_plasticity",
    name="Synaptic Plasticity (STDP)",
    category="neuroscience",
    description="Spike-timing dependent plasticity and Hebbian learning simulation",
)
class SynapticPlasticityPattern(SimulationPattern):
    """
    Synaptic plasticity models for learning and memory

    Simulates how synaptic weights change based on pre- and postsynaptic
    activity patterns. Implements multiple learning rules:

    1. STDP: Spike-Timing Dependent Plasticity
       - Potentiation when presynaptic spike precedes postsynaptic
       - Depression when postsynaptic precedes presynaptic

    2. BCM: Bienenstock-Cooper-Munro theory
       - Sliding threshold for homeostasis
       - Rate-based plasticity

    3. Oja's rule: Hebbian learning with normalization
       - Principal component extraction
       - Stable weight dynamics

    4. Calcium-based: Biophysical plasticity model
       - NMDA receptor-mediated calcium influx
       - Threshold-dependent LTP/LTD
    """

    parameters = [
        SimulationParameter(
            name="rule",
            type="select",
            default="stdp",
            options=["stdp", "bcm", "oja", "calcium"],
            description="Plasticity learning rule",
        ),
        SimulationParameter(
            name="A_plus",
            type="float",
            default=0.01,
            min=0.0,
            max=0.1,
            description="STDP LTP amplitude",
        ),
        SimulationParameter(
            name="A_minus",
            type="float",
            default=0.0105,
            min=0.0,
            max=0.1,
            description="STDP LTD amplitude",
        ),
        SimulationParameter(
            name="tau_plus",
            type="float",
            default=20.0,
            min=1.0,
            max=100.0,
            description="LTP time constant (ms)",
        ),
        SimulationParameter(
            name="tau_minus",
            type="float",
            default=20.0,
            min=1.0,
            max=100.0,
            description="LTD time constant (ms)",
        ),
        SimulationParameter(
            name="num_pre",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Number of presynaptic neurons",
        ),
        SimulationParameter(
            name="num_post",
            type="int",
            default=10,
            min=1,
            max=100,
            description="Number of postsynaptic neurons",
        ),
        SimulationParameter(
            name="simulation_time",
            type="float",
            default=10000.0,
            min=1000.0,
            max=100000.0,
            description="Simulation duration (ms)",
        ),
        SimulationParameter(
            name="input_rate",
            type="float",
            default=10.0,
            min=0.1,
            max=100.0,
            description="Input firing rate (Hz)",
        ),
        SimulationParameter(
            name="protocol",
            type="select",
            default="poisson",
            options=["poisson", "theta_burst", "pairing"],
            description="Stimulation protocol",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: SynapticPlasticityConfig = SynapticPlasticityConfig()
        self.rng = np.random.default_rng(seed=42)

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if plasticity model can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "plasticity", "stdp", "hebbian", "learning", "memory",
            "synapse", "potentiation", "depression", "ltp", "ltd",
            "spike timing", "bcm", "oja", "correlation", "causal",
            "weight", "training", "associative", "homosynaptic",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute synaptic plasticity simulation"""
        start_time = datetime.now()
        simulation_id = f"sp_{start_time.timestamp()}"

        logger.info(f"Starting synaptic plasticity simulation {simulation_id}")

        try:
            # Parse configuration
            self.config = self._parse_config(config)

            # Run simulation based on rule type
            if self.config.rule == PlasticityRule.STDP:
                results = await self._stdp_simulation()
            elif self.config.rule == PlasticityRule.BCM:
                results = await self._bcm_simulation()
            elif self.config.rule == PlasticityRule.OJA:
                results = await self._oja_simulation()
            else:
                results = await self._calcium_simulation()

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
            logger.exception("Synaptic plasticity simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> SynapticPlasticityConfig:
        """Parse configuration dictionary"""
        cfg = SynapticPlasticityConfig()

        if "rule" in config:
            cfg.rule = PlasticityRule(config["rule"])
        if "A_plus" in config:
            cfg.A_plus = float(config["A_plus"])
        if "A_minus" in config:
            cfg.A_minus = float(config["A_minus"])
        if "tau_plus" in config:
            cfg.tau_plus = float(config["tau_plus"])
        if "tau_minus" in config:
            cfg.tau_minus = float(config["tau_minus"])
        if "w_min" in config:
            cfg.w_min = float(config["w_min"])
        if "w_max" in config:
            cfg.w_max = float(config["w_max"])
        if "num_pre" in config:
            cfg.num_pre = int(config["num_pre"])
        if "num_post" in config:
            cfg.num_post = int(config["num_post"])
        if "simulation_time" in config:
            cfg.simulation_time = float(config["simulation_time"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "input_rate" in config:
            cfg.input_rate = float(config["input_rate"])
        if "correlation" in config:
            cfg.correlation = float(config["correlation"])
        if "protocol" in config:
            cfg.protocol = config["protocol"]

        return cfg

    async def _stdp_simulation(self) -> dict[str, Any]:
        """Spike-Timing Dependent Plasticity simulation"""

        cfg = self.config

        # Initialize weights
        weights = self.rng.uniform(0.1, 0.5, (cfg.num_pre, cfg.num_post))
        weight_history = [weights.copy()]

        # Time steps
        n_steps = int(cfg.simulation_time / cfg.dt)

        # Spike traces for STDP
        pre_trace = np.zeros(cfg.num_pre)
        post_trace = np.zeros(cfg.num_post)

        # Spike times storage
        pre_spikes_all = []
        post_spikes_all = []

        # Run simulation
        for step in range(n_steps):
            step * cfg.dt

            # Generate Poisson spikes
            pre_spikes = self.rng.random(cfg.num_pre) < (cfg.input_rate * cfg.dt / 1000)

            # Postsynaptic activity (weighted sum + threshold)
            post_input = weights.T @ pre_spikes.astype(float)
            post_spikes = post_input > 0.5  # Simple threshold

            # Update traces
            pre_trace = pre_trace * np.exp(-cfg.dt / cfg.tau_plus) + pre_spikes.astype(float)
            post_trace = post_trace * np.exp(-cfg.dt / cfg.tau_minus) + post_spikes.astype(float)

            # STDP weight update
            for i in range(cfg.num_pre):
                for j in range(cfg.num_post):
                    # LTP: pre before post
                    if pre_spikes[i]:
                        dw = cfg.A_plus * post_trace[j]
                        weights[i, j] += dw

                    # LTD: post before pre
                    if post_spikes[j]:
                        dw = -cfg.A_minus * pre_trace[i]
                        weights[i, j] += dw

            # Hard bounds
            weights = np.clip(weights, cfg.w_min, cfg.w_max)

            # Store spike times
            pre_spikes_all.append(np.where(pre_spikes)[0])
            post_spikes_all.append(np.where(post_spikes)[0])

            # Record weight history (every 100ms)
            if step % 1000 == 0:
                weight_history.append(weights.copy())

            # Yield control
            if step % 10000 == 0:
                await asyncio.sleep(0)

        # Calculate metrics
        metrics = self._calculate_plasticity_metrics(weights, weight_history, pre_spikes_all, post_spikes_all)

        logs = [
            "STDP simulation completed",
            f"Rule: A+={cfg.A_plus}, A-={cfg.A_minus}, tau+={cfg.tau_plus}ms",
            f"Network: {cfg.num_pre} pre → {cfg.num_post} post",
            f"Initial mean weight: {metrics['initial_mean_weight']:.4f}",
            f"Final mean weight: {metrics['final_mean_weight']:.4f}",
            f"Weight change: {metrics['weight_change_percent']:.2f}%",
            f"Weight variance: {metrics['final_weight_variance']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "final_weights": weights.tolist(),
            "weight_history": [w.tolist() for w in weight_history],
        }

    async def _bcm_simulation(self) -> dict[str, Any]:
        """BCM theory simulation"""

        cfg = self.config

        # Initialize
        weights = self.rng.uniform(0.1, 0.5, cfg.num_pre)
        theta_M = cfg.theta_M  # Modification threshold

        n_steps = int(cfg.simulation_time / cfg.dt)

        # Run simulation
        for step in range(n_steps):
            # Generate input pattern
            x = self.rng.random(cfg.num_pre) < (cfg.input_rate * cfg.dt / 1000)
            x = x.astype(float)

            # Postsynaptic response
            y = np.dot(weights, x)

            # Update threshold (homeostasis)
            theta_M += cfg.dt / 1000 / cfg.tau_theta * (y**2 - theta_M)

            # BCM weight update
            dw = cfg.alpha * x * y * (y - theta_M)
            weights += dw * cfg.dt

            # Bounds
            weights = np.clip(weights, cfg.w_min, cfg.w_max)

            if step % 10000 == 0:
                await asyncio.sleep(0)

        metrics = {
            "final_mean_weight": float(np.mean(weights)),
            "final_weight_variance": float(np.var(weights)),
            "final_threshold": float(theta_M),
            "rule": "bcm",
        }

        logs = [
            "BCM simulation completed",
            f"Final threshold theta_M: {theta_M:.4f}",
            f"Mean weight: {metrics['final_mean_weight']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "final_weights": weights.tolist(),
        }

    async def _oja_simulation(self) -> dict[str, Any]:
        """Oja's learning rule simulation"""

        cfg = self.config

        # Initialize
        weights = self.rng.uniform(0.1, 0.5, cfg.num_pre)

        n_steps = int(cfg.simulation_time / cfg.dt)

        for step in range(n_steps):
            # Generate correlated input
            x = self.rng.random(cfg.num_pre) < (cfg.input_rate * cfg.dt / 1000)
            x = x.astype(float)

            # Postsynaptic response
            y = np.dot(weights, x)

            # Oja's rule with normalization
            dw = cfg.alpha * (y * x - cfg.gamma * y**2 * weights)
            weights += dw * cfg.dt

            # Soft bounds
            weights = np.clip(weights, cfg.w_min, cfg.w_max)

            if step % 10000 == 0:
                await asyncio.sleep(0)

        metrics = {
            "final_mean_weight": float(np.mean(weights)),
            "final_weight_norm": float(np.linalg.norm(weights)),
            "rule": "oja",
        }

        logs = [
            "Oja simulation completed",
            f"Final weight norm: {metrics['final_weight_norm']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "final_weights": weights.tolist(),
        }

    async def _calcium_simulation(self) -> dict[str, Any]:
        """Calcium-based plasticity model"""

        cfg = self.config

        # Initialize
        weights = self.rng.uniform(0.3, 0.7, (cfg.num_pre, cfg.num_post))
        calcium = np.zeros((cfg.num_pre, cfg.num_post))

        n_steps = int(cfg.simulation_time / cfg.dt)

        for step in range(n_steps):
            # Generate spikes
            pre_spikes = self.rng.random(cfg.num_pre) < (cfg.input_rate * cfg.dt / 1000)

            # Postsynaptic activity
            post_input = weights.T @ pre_spikes.astype(float)
            post_spikes = post_input > 0.3

            # Update calcium for each synapse
            for i in range(cfg.num_pre):
                for j in range(cfg.num_post):
                    # Calcium influx
                    dCa = -calcium[i, j] / cfg.tau_Ca * cfg.dt

                    if pre_spikes[i]:
                        dCa += cfg.C_pre
                    if post_spikes[j]:
                        dCa += cfg.C_post

                    calcium[i, j] += dCa

                    # Weight update based on calcium levels
                    if calcium[i, j] > cfg.theta_p:
                        # Potentiation
                        weights[i, j] += 0.001 * (1 - weights[i, j])
                    elif calcium[i, j] > cfg.theta_d:
                        # Depression
                        weights[i, j] -= 0.001 * weights[i, j]

            weights = np.clip(weights, cfg.w_min, cfg.w_max)

            if step % 10000 == 0:
                await asyncio.sleep(0)

        metrics = {
            "final_mean_weight": float(np.mean(weights)),
            "mean_calcium": float(np.mean(calcium)),
            "rule": "calcium",
        }

        logs = [
            "Calcium-based plasticity simulation completed",
            f"Mean calcium level: {metrics['mean_calcium']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "final_weights": weights.tolist(),
        }

    def _calculate_plasticity_metrics(
        self, final_weights: np.ndarray,
        weight_history: list[np.ndarray],
        pre_spikes_all: list,
        post_spikes_all: list
    ) -> dict[str, float]:
        """Calculate plasticity metrics"""

        initial = weight_history[0]

        # Weight statistics
        initial_mean = float(np.mean(initial))
        final_mean = float(np.mean(final_weights))
        weight_change = ((final_mean - initial_mean) / initial_mean * 100) if initial_mean > 0 else 0

        # Distribution metrics
        final_var = float(np.var(final_weights))
        final_std = float(np.std(final_weights))

        # Weight bounds
        n_saturated = int(np.sum((final_weights <= self.config.w_min + 0.01) |
                                  (final_weights >= self.config.w_max - 0.01)))
        saturation_ratio = n_saturated / final_weights.size if final_weights.size > 0 else 0

        # Stability (last 10% of simulation)
        if len(weight_history) > 10:
            recent = np.array([np.mean(w) for w in weight_history[-10:]])
            stability = float(np.std(recent))
        else:
            stability = 0.0

        # Spike statistics
        total_pre_spikes = sum(len(s) for s in pre_spikes_all)
        total_post_spikes = sum(len(s) for s in post_spikes_all)

        return {
            "initial_mean_weight": initial_mean,
            "final_mean_weight": final_mean,
            "weight_change_percent": weight_change,
            "final_weight_variance": final_var,
            "final_weight_std": final_std,
            "saturated_synapses": n_saturated,
            "saturation_ratio": saturation_ratio,
            "stability": stability,
            "total_pre_spikes": total_pre_spikes,
            "total_post_spikes": total_post_spikes,
            "pre_rate_hz": total_pre_spikes / self.config.simulation_time * 1000 / self.config.num_pre,
            "post_rate_hz": total_post_spikes / self.config.simulation_time * 1000 / self.config.num_post,
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Weight change occurred
        change = abs(metrics.get("weight_change_percent", 0))
        if 1 < change < 100:
            factors.append(0.3)

        # Not too many saturated synapses
        sat = metrics.get("saturation_ratio", 0)
        if sat < 0.5:
            factors.append(0.25)

        # Reasonable spike rates
        pre_rate = metrics.get("pre_rate_hz", 0)
        if 0 < pre_rate < 100:
            factors.append(0.25)

        # Stability
        stab = metrics.get("stability", 1)
        if stab < 0.1:
            factors.append(0.2)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        num_pre = params.get("num_pre", 100)
        num_post = params.get("num_post", 10)
        sim_time = params.get("simulation_time", 10000)

        n_synapses = num_pre * num_post
        n_steps = int(sim_time / 0.1)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + n_synapses * 1e-5,
            "gpu_required": False,
            "estimated_time_seconds": n_steps * n_synapses / 1e7,
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
                "Bi, G.Q. & Poo, M.M. (1998). Synaptic modifications in cultured hippocampal neurons",
                "Bienenstock, E.L. et al. (1982). Theory for the development of neuron selectivity",
                "Shouval, H.Z. et al. (2002). Spike timing dependent plasticity: a consequence of Poisson firing",
            ],
        }
