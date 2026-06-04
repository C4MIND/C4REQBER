"""
Ising Model Pattern
Statistical mechanics simulation with Metropolis and Wolff algorithms

Based on:
- Ising model (Ernst Ising, 1925)
- Metropolis-Hastings algorithm
- Wolff cluster algorithm
- Critical phenomena and phase transitions
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
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


class Algorithm(Enum):
    """Simulation algorithms"""
    METROPOLIS = "metropolis"
    WOLFF = "wolff"
    SWENDSEN_WANG = "swendsen_wang"


@dataclass
class IsingConfig:
    """Configuration for Ising model simulation"""
    lattice_size: int = 32
    temperature: float = 2.27  # Critical Tc ≈ 2.269 for 2D
    J: float = 1.0  # Coupling constant
    h: float = 0.0  # External field
    n_sweeps: int = 10000
    thermalization: int = 1000
    algorithm: str = "metropolis"
    measure_every: int = 10
    random_seed: int | None = None

    def __post_init__(self) -> None:
        if self.algorithm not in [a.value for a in Algorithm]:
            self.algorithm = "metropolis"


@simulation_pattern(
    id="ising_model",
    name="Ising Model",
    category="physics",
    description="Statistical mechanics simulation with Metropolis and Wolff algorithms",
)
class IsingModelPattern(SimulationPattern):
    """
    Ising model simulation for magnetic systems and phase transitions

    Implements:
    - 2D square lattice with periodic boundary conditions
    - Metropolis single-spin flip algorithm
    - Wolff cluster flip algorithm
    - Swendsen-Wang cluster algorithm
    - Critical phenomena measurements
    - Binder cumulant for phase transition detection
    """

    parameters = [
        SimulationParameter(
            name="lattice_size",
            type="int",
            default=32,
            min=4,
            max=256,
            description="Size of L×L lattice",
        ),
        SimulationParameter(
            name="temperature",
            type="float",
            default=2.27,
            min=0.1,
            max=10.0,
            description="Temperature in units of J/kB",
        ),
        SimulationParameter(
            name="J",
            type="float",
            default=1.0,
            min=-2.0,
            max=2.0,
            description="Coupling constant (J>0: ferromagnetic)",
        ),
        SimulationParameter(
            name="h",
            type="float",
            default=0.0,
            min=-5.0,
            max=5.0,
            description="External magnetic field",
        ),
        SimulationParameter(
            name="n_sweeps",
            type="int",
            default=10000,
            min=100,
            max=1000000,
            description="Number of Monte Carlo sweeps",
        ),
        SimulationParameter(
            name="algorithm",
            type="select",
            default="metropolis",
            options=["metropolis", "wolff", "swendsen_wang"],
            description="MCMC algorithm to use",
        ),
        SimulationParameter(
            name="thermalization",
            type="int",
            default=1000,
            min=0,
            max=50000,
            description="Thermalization sweeps before measurement",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rng = np.random.default_rng()
        self.lattice: np.ndarray = np.array([])
        self.config: IsingConfig | None = None
        self.measurements: dict[str, list[float]] = {}

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "ising", "magnet", "spin", "ferromagnet", "paramagnet",
            "phase transition", "critical", "curie", "spontaneous symmetry",
            "statistical mechanics", "lattice", "monte carlo", "mcmc",
            "magnetization", "susceptibility", "specific heat",
            "binder cumulant", "finite size scaling",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute Ising model simulation"""
        start_time = datetime.now()
        simulation_id = f"ising_{start_time.timestamp()}"

        logger.info(f"Starting Ising simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.random_seed:
                self.rng = np.random.default_rng(self.config.random_seed)

            results = await self._simulate(hypothesis)

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=datetime.now(),
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Ising simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> IsingConfig:
        """Parse configuration dict into IsingConfig"""
        return IsingConfig(
            lattice_size=config.get("lattice_size", 32),
            temperature=config.get("temperature", 2.27),
            J=config.get("J", 1.0),
            h=config.get("h", 0.0),
            n_sweeps=config.get("n_sweeps", 10000),
            thermalization=config.get("thermalization", 1000),
            algorithm=config.get("algorithm", "metropolis"),
            measure_every=config.get("measure_every", 10),
            random_seed=config.get("random_seed"),
        )

    async def _simulate(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Run Ising simulation"""
        L = self.config.lattice_size  # type: ignore[union-attr]
        T = self.config.temperature  # type: ignore[union-attr]
        J = self.config.J  # type: ignore[union-attr]
        h = self.config.h  # type: ignore[union-attr]

        # Initialize lattice: random spins ±1
        self.lattice = 2 * self.rng.integers(0, 2, size=(L, L)) - 1

        # Initialize measurements
        self.measurements = {
            "magnetization": [],
            "energy": [],
            "magnetization_squared": [],
            "energy_squared": [],
            "abs_magnetization": [],
        }

        # Select algorithm
        if self.config.algorithm == "metropolis":  # type: ignore[union-attr]
            await self._metropolis()
        elif self.config.algorithm == "wolff":  # type: ignore[union-attr]
            await self._wolff()
        elif self.config.algorithm == "swendsen_wang":  # type: ignore[union-attr]
            await self._swendsen_wang()

        # Calculate results
        return self._analyze_results()

    async def _metropolis(self) -> None:
        """Metropolis single-spin flip algorithm"""
        L = self.config.lattice_size  # type: ignore[union-attr]
        T = self.config.temperature  # type: ignore[union-attr]
        J = self.config.J  # type: ignore[union-attr]
        h = self.config.h  # type: ignore[union-attr]
        N = L * L

        for sweep in range(self.config.n_sweeps + self.config.thermalization):  # type: ignore[union-attr]
            # N attempts per sweep
            for _ in range(N):
                i, j = self.rng.integers(0, L, size=2)

                # Calculate energy change
                s = self.lattice[i, j]
                neighbors = (
                    self.lattice[(i+1)%L, j] + self.lattice[(i-1)%L, j] +
                    self.lattice[i, (j+1)%L] + self.lattice[i, (j-1)%L]
                )
                delta_E = 2 * s * (J * neighbors + h)

                # Metropolis acceptance
                if delta_E <= 0 or self.rng.random() < np.exp(-delta_E / T):
                    self.lattice[i, j] = -s

            # Measure after thermalization
            if sweep >= self.config.thermalization:  # type: ignore[union-attr]
                if (sweep - self.config.thermalization) % self.config.measure_every == 0:  # type: ignore[union-attr]
                    self._measure()

            # Yield control periodically
            if sweep % 100 == 0:
                await asyncio.sleep(0)

    async def _wolff(self) -> None:
        """Wolff cluster flip algorithm"""
        L = self.config.lattice_size  # type: ignore[union-attr]
        T = self.config.temperature  # type: ignore[union-attr]
        J = self.config.J  # type: ignore[union-attr]
        N = L * L

        # Cluster bond probability
        p_add = 1 - np.exp(-2 * abs(J) / T) if J > 0 else 0

        for sweep in range(self.config.n_sweeps + self.config.thermalization):  # type: ignore[union-attr]
            # Build and flip clusters until ~N spins flipped
            n_flipped = 0
            while n_flipped < N:
                n_flipped += self._wolff_step(L, p_add)

            # Measure after thermalization
            if sweep >= self.config.thermalization:  # type: ignore[union-attr]
                if (sweep - self.config.thermalization) % self.config.measure_every == 0:  # type: ignore[union-attr]
                    self._measure()

            if sweep % 100 == 0:
                await asyncio.sleep(0)

    def _wolff_step(self, L: int, p_add: float) -> int:
        """Single Wolff cluster flip"""
        # Random seed spin
        i, j = self.rng.integers(0, L, size=2)
        seed_spin = self.lattice[i, j]

        # BFS to build cluster
        cluster: set[tuple[int, int]] = {(i, j)}
        queue = deque([(i, j)])

        while queue:
            ci, cj = queue.popleft()
            for ni, nj in [((ci+1)%L, cj), ((ci-1)%L, cj), (ci, (cj+1)%L), (ci, (cj-1)%L)]:
                if (ni, nj) not in cluster and self.lattice[ni, nj] == seed_spin:
                    if self.rng.random() < p_add:
                        cluster.add((ni, nj))
                        queue.append((ni, nj))

        # Flip cluster
        for ci, cj in cluster:
            self.lattice[ci, cj] *= -1

        return len(cluster)

    async def _swendsen_wang(self) -> None:
        """Swendsen-Wang cluster algorithm"""
        L = self.config.lattice_size  # type: ignore[union-attr]
        T = self.config.temperature  # type: ignore[union-attr]
        J = self.config.J  # type: ignore[union-attr]

        p_bond = 1 - np.exp(-2 * abs(J) / T) if J > 0 else 0

        for sweep in range(self.config.n_sweeps + self.config.thermalization):  # type: ignore[union-attr]
            # Create bonds
            bonds_h = self.rng.random((L, L)) < p_bond
            bonds_v = self.rng.random((L, L)) < p_bond

            # Label clusters using union-find
            labels = np.arange(L * L).reshape(L, L)

            # Horizontal bonds
            for i in range(L):
                for j in range(L):
                    if bonds_h[i, j] and self.lattice[i, j] == self.lattice[i, (j+1)%L]:
                        self._union(labels, i, j, i, (j+1)%L, L)

            # Vertical bonds
            for i in range(L):
                for j in range(L):
                    if bonds_v[i, j] and self.lattice[i, j] == self.lattice[(i+1)%L, j]:
                        self._union(labels, i, j, (i+1)%L, j, L)

            # Flatten labels
            for i in range(L):
                for j in range(L):
                    labels[i, j] = self._find(labels, i, j, L)

            # Flip clusters randomly
            unique_labels = np.unique(labels)
            for label in unique_labels:
                if self.rng.random() < 0.5:
                    mask = labels == label
                    self.lattice[mask] *= -1

            # Measure after thermalization
            if sweep >= self.config.thermalization:  # type: ignore[union-attr]
                if (sweep - self.config.thermalization) % self.config.measure_every == 0:  # type: ignore[union-attr]
                    self._measure()

            if sweep % 100 == 0:
                await asyncio.sleep(0)

    def _union(self, labels: np.ndarray, i1: int, j1: int, i2: int, j2: int, L: int) -> None:
        """Union two sites in union-find"""
        root1 = self._find(labels, i1, j1, L)
        root2 = self._find(labels, i2, j2, L)
        labels[root2 // L, root2 % L] = root1

    def _find(self, labels: np.ndarray, i: int, j: int, L: int) -> int:
        """Find root in union-find with path compression"""
        idx = i * L + j
        while labels[i, j] != idx:
            i, j = labels[i, j] // L, labels[i, j] % L
            idx = i * L + j
        return idx

    def _measure(self) -> None:
        """Measure observables"""
        L = self.config.lattice_size  # type: ignore[union-attr]
        N = L * L

        # Ensure measurements dict is initialized
        if not self.measurements:
            self.measurements = {
                "magnetization": [],
                "energy": [],
                "magnetization_squared": [],
                "energy_squared": [],
                "abs_magnetization": [],
            }

        # Magnetization per spin
        M = np.sum(self.lattice) / N
        self.measurements["magnetization"].append(M)
        self.measurements["abs_magnetization"].append(abs(M))
        self.measurements["magnetization_squared"].append(M * M)

        # Energy per spin
        E = 0.0
        for i in range(L):
            for j in range(L):
                s = self.lattice[i, j]
                neighbors = (
                    self.lattice[(i+1)%L, j] + self.lattice[i, (j+1)%L]
                )
                E -= self.config.J * s * neighbors  # type: ignore[union-attr]
        E = E / N - self.config.h * np.sum(self.lattice) / N  # type: ignore[union-attr]
        self.measurements["energy"].append(E)
        self.measurements["energy_squared"].append(E * E)

    def _analyze_results(self) -> dict[str, Any]:
        """Analyze simulation results"""
        if not self.measurements or not self.measurements.get("magnetization"):
            return {"metrics": {}, "logs": ["No measurements taken"]}

        L = self.config.lattice_size  # type: ignore[union-attr]
        N = L * L
        T = self.config.temperature  # type: ignore[union-attr]

        # Calculate averages
        M_vals = np.array(self.measurements["magnetization"])
        abs_M_vals = np.array(self.measurements["abs_magnetization"])
        M2_vals = np.array(self.measurements["magnetization_squared"])
        E_vals = np.array(self.measurements["energy"])
        E2_vals = np.array(self.measurements["energy_squared"])

        # Magnetization (use |M| for T < Tc)
        M_mean = float(np.mean(abs_M_vals))
        M_var = float(np.var(M_vals))

        # Susceptibility: χ = β * N * (⟨M²⟩ - ⟨|M|⟩²)
        chi = float((M_var * N) / T) if T > 0 else 0

        # Energy and specific heat
        E_mean = float(np.mean(E_vals))
        E_var = float(np.var(E_vals))
        C = float(E_var / (T * T)) if T > 0 else 0

        # Binder cumulant: U_L = 1 - ⟨M⁴⟩ / (3⟨M²⟩²)
        M4_mean = float(np.mean(M_vals**4))
        M2_mean = float(np.mean(M2_vals))
        U_L = 1 - M4_mean / (3 * M2_mean**2) if M2_mean > 0 else 0

        # Autocorrelation time estimate
        if len(M_vals) > 10:
            autocorr = np.corrcoef(M_vals[:-1], M_vals[1:])[0, 1]
        else:
            autocorr = 0

        metrics = {
            "temperature": T,
            "magnetization": M_mean,
            "susceptibility": chi,
            "energy": E_mean,
            "specific_heat": C,
            "binder_cumulant": U_L,
            "autocorrelation": float(autocorr),
            "n_measurements": len(M_vals),
            "lattice_size": L,
        }

        logs = [
            f"Ising model: {L}×{L} lattice, T={T:.3f}, algorithm={self.config.algorithm}",  # type: ignore[union-attr]
            f"Magnetization: {M_mean:.4f}",
            f"Susceptibility: {chi:.4f}",
            f"Specific heat: {C:.4f}",
            f"Binder cumulant: {U_L:.4f}",
            f"Autocorrelation: {autocorr:.4f}",
        ]

        if T < 2.3 and M_mean > 0.5:
            logs.append("System appears to be in ordered (ferromagnetic) phase")
        elif T > 2.3 and M_mean < 0.3:
            logs.append("System appears to be in disordered (paramagnetic) phase")

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        n_meas = metrics.get("n_measurements", 0)
        if n_meas >= 100:
            factors.append(0.3)
        elif n_meas >= 50:
            factors.append(0.2)

        autocorr = abs(metrics.get("autocorrelation", 1))
        if autocorr < 0.1:
            factors.append(0.3)
        elif autocorr < 0.5:
            factors.append(0.2)

        L = metrics.get("lattice_size", 0)
        if L >= 64:
            factors.append(0.2)
        elif L >= 32:
            factors.append(0.1)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        L = params.get("lattice_size", 32)
        n_sweeps = params.get("n_sweeps", 10000)

        estimated_time = (L * L * n_sweeps) / 1e6

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + (L * L) / 1e6,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
