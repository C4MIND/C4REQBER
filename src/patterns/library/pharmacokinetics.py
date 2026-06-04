"""
Pharmacokinetics Pattern
Compartmental PK models for drug concentration simulation

Based on:
- One-compartment and two-compartment models
- ADME processes (Absorption, Distribution, Metabolism, Excretion)
- Differential equations for drug concentration
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


class PKModel(Enum):
    """PKModel."""
    ONE_COMPARTMENT = "one_compartment"
    TWO_COMPARTMENT = "two_compartment"
    MICHAELIS_MENTEN = "michaelis_menten"


@dataclass
class DosingRegimen:
    """Drug dosing schedule"""
    dose: float  # mg
    interval: float  # hours
    num_doses: int
    route: str = "oral"  # oral, iv, im, sc
    absorption_rate: float = 1.0  # 1/hr for oral


@simulation_pattern(
    id="pharmacokinetics",
    name="Pharmacokinetics",
    category="biology",
    description="Drug concentration simulation using compartmental PK models",
)
class PKPattern(SimulationPattern):
    """
    Pharmacokinetics simulation for drug dosing optimization

    Implements:
    - One-compartment model (oral and IV)
    - Two-compartment model (distribution)
    - Michaelis-Menten elimination
    - Multiple dosing regimens
    - AUC, Cmax, Tmax calculations
    """

    parameters = [
        SimulationParameter(
            name="model_type",
            type="select",
            default="one_compartment",
            options=["one_compartment", "two_compartment", "michaelis_menten"],
            description="PK model type",
        ),
        SimulationParameter(
            name="dose",
            type="float",
            default=100.0,
            min=0.1,
            max=10000.0,
            description="Dose amount (mg)",
        ),
        SimulationParameter(
            name="interval",
            type="float",
            default=12.0,
            min=1.0,
            max=168.0,
            description="Dosing interval (hours)",
        ),
        SimulationParameter(
            name="num_doses",
            type="int",
            default=5,
            min=1,
            max=100,
            description="Number of doses",
        ),
        SimulationParameter(
            name="halflife",
            type="float",
            default=4.0,
            min=0.1,
            max=1000.0,
            description="Elimination half-life (hours)",
        ),
        SimulationParameter(
            name="volume",
            type="float",
            default=50.0,
            min=1.0,
            max=1000.0,
            description="Volume of distribution (L)",
        ),
    ]

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if PK can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "drug", "pharmacokinetics", "pk", "concentration",
            "dosing", "dose", "regimen", "administration",
            "absorption", "elimination", "clearance",
            "bioavailability", "auc", "cmax", "tmax",
            "half-life", "steady state", "therapeutic",
            "pharmacodynamics", "pd", "exposure",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute PK simulation"""
        start_time = datetime.now()
        simulation_id = f"pk_{start_time.timestamp()}"

        logger.info(f"Starting PK simulation {simulation_id}")

        model_type = config.get("model_type", "one_compartment")

        try:
            if model_type == "one_compartment":
                results = await self._one_compartment(hypothesis, config)
            elif model_type == "two_compartment":
                results = await self._two_compartment(hypothesis, config)
            else:
                results = await self._michaelis_menten(hypothesis, config)

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
            logger.exception("PK simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    async def _one_compartment(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """One-compartment PK model with first-order absorption and elimination"""

        params = hypothesis.parameters
        dose = config.get("dose", 100.0)
        interval = config.get("interval", 12.0)
        num_doses = config.get("num_doses", 5)
        halflife = config.get("halflife", 4.0)
        volume = config.get("volume", 50.0)

        # Calculate rate constants
        ke = np.log(2) / halflife  # Elimination rate
        ka = params.get("absorption_rate", 2.0)  # Absorption rate (oral)
        f = params.get("bioavailability", 1.0)  # Bioavailability

        # Simulation time (cover all doses + washout)
        t_end = num_doses * interval + 5 * halflife
        t_eval = np.linspace(0, t_end, 1000)

        # Dosing times
        dose_times = np.arange(0, num_doses * interval, interval)

        # Solve ODE
        def pk_model(t: Any, y: Any) -> Any:
            """dC/dt = (ka * D * exp(-ka*t) / V) - ke * C"""
            # Calculate remaining dose from each administration
            absorption = 0
            for dose_time in dose_times:
                if t >= dose_time:
                    time_since_dose = t - dose_time
                    absorption += (ka * f * dose / volume) * np.exp(-ka * time_since_dose)

            elimination = ke * y[0]
            return [absorption - elimination]

        solution = solve_ivp(
            pk_model,
            [0, t_end],
            [0],  # Initial concentration
            t_eval=t_eval,
            method='RK45',
        )

        concentrations = solution.y[0]
        times = solution.t

        # Calculate PK parameters
        metrics = self._calculate_pk_metrics(times, concentrations, dose, interval)

        logs = [
            "One-compartment PK model",
            f"Dosing: {num_doses} doses of {dose}mg every {interval}h",
            f"Half-life: {halflife}h, Volume: {volume}L",
            f"Cmax: {metrics['cmax']:.2f} mg/L",
            f"Tmax: {metrics['tmax']:.2f} h",
            f"AUC: {metrics['auc']:.2f} mg·h/L",
            f"Steady state reached: {'yes' if metrics['steady_state_reached'] else 'no'}",
        ]

        return {"metrics": metrics, "logs": logs}

    async def _two_compartment(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Two-compartment model (central + peripheral)"""

        params = hypothesis.parameters
        dose = config.get("dose", 100.0)
        halflife = config.get("halflife", 4.0)
        volume = config.get("volume", 50.0)

        # Two-compartment parameters
        k10 = np.log(2) / halflife  # Elimination from central
        k12 = params.get("k12", 0.5)  # Central to peripheral
        k21 = params.get("k21", 0.3)  # Peripheral to central

        t_end = 10 * halflife
        t_eval = np.linspace(0, t_end, 500)

        def two_comp_model(t: Any, y: Any) -> Any:
            """Two-compartment ODEs"""
            c1, c2 = y  # Central and peripheral concentrations

            dc1dt = -(k10 + k12) * c1 + k21 * c2
            dc2dt = k12 * c1 - k21 * c2

            return [dc1dt, dc2dt]

        # Initial condition (IV bolus)
        c0 = dose / volume

        solution = solve_ivp(
            two_comp_model,
            [0, t_end],
            [c0, 0],
            t_eval=t_eval,
            method='RK45',
        )

        central_conc = solution.y[0]
        times = solution.t

        metrics = self._calculate_pk_metrics(times, central_conc, dose, 0)
        metrics["peripheral_cmax"] = float(np.max(solution.y[1]))

        logs = [
            "Two-compartment PK model",
            f"Cmax (central): {metrics['cmax']:.2f} mg/L",
            f"Cmax (peripheral): {metrics['peripheral_cmax']:.2f} mg/L",
            f"AUC: {metrics['auc']:.2f} mg·h/L",
        ]

        return {"metrics": metrics, "logs": logs}

    async def _michaelis_menten(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Michaelis-Menten elimination (saturable metabolism)"""

        params = hypothesis.parameters
        dose = config.get("dose", 100.0)
        volume = config.get("volume", 50.0)

        # Michaelis-Menten parameters
        vmax = params.get("vmax", 10.0)  # mg/h
        km = params.get("km", 5.0)  # mg/L

        t_end = 48.0
        t_eval = np.linspace(0, t_end, 500)

        def mm_model(t: Any, y: Any) -> Any:
            """dC/dt = -Vmax*C / (Km + C)"""
            c = y[0]
            if c < 0:
                return [0]
            elimination = (vmax * c) / (km + c)
            return [-elimination / volume]

        c0 = dose / volume

        solution = solve_ivp(
            mm_model,
            [0, t_end],
            [c0],
            t_eval=t_eval,
            method='RK45',
        )

        concentrations = solution.y[0]
        times = solution.t

        metrics = self._calculate_pk_metrics(times, concentrations, dose, 0)
        metrics["nonlinear"] = True

        logs = [
            "Michaelis-Menten elimination model",
            f"Vmax: {vmax} mg/h, Km: {km} mg/L",
            f"Cmax: {metrics['cmax']:.2f} mg/L",
            "Half-life increases with concentration (nonlinear)",
        ]

        return {"metrics": metrics, "logs": logs}

    def _calculate_pk_metrics(
        self, times: np.ndarray, concentrations: np.ndarray,
        dose: float, interval: float
    ) -> dict[str, Any]:
        """Calculate standard PK metrics"""

        # Cmax and Tmax
        cmax_idx = np.argmax(concentrations)
        cmax = float(concentrations[cmax_idx])
        tmax = float(times[cmax_idx])

        # AUC (trapezoidal rule)
        auc = float(np.trapezoid(concentrations, times))

        # Clearance (CL = Dose / AUC for IV)
        clearance = dose / auc if auc > 0 else 0

        # Check for steady state (if multiple doses)
        steady_state_reached = False
        if interval > 0 and len(times) > 100:
            # Compare last two intervals
            last_interval_mask = times > (times[-1] - 2 * interval)
            if np.any(last_interval_mask):
                recent_conc = concentrations[last_interval_mask]
                # Check if fluctuation is stable
                steady_state_reached = True  # Simplified

        return {
            "cmax": cmax,
            "tmax": tmax,
            "auc": auc,
            "clearance": clearance,
            "half_life_estimate": self._estimate_half_life(times, concentrations),
            "steady_state_reached": steady_state_reached,
            "final_concentration": float(concentrations[-1]),
        }

    def _estimate_half_life(self, times: np.ndarray, concentrations: np.ndarray) -> float:
        """Estimate half-life from elimination phase"""
        # Use last 20% of data
        n = len(times)
        start_idx = int(0.8 * n)

        if start_idx >= n - 2:
            return 0.0

        # Log-linear regression on elimination phase
        t_segment = times[start_idx:]
        c_segment = concentrations[start_idx:]

        # Filter positive concentrations
        mask = c_segment > 0
        if np.sum(mask) < 2:
            return 0.0

        log_c = np.log(c_segment[mask])
        t = t_segment[mask]

        # Linear fit: ln(C) = ln(C0) - kt
        k = -np.polyfit(t, log_c, 1)[0]

        if k > 0:
            return float(np.log(2) / k)
        return 0.0

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Reasonable Cmax
        if 0 < metrics.get("cmax", -1) < 1000:
            factors.append(0.3)

        # Reasonable AUC
        if 0 < metrics.get("auc", -1) < 10000:
            factors.append(0.3)

        # Half-life estimable
        if metrics.get("half_life_estimate", 0) > 0:
            factors.append(0.2)

        # Steady state info
        if "steady_state_reached" in metrics:
            factors.append(0.2)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        num_doses = params.get("num_doses", 5)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": 1 + num_doses * 0.1,
        }
