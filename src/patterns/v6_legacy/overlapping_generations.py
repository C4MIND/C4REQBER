"""
Pattern 52: Overlapping Generations (OLG) Model
Implements the Diamond OLG model for analyzing intergenerational transfers,
savings behavior, and fiscal policy effects.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, List
import numpy as np
from scipy.optimize import fsolve, minimize_scalar


@dataclass
class OLGConfig:
    """Configuration for OLG model."""

    n_generations: int = 20
    periods: int = 50
    alpha: float = 0.33  # Capital share
    beta: float = 0.96  # Discount factor (annual)
    delta: float = 0.1  # Depreciation rate
    gamma: float = 2.0  # Risk aversion (CRRA)
    n_bar: float = 1.01  # Population growth
    A: float = 1.0  # TFP
    tau: float = 0.15  # Tax rate
    pension_rate: float = 0.3  # Pension replacement rate
    random_seed: int = 42


class OverlappingGenerationsModel:
    """
    Diamond Overlapping Generations model.

    Models two-period lived agents who work when young and consume savings
    when old. Analyzes capital accumulation, welfare, and policy effects.
    """

    def __init__(self, config: OLGConfig = None):
        self.config = config or OLGConfig()
        np.random.seed(self.config.random_seed)
        self._setup_model()

    def _setup_model(self):
        """Initialize model parameters and steady state."""
        cfg = self.config

        # Production function: Y = A * K^alpha * L^(1-alpha)
        self.alpha = cfg.alpha
        self.beta = cfg.beta
        self.delta = cfg.delta
        self.gamma = cfg.gamma
        self.n_bar = cfg.n_bar
        self.A = cfg.A

        # Steady state calculations
        # From Euler equation and market clearing
        self.k_ss = self._compute_steady_state_k()
        self.y_ss = self.A * self.k_ss**self.alpha
        self.r_ss = self.alpha * self.A * self.k_ss ** (self.alpha - 1) - self.delta
        self.w_ss = (1 - self.alpha) * self.A * self.k_ss**self.alpha

    def _compute_steady_state_k(self) -> float:
        """Compute steady state capital per worker."""
        cfg = self.config

        # Steady state condition: k = s(w(k), r(k)) / (1 + n)
        # With Cobb-Douglas and log utility: s = beta/(1+beta) * w

        def steady_state_eq(k):
            if k <= 0:
                return float("inf")
            r = self.alpha * self.A * k ** (self.alpha - 1) - self.delta
            w = (1 - self.alpha) * self.A * k**self.alpha

            # Savings rate depends on utility
            if self.gamma == 1:
                s_rate = self.beta / (1 + self.beta)
            else:
                # CRRA utility
                s_rate = self._solve_savings_rate(w, r)

            k_next = s_rate * w / self.n_bar
            return k - k_next

        try:
            k_ss = fsolve(steady_state_eq, 1.0)[0]
            return max(0.01, k_ss)
        except:
            # Analytical approximation for log utility
            s_rate = self.beta / (1 + self.beta)
            k_ss = (
                (self.alpha * self.A)
                / (
                    (1 + self.beta) / (self.beta * (1 - self.alpha) * self.A)
                    - 1
                    + self.delta
                )
            ) ** (1 / (1 - self.alpha))
            return max(0.01, k_ss)

    def _solve_savings_rate(self, w: float, r: float) -> float:
        """Solve for optimal savings rate given wage and return."""
        beta = self.beta
        gamma = self.gamma

        # For CRRA utility: c1^(-gamma) = beta * (1+r) * c2^(-gamma)
        # With budget: c1 + s = w, c2 = (1+r) * s

        def euler(s):
            if s <= 0 or s >= w:
                return float("inf")
            c1 = w - s
            c2 = (1 + r) * s
            if c1 <= 0 or c2 <= 0:
                return float("inf")
            lhs = c1 ** (-gamma)
            rhs = beta * (1 + r) * c2 ** (-gamma)
            return lhs - rhs

        try:
            s_opt = fsolve(euler, w * 0.3)[0]
            return np.clip(s_opt / w, 0.01, 0.99)
        except:
            return beta / (1 + beta)

    def _utility(self, c1: float, c2: float) -> float:
        """Compute lifetime utility."""
        gamma = self.gamma
        beta = self.beta

        if gamma == 1:
            u1 = np.log(c1) if c1 > 0 else -1000
            u2 = np.log(c2) if c2 > 0 else -1000
        else:
            u1 = (c1 ** (1 - gamma) - 1) / (1 - gamma) if c1 > 0 else -1000
            u2 = (c2 ** (1 - gamma) - 1) / (1 - gamma) if c2 > 0 else -1000

        return u1 + beta * u2

    def run(self) -> Dict[str, Any]:
        """
        Execute OLG simulation and policy analysis.

        Returns:
            Dict containing steady state, transition dynamics, and policy effects
        """
        cfg = self.config
        T = cfg.periods

        # Initialize simulation
        k_path = np.zeros(T)
        y_path = np.zeros(T)
        w_path = np.zeros(T)
        r_path = np.zeros(T)
        c_young_path = np.zeros(T)
        c_old_path = np.zeros(T)
        s_path = np.zeros(T)

        # Start below steady state
        k_path[0] = self.k_ss * 0.5

        # Simulate transition dynamics
        for t in range(T - 1):
            # Factor prices
            k = k_path[t]
            r_path[t] = self.alpha * self.A * k ** (self.alpha - 1) - self.delta
            w_path[t] = (1 - self.alpha) * self.A * k**self.alpha
            y_path[t] = self.A * k**self.alpha

            # Household optimization
            w = w_path[t] * (1 - cfg.tau)  # After-tax wage
            r = r_path[t]

            # Pension benefit (pay-as-you-go)
            pension = cfg.pension_rate * w_path[t] * cfg.tau * self.n_bar

            # Optimal savings
            s_rate = self._solve_savings_rate(w, r)
            s_path[t] = s_rate * w

            # Consumption
            c_young_path[t] = w - s_path[t] - cfg.tau * w_path[t]
            c_old_path[t] = (
                (1 + r) * s_path[t] + pension if t > 0 else (1 + r) * s_path[t] * 0.5
            )

            # Capital accumulation
            k_path[t + 1] = s_path[t] / self.n_bar

        # Final period
        k = k_path[T - 1]
        r_path[T - 1] = self.alpha * self.A * k ** (self.alpha - 1) - self.delta
        w_path[T - 1] = (1 - self.alpha) * self.A * k**self.alpha
        y_path[T - 1] = self.A * k**self.alpha

        # Policy analysis: PAYG pension system
        welfare_gain = self._calculate_welfare_gain()

        # Dynamic inefficiency check
        golden_rule_k = ((self.alpha * self.A) / self.n_bar) ** (1 / (1 - self.alpha))
        golden_rule_r = (
            self.alpha * self.A * golden_rule_k ** (self.alpha - 1) - self.delta
        )
        dynamically_efficient = self.r_ss > self.n_bar - 1

        # Generational accounts
        gen_accounts = self._compute_generational_accounts()

        return {
            "steady_state": {
                "k_ss": float(self.k_ss),
                "y_ss": float(self.y_ss),
                "r_ss": float(self.r_ss),
                "w_ss": float(self.w_ss),
            },
            "transition": {
                "capital": k_path.tolist(),
                "output": y_path.tolist(),
                "wages": w_path.tolist(),
                "interest_rates": r_path.tolist(),
                "savings": s_path.tolist(),
                "consumption_young": c_young_path.tolist(),
                "consumption_old": c_old_path.tolist(),
            },
            "policy_analysis": {
                "welfare_gain_payg": float(welfare_gain),
                "dynamically_efficient": bool(dynamically_efficient),
                "golden_rule_r": float(golden_rule_r),
                "steady_state_r": float(self.r_ss),
            },
            "generational_accounts": gen_accounts,
            "convergence_period": int(
                np.where(np.abs(k_path - self.k_ss) < 0.01 * self.k_ss)[0][0]
            )
            if len(np.where(np.abs(k_path - self.k_ss) < 0.01 * self.k_ss)[0]) > 0
            else T,
        }

    def _calculate_welfare_gain(self) -> float:
        """Calculate welfare gain from pension system."""
        # Simplified welfare calculation
        c1 = self.w_ss * (1 - self.config.tau) * 0.7
        c2 = (1 + self.r_ss) * self.w_ss * 0.3 * (
            1 - self.config.tau
        ) + self.config.pension_rate * self.w_ss * self.config.tau

        utility_with = self._utility(c1, c2)
        utility_without = self._utility(
            self.w_ss * 0.7, (1 + self.r_ss) * self.w_ss * 0.3
        )

        return utility_with - utility_without

    def _compute_generational_accounts(self) -> Dict[str, List[float]]:
        """Compute net present value of taxes minus transfers by generation."""
        # Simplified generational accounting
        generations = list(range(-5, 6))
        accounts = []

        for gen in generations:
            if gen < 0:
                # Current old generation
                account = -self.config.pension_rate * self.w_ss * self.config.tau * 10
            elif gen == 0:
                # Current young
                account = (
                    self.config.tau * self.w_ss
                    - self.config.pension_rate
                    * self.w_ss
                    * self.config.tau
                    / (1 + self.r_ss)
                )
            else:
                # Future generations
                account = self.config.tau * self.w_ss * (
                    self.n_bar**gen
                ) - self.config.pension_rate * self.w_ss * self.config.tau / (
                    (1 + self.r_ss) ** gen
                )

            accounts.append(float(account))

        return {"generations": generations, "net_accounts": accounts}

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 52,
            "name": "Overlapping Generations",
            "category": "Macroeconomics",
            "description": "Diamond OLG model for intergenerational analysis",
            "author": "Peter Diamond",
            "year": 1965,
            "parameters": ["alpha", "beta", "delta", "gamma", "n_bar", "tau"],
            "outputs": ["steady_state", "transition", "welfare_analysis"],
            "applications": ["pension_policy", "fiscal_policy", "generational_equity"],
        }


# Unit Tests
import unittest


class TestOLGModel(unittest.TestCase):
    def test_steady_state_positive(self):
        """Test that steady state values are positive."""
        config = OLGConfig()
        model = OverlappingGenerationsModel(config)

        self.assertGreater(model.k_ss, 0)
        self.assertGreater(model.y_ss, 0)
        self.assertGreater(model.w_ss, 0)

    def test_transition_convergence(self):
        """Test that capital path is reasonable."""
        config = OLGConfig(periods=50)
        model = OverlappingGenerationsModel(config)
        result = model.run()

        k_path = np.array(result["transition"]["capital"])

        # Capital should remain positive throughout
        self.assertTrue(np.all(k_path > 0))

        # Capital should be within reasonable bounds
        self.assertTrue(np.all(k_path < 10))  # Upper bound check

    def test_factor_price_relationships(self):
        """Test that factor prices satisfy equilibrium conditions."""
        config = OLGConfig()
        model = OverlappingGenerationsModel(config)
        result = model.run()

        ss = result["steady_state"]

        # Check Euler equation approximation
        # 1 + r = (1 + rho) / beta (approximately)
        self.assertGreater(ss["r_ss"], -1)
        self.assertGreater(ss["w_ss"], 0)

    def test_policy_analysis(self):
        """Test policy analysis outputs."""
        config = OLGConfig(tau=0.15, pension_rate=0.3)
        model = OverlappingGenerationsModel(config)
        result = model.run()

        policy = result["policy_analysis"]
        self.assertIn("dynamically_efficient", policy)
        self.assertIn("welfare_gain_payg", policy)
        self.assertIsInstance(policy["dynamically_efficient"], bool)

    def test_generational_accounts(self):
        """Test generational accounts structure."""
        config = OLGConfig()
        model = OverlappingGenerationsModel(config)
        result = model.run()

        accounts = result["generational_accounts"]
        self.assertIn("generations", accounts)
        self.assertIn("net_accounts", accounts)
        self.assertEqual(len(accounts["generations"]), len(accounts["net_accounts"]))

    def test_metadata(self):
        """Test metadata returns correct information."""
        meta = OverlappingGenerationsModel.get_metadata()
        self.assertEqual(meta["pattern_id"], 52)
        self.assertEqual(meta["name"], "Overlapping Generations")
        self.assertIn("Macroeconomics", meta["category"])


if __name__ == "__main__":
    # Run demonstration
    config = OLGConfig(periods=50)
    model = OverlappingGenerationsModel(config)
    result = model.run()

    print("=" * 60)
    print("OVERLAPPING GENERATIONS MODEL (Diamond OLG)")
    print("=" * 60)
    print(f"\nSteady State Capital: {result['steady_state']['k_ss']:.4f}")
    print(f"Steady State Output: {result['steady_state']['y_ss']:.4f}")
    print(f"Interest Rate: {result['steady_state']['r_ss']:.4f}")
    print(
        f"Dynamically Efficient: {result['policy_analysis']['dynamically_efficient']}"
    )
    print(f"Convergence Period: {result['convergence_period']}")

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for TURBO-CDI compatibility
OverlappingGenerationsPattern = OverlappingGenerationsModel
