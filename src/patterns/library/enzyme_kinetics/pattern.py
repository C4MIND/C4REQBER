"""
Enzyme Kinetics Pattern[str]
Main pattern class for enzyme kinetics simulation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ...core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)
from .config import EnzymeKineticsConfig, KineticModel
from .core import EnzymeKineticsSimulator


logger = logging.getLogger(__name__)

@simulation_pattern(
    id="enzyme_kinetics",
    name="Enzyme Kinetics",
    category="biology",
    description="Michaelis-Menten and advanced enzyme kinetics simulation",
)
class EnzymeKineticsPattern(SimulationPattern):
    """
    Enzyme kinetics simulation for biochemical reactions

    Models enzyme-catalyzed reactions with various kinetic formalisms:

    1. Michaelis-Menten: Classic steady-state approximation
    2. Briggs-Haldane: Individual rate constants
    3. Competitive Inhibition: Reversible inhibitor binding
    4. Hill Equation: Cooperative binding (sigmoid kinetics)
    5. MWC: Allosteric regulation model

    Applications:
    - Drug metabolism (CYP450 enzymes)
    - Metabolic pathway modeling
    - Enzyme inhibitor screening
    - Bioprocess optimization
    """

    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="michaelis_menten",
            options=["michaelis_menten", "briggs_haldane", "competitive_inhibition", "hill", "mwc"],
            description="Kinetic model type",
        ),
        SimulationParameter(
            name="Vmax",
            type="float",
            default=100.0,
            min=0.1,
            max=10000.0,
            description="Maximum reaction rate (uM/s)",
        ),
        SimulationParameter(
            name="Km",
            type="float",
            default=50.0,
            min=0.1,
            max=10000.0,
            description="Michaelis constant (uM)",
        ),
        SimulationParameter(
            name="E0",
            type="float",
            default=1.0,
            min=0.01,
            max=1000.0,
            description="Enzyme concentration (uM)",
        ),
        SimulationParameter(
            name="S0",
            type="float",
            default=100.0,
            min=0.0,
            max=10000.0,
            description="Substrate concentration (uM)",
        ),
        SimulationParameter(
            name="I0",
            type="float",
            default=0.0,
            min=0.0,
            max=10000.0,
            description="Inhibitor concentration (uM)",
        ),
        SimulationParameter(
            name="Ki",
            type="float",
            default=10.0,
            min=0.1,
            max=10000.0,
            description="Inhibition constant (uM)",
        ),
        SimulationParameter(
            name="n",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Hill coefficient",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=100.0,
            min=1.0,
            max=1000.0,
            description="Simulation duration (s)",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: EnzymeKineticsConfig = EnzymeKineticsConfig()
        self._simulator: EnzymeKineticsSimulator | None = None

    async def _michaelis_menten_simulation(self) -> dict[str, Any]:
        if self._simulator is None:
            self._simulator = EnzymeKineticsSimulator(self.config)
        self._simulator.config = self.config
        return self._simulator._michaelis_menten_simulation()

    async def _briggs_haldane_simulation(self) -> dict[str, Any]:
        if self._simulator is None:
            self._simulator = EnzymeKineticsSimulator(self.config)
        self._simulator.config = self.config
        return self._simulator._briggs_haldane_simulation()

    async def _competitive_inhibition_simulation(self) -> dict[str, Any]:
        if self._simulator is None:
            self._simulator = EnzymeKineticsSimulator(self.config)
        self._simulator.config = self.config
        return self._simulator._competitive_inhibition_simulation()

    async def _hill_simulation(self) -> dict[str, Any]:
        if self._simulator is None:
            self._simulator = EnzymeKineticsSimulator(self.config)
        self._simulator.config = self.config
        return self._simulator._hill_simulation()

    async def _mwc_simulation(self) -> dict[str, Any]:
        if self._simulator is None:
            self._simulator = EnzymeKineticsSimulator(self.config)
        self._simulator.config = self.config
        return self._simulator._mwc_simulation()

    def _calculate_mm_metrics(self, t: Any, S: Any, P: Any, v: Any, S_range: Any, v_curve: Any) -> dict[str, float]:
        if self._simulator is None:
            self._simulator = EnzymeKineticsSimulator(self.config)
        return self._simulator._calculate_mm_metrics(t, S, P, v, S_range, v_curve)

    @classmethod
    def can_simulate(cls, hypothesis: Hypothesis) -> bool:
        """Check if enzyme kinetics can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "enzyme", "kinetics", "michaelis", "menten", "substrate",
            "product", "catalysis", "inhibition", "reaction rate",
            "km", "vmax", "hill", "cooperative", "allosteric",
            "metabolism", "biochemical", "pathway", "cyp",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(
        self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None
    ) -> SimulationResult:
        """Execute enzyme kinetics simulation"""
        start_time = datetime.now()
        simulation_id = f"ek_{start_time.timestamp()}"

        logger.info(f"Starting enzyme kinetics simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)  # type: ignore[arg-type]
            simulator = EnzymeKineticsSimulator(self.config)
            results = simulator.simulate()

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
            logger.exception("Enzyme kinetics simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> EnzymeKineticsConfig:
        """Parse configuration dictionary"""
        cfg = EnzymeKineticsConfig()

        if "model" in config:
            cfg.model = KineticModel(config["model"])
        if "Vmax" in config:
            cfg.Vmax = float(config["Vmax"])
        if "Km" in config:
            cfg.Km = float(config["Km"])
        if "E0" in config:
            cfg.E0 = float(config["E0"])
        if "S0" in config:
            cfg.S0 = float(config["S0"])
        if "P0" in config:
            cfg.P0 = float(config["P0"])
        if "ES0" in config:
            cfg.ES0 = float(config["ES0"])
        if "k1" in config:
            cfg.k1 = float(config["k1"])
        if "k_1" in config:
            cfg.k_1 = float(config["k_1"])
        if "k2" in config:
            cfg.k2 = float(config["k2"])
        if "I0" in config:
            cfg.I0 = float(config["I0"])
        if "Ki" in config:
            cfg.Ki = float(config["Ki"])
        if "n" in config:
            cfg.n = float(config["n"])
        if "Kd" in config:
            cfg.Kd = float(config["Kd"])
        if "L" in config:
            cfg.L = float(config["L"])
        if "c" in config:
            cfg.c = float(config["c"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "num_points" in config:
            cfg.num_points = int(config["num_points"])

        return cfg

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Reaction proceeded
        extent = metrics.get("reaction_extent", 0)
        if 0.01 < extent < 1.0:
            factors.append(0.3)

        # Fitted parameters reasonable
        fitted_km = metrics.get("fitted_Km", 0)
        if 0.1 < fitted_km < 10000:
            factors.append(0.25)

        # Positive concentrations
        if metrics.get("final_product", 0) >= 0:
            factors.append(0.25)

        # Model-specific checks
        if self.config.model == KineticModel.MICHAELIS_MENTEN:
            input_km = metrics.get("input_Km", 0)
            if abs(fitted_km - input_km) / (input_km + 1) < 0.5:
                factors.append(0.2)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis | None = None) -> dict[str, Any]:
        """Estimate resources."""
        if hypothesis is None:
            return {}
        """Estimate computational resources"""
        params = hypothesis.parameters
        t_max = params.get("t_max", 100.0)
        num_points = params.get("num_points", 20)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": 1 + t_max / 100 + num_points / 10,
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
                "Michaelis, L. & Menten, M. (1913). Die Kinetik der Invertinwirkung",
                "Briggs, G.E. & Haldane, J.B.S. (1925). A note on the kinetics of enzyme action",
                "Monod, J. et al. (1965). On the nature of allosteric transitions",
            ],
        }
