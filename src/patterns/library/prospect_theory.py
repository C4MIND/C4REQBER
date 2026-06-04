"""
Pattern 61: Prospect Theory (Cumulative Prospect Theory)
Implements Kahneman-Tversky value function, probability weighting,
and cumulative prospect theory for decision making under risk.
"""

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass
class ProspectTheoryConfig:
    """Configuration for prospect theory model."""
    alpha: float = 0.88       # Value function curvature (gains)
    beta: float = 0.88        # Value function curvature (losses)
    lambda_param: float = 2.25  # Loss aversion coefficient
    gamma: float = 0.65       # Probability weighting parameter
    delta: float = 0.65       # Probability weighting for losses
    reference_point: float = 0.0
    random_seed: int = 42


class ProspectTheoryModel:
    """
    Cumulative Prospect Theory (CPT) implementation.

    Models decision making under risk with:
    - Reference-dependent preferences
    - Diminishing sensitivity
    - Loss aversion
    - Probability weighting
    """

    def __init__(self, config: ProspectTheoryConfig = None) -> None:  # type: ignore[assignment]
        self.config = config or ProspectTheoryConfig()
        np.random.seed(self.config.random_seed)

    def value_function(self, x: float) -> float:
        """
        Kahneman-Tversky value function.

        v(x) = x^alpha if x >= 0
               -lambda * (-x)^beta if x < 0

        Args:
            x: Outcome relative to reference point

        Returns:
            Value of outcome
        """
        cfg = self.config
        if x >= 0:
            return x ** cfg.alpha  # type: ignore[no-any-return]
        else:
            return -cfg.lambda_param * ((-x) ** cfg.beta)  # type: ignore[no-any-return]

    def probability_weighting(self, p: float, is_gain: bool = True) -> float:
        """
        Tversky-Kahneman probability weighting function.

        w(p) = p^gamma / (p^gamma + (1-p)^gamma)^(1/gamma)

        Args:
            p: Probability (0 to 1)
            is_gain: Whether this is for gains or losses

        Returns:
            Weighted probability
        """
        cfg = self.config
        param = cfg.gamma if is_gain else cfg.delta

        if p <= 0:
            return 0
        if p >= 1:
            return 1

        return (p ** param) / ((p ** param + (1 - p) ** param) ** (1 / param))  # type: ignore[no-any-return]

    def cumulative_prospect_value(self, outcomes: list[float],
                                   probabilities: list[float]) -> float:
        """
        Calculate CPT value of a prospect.

        Args:
            outcomes: List of outcomes
            probabilities: List of probabilities (sum to 1)

        Returns:
            CPT value
        """
        cfg = self.config

        # Sort outcomes and probabilities
        sorted_pairs = sorted(zip(outcomes, probabilities, strict=False))
        outcomes = np.array([o - cfg.reference_point for o, _ in sorted_pairs])  # type: ignore[assignment]
        probabilities = np.array([p for _, p in sorted_pairs])  # type: ignore[assignment]

        # Separate gains and losses
        gain_mask = outcomes >= 0  # type: ignore[operator]
        loss_mask = outcomes < 0  # type: ignore[operator]

        cpt_value = 0

        # Process gains (ranked from worst to best)
        gain_outcomes = outcomes[gain_mask]
        gain_probs = probabilities[gain_mask]

        if len(gain_outcomes) > 0:
            # Cumulative probabilities
            cum_probs = np.cumsum(gain_probs)

            # Decision weights
            weights = []
            for i, p in enumerate(cum_probs):
                if i == 0:
                    w = self.probability_weighting(p, is_gain=True)
                else:
                    w = self.probability_weighting(p, is_gain=True) - \
                        self.probability_weighting(cum_probs[i-1], is_gain=True)
                weights.append(w)

            # CPT value for gains
            for v, w in zip(gain_outcomes, weights, strict=False):
                cpt_value += self.value_function(v) * w  # type: ignore[assignment]

        # Process losses (ranked from best to worst, i.e., reverse)
        loss_outcomes = outcomes[loss_mask]
        loss_probs = probabilities[loss_mask]

        if len(loss_outcomes) > 0:
            # Reverse order for losses
            sorted_loss_indices = np.argsort(loss_outcomes)[::-1]
            loss_outcomes = loss_outcomes[sorted_loss_indices]
            loss_probs = loss_probs[sorted_loss_indices]

            # Cumulative probabilities
            cum_probs = np.cumsum(loss_probs)

            # Decision weights
            weights = []
            for i, p in enumerate(cum_probs):
                if i == 0:
                    w = self.probability_weighting(p, is_gain=False)
                else:
                    w = self.probability_weighting(p, is_gain=False) - \
                        self.probability_weighting(cum_probs[i-1], is_gain=False)
                weights.append(w)

            # CPT value for losses
            for v, w in zip(loss_outcomes, weights, strict=False):
                cpt_value += self.value_function(v) * w  # type: ignore[assignment]

        return cpt_value

    def expected_utility(self, outcomes: list[float],
                         probabilities: list[float],
                         utility_fn: Callable = None) -> float:  # type: ignore[assignment]
        """
        Calculate expected utility for comparison.

        Args:
            outcomes: List of outcomes
            probabilities: List of probabilities
            utility_fn: Utility function (default: log)

        Returns:
            Expected utility
        """
        fn = utility_fn if utility_fn is not None else lambda x: float(np.log(x + 100)) if x + 100 > 0 else -100.0

        return sum(p * fn(o) for o, p in zip(outcomes, probabilities, strict=False))  # type: ignore[no-any-return]

    def analyze_gamble(self, outcomes: list[float],
                       probabilities: list[float],
                       name: str = "Gamble") -> dict[str, Any]:
        """
        Analyze a gamble using CPT and EU.

        Args:
            outcomes: List of outcomes
            probabilities: List of probabilities
            name: Name of the gamble

        Returns:
            Dict with analysis
        """
        # Normalize probabilities
        probs = np.array(probabilities) / sum(probabilities)

        # CPT value
        cpt_value = self.cumulative_prospect_value(outcomes, probs.tolist())

        # Expected value
        ev = sum(o * p for o, p in zip(outcomes, probs, strict=False))

        # Expected utility (risk averse)
        eu = self.expected_utility(outcomes, probs.tolist())

        # Certainty equivalent
        def certainty_equivalent(cpt_val: Any) -> None:
            if cpt_val >= 0:
                return cpt_val ** (1 / self.config.alpha)  # type: ignore[no-any-return]
            else:
                return -((-cpt_val) / self.config.lambda_param) ** (1 / self.config.beta)  # type: ignore[no-any-return]

        ce = certainty_equivalent(cpt_value)  # type: ignore[func-returns-value]

        # Risk premium
        risk_premium = ev - ce

        return {
            "name": name,
            "outcomes": outcomes,
            "probabilities": probs.tolist(),
            "cpt_value": float(cpt_value),
            "expected_value": float(ev),
            "expected_utility": float(eu),
            "certainty_equivalent": float(ce),
            "risk_premium": float(risk_premium)
        }

    def fourfold_pattern(self) -> dict[str, Any]:
        """
        Demonstrate the fourfold pattern of risk attitudes.

        Returns:
            Dict with fourfold pattern analysis
        """
        gambles = {
            "high_prob_gain": {
                "outcomes": [3000, 0],
                "probs": [0.95, 0.05],
                "description": "95% chance of $3000"
            },
            "low_prob_gain": {
                "outcomes": [3000, 0],
                "probs": [0.05, 0.95],
                "description": "5% chance of $3000"
            },
            "high_prob_loss": {
                "outcomes": [-3000, 0],
                "probs": [0.95, 0.05],
                "description": "95% chance of losing $3000"
            },
            "low_prob_loss": {
                "outcomes": [-3000, 0],
                "probs": [0.05, 0.95],
                "description": "5% chance of losing $3000"
            }
        }

        results = {}
        for key, g in gambles.items():
            analysis = self.analyze_gamble(g["outcomes"], g["probs"], key)  # type: ignore[arg-type]
            analysis["description"] = g["description"]
            results[key] = analysis

        # Certainty equivalents for comparison
        certain_gains = [3000 * 0.95, 3000 * 0.05, -3000 * 0.95, -3000 * 0.05]
        cpt_ces = [results[k]["certainty_equivalent"] for k in gambles.keys()]

        return {
            "gambles": results,
            "pattern": {
                "high_prob_gain": "Risk averse (certainty seeking)",
                "low_prob_gain": "Risk seeking",
                "high_prob_loss": "Risk seeking",
                "low_prob_loss": "Risk averse (certainty seeking)"
            },
            "certainty_equivalents": dict(zip(gambles.keys(), cpt_ces, strict=False))
        }

    def loss_aversion_analysis(self) -> dict[str, Any]:
        """
        Analyze loss aversion effects.

        Returns:
            Dict with loss aversion analysis
        """
        cfg = self.config

        # Symmetric gain/loss prospects
        gain_gamble = self.analyze_gamble([100, 0], [0.5, 0.5], "Gain")
        loss_gamble = self.analyze_gamble([-100, 0], [0.5, 0.5], "Loss")

        # Mixed gamble
        mixed_gamble = self.analyze_gamble([100, -100], [0.5, 0.5], "Mixed")

        # Value sensitivity
        gains = [50, 100, 200, 500, 1000]
        loss_equivalents = []

        for g in gains:
            # Find loss that gives same magnitude of value
            gain_val = self.value_function(g)
            required_loss = (gain_val / cfg.lambda_param) ** (1 / cfg.beta)
            loss_equivalents.append(required_loss)

        return {
            "loss_aversion_coefficient": cfg.lambda_param,
            "gain_sensitivity": cfg.alpha,
            "loss_sensitivity": cfg.beta,
            "gain_gamble": gain_gamble,
            "loss_gamble": loss_gamble,
            "mixed_gamble": mixed_gamble,
            "loss_aversion_ratio": abs(loss_gamble["cpt_value"] / gain_gamble["cpt_value"]) if gain_gamble["cpt_value"] != 0 else float('inf'),
            "equivalent_losses": dict(zip(gains, loss_equivalents, strict=False))
        }

    def preference_reversals(self) -> dict[str, Any]:
        """
        Demonstrate common consequence and common ratio effects.

        Returns:
            Dict with preference reversal analysis
        """
        # Allais paradox - Common consequence effect
        problem_1a = self.analyze_gamble([2500, 0], [0.33, 0.67], "A")
        problem_1b = self.analyze_gamble([2400], [1.0], "B")

        problem_2a = self.analyze_gamble([2500, 2400, 0], [0.33, 0.66, 0.01], "A'")
        problem_2b = self.analyze_gamble([2400, 0], [0.34, 0.66], "B'")

        # Common ratio effect
        problem_3a = self.analyze_gamble([3000], [1.0], "C")
        problem_3b = self.analyze_gamble([4000, 0], [0.8, 0.2], "D")

        problem_4a = self.analyze_gamble([3000, 0], [0.25, 0.75], "C'")
        problem_4b = self.analyze_gamble([4000, 0], [0.2, 0.8], "D'")

        return {
            "common_consequence": {
                "problem_1": {"A": problem_1a, "B": problem_1b},
                "problem_2": {"A'": problem_2a, "B'": problem_2b},
                "explanation": "People prefer B over A but A' over B' (Allais paradox)"
            },
            "common_ratio": {
                "problem_3": {"C": problem_3a, "D": problem_3b},
                "problem_4": {"C'": problem_4a, "D'": problem_4b},
                "explanation": "People prefer C over D but D' over C'"
            },
            "cpt_prediction": "CPT can explain these reversals through probability weighting"
        }

    def run(self) -> dict[str, Any]:
        """Execute complete prospect theory analysis."""
        cfg = self.config

        # Fourfold pattern
        fourfold = self.fourfold_pattern()

        # Loss aversion
        loss_aversion = self.loss_aversion_analysis()

        # Preference reversals
        reversals = self.preference_reversals()

        # Value function shape
        x_range = np.linspace(-1000, 1000, 100)
        values = [self.value_function(x) for x in x_range]

        # Probability weighting
        p_range = np.linspace(0, 1, 50)
        w_gains = [self.probability_weighting(p, True) for p in p_range]
        w_losses = [self.probability_weighting(p, False) for p in p_range]

        return {
            "fourfold_pattern": fourfold,
            "loss_aversion": loss_aversion,
            "preference_reversals": reversals,
            "value_function": {
                "x": x_range.tolist(),
                "v": values
            },
            "probability_weighting": {
                "p": p_range.tolist(),
                "w_gains": w_gains,
                "w_losses": w_losses
            },
            "parameters": {
                "alpha": cfg.alpha,
                "beta": cfg.beta,
                "lambda": cfg.lambda_param,
                "gamma": cfg.gamma,
                "delta": cfg.delta
            },
            "model_type": "prospect_theory"
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 61,
            "name": "Prospect Theory",
            "category": "Behavioral Economics",
            "description": "Cumulative Prospect Theory with value function and probability weighting",
            "author": "Kahneman and Tversky",
            "year": 1979,
            "parameters": ["alpha", "beta", "lambda", "gamma", "delta"],
            "outputs": ["cpt_value", "certainty_equivalent", "fourfold_pattern"],
            "applications": ["behavioral_finance", "risk_management", "policy_design"]
        }


