"""
Markov Chain Pattern
State transitions and steady-state analysis

Based on:
- Discrete-time Markov chains
- Transition matrix
- Stationary distribution
- Mixing time
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from scipy.linalg import eig

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


@dataclass
class MarkovChainConfig:
    """Configuration for Markov chain simulation"""
    n_states: int = 3
    n_steps: int = 1000
    n_simulations: int = 100
    transition_matrix: list[list[float]] | None = None
    initial_state: int = 0


@simulation_pattern(
    id="markov_chain",
    name="Markov Chain",
    category="mathematics",
    description="Discrete-time Markov chain with steady-state analysis",
)
class MarkovChainPattern(SimulationPattern):
    """
    Markov chain simulation

    Implements:
    - Transition matrix validation
    - Stationary distribution computation
    - Monte Carlo trajectory simulation
    - Mixing time estimation
    - Absorption analysis
    """

    parameters = [
        SimulationParameter(
            name="n_states",
            type="int",
            default=3,
            min=2,
            max=20,
            description="Number of states",
        ),
        SimulationParameter(
            name="n_steps",
            type="int",
            default=1000,
            min=100,
            max=100000,
            description="Number of steps",
        ),
        SimulationParameter(
            name="n_simulations",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Number of Monte Carlo simulations",
        ),
        SimulationParameter(
            name="initial_state",
            type="int",
            default=0,
            min=0,
            max=19,
            description="Initial state",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: MarkovChainConfig = MarkovChainConfig()

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if can simulate."""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "markov chain", "markov process", "state transition",
            "stationary distribution", "steady state", "random walk",
            "mixing time", "ergodic", "irreducible", "absorbing",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> SimulationResult:
        """Run."""
        start_time = datetime.now()
        simulation_id = f"mc_{start_time.timestamp()}"
        logger.info(f"Starting Markov chain simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            results = await self._simulate_markov()
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
            logger.exception("Markov chain simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> MarkovChainConfig:
        cfg = MarkovChainConfig()
        if "n_states" in config:
            cfg.n_states = int(config["n_states"])
        if "n_steps" in config:
            cfg.n_steps = int(config["n_steps"])
        if "n_simulations" in config:
            cfg.n_simulations = int(config["n_simulations"])
        if "initial_state" in config:
            cfg.initial_state = int(config["initial_state"])
        if "transition_matrix" in config:
            cfg.transition_matrix = config["transition_matrix"]
        return cfg

    async def _simulate_markov(self) -> dict[str, Any]:
        cfg = self.config
        n = cfg.n_states

        # Create transition matrix
        if cfg.transition_matrix is not None:
            P = np.array(cfg.transition_matrix, dtype=float)
        else:
            # Random stochastic matrix
            P = np.random.rand(n, n)
            P = P / P.sum(axis=1, keepdims=True)

        # Validate stochastic matrix
        assert np.allclose(P.sum(axis=1), 1.0), "Transition matrix rows must sum to 1"
        assert np.all(P >= 0), "Transition matrix must be non-negative"

        # Compute stationary distribution (left eigenvector with eigenvalue 1)
        eigenvalues, eigenvectors = eig(P.T)
        idx = np.argmin(np.abs(eigenvalues - 1.0))
        stationary = np.real(eigenvectors[:, idx])
        stationary = stationary / np.sum(stationary)

        # Check if irreducible (all states communicate)
        # Simplified: check if P^n has all positive entries for some n
        P_power = np.linalg.matrix_power(P, n)
        is_irreducible = np.all(P_power > 0)

        # Mixing time: how many steps to get close to stationary
        mixing_time = 0
        current_dist = np.zeros(n)
        current_dist[cfg.initial_state] = 1.0
        for step in range(cfg.n_steps):
            current_dist = current_dist @ P
            tv_distance = 0.5 * np.sum(np.abs(current_dist - stationary))
            if tv_distance < 0.01:
                mixing_time = step
                break

        # Monte Carlo simulations
        final_states = np.zeros(n)
        for _ in range(cfg.n_simulations):
            state = cfg.initial_state
            for _ in range(cfg.n_steps):
                state = np.random.choice(n, p=P[state])
            final_states[state] += 1

        empirical_stationary = final_states / cfg.n_simulations

        # Mean first passage time (simplified)
        mftp = np.zeros(n)
        for target in range(n):
            if target == cfg.initial_state:
                mftp[target] = 0.0
            else:
                # Absorbing Markov chain approach
                Q = np.delete(np.delete(P, target, axis=0), target, axis=1)
                try:
                    N_mat = np.linalg.inv(np.eye(n-1) - Q)
                    init = cfg.initial_state if cfg.initial_state < target else cfg.initial_state - 1
                    if init < n - 1:
                        mftp[target] = np.sum(N_mat[init])
                    else:
                        mftp[target] = float('inf')
                except np.linalg.LinAlgError:
                    mftp[target] = float('inf')

        metrics = {
            "n_states": n,
            "n_steps": cfg.n_steps,
            "is_irreducible": is_irreducible,
            "mixing_time": int(mixing_time),
            "spectral_gap": float(1 - np.sort(np.abs(eigenvalues))[-2]),
            "tv_distance_final": float(0.5 * np.sum(np.abs(empirical_stationary - stationary))),
            "initial_state": cfg.initial_state,
        }

        # Add stationary distribution components
        for i in range(n):
            metrics[f"stationary_{i}"] = float(stationary[i])
            metrics[f"empirical_{i}"] = float(empirical_stationary[i])

        logs = [
            f"Markov chain: {n} states, {cfg.n_steps} steps, {cfg.n_simulations} simulations",
            f"Irreducible: {is_irreducible}",
            f"Mixing time (TV < 0.01): {mixing_time}",
            f"Spectral gap: {metrics['spectral_gap']:.6f}",
            f"Stationary distribution: {stationary.round(4).tolist()}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "transition_matrix": P.tolist(),
            "stationary_distribution": stationary.tolist(),
            "empirical_distribution": empirical_stationary.tolist(),
            "eigenvalues": np.real(eigenvalues).tolist(),
            "mean_first_passage_time": mftp.tolist(),
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        metrics = results["metrics"]
        factors = []

        if metrics.get("is_irreducible", False):
            factors.append(0.3)

        if metrics.get("mixing_time", -1) >= 0:
            factors.append(0.2)

        if metrics.get("spectral_gap", 0) > 0:
            factors.append(0.25)

        tv = metrics.get("tv_distance_final", 1.0)
        if tv < 0.5:
            factors.append(0.25)

        return min(0.9, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:
        """Estimate resources."""
        params = hypothesis.parameters
        n = params.get("n_states", 3)
        n_sim = params.get("n_simulations", 100)
        n_steps = params.get("n_steps", 1000)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + n * n * 8e-9,
            "gpu_required": False,
            "estimated_time_seconds": n_sim * n_steps / 1e6,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.id,
            "name": cls.name,
            "category": cls.category,
            "description": cls.description,
            "parameters": [
                {"name": p.name, "type": p.type, "default": p.default,
                 "min": p.min, "max": p.max, "description": p.description}
                for p in cls.parameters
            ],
            "references": [
                "Norris, J.R. (1998). Markov Chains",
            ],
        }
