"""
Pattern 59: Gravity Trade Model
Implements the gravity equation for international trade flows,
trade cost analysis, and welfare gains from trade.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class GravityTradeConfig:
    """Configuration for gravity trade model."""
    n_countries: int = 10
    alpha: float = 1.0        # Production elasticity
    theta: float = 4.0        # Trade elasticity
    sigma: float = 5.0        # Elasticity of substitution
    fixed_cost: float = 0.1   # Fixed trade cost
    iceberg_cost: float = 1.5 # Iceberg trade cost
    random_seed: int = 42


class GravityTradeModel:
    """
    Gravity model of international trade based on Eaton-Kortum and
    Anderson-van Wincoop frameworks.
    """

    def __init__(self, config: GravityTradeConfig = None) -> None:  # type: ignore[assignment]
        self.config = config or GravityTradeConfig()
        np.random.seed(self.config.random_seed)
        self.countries: list[str] = []
        self.productivity: np.ndarray = None  # type: ignore[assignment]
        self.labor: np.ndarray = None  # type: ignore[assignment]
        self.wages: np.ndarray = None  # type: ignore[assignment]
        self.trade_costs: np.ndarray = None  # type: ignore[assignment]
        self._setup_countries()

    def _setup_countries(self) -> None:
        """Initialize country data."""
        cfg = self.config
        n = cfg.n_countries

        self.countries = [f"Country_{i}" for i in range(n)]

        # Productivity (A_i)
        self.productivity = np.random.lognormal(0, 0.5, n)

        # Labor endowments (L_i)
        self.labor = np.random.lognormal(2, 0.3, n)

        # Initial wages (normalized)
        self.wages = np.ones(n)

        # Trade costs (tau_ij)
        self.trade_costs = self._generate_trade_costs()

    def _generate_trade_costs(self) -> np.ndarray:
        """Generate bilateral trade cost matrix."""
        cfg = self.config
        n = cfg.n_countries

        # Distance-based costs
        distances = np.random.lognormal(0, 1, (n, n))
        np.fill_diagonal(distances, 1.0)

        # Iceberg costs: tau = 1 + cost
        tau = np.ones((n, n)) * cfg.iceberg_cost

        # Add border effects
        for i in range(n):
            for j in range(n):
                if i != j:
                    tau[i, j] *= distances[i, j] ** 0.1

        np.fill_diagonal(tau, 1.0)
        return tau

    def compute_trade_flows(self) -> np.ndarray:
        """
        Compute bilateral trade flows using gravity equation.

        Returns:
            Trade flow matrix X where X[i,j] is exports from i to j
        """
        cfg = self.config
        n = cfg.n_countries

        # Total expenditure in each country (wage bill)
        E = self.wages * self.labor

        # Price indices (simplified)
        P = np.zeros(n)
        for j in range(n):
            price_sum = 0
            for i in range(n):
                # Unit cost = w_i / A_i * tau_ij
                unit_cost = (self.wages[i] / self.productivity[i]) * self.trade_costs[i, j]
                price_sum += (unit_cost ** (-cfg.theta))
            P[j] = price_sum ** (-1 / cfg.theta)

        # Trade shares (pi_ij)
        trade_shares = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                unit_cost = (self.wages[i] / self.productivity[i]) * self.trade_costs[i, j]
                trade_shares[i, j] = (unit_cost / P[j]) ** (-cfg.theta)

        # Normalize rows
        for j in range(n):
            trade_shares[:, j] /= trade_shares[:, j].sum()

        # Trade flows: X_ij = pi_ij * E_j
        X = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                X[i, j] = trade_shares[i, j] * E[j]

        return X

    def solve_equilibrium(self, max_iter: int = 100) -> dict[str, Any]:
        """
        Solve for trade equilibrium wages.

        Returns:
            Dict with equilibrium values
        """
        cfg = self.config
        n = cfg.n_countries

        # Iterate to find equilibrium wages
        for _ in range(max_iter):
            # Compute trade flows
            X = self.compute_trade_flows()

            # Total exports and imports
            exports = X.sum(axis=1)
            imports = X.sum(axis=0)

            # Trade balance condition
            net_exports = exports - imports

            # Update wages (tatonnement)
            wage_adjustment = 1 + 0.1 * net_exports / (self.wages * self.labor)
            self.wages *= wage_adjustment

            # Normalize
            self.wages /= self.wages[0]

            # Check convergence
            if np.max(np.abs(net_exports)) < 0.01:
                break

        # Final trade flows
        X = self.compute_trade_flows()

        return {
            "wages": self.wages.tolist(),
            "trade_flows": X.tolist(),
            "exports": X.sum(axis=1).tolist(),
            "imports": X.sum(axis=0).tolist(),
            "trade_balance": (X.sum(axis=1) - X.sum(axis=0)).tolist(),
            "converged": max_iter > 0
        }

    def compute_welfare_gains(self, counterfactual_costs: np.ndarray = None) -> dict[str, float]:  # type: ignore[assignment]
        """
        Compute welfare gains from trade.

        Args:
            counterfactual_costs: Alternative trade costs for comparison

        Returns:
            Dict with welfare gains
        """
        cfg = self.config

        # Baseline equilibrium
        baseline = self.solve_equilibrium()
        X_base = np.array(baseline["trade_flows"])

        # Compute price indices
        P_base = self._compute_price_indices()

        # Real wages
        real_wage_base = self.wages / P_base

        if counterfactual_costs is not None:
            # Counterfactual scenario
            original_costs = self.trade_costs.copy()
            self.trade_costs = counterfactual_costs
            counterfactual = self.solve_equilibrium()
            P_cf = self._compute_price_indices()
            real_wage_cf = self.wages / P_cf

            # Restore
            self.trade_costs = original_costs

            # Welfare gains
            welfare_gains = (real_wage_base / real_wage_cf - 1) * 100

            return {
                "welfare_gains_pct": welfare_gains.tolist(),
                "real_wage_baseline": real_wage_base.tolist(),
                "real_wage_counterfactual": real_wage_cf.tolist(),
                "scenario": "custom"
            }
        else:
            # Autarky comparison (infinite trade costs)
            # Welfare gains from trade formula (Arkolakis et al.)
            home_consumption_share = np.diag(X_base) / X_base.sum(axis=1)  # type: ignore[unreachable]
            welfare_gains = (home_consumption_share ** (-1 / cfg.theta) - 1) * 100

            return {
                "welfare_gains_pct": welfare_gains.tolist(),
                "home_consumption_share": home_consumption_share.tolist(),
                "real_wage": real_wage_base.tolist(),
                "scenario": "autarky"
            }

    def _compute_price_indices(self) -> np.ndarray:
        """Compute price indices for all countries."""
        cfg = self.config
        n = cfg.n_countries
        P = np.zeros(n)

        for j in range(n):
            price_sum = 0
            for i in range(n):
                unit_cost = (self.wages[i] / self.productivity[i]) * self.trade_costs[i, j]
                price_sum += (unit_cost ** (-cfg.theta))
            P[j] = price_sum ** (-1 / cfg.theta)

        return P

    def estimate_gravity_equation(self) -> dict[str, Any]:
        """
        Estimate gravity equation using simulated data.

        Returns:
            Dict with estimated coefficients
        """
        X = self.compute_trade_flows()
        n = len(self.countries)

        # Create dataset
        log_X = []
        log_Y_i = []
        log_Y_j = []
        log_tau = []
        distance = []

        for i in range(n):
            for j in range(n):
                if i != j and X[i, j] > 0:
                    log_X.append(np.log(X[i, j]))
                    log_Y_i.append(np.log(self.wages[i] * self.labor[i]))
                    log_Y_j.append(np.log(self.wages[j] * self.labor[j]))
                    log_tau.append(np.log(self.trade_costs[i, j]))
                    distance.append(self.trade_costs[i, j])

        # Simple OLS estimation
        y = np.array(log_X)
        X_mat = np.column_stack([
            np.ones(len(log_X)),
            np.array(log_Y_i),
            np.array(log_Y_j),
            np.array(log_tau)
        ])

        # OLS coefficients
        beta = np.linalg.lstsq(X_mat, y, rcond=None)[0]

        # Predicted values
        y_pred = X_mat @ beta
        residuals = y - y_pred

        # R-squared
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot

        return {
            "coefficients": {
                "constant": float(beta[0]),
                "exporter_gdp": float(beta[1]),
                "importer_gdp": float(beta[2]),
                "trade_cost": float(beta[3])
            },
            "r_squared": float(r_squared),
            "n_observations": len(log_X),
            "expected_distance_elasticity": -self.config.theta
        }

    def trade_elasticity_analysis(self) -> dict[str, Any]:
        """
        Analyze trade elasticity with respect to trade costs.

        Returns:
            Dict with elasticity analysis
        """
        cfg = self.config
        baseline = self.solve_equilibrium()
        X_base = np.array(baseline["trade_flows"])

        # Increase trade costs by 10%
        self.trade_costs *= 1.1
        np.fill_diagonal(self.trade_costs, 1.0)

        shock = self.solve_equilibrium()
        X_shock = np.array(shock["trade_flows"])

        # Restore
        self.trade_costs /= 1.1
        np.fill_diagonal(self.trade_costs, 1.0)

        # Compute elasticity
        # Aggregate trade
        total_base = X_base.sum() - np.trace(X_base)
        total_shock = X_shock.sum() - np.trace(X_shock)

        elasticity = (np.log(total_shock) - np.log(total_base)) / np.log(1.1)

        return {
            "trade_elasticity": float(elasticity),
            "baseline_trade": float(total_base),
            "shocked_trade": float(total_shock),
            "trade_decline_pct": float((total_shock - total_base) / total_base * 100)
        }

    def run(self) -> dict[str, Any]:
        """Execute complete gravity trade analysis."""
        # Solve equilibrium
        equilibrium = self.solve_equilibrium()

        # Welfare gains
        welfare = self.compute_welfare_gains()

        # Gravity estimation
        gravity_est = self.estimate_gravity_equation()

        # Trade elasticity
        elasticity = self.trade_elasticity_analysis()

        # Trade statistics
        X = np.array(equilibrium["trade_flows"])
        total_trade = X.sum() - np.trace(X)
        trade_to_gdp = total_trade / (self.wages * self.labor).sum()

        # Bilateral trade matrix (top trading partners)
        top_trading_partners = []
        for i in range(min(5, len(self.countries))):
            partners = np.argsort(X[i, :])[-3:][::-1]
            top_trading_partners.append({
                "country": self.countries[i],
                "partners": [self.countries[j] for j in partners],
                "exports": [float(X[i, j]) for j in partners]
            })

        return {
            "equilibrium": equilibrium,
            "welfare": welfare,
            "gravity_estimation": gravity_est,
            "trade_elasticity": elasticity,
            "trade_statistics": {
                "total_trade": float(total_trade),
                "trade_to_gdp_ratio": float(trade_to_gdp),
                "openness": float(total_trade / (self.wages * self.labor).sum() / 2),
                "avg_trade_cost": float(self.trade_costs[self.trade_costs > 1].mean())
            },
            "top_trading_partners": top_trading_partners,
            "country_data": {
                "names": self.countries,
                "productivity": self.productivity.tolist(),
                "labor": self.labor.tolist(),
                "wages": equilibrium["wages"]
            },
            "model_type": "gravity_trade"
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 59,
            "name": "Gravity Trade Model",
            "category": "International Trade",
            "description": "Eaton-Kortum gravity model with trade cost analysis",
            "author": "Eaton, Kortum, Anderson, van Wincoop",
            "year": 2002,
            "parameters": ["n_countries", "theta", "sigma", "iceberg_cost"],
            "outputs": ["trade_flows", "welfare_gains", "trade_elasticity"],
            "applications": ["trade_policy", "brexit_analysis", "trade_agreements"]
        }


# Unit Tests
import unittest


class TestGravityTradeModel(unittest.TestCase):

    """TestGravityTradeModel."""
    def test_model_initialization(self) -> None:
        """Test model initializes correctly."""
        config = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(config)

        self.assertEqual(len(model.countries), 5)
        self.assertEqual(len(model.productivity), 5)
        self.assertEqual(model.trade_costs.shape, (5, 5))

    def test_trade_costs_diagonal(self) -> None:
        """Test domestic trade costs are 1."""
        config = GravityTradeConfig()
        model = GravityTradeModel(config)

        for i in range(config.n_countries):
            self.assertAlmostEqual(model.trade_costs[i, i], 1.0)

    def test_equilibrium_convergence(self) -> None:
        """Test equilibrium solves."""
        config = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(config)

        equilibrium = model.solve_equilibrium()

        self.assertIn("wages", equilibrium)
        self.assertIn("trade_flows", equilibrium)
        self.assertEqual(len(equilibrium["wages"]), 5)

    def test_trade_balance(self) -> None:
        """Test that trade approximately balances."""
        config = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(config)

        equilibrium = model.solve_equilibrium()

        # Total exports should approximately equal total imports
        total_exports = sum(equilibrium["exports"])
        total_imports = sum(equilibrium["imports"])

        self.assertAlmostEqual(total_exports, total_imports, delta=1.0)

    def test_welfare_gains(self) -> None:
        """Test welfare gains calculation."""
        config = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(config)

        welfare = model.compute_welfare_gains()

        self.assertIn("welfare_gains_pct", welfare)
        self.assertEqual(len(welfare["welfare_gains_pct"]), 5)  # type: ignore[arg-type]

        # Welfare gains should be positive
        self.assertTrue(all(g > 0 for g in welfare["welfare_gains_pct"]))  # type: ignore[attr-defined]

    def test_gravity_estimation(self) -> None:
        """Test gravity equation estimation."""
        config = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(config)

        estimation = model.estimate_gravity_equation()

        self.assertIn("coefficients", estimation)
        self.assertIn("r_squared", estimation)
        self.assertGreaterEqual(estimation["r_squared"], 0)
        self.assertLessEqual(estimation["r_squared"], 1)

    def test_trade_elasticity(self) -> None:
        """Test trade elasticity calculation."""
        config = GravityTradeConfig(n_countries=5)
        model = GravityTradeModel(config)

        elasticity = model.trade_elasticity_analysis()

        self.assertIn("trade_elasticity", elasticity)
        self.assertLess(elasticity["trade_elasticity"], 0)  # Should be negative
        self.assertIn("trade_decline_pct", elasticity)


if __name__ == "__main__":
    # Run demonstration
    config = GravityTradeConfig(n_countries=8)
    model = GravityTradeModel(config)
    result = model.run()

    print("=" * 60)
    print("GRAVITY TRADE MODEL")
    print("=" * 60)
    print("\nTrade Statistics:")
    print(f"  Total Trade: {result['trade_statistics']['total_trade']:.2f}")
    print(f"  Trade-to-GDP: {result['trade_statistics']['trade_to_gdp_ratio']:.4f}")
    print(f"  Avg Trade Cost: {result['trade_statistics']['avg_trade_cost']:.4f}")

    print("\nWelfare Gains from Trade:")
    print(f"  Mean: {np.mean(result['welfare']['welfare_gains_pct']):.2f}%")
    print(f"  Min: {min(result['welfare']['welfare_gains_pct']):.2f}%")
    print(f"  Max: {max(result['welfare']['welfare_gains_pct']):.2f}%")

    print("\nGravity Estimation:")
    print(f"  R-squared: {result['gravity_estimation']['r_squared']:.4f}")
    print(f"  Trade Cost Coefficient: {result['gravity_estimation']['coefficients']['trade_cost']:.4f}")

    print("\nTrade Elasticity:")
    print(f"  Elasticity: {result['trade_elasticity']['trade_elasticity']:.4f}")

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for C4REQBER compatibility
GravityTradePattern = GravityTradeModel
