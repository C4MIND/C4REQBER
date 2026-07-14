"""
Pattern 55: Option Pricing Model
Implements Black-Scholes, Binomial Tree, and Monte Carlo option pricing models
for European and American options.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm


@dataclass
class OptionPricingConfig:
    """Configuration for option pricing models."""

    S0: float = 100.0  # Initial stock price
    K: float = 100.0  # Strike price
    T: float = 1.0  # Time to maturity (years)
    r: float = 0.05  # Risk-free rate
    sigma: float = 0.2  # Volatility
    q: float = 0.0  # Dividend yield
    n_steps: int = 100  # Binomial tree steps
    n_simulations: int = 100000  # Monte Carlo simulations
    option_type: str = "call"  # "call" or "put"
    exercise_type: str = "european"  # "european" or "american"
    random_seed: int = 42


class OptionPricingModel:
    """
    Option pricing using multiple methods:
    - Black-Scholes (analytical)
    - Binomial Tree (discrete time)
    - Monte Carlo simulation
    """

    def __init__(self, config: OptionPricingConfig = None) -> None:  # type: ignore[assignment]
        self.config = config or OptionPricingConfig()
        np.random.seed(self.config.random_seed)

    def black_scholes(
        self,
        S: float = None,  # type: ignore[assignment]
        K: float = None,  # type: ignore[assignment]
        T: float = None,  # type: ignore[assignment]
        r: float = None,  # type: ignore[assignment]
        sigma: float = None,  # type: ignore[assignment]
        q: float = None,  # type: ignore[assignment]
        option_type: str = None,  # type: ignore[assignment]
    ) -> dict[str, float]:
        """
        Black-Scholes formula for European options.

        Returns:
            Dict with price and Greeks
        """
        cfg = self.config
        S = S or cfg.S0
        K = K or cfg.K
        T = T or cfg.T
        r = r or cfg.r
        sigma = sigma or cfg.sigma
        q = q or cfg.q
        option_type = option_type or cfg.option_type

        if T <= 0:
            # At expiry
            if option_type.lower() == "call":
                price = max(S - K, 0)
            else:
                price = max(K - S, 0)
            return {
                "price": price,
                "delta": 0,
                "gamma": 0,
                "theta": 0,
                "vega": 0,
                "rho": 0,
            }

        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type.lower() == "call":
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(
                d2
            )
            delta = np.exp(-q * T) * norm.cdf(d1)
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(
                -d1
            )
            delta = -np.exp(-q * T) * norm.cdf(-d1)
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

        # Greeks
        gamma = np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
        vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)

        theta = -(S * norm.pdf(d1) * sigma * np.exp(-q * T)) / (2 * np.sqrt(T))
        theta += (
            q * S * np.exp(-q * T) * norm.cdf(d1)
            if option_type.lower() == "call"
            else -q * S * np.exp(-q * T) * norm.cdf(-d1)
        )
        theta += (
            -r * K * np.exp(-r * T) * norm.cdf(d2)
            if option_type.lower() == "call"
            else r * K * np.exp(-r * T) * norm.cdf(-d2)
        )

        return {
            "price": float(price),
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho),
            "d1": float(d1),
            "d2": float(d2),
            "implied_volatility": float(sigma),
        }

    def binomial_tree(self, american: bool = False) -> dict[str, Any]:
        """
        Cox-Ross-Rubinstein binomial tree model.

        Args:
            american: Whether to price American option

        Returns:
            Dict with price and tree structure
        """
        cfg = self.config
        S0, K, T, r, sigma, q, n = (
            cfg.S0,
            cfg.K,
            cfg.T,
            cfg.r,
            cfg.sigma,
            cfg.q,
            cfg.n_steps,
        )

        dt = T / n
        u = np.exp(sigma * np.sqrt(dt))  # Up factor
        d = 1 / u  # Down factor
        p = (np.exp((r - q) * dt) - d) / (u - d)  # Risk-neutral probability

        # Discount factor
        disc = np.exp(-r * dt)

        # Stock price tree
        stock_tree = np.zeros((n + 1, n + 1))
        for i in range(n + 1):
            for j in range(i + 1):
                stock_tree[j, i] = S0 * (u ** (i - j)) * (d**j)

        # Option value tree
        option_tree = np.zeros((n + 1, n + 1))

        # Terminal values
        for j in range(n + 1):
            if cfg.option_type.lower() == "call":
                option_tree[j, n] = max(stock_tree[j, n] - K, 0)
            else:
                option_tree[j, n] = max(K - stock_tree[j, n], 0)

        # Backward induction
        for i in range(n - 1, -1, -1):
            for j in range(i + 1):
                # Expected value (risk-neutral)
                expected = disc * (
                    p * option_tree[j, i + 1] + (1 - p) * option_tree[j + 1, i + 1]
                )

                if american or cfg.exercise_type.lower() == "american":
                    # Early exercise value
                    if cfg.option_type.lower() == "call":
                        exercise = max(stock_tree[j, i] - K, 0)
                    else:
                        exercise = max(K - stock_tree[j, i], 0)
                    option_tree[j, i] = max(expected, exercise)
                else:
                    option_tree[j, i] = expected

        # Calculate Greeks using finite differences
        price = option_tree[0, 0]
        delta = (option_tree[0, 1] - option_tree[1, 1]) / (
            stock_tree[0, 1] - stock_tree[1, 1]
        )
        gamma = (
            (option_tree[0, 2] - option_tree[1, 2])
            / (stock_tree[0, 2] - stock_tree[1, 2])
            - (option_tree[1, 2] - option_tree[2, 2])
            / (stock_tree[1, 2] - stock_tree[2, 2])
        ) / ((stock_tree[0, 2] - stock_tree[2, 2]) / 2)

        return {
            "price": float(price),
            "delta": float(delta),
            "gamma": float(gamma),
            "up_factor": float(u),
            "down_factor": float(d),
            "risk_neutral_prob": float(p),
            "stock_tree": stock_tree[:5, :5].tolist(),  # First 5 levels
            "option_tree": option_tree[:5, :5].tolist(),
        }

    def monte_carlo(
        self, n_simulations: int = None, antithetic: bool = True  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """
        Monte Carlo simulation for option pricing.

        Args:
            n_simulations: Number of paths to simulate
            antithetic: Use antithetic variates for variance reduction

        Returns:
            Dict with price estimate and confidence interval
        """
        cfg = self.config
        n = n_simulations or cfg.n_simulations
        S0, K, T, r, sigma, q = cfg.S0, cfg.K, cfg.T, cfg.r, cfg.sigma, cfg.q

        dt = T / cfg.n_steps

        if antithetic:
            n_half = n // 2
            Z = np.random.standard_normal((n_half, cfg.n_steps))
            Z = np.vstack([Z, -Z])  # Antithetic variates
            n = n_half * 2
        else:
            Z = np.random.standard_normal((n, cfg.n_steps))

        # Simulate paths
        S = np.zeros((n, cfg.n_steps + 1))
        S[:, 0] = S0

        for t in range(1, cfg.n_steps + 1):
            S[:, t] = S[:, t - 1] * np.exp(
                (r - q - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z[:, t - 1]
            )

        # Payoffs
        if cfg.option_type.lower() == "call":
            payoffs = np.maximum(S[:, -1] - K, 0)
        else:
            payoffs = np.maximum(K - S[:, -1], 0)

        # Discount
        prices = np.exp(-r * T) * payoffs

        # Statistics
        price = np.mean(prices)
        std_error = np.std(prices) / np.sqrt(n)
        ci_lower = price - 1.96 * std_error
        ci_upper = price + 1.96 * std_error

        return {
            "price": float(price),
            "std_error": float(std_error),
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
            "n_simulations": n,
            "paths": S[:10, :].tolist(),  # First 10 paths
        }

    def implied_volatility(self, market_price: float, tol: float = 1e-6) -> float:
        """
        Calculate implied volatility from market price.

        Args:
            market_price: Observed market price
            tol: Tolerance for convergence

        Returns:
            Implied volatility
        """
        try:

            def objective(sigma: Any) -> Any:
                """Objective."""
                price = self.black_scholes(sigma=sigma)["price"]
                return price - market_price

            iv = brentq(objective, 0.001, 5.0, xtol=tol)
            return iv  # type: ignore[no-any-return]
        except (ValueError, RuntimeError):
            return None  # type: ignore[return-value]

    def sensitivity_analysis(self) -> dict[str, list]:
        """
        Perform sensitivity analysis on key parameters.

        Returns:
            Dict with price sensitivities
        """
        cfg = self.config

        # Vary stock price
        S_range = np.linspace(cfg.K * 0.5, cfg.K * 1.5, 50)
        prices_S = [self.black_scholes(S=s)["price"] for s in S_range]

        # Vary volatility
        sigma_range = np.linspace(0.05, 0.5, 50)
        prices_sigma = [self.black_scholes(sigma=s)["price"] for s in sigma_range]

        # Vary time to maturity
        T_range = np.linspace(0.1, 2.0, 50)
        prices_T = [self.black_scholes(T=t)["price"] for t in T_range]

        # Vary interest rate
        r_range = np.linspace(0.0, 0.1, 50)
        prices_r = [self.black_scholes(r=rate)["price"] for rate in r_range]

        return {
            "stock_price": {"parameter": S_range.tolist(), "price": prices_S},  # type: ignore[dict-item]
            "volatility": {"parameter": sigma_range.tolist(), "price": prices_sigma},  # type: ignore[dict-item]
            "time_to_maturity": {"parameter": T_range.tolist(), "price": prices_T},  # type: ignore[dict-item]
            "interest_rate": {"parameter": r_range.tolist(), "price": prices_r},  # type: ignore[dict-item]
        }

    def run(self) -> dict[str, Any]:
        """
        Execute complete option pricing analysis.

        Returns:
            Dict with all pricing methods and analysis
        """
        # Black-Scholes
        bs_result = self.black_scholes()

        # Binomial Tree
        binomial_european = self.binomial_tree(american=False)
        binomial_american = self.binomial_tree(american=True)

        # Monte Carlo
        mc_result = self.monte_carlo()

        # Implied volatility (from binomial price as "market price")
        iv = self.implied_volatility(binomial_european["price"])

        # Sensitivity analysis
        sensitivity = self.sensitivity_analysis()

        # Convergence analysis for binomial tree
        convergence = []
        for n in [10, 20, 50, 100, 200, 500]:
            self.config.n_steps = n
            price = self.binomial_tree(american=False)["price"]
            convergence.append({"steps": n, "price": price})
        self.config.n_steps = 100  # Reset

        return {
            "black_scholes": bs_result,
            "binomial_european": binomial_european,
            "binomial_american": binomial_american,
            "american_premium": binomial_american["price"] - binomial_european["price"],
            "monte_carlo": mc_result,
            "implied_volatility": iv,
            "sensitivity": sensitivity,
            "binomial_convergence": convergence,
            "model_type": "option_pricing",
            "parameters": {
                "S0": self.config.S0,
                "K": self.config.K,
                "T": self.config.T,
                "r": self.config.r,
                "sigma": self.config.sigma,
                "option_type": self.config.option_type,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 55,
            "name": "Option Pricing",
            "category": "Financial Derivatives",
            "description": "Black-Scholes, Binomial Tree, and Monte Carlo option pricing",
            "author": "Black, Scholes, Merton; Cox, Ross, Rubinstein",
            "year": 1973,
            "parameters": ["S0", "K", "T", "r", "sigma", "option_type"],
            "outputs": ["price", "greeks", "implied_volatility"],
            "applications": ["derivatives_pricing", "risk_management", "hedging"],
        }


# Unit Tests
import unittest


class TestOptionPricingModel(unittest.TestCase):
    """TestOptionPricingModel."""
    def test_black_scholes_call(self) -> None:
        """Test Black-Scholes call price."""
        config = OptionPricingConfig(
            S0=100, K=100, T=1, r=0.05, sigma=0.2, option_type="call"
        )
        model = OptionPricingModel(config)
        result = model.black_scholes()

        # At-the-money call with these parameters should be around 10
        self.assertGreater(result["price"], 5)
        self.assertLess(result["price"], 20)

        # Delta should be around 0.6 for ATM call
        self.assertGreater(result["delta"], 0.5)
        self.assertLess(result["delta"], 0.7)

    def test_black_scholes_put_call_parity(self) -> None:
        """Test put-call parity."""
        config = OptionPricingConfig(S0=100, K=100, T=1, r=0.05, sigma=0.2, q=0.02)

        # Call price
        config.option_type = "call"
        model_call = OptionPricingModel(config)
        call_price = model_call.black_scholes()["price"]

        # Put price
        config.option_type = "put"
        model_put = OptionPricingModel(config)
        put_price = model_put.black_scholes()["price"]

        # Put-call parity: C - P = S0 * exp(-qT) - K * exp(-rT)
        lhs = call_price - put_price
        rhs = config.S0 * np.exp(-config.q * config.T) - config.K * np.exp(
            -config.r * config.T
        )

        self.assertAlmostEqual(lhs, rhs, delta=0.01)

    def test_binomial_convergence(self) -> None:
        """Test binomial tree converges to Black-Scholes."""
        config = OptionPricingConfig(n_steps=500, option_type="call")
        model = OptionPricingModel(config)

        bs_price = model.black_scholes()["price"]
        binomial_price = model.binomial_tree(american=False)["price"]

        # Should be close for large n
        self.assertAlmostEqual(bs_price, binomial_price, delta=0.5)

    def test_american_put_premium(self) -> None:
        """Test American put has early exercise premium."""
        config = OptionPricingConfig(option_type="put", S0=80, K=100)
        model = OptionPricingModel(config)

        european = model.binomial_tree(american=False)["price"]
        american = model.binomial_tree(american=True)["price"]

        # American should be worth more (or equal)
        self.assertGreaterEqual(american, european)

    def test_implied_volatility(self) -> None:
        """Test implied volatility calculation."""
        config = OptionPricingConfig(sigma=0.25)
        model = OptionPricingModel(config)

        # Get theoretical price
        theoretical_price = model.black_scholes()["price"]

        # Recover implied volatility
        iv = model.implied_volatility(theoretical_price)

        self.assertIsNotNone(iv)
        self.assertAlmostEqual(iv, 0.25, delta=0.001)

    def test_monte_carlo_properties(self) -> None:
        """Test Monte Carlo returns reasonable results."""
        config = OptionPricingConfig(n_simulations=10000)
        model = OptionPricingModel(config)

        mc = model.monte_carlo()
        bs = model.black_scholes()["price"]

        # Monte Carlo should be within confidence interval of BS
        self.assertGreater(mc["ci_lower"], 0)
        self.assertGreater(mc["ci_upper"], mc["price"])

        # Price should be close to Black-Scholes
        self.assertAlmostEqual(mc["price"], bs, delta=1.0)


if __name__ == "__main__":
    # Run demonstration
    config = OptionPricingConfig(S0=100, K=100, T=1.0, r=0.05, sigma=0.2)
    model = OptionPricingModel(config)
    result = model.run()

    print("=" * 60)
    print("OPTION PRICING MODEL")
    print("=" * 60)
    print(f"\nBlack-Scholes Price: {result['black_scholes']['price']:.4f}")
    print(f"Binomial Tree Price: {result['binomial_european']['price']:.4f}")
    print(
        f"Monte Carlo Price: {result['monte_carlo']['price']:.4f} ± {result['monte_carlo']['std_error']:.4f}"
    )
    print("\nGreeks (BS):")
    print(f"  Delta: {result['black_scholes']['delta']:.4f}")
    print(f"  Gamma: {result['black_scholes']['gamma']:.4f}")
    print(f"  Vega:  {result['black_scholes']['vega']:.4f}")
    print(f"  Theta: {result['black_scholes']['theta']:.4f}")
    print(f"  Rho:   {result['black_scholes']['rho']:.4f}")

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for C4REQBER compatibility
OptionPricingPattern = OptionPricingModel
