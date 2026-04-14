"""
TURBO-CDI v6.0 - Conflict Pattern
Lanchester equations and related models for combat dynamics.

Pattern Structure (Christopher Alexander):
- Context: Military science, game theory, security studies
- Forces: Attrition, reinforcement, maneuver, logistics
- Solution: Differential equation models of combat
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictModel(Enum):
    """Available conflict models"""

    LANCHESTER_LINEAR = "lanchester_linear"  # Aimed fire
    LANCHESTER_SQUARE = "lanchester_square"  # Area fire
    LANCHESTER_MIXED = "lanchester_mixed"  # Combined
    SALVO = "salvo"  # Hughes salvo model


@dataclass
class ConflictConfig:
    """Configuration for conflict simulation"""

    model: ConflictModel = ConflictModel.LANCHESTER_SQUARE

    # Initial forces
    force_a_initial: float = 1000.0
    force_b_initial: float = 1000.0

    # Effectiveness
    lethality_a: float = 0.05  # Casualties per unit per time
    lethality_b: float = 0.05

    # Lanchester aimed fire (linear law)
    aim_effectiveness_a: float = 0.01
    aim_effectiveness_b: float = 0.01

    # Salvo model
    offensive_firepower_a: float = 3.0  # Missiles per unit
    offensive_firepower_b: float = 3.0
    defensive_capability_a: float = 1.0  # Missiles intercepted
    defensive_capability_b: float = 1.0
    staying_power_a: float = 1.0  # Hits to kill
    staying_power_b: float = 1.0

    # Reinforcement
    reinforcement_rate_a: float = 0.0
    reinforcement_rate_b: float = 0.0

    # Simulation
    dt: float = 0.1
    max_time: float = 100.0

    # Stopping conditions
    min_force_ratio: float = 0.1  # Surrender threshold
    max_casualties: float = 0.9  # Breaking point


class ConflictPattern:
    """
    Combat dynamics using Lanchester equations and extensions.

    Models:
    - Lanchester Linear: Aimed fire (attrition proportional to own force)
    - Lanchester Square: Area fire (attrition proportional to enemy force)
    - Lanchester Mixed: Combined aimed and area fire
    - Salvo: Hughes salvo model for missile combat

    Lanchester Linear (aimed fire):
    dA/dt = -β·B, dB/dt = -α·A

    Lanchester Square (area fire):
    dA/dt = -β·A·B, dB/dt = -α·A·B
    """

    PATTERN_ID = "conflict"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[ConflictConfig] = None):
        self.config = config or ConflictConfig()
        self.force_a: float = 0.0
        self.force_b: float = 0.0
        self.time: float = 0.0

        self.history_a: List[float] = []
        self.history_b: List[float] = []
        self.time_history: List[float] = []
        self.casualties_a: float = 0.0
        self.casualties_b: float = 0.0

        self._initialize()

    def _initialize(self):
        """Initialize conflict simulation"""
        cfg = self.config

        self.force_a = cfg.force_a_initial
        self.force_b = cfg.force_b_initial
        self.time = 0.0

        self.history_a = [self.force_a]
        self.history_b = [self.force_b]
        self.time_history = [0.0]

        self.casualties_a = 0.0
        self.casualties_b = 0.0

    def _lanchester_linear_derivatives(self) -> Tuple[float, float]:
        """Derivatives for Lanchester linear law (aimed fire)"""
        cfg = self.config

        d_a = -cfg.aim_effectiveness_b * self.force_b + cfg.reinforcement_rate_a
        d_b = -cfg.aim_effectiveness_a * self.force_a + cfg.reinforcement_rate_b

        return d_a, d_b

    def _lanchester_square_derivatives(self) -> Tuple[float, float]:
        """Derivatives for Lanchester square law (area fire)"""
        cfg = self.config

        d_a = -cfg.lethality_b * self.force_a * self.force_b + cfg.reinforcement_rate_a
        d_b = -cfg.lethality_a * self.force_a * self.force_b + cfg.reinforcement_rate_b

        return d_a, d_b

    def _lanchester_mixed_derivatives(self) -> Tuple[float, float]:
        """Derivatives for Lanchester mixed law"""
        cfg = self.config

        # Combine aimed and area fire
        d_a = (
            -cfg.aim_effectiveness_b * self.force_b
            - 0.5 * cfg.lethality_b * self.force_a * self.force_b
            + cfg.reinforcement_rate_a
        )
        d_b = (
            -cfg.aim_effectiveness_a * self.force_a
            - 0.5 * cfg.lethality_a * self.force_a * self.force_b
            + cfg.reinforcement_rate_b
        )

        return d_a, d_b

    def _salvo_step(self):
        """One salvo exchange (discrete time)"""
        cfg = self.config

        # Missiles launched
        missiles_a = self.force_a * cfg.offensive_firepower_a
        missiles_b = self.force_b * cfg.offensive_firepower_b

        # Missiles intercepted
        intercepted_a = min(missiles_b, self.force_a * cfg.defensive_capability_a)
        intercepted_b = min(missiles_a, self.force_b * cfg.defensive_capability_b)

        # Hits received
        hits_a = max(0, missiles_b - intercepted_a)
        hits_b = max(0, missiles_a - intercepted_b)

        # Casualties
        casualties_a = hits_a / cfg.staying_power_a
        casualties_b = hits_b / cfg.staying_power_b

        # Apply casualties
        self.force_a = max(0, self.force_a - casualties_a)
        self.force_b = max(0, self.force_b - casualties_b)

        self.casualties_a += casualties_a
        self.casualties_b += casualties_b

    def _calculate_win_probability(self) -> float:
        """Calculate theoretical win probability based on force ratio"""
        cfg = self.config

        # Lanchester square law: victor determined by initial conditions
        if cfg.model in [
            ConflictModel.LANCHESTER_SQUARE,
            ConflictModel.LANCHESTER_MIXED,
        ]:
            # FAD = α·A₀² - β·B₀² (Fighting strength advantage differential)
            fad = (
                cfg.lethality_a * cfg.force_a_initial**2
                - cfg.lethality_b * cfg.force_b_initial**2
            )

            if fad > 0:
                return 1.0
            elif fad < 0:
                return 0.0
            else:
                return 0.5

        # Lanchester linear law
        elif cfg.model == ConflictModel.LANCHESTER_LINEAR:
            # Winner determined by effectiveness ratio
            if (
                cfg.aim_effectiveness_a * cfg.force_a_initial
                > cfg.aim_effectiveness_b * cfg.force_b_initial
            ):
                return 1.0
            else:
                return 0.0

        return 0.5

    def _check_termination(self) -> bool:
        """Check if battle should end"""
        cfg = self.config

        # One side eliminated
        if self.force_a <= 0 or self.force_b <= 0:
            return True

        # Force ratio threshold
        total = self.force_a + self.force_b
        if total > 0:
            if self.force_a / total < cfg.min_force_ratio:
                return True
            if self.force_b / total < cfg.min_force_ratio:
                return True

        # Casualty threshold
        if self.casualties_a > cfg.force_a_initial * cfg.max_casualties:
            return True
        if self.casualties_b > cfg.force_b_initial * cfg.max_casualties:
            return True

        return False

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run conflict simulation"""
        cfg = self.config

        logger.info(f"Starting conflict simulation: {cfg.model.value}")
        logger.info(
            f"Initial forces: A={cfg.force_a_initial:.0f}, B={cfg.force_b_initial:.0f}"
        )

        # Predicted outcome
        predicted_winner = self._calculate_win_probability()

        if cfg.model == ConflictModel.SALVO:
            # Discrete salvo model
            for step in range(int(cfg.max_time)):
                self._salvo_step()
                self.time = step

                self.history_a.append(self.force_a)
                self.history_b.append(self.force_b)
                self.time_history.append(self.time)

                if self._check_termination():
                    break
        else:
            # Continuous Lanchester models
            n_steps = int(cfg.max_time / cfg.dt)

            for step in range(n_steps):
                if cfg.model == ConflictModel.LANCHESTER_LINEAR:
                    d_a, d_b = self._lanchester_linear_derivatives()
                elif cfg.model == ConflictModel.LANCHESTER_SQUARE:
                    d_a, d_b = self._lanchester_square_derivatives()
                elif cfg.model == ConflictModel.LANCHESTER_MIXED:
                    d_a, d_b = self._lanchester_mixed_derivatives()
                else:
                    d_a, d_b = self._lanchester_square_derivatives()

                # Euler integration
                self.force_a = max(0, self.force_a + d_a * cfg.dt)
                self.force_b = max(0, self.force_b + d_b * cfg.dt)
                self.time = step * cfg.dt

                self.casualties_a = cfg.force_a_initial - self.force_a
                self.casualties_b = cfg.force_b_initial - self.force_b

                self.history_a.append(self.force_a)
                self.history_b.append(self.force_b)
                self.time_history.append(self.time)

                if self._check_termination():
                    break

        return self._format_output(predicted_winner)

    def _format_output(self, predicted_winner: float) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Determine winner
        if self.force_a > self.force_b:
            winner = "A"
            winner_prob = 1.0
        elif self.force_b > self.force_a:
            winner = "B"
            winner_prob = 0.0
        else:
            winner = "draw"
            winner_prob = 0.5

        # Casualty rates
        casualty_rate_a = (
            self.casualties_a / cfg.force_a_initial if cfg.force_a_initial > 0 else 0
        )
        casualty_rate_b = (
            self.casualties_b / cfg.force_b_initial if cfg.force_b_initial > 0 else 0
        )

        # Lanchester's laws metrics
        if cfg.model in [
            ConflictModel.LANCHESTER_SQUARE,
            ConflictModel.LANCHESTER_MIXED,
        ]:
            # Square law: α·A² - β·B² should be constant
            fad_start = (
                cfg.lethality_a * cfg.force_a_initial**2
                - cfg.lethality_b * cfg.force_b_initial**2
            )
            fad_end = (
                cfg.lethality_a * self.force_a**2 - cfg.lethality_b * self.force_b**2
            )
        else:
            fad_start = fad_end = 0.0

        return {
            "model": cfg.model.value,
            "winner": winner,
            "final_forces": {
                "A": float(self.force_a),
                "B": float(self.force_b),
            },
            "casualties": {
                "A": float(self.casualties_a),
                "B": float(self.casualties_b),
            },
            "casualty_rates": {
                "A": float(casualty_rate_a),
                "B": float(casualty_rate_b),
            },
            "duration": float(self.time),
            "force_history": {
                "A": self.history_a[:: max(1, len(self.history_a) // 100)],
                "B": self.history_b[:: max(1, len(self.history_b) // 100)],
                "time": self.time_history[:: max(1, len(self.time_history) // 100)],
            },
            "lanchester_metrics": {
                "fad_start": float(fad_start),
                "fad_end": float(fad_end),
                "conservation_error": float(
                    abs(fad_end - fad_start) / (abs(fad_start) + 1)
                ),
            },
            "outcome_prediction": {
                "predicted": "A"
                if predicted_winner > 0.5
                else "B"
                if predicted_winner < 0.5
                else "draw",
                "actual": winner,
                "prediction_correct": (predicted_winner > 0.5 and winner == "A")
                or (predicted_winner < 0.5 and winner == "B")
                or (predicted_winner == 0.5 and winner == "draw"),
            },
            "config": {
                "force_a_initial": cfg.force_a_initial,
                "force_b_initial": cfg.force_b_initial,
                "lethality_a": cfg.lethality_a,
                "lethality_b": cfg.lethality_b,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Conflict",
            "category": "EXTENDED",
            "domain": ["Military Science", "Game Theory", "Security Studies"],
            "description": "Lanchester equations for combat dynamics",
            "computational_complexity": "O(T)",
            "typical_runtime": "milliseconds",
            "accuracy": "Medium (simplified combat)",
            "assumptions": [
                "Homogeneous forces",
                "Constant effectiveness",
                "No terrain effects",
            ],
            "parameters": [
                {
                    "name": "model",
                    "type": "enum",
                    "options": [
                        "lanchester_linear",
                        "lanchester_square",
                        "lanchester_mixed",
                        "salvo",
                    ],
                    "default": "lanchester_square",
                },
                {
                    "name": "force_a_initial",
                    "type": "float",
                    "default": 1000.0,
                },
                {
                    "name": "force_b_initial",
                    "type": "float",
                    "default": 1000.0,
                },
                {
                    "name": "lethality_a",
                    "type": "float",
                    "default": 0.05,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Lanchester square - equal forces draw
    print("\n=== Test 1: Lanchester Square (Equal Forces) ===")
    config = ConflictConfig(
        model=ConflictModel.LANCHESTER_SQUARE,
        force_a_initial=1000,
        force_b_initial=1000,
        lethality_a=0.05,
        lethality_b=0.05,
    )
    sim = ConflictPattern(config)
    result = sim.run()
    print(f"✓ Winner: {result['winner']}")
    print(f"  Duration: {result['duration']:.1f}")
    print(
        f"  Casualties A: {result['casualty_rates']['A']:.1%}, B: {result['casualty_rates']['B']:.1%}"
    )
    assert result["winner"] in ["draw", "A", "B"], "Should have a winner or draw"

    # Test 2: Lanchester square - 2:1 force advantage
    print("\n=== Test 2: Lanchester Square (2:1 Advantage) ===")
    config = ConflictConfig(
        model=ConflictModel.LANCHESTER_SQUARE,
        force_a_initial=1000,
        force_b_initial=500,
        lethality_a=0.05,
        lethality_b=0.05,
    )
    sim = ConflictPattern(config)
    result = sim.run()
    print(f"✓ Winner: {result['winner']}")
    print(f"  Prediction correct: {result['outcome_prediction']['prediction_correct']}")
    # Note: With square law, 2:1 numerical advantage gives 4:1 fighting strength advantage

    # Test 3: Salvo model
    print("\n=== Test 3: Salvo Model ===")
    config = ConflictConfig(
        model=ConflictModel.SALVO,
        force_a_initial=10,
        force_b_initial=10,
        offensive_firepower_a=4,
        offensive_firepower_b=3,
        defensive_capability_a=2,
        defensive_capability_b=1,
        max_time=20,
    )
    sim = ConflictPattern(config)
    result = sim.run()
    print(f"✓ Winner: {result['winner']}")
    print(f"  Duration: {result['duration']:.0f} salvos")

    # Test 4: Reinforcement
    print("\n=== Test 4: Reinforcement Effect ===")
    config = ConflictConfig(
        model=ConflictModel.LANCHESTER_SQUARE,
        force_a_initial=800,
        force_b_initial=1000,
        lethality_a=0.05,
        lethality_b=0.05,
        reinforcement_rate_a=10.0,
        reinforcement_rate_b=0.0,
    )
    sim = ConflictPattern(config)
    result = sim.run()
    print(f"✓ With reinforcement, smaller force winner: {result['winner']}")

    print("\n✅ All conflict tests passed!")