# Unit Tests
import unittest


class TestProspectTheoryModel(unittest.TestCase):

    """TestProspectTheoryModel."""
    def test_value_function_concave_gains(self) -> None:
        """Test value function is concave for gains."""
        config = ProspectTheoryConfig()
        model = ProspectTheoryModel(config)

        v1 = model.value_function(100)
        v2 = model.value_function(200)

        # Diminishing sensitivity: v(200) < 2*v(100)
        self.assertLess(v2, 2 * v1)

    def test_value_function_convex_losses(self) -> None:
        """Test value function is convex for losses."""
        config = ProspectTheoryConfig()
        model = ProspectTheoryModel(config)

        v1 = model.value_function(-100)
        v2 = model.value_function(-200)

        # Convex: v(-200) > 2*v(-100)
        self.assertGreater(v2, 2 * v1)

    def test_loss_aversion(self) -> None:
        """Test loss aversion coefficient."""
        config = ProspectTheoryConfig(lambda_param=2.25)
        model = ProspectTheoryModel(config)

        v_gain = model.value_function(100)
        v_loss = model.value_function(-100)

        # Loss should loom larger than gain
        self.assertGreater(abs(v_loss), v_gain)
        self.assertAlmostEqual(abs(v_loss) / v_gain, 2.25, delta=0.1)

    def test_probability_weighting_inverse_s(self) -> None:
        """Test probability weighting has inverse-S shape."""
        config = ProspectTheoryConfig()
        model = ProspectTheoryModel(config)

        # Overweight low probabilities
        w_low = model.probability_weighting(0.05)
        self.assertGreater(w_low, 0.05)

        # Underweight high probabilities
        w_high = model.probability_weighting(0.95)
        self.assertLess(w_high, 0.95)

        # Certainty effect
        self.assertAlmostEqual(model.probability_weighting(1.0), 1.0)
        self.assertAlmostEqual(model.probability_weighting(0.0), 0.0)

    def test_cpt_calculation(self) -> None:
        """Test CPT value calculation."""
        config = ProspectTheoryConfig()
        model = ProspectTheoryModel(config)

        outcomes = [100, -50]
        probs = [0.5, 0.5]

        cpt = model.cumulative_prospect_value(outcomes, probs)  # type: ignore[arg-type]

        # Should be finite
        self.assertTrue(np.isfinite(cpt))

    def test_fourfold_pattern(self) -> None:
        """Test fourfold pattern generation."""
        config = ProspectTheoryConfig()
        model = ProspectTheoryModel(config)

        fourfold = model.fourfold_pattern()

        self.assertIn("gambles", fourfold)
        self.assertEqual(len(fourfold["gambles"]), 4)

    def test_preference_reversals(self) -> None:
        """Test preference reversal demonstration."""
        config = ProspectTheoryConfig()
        model = ProspectTheoryModel(config)

        reversals = model.preference_reversals()

        self.assertIn("common_consequence", reversals)
        self.assertIn("common_ratio", reversals)


if __name__ == "__main__":
    # Run demonstration
    config = ProspectTheoryConfig()
    model = ProspectTheoryModel(config)
    result = model.run()

    print("=" * 60)
    print("PROSPECT THEORY MODEL (Cumulative)")
    print("=" * 60)
    print("\nParameters:")
    print(f"  alpha (gain curvature): {result['parameters']['alpha']}")
    print(f"  beta (loss curvature): {result['parameters']['beta']}")
    print(f"  lambda (loss aversion): {result['parameters']['lambda']}")

    print("\nLoss Aversion Analysis:")
    print(f"  Loss aversion coefficient: {result['loss_aversion']['loss_aversion_coefficient']}")
    print(f"  Loss aversion ratio: {result['loss_aversion']['loss_aversion_ratio']:.4f}")

    print("\nFourfold Pattern:")
    for key, val in result['fourfold']['pattern'].items():
        print(f"  {key}: {val}")

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for C4REQBER compatibility
ProspectTheoryPattern = ProspectTheoryModel
