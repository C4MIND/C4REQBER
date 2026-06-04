"""
Connectome Pattern[str]
Main pattern class for brain network dynamics simulation.
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
from .config import ConnectomeConfig, NetworkModel
from .core import ConnectomeSimulator


logger = logging.getLogger(__name__)

@simulation_pattern(
    id="connectome",
    name="Connectome Network Dynamics",
    category="neuroscience",
    description="Large-scale brain network dynamics on structural connectivity",
)
class ConnectomePattern(SimulationPattern):
    """
    Whole-brain connectome dynamics simulation

    Simulates neural activity across the brain's structural connectivity
    network to study resting-state networks, functional connectivity,
    and network dynamics.

    Models supported:
    1. Kuramoto: Phase oscillator model for synchronization
    2. Wilson-Cowan: Firing rate model with excitation/inhibition
    3. Hopf: Normal form of supercritical Hopf bifurcation
    4. FitzHugh-Nagumo: Simplified action potential model

    Applications:
    - Resting-state fMRI simulation
    - Functional connectivity analysis
    - Network perturbation/stimulation
    - Disease modeling (AD, Parkinson's)
    """

    parameters = [
        SimulationParameter(
            name="num_regions",
            type="int",
            default=68,
            min=10,
            max=1000,
            description="Number of brain regions (nodes)",
        ),
        SimulationParameter(
            name="model",
            type="select",
            default="kuramoto",
            options=["kuramoto", "wilson_cowan", "hopf", "fitzhugh_nagumo"],
            description="Network dynamics model",
        ),
        SimulationParameter(
            name="coupling_strength",
            type="float",
            default=0.5,
            min=0.0,
            max=2.0,
            description="Global coupling strength",
        ),
        SimulationParameter(
            name="noise_level",
            type="float",
            default=0.01,
            min=0.0,
            max=1.0,
            description="Intrinsic noise amplitude",
        ),
        SimulationParameter(
            name="omega_mean",
            type="float",
            default=40.0,
            min=1.0,
            max=100.0,
            description="Mean intrinsic frequency (Hz)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=60.0,
            min=10.0,
            max=600.0,
            description="Simulation duration (seconds)",
        ),
        SimulationParameter(
            name="stimulation_site",
            type="int",
            default=-1,
            min=-1,
            max=999,
            description="Stimulated region (-1 for none)",
        ),
        SimulationParameter(
            name="stimulation_amp",
            type="float",
            default=0.0,
            min=0.0,
            max=10.0,
            description="Stimulation amplitude",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: ConnectomeConfig = ConnectomeConfig()
        self.rng = np.random.default_rng(seed=42)
        self.structural_connectivity = None
        self._simulator: ConnectomeSimulator | None = None

    def _generate_connectivity(self) -> np.ndarray:
        if self._simulator is None:
            self._simulator = ConnectomeSimulator(self.config, self.rng)
        sc = self._simulator.generate_connectivity()
        self.structural_connectivity = sc
        return sc

    def _calculate_fc_kuramoto(self, theta: np.ndarray) -> np.ndarray:
        n_time, n_regions = theta.shape
        fc = np.zeros((n_regions, n_regions))
        for i in range(n_regions):
            for j in range(i + 1, n_regions):
                phase_diff = theta[:, i] - theta[:, j]
                plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                fc[i, j] = plv
                fc[j, i] = plv
        return fc

    def _calculate_order_parameters(self, theta: np.ndarray, sc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n_time, n_regions = theta.shape
        r_global = np.zeros(n_time)
        r_local = np.zeros(n_time)
        for t in range(n_time):
            z = np.mean(np.exp(1j * theta[t, :]))
            r_global[t] = np.abs(z)
            r_local[t] = np.abs(z)
        return r_global, r_local

    def _calculate_network_metrics(self, activity: np.ndarray, fc: np.ndarray, sc: np.ndarray,
                                    r_global: np.ndarray, r_local: np.ndarray) -> dict[str, Any]:
        n = sc.shape[0]
        sc_flat = sc[np.triu_indices(n, k=1)]
        fc_flat = fc[np.triu_indices(n, k=1)]
        mask = (sc_flat > 0) & (fc_flat > 0)
        if np.sum(mask) > 1:
            sc_fc_corr = float(np.corrcoef(sc_flat[mask], fc_flat[mask])[0, 1])
        else:
            sc_fc_corr = 0.0
        return {
            "sc_fc_correlation": sc_fc_corr if not np.isnan(sc_fc_corr) else 0.0,
            "fc_mean": float(np.mean(fc)),
            "fc_variance": float(np.var(fc)),
            "fc_std": float(np.std(fc)),
            "sc_density": float(np.mean(sc > 0)),
            "mean_order_parameter": float(np.mean(r_global)),
            "metastability": float(np.std(r_global)),
            "integration": float(np.mean(fc)),
            "segregation": float(np.mean(np.diag(fc))),
        }

    @classmethod
    def can_simulate(cls, hypothesis: Hypothesis) -> bool:
        """Check if connectome can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "connectome", "connectivity", "network", "brain", "rsn",
            "resting state", "functional connectivity", "structural connectivity",
            "fmri", "meg", "eeg", "synchronization", "kuramoto",
            "graph", "node", "edge", "community", "module",
            "stimulation", "tms", "tdcs", "perturbation",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(
        self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None
    ) -> SimulationResult:
        """Execute connectome simulation"""
        start_time = datetime.now()
        simulation_id = f"conn_{start_time.timestamp()}"

        logger.info(f"Starting connectome simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)  # type: ignore[arg-type]

            simulator = ConnectomeSimulator(self.config, self.rng)
            simulator.generate_connectivity()

            if self.config.model == NetworkModel.KURAMOTO:
                results = await simulator.run_kuramoto()
            elif self.config.model == NetworkModel.WILSON_COWAN:
                results = await simulator.run_wilson_cowan()
            elif self.config.model == NetworkModel.HOPF:
                results = await simulator.run_hopf()
            else:
                results = await simulator.run_fitzhugh_nagumo()

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
            logger.exception("Connectome simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> ConnectomeConfig:
        """Parse configuration dictionary"""
        cfg = ConnectomeConfig()

        if "num_regions" in config:
            cfg.num_regions = int(config["num_regions"])
        if "connection_density" in config:
            cfg.connection_density = float(config["connection_density"])
        if "model" in config:
            cfg.model = NetworkModel(config["model"])
        if "coupling_strength" in config:
            cfg.coupling_strength = float(config["coupling_strength"])
        if "noise_level" in config:
            cfg.noise_level = float(config["noise_level"])
        if "omega_mean" in config:
            cfg.omega_mean = float(config["omega_mean"])
        if "omega_std" in config:
            cfg.omega_std = float(config["omega_std"])
        if "tau_exc" in config:
            cfg.tau_exc = float(config["tau_exc"])
        if "tau_inh" in config:
            cfg.tau_inh = float(config["tau_inh"])
        if "a" in config:
            cfg.a = float(config["a"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "transient" in config:
            cfg.transient = float(config["transient"])
        if "fmin" in config:
            cfg.fmin = float(config["fmin"])
        if "fmax" in config:
            cfg.fmax = float(config["fmax"])
        if "stimulation_site" in config:
            site = config["stimulation_site"]
            cfg.stimulation_site = int(site) if site >= 0 else None
        if "stimulation_amp" in config:
            cfg.stimulation_amp = float(config["stimulation_amp"])
        if "stimulation_freq" in config:
            cfg.stimulation_freq = float(config["stimulation_freq"])

        return cfg

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        fc_mean = metrics.get("fc_mean", 0)
        if 0 < fc_mean < 1:
            factors.append(0.3)

        sc_fc = metrics.get("sc_fc_correlation", 0)
        if 0 < sc_fc < 1:
            factors.append(0.3)

        order = metrics.get("mean_order_parameter", 0.5)
        if 0.1 < order < 0.9:
            factors.append(0.2)

        activity = metrics.get("mean_activity", 0)
        if activity > 0:
            factors.append(0.2)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis | None = None) -> dict[str, Any]:
        """Estimate resources."""
        if hypothesis is None:
            return {}
        """Estimate computational resources"""
        params = hypothesis.parameters
        N = params.get("num_regions", 68)
        t_max = params.get("t_max", 60)
        dt = params.get("dt", 0.001)

        n_steps = int(t_max / dt)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + N * N * 1e-5,
            "gpu_required": False,
            "estimated_time_seconds": n_steps * N / 1e5,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": getattr(cls, 'id', ''),
            "name": getattr(cls, 'name', ''),
            "category": getattr(cls, 'category', ''),
            "description": getattr(cls, 'description', ''),
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
                "Hagmann, P. et al. (2008). Mapping the structural core of human cerebral cortex",
                "Honey, C.J. et al. (2009). Predicting human resting-state functional connectivity",
                "Deco, G. et al. (2013). RSNs emerge from collective dynamics",
            ],
        }
