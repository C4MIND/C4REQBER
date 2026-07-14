from __future__ import annotations


"""
Signal Transduction Pattern[str]
ODE-based signaling cascade and network simulation

Based on:
- MAPK cascade (Huang-Ferrell, 1996)
- GPCR signaling (Kenakin, 2009)
- Ultrasensitivity and bistability
- Adaptation and oscillations
"""

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
from .config import SignalingModel, SignalTransductionConfig
from .models import AdaptationModel, GPCRModel, MAPKModel, RepressilatorModel, ToggleSwitchModel


logger = logging.getLogger(__name__)

@simulation_pattern(
    id="signal_transduction",
    name="Signal Transduction",
    category="biology",
    description="ODE-based signaling cascade and network dynamics",
)
class SignalTransductionPattern(SimulationPattern):
    """
    Signal transduction pathway simulation

    Models cellular signaling cascades using systems of ODEs.
    Captures key signaling properties like amplification,
    ultrasensitivity, adaptation, and oscillations.

    Models supported:
    1. MAPK Cascade: Three-tier phosphorylation cascade
    2. GPCR: G-protein coupled receptor signaling
    3. Adaptation: Perfect or near-perfect adaptation
    4. Repressilator: Synthetic genetic oscillator
    5. Toggle Switch: Bistable genetic switch

    Applications:
    - Drug target identification
    - Cancer signaling studies
    - Synthetic biology design
    - Systems pharmacology
    """

    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="mapk_cascade",
            options=["mapk_cascade", "gpcr", "adaptation", "repressilator", "toggle_switch"],
            description="Signaling pathway model",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=1000.0,
            min=10.0,
            max=10000.0,
            description="Simulation duration (s)",
        ),
        SimulationParameter(
            name="E1_total",
            type="float",
            default=0.1,
            min=0.001,
            max=10.0,
            description="MAPKKK kinase (uM)",
        ),
        SimulationParameter(
            name="MAPKK_total",
            type="float",
            default=10.0,
            min=0.1,
            max=100.0,
            description="Total MAPKK (uM)",
        ),
        SimulationParameter(
            name="MAPK_total",
            type="float",
            default=10.0,
            min=0.1,
            max=100.0,
            description="Total MAPK (uM)",
        ),
        SimulationParameter(
            name="ligand_conc",
            type="float",
            default=0.1,
            min=0.0,
            max=10.0,
            description="Ligand concentration (uM)",
        ),
        SimulationParameter(
            name="stimulus_amp",
            type="float",
            default=1.0,
            min=0.0,
            max=10.0,
            description="Stimulus amplitude",
        ),
        SimulationParameter(
            name="alpha",
            type="float",
            default=250.0,
            min=10.0,
            max=1000.0,
            description="Promoter strength (repressilator)",
        ),
        SimulationParameter(
            name="beta",
            type="float",
            default=5.0,
            min=0.1,
            max=50.0,
            description="Decay ratio (repressilator)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: SignalTransductionConfig = SignalTransductionConfig()

    async def _mapk_simulation(self) -> dict[str, Any]:
        model = MAPKModel(self.config)
        return model.simulate()

    async def _gpcr_simulation(self) -> dict[str, Any]:
        model = GPCRModel(self.config)
        return model.simulate()

    async def _adaptation_simulation(self) -> dict[str, Any]:
        model = AdaptationModel(self.config)
        return model.simulate()

    async def _repressilator_simulation(self) -> dict[str, Any]:
        model = RepressilatorModel(self.config)
        return model.simulate()

    async def _toggle_switch_simulation(self) -> dict[str, Any]:
        model = ToggleSwitchModel(self.config)
        return model.simulate()

    def _mapk_dose_response(self) -> dict[str, Any]:
        model = MAPKModel(self.config)
        return model._calculate_dose_response()

    def _estimate_hill_coefficient(self, dose_response: dict[str, Any]) -> float:
        model = MAPKModel(self.config)
        return model._estimate_hill_coefficient(dose_response)

    def _find_peaks(self, t: np.ndarray, signal: np.ndarray) -> list[int]:
        from scipy.signal import find_peaks as scipy_find_peaks
        peaks, _ = scipy_find_peaks(signal)
        return peaks.tolist()

    @classmethod
    def can_simulate(cls, hypothesis: Hypothesis) -> bool:
        """Check if signal transduction can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "signaling", "transduction", "cascade", "mapk", "erk", "kinase",
            "phosphorylation", "receptor", "gpcr", "g-protein", "second messenger",
            "adaptation", "oscillation", "bistability", "ultrasensitive",
            "synthetic biology", "repressilator", "toggle", "feedback",
            "cellular response", "signal amplification",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(
        self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None
    ) -> SimulationResult:
        """Execute signal transduction simulation"""
        start_time = datetime.now()
        simulation_id = f"st_{start_time.timestamp()}"

        logger.info(f"Starting signal transduction simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)  # type: ignore[arg-type]

            if self.config.model == SignalingModel.MAPK_CASCADE:
                model = MAPKModel(self.config)
            elif self.config.model == SignalingModel.GPCR:
                model = GPCRModel(self.config)  # type: ignore[assignment]
            elif self.config.model == SignalingModel.ADAPTATION:
                model = AdaptationModel(self.config)  # type: ignore[assignment]
            elif self.config.model == SignalingModel.REPRESSILATOR:
                model = RepressilatorModel(self.config)  # type: ignore[assignment]
            else:
                model = ToggleSwitchModel(self.config)  # type: ignore[assignment]

            results = model.simulate()
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
            logger.exception("Signal transduction simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> SignalTransductionConfig:
        """Parse configuration dictionary"""
        cfg = SignalTransductionConfig()

        if "model" in config:
            cfg.model = SignalingModel(config["model"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "E1_total" in config:
            cfg.E1_total = float(config["E1_total"])
        if "E2_total" in config:
            cfg.E2_total = float(config["E2_total"])
        if "MAPKK_total" in config:
            cfg.MAPKK_total = float(config["MAPKK_total"])
        if "MAPK_total" in config:
            cfg.MAPK_total = float(config["MAPK_total"])
        if "k1" in config:
            cfg.k1 = float(config["k1"])
        if "k2" in config:
            cfg.k2 = float(config["k2"])
        if "k3" in config:
            cfg.k3 = float(config["k3"])
        if "k4" in config:
            cfg.k4 = float(config["k4"])
        if "R_total" in config:
            cfg.R_total = float(config["R_total"])
        if "G_total" in config:
            cfg.G_total = float(config["G_total"])
        if "ligand_conc" in config:
            cfg.ligand_conc = float(config["ligand_conc"])
        if "stimulus_amp" in config:
            cfg.stimulus_amp = float(config["stimulus_amp"])
        if "stimulus_duration" in config:
            cfg.stimulus_duration = float(config["stimulus_duration"])
        if "adaptation_rate" in config:
            cfg.adaptation_rate = float(config["adaptation_rate"])
        if "n_genes" in config:
            cfg.n_genes = int(config["n_genes"])
        if "alpha" in config:
            cfg.alpha = float(config["alpha"])
        if "beta" in config:
            cfg.beta = float(config["beta"])
        if "n_hill" in config:
            cfg.n_hill = float(config["n_hill"])
        if "gamma" in config:
            cfg.gamma = float(config["gamma"])
        if "K" in config:
            cfg.K = float(config["K"])

        return cfg

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        if self.config.model == SignalingModel.MAPK_CASCADE:
            if metrics.get("amplification_factor", 0) > 1:
                factors.append(0.4)
            if metrics.get("hill_coefficient", 1) > 1:
                factors.append(0.3)

        elif self.config.model == SignalingModel.REPRESSILATOR:
            if metrics.get("oscillation_detected", False):
                factors.append(0.7)

        elif self.config.model == SignalingModel.TOGGLE_SWITCH:
            if metrics.get("bistable", False):
                factors.append(0.7)

        elif self.config.model == SignalingModel.ADAPTATION:
            if metrics.get("adaptation_quality") == "perfect":
                factors.append(0.7)

        factors.append(0.25)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis | None = None) -> dict[str, Any]:
        """Estimate resources."""
        if hypothesis is None:
            return {}
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 1000.0)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": 1 + t_max / 1000,
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
                "Huang, C.Y. & Ferrell, J.E. (1996). Ultrasensitivity in the MAPK cascade",
                "Elowitz, M.B. & Leibler, S. (2000). A synthetic oscillatory network",
                "Gardner, T.S. et al. (2000). Construction of a genetic toggle switch",
            ],
        }
