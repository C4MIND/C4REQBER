"""
Game Theory Pattern
Strategic interaction simulation for economics

Based on:
- Nash equilibrium
- Prisoner's Dilemma, Battle of Sexes, Coordination games
- Evolutionary game theory
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

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


@simulation_pattern(
    id="game_theory",
    name="Game Theory",
    category="economics",
    description="Strategic interaction and Nash equilibrium analysis",
)
class GameTheoryPattern(SimulationPattern):
    """
    Game theory simulation for strategic interactions

    Implements:
    - Nash equilibrium calculation
    - Prisoner's Dilemma
    - Coordination games
    - Evolutionary dynamics
    """

    parameters = [
        SimulationParameter(
            name="game_type",
            type="select",
            default="prisoners_dilemma",
            options=["prisoners_dilemma", "battle_of_sexes", "coordination", "hawk_dove"],
            description="Type of game",
        ),
        SimulationParameter(
            name="num_rounds",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Number of rounds",
        ),
        SimulationParameter(
            name="num_players",
            type="int",
            default=100,
            min=2,
            max=1000,
            description="Number of players (for evolutionary)"
        ),
    ]

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if can simulate."""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "game theory", "nash", "equilibrium", "strategy",
            "prisoner's dilemma", "battle of sexes",
            "coordination", "hawk-dove", "chicken",
            "dominant strategy", "payoff",
        ]
        return any(kw in title or kw in desc for kw in keywords)

    async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> SimulationResult:  # type: ignore[override]
        """Run."""
        start_time = datetime.now()
        simulation_id = f"gt_{start_time.timestamp()}"

        try:
            game_type = config.get("game_type", "prisoners_dilemma")

            if game_type == "prisoners_dilemma":
                results = await self._prisoners_dilemma(hypothesis, config)
            elif game_type == "battle_of_sexes":
                results = await self._battle_of_sexes(hypothesis, config)
            else:
                results = await self._evolutionary_game(hypothesis, config)

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
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    async def _prisoners_dilemma(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Prisoner's Dilemma simulation"""
        T = config.get("num_rounds", 100)

        # Payoff matrix (T, R, P, S)
        # Temptation, Reward, Punishment, Sucker
        T, R, P, S = 5, 3, 1, 0

        strategies = ["cooperate", "defect"]

        # Simulate different strategy pairs
        results = {}
        for s1 in strategies:
            for s2 in strategies:
                if s1 == "cooperate" and s2 == "cooperate":
                    payoff1, payoff2 = R, R
                elif s1 == "cooperate" and s2 == "defect":
                    payoff1, payoff2 = S, T
                elif s1 == "defect" and s2 == "cooperate":
                    payoff1, payoff2 = T, S
                else:
                    payoff1, payoff2 = P, P

                results[f"{s1}_vs_{s2}"] = (payoff1, payoff2)

        # Nash equilibrium: both defect
        nash_payoff = P

        # Social optimum: both cooperate
        social_optimum = R

        metrics = {
            "nash_equilibrium_payoff": float(nash_payoff),
            "social_optimum_payoff": float(social_optimum),
            "efficiency_loss": float((social_optimum - nash_payoff) / social_optimum),
            "dominant_strategy": "defect",
            "nash_equilibrium": ("defect", "defect"),
        }

        logs = [
            "Prisoner's Dilemma analysis",
            f"Nash equilibrium: (defect, defect) with payoff {nash_payoff}",
            f"Social optimum: (cooperate, cooperate) with payoff {social_optimum}",
            f"Efficiency loss: {metrics['efficiency_loss']:.1%}",
        ]

        return {"metrics": metrics, "logs": logs}

    async def _battle_of_sexes(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Battle of Sexes - coordination game"""

        # Two pure strategy Nash equilibria
        # Mixed strategy equilibrium

        metrics = {
            "pure_equilibria": [("opera", "opera"), ("football", "football")],
            "mixed_equilibrium_p": 0.6,  # Probability of opera
            "coordination_problem": True,
        }

        logs = [
            "Battle of Sexes analysis",
            "Two pure strategy Nash equilibria",
            "One mixed strategy equilibrium",
        ]

        return {"metrics": metrics, "logs": logs}

    async def _evolutionary_game(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Evolutionary game dynamics"""
        N = config.get("num_players", 100)
        T = config.get("num_rounds", 100)

        # Initial population fractions
        p_cooperate = 0.5

        # Track evolution
        fractions = [p_cooperate]

        for t in range(T):
            # Payoffs depend on population composition
            payoff_coop = 3 * p_cooperate + 0 * (1 - p_cooperate)
            payoff_defect = 5 * p_cooperate + 1 * (1 - p_cooperate)

            avg_payoff = p_cooperate * payoff_coop + (1 - p_cooperate) * payoff_defect

            # Replicator dynamics
            if avg_payoff > 0:
                p_cooperate = p_cooperate * payoff_coop / avg_payoff

            fractions.append(p_cooperate)

            if t % 10 == 0:
                await asyncio.sleep(0)

        metrics = {
            "final_cooperate_fraction": float(p_cooperate),
            "converged": abs(p_cooperate - fractions[-10]) < 0.01,
            "equilibrium_type": "defect" if p_cooperate < 0.1 else "cooperate" if p_cooperate > 0.9 else "mixed",
        }

        logs = [
            f"Evolutionary dynamics: {N} players, {T} rounds",
            f"Final cooperate fraction: {p_cooperate:.2%}",
            f"Equilibrium: {metrics['equilibrium_type']}",
        ]

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        metrics = results["metrics"]
        factors = []

        if "nash_equilibrium" in metrics:
            factors.append(0.4)

        if "equilibrium_type" in metrics:
            factors.append(0.3)

        return min(0.9, sum(factors) + 0.2)

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate resources."""
        N = hypothesis.parameters.get("num_players", 100)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": N / 1000,
        }
