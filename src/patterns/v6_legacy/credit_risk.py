"""
Pattern 56: Credit Risk Model
Implements credit risk models including:
- Merton structural model
- Copula models for portfolio credit risk
- CreditMetrics-style migration
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize


@dataclass
class CreditRiskConfig:
    """Configuration for credit risk models."""
    n_obligors: int = 100
    n_simulations: int = 10000
    time_horizon: float = 1.0
    recovery_rate: float = 0.4
    correlation: float = 0.2
    confidence_levels: List[float] = None
    random_seed: int = 42


class CreditRiskModel:
    """
    Credit risk modeling using multiple approaches:
    - Merton structural model
    - Gaussian copula for portfolio risk
    - Credit rating migration
    """
    
    def __init__(self, config: CreditRiskConfig = None):
        self.config = config or CreditRiskConfig()
        if self.config.confidence_levels is None:
            self.config.confidence_levels = [0.95, 0.99, 0.999]
        np.random.seed(self.config.random_seed)
    
    def merton_model(self, V0: float, K: float, sigma_V: float, 
                     r: float, T: float) -> Dict[str, float]:
        """
        Merton structural model for default probability.
        
        Args:
            V0: Firm asset value
            K: Debt face value
            sigma_V: Asset volatility
            r: Risk-free rate
            T: Time horizon
        
        Returns:
            Dict with default probability and credit spread
        """
        # Distance to default
        dd = (np.log(V0 / K) + (r + 0.5 * sigma_V ** 2) * T) / (sigma_V * np.sqrt(T))
        
        # Risk-neutral default probability
        pd = norm.cdf(-dd)
        
        # Expected recovery
        recovery = self.config.recovery_rate
        
        # Credit spread (approximate)
        if pd < 1:
            credit_spread = -np.log(1 - pd * (1 - recovery)) / T
        else:
            credit_spread = float('inf')
        
        # Equity value (call option on assets)
        d1 = dd
        d2 = d1 - sigma_V * np.sqrt(T)
        equity = V0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        
        # Debt value
        debt = V0 - equity
        
        return {
            "distance_to_default": float(dd),
            "default_probability": float(pd),
            "credit_spread": float(credit_spread),
            "equity_value": float(equity),
            "debt_value": float(debt),
            "firm_value": float(V0),
            "leverage": float(K / V0)
        }
    
    def gaussian_copula_simulation(self, exposures: np.ndarray, 
                                    default_probs: np.ndarray) -> Dict[str, Any]:
        """
        Gaussian copula model for portfolio credit risk.
        
        Args:
            exposures: Array of exposure at default for each obligor
            default_probs: Array of default probabilities
        
        Returns:
            Dict with portfolio loss distribution
        """
        cfg = self.config
        n = cfg.n_obligors
        m = cfg.n_simulations
        
        # Generate correlated latent variables
        # Factor model: Z_i = sqrt(rho) * F + sqrt(1-rho) * eps_i
        F = np.random.standard_normal(m)  # Common factor
        eps = np.random.standard_normal((m, n))  # Idiosyncratic
        
        rho = cfg.correlation
        Z = np.sqrt(rho) * F[:, np.newaxis] + np.sqrt(1 - rho) * eps
        
        # Default thresholds
        thresholds = norm.ppf(default_probs)
        
        # Defaults
        defaults = Z < thresholds
        
        # Losses
        lgd = 1 - cfg.recovery_rate  # Loss given default
        losses = defaults * exposures * lgd
        portfolio_losses = losses.sum(axis=1)
        
        # Expected loss
        el = np.mean(portfolio_losses)
        
        # Unexpected loss (standard deviation)
        ul = np.std(portfolio_losses)
        
        # Value at Risk and Expected Shortfall
        var = {}
        es = {}
        for cl in cfg.confidence_levels:
            var[cl] = np.percentile(portfolio_losses, cl * 100)
            es[cl] = np.mean(portfolio_losses[portfolio_losses >= var[cl]])
        
        # Loss distribution percentiles
        percentiles = [50, 75, 90, 95, 99, 99.9]
        loss_distribution = {p: np.percentile(portfolio_losses, p) for p in percentiles}
        
        return {
            "expected_loss": float(el),
            "unexpected_loss": float(ul),
            "var": {k: float(v) for k, v in var.items()},
            "expected_shortfall": {k: float(v) for k, v in es.items()},
            "loss_distribution": {k: float(v) for k, v in loss_distribution.items()},
            "correlation": float(rho),
            "loss_samples": portfolio_losses[:1000].tolist()
        }
    
    def credit_migration(self, current_ratings: List[str], 
                         migration_matrix: np.ndarray = None) -> Dict[str, Any]:
        """
        Credit rating migration analysis (CreditMetrics style).
        
        Args:
            current_ratings: List of current ratings for each obligor
            migration_matrix: Rating transition matrix
        
        Returns:
            Dict with migration analysis
        """
        ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']
        
        if migration_matrix is None:
            # Simplified transition matrix (annual)
            migration_matrix = np.array([
                [0.908, 0.083, 0.007, 0.002, 0.000, 0.000, 0.000, 0.000],
                [0.007, 0.907, 0.080, 0.005, 0.001, 0.000, 0.000, 0.000],
                [0.001, 0.022, 0.913, 0.058, 0.005, 0.001, 0.000, 0.000],
                [0.000, 0.003, 0.047, 0.893, 0.046, 0.009, 0.001, 0.001],
                [0.000, 0.001, 0.004, 0.064, 0.837, 0.076, 0.011, 0.007],
                [0.000, 0.001, 0.002, 0.008, 0.071, 0.825, 0.063, 0.030],
                [0.000, 0.000, 0.002, 0.004, 0.016, 0.074, 0.670, 0.234],
                [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 1.000]
            ])
        
        # Credit spreads by rating (basis points)
        spreads = {
            'AAA': 50, 'AA': 75, 'A': 100, 'BBB': 150,
            'BB': 300, 'B': 500, 'CCC': 1000, 'D': 0
        }
        
        # Simulate migrations
        n = len(current_ratings)
        future_ratings = []
        
        for rating in current_ratings:
            idx = ratings.index(rating)
            probs = migration_matrix[idx]
            new_rating = np.random.choice(ratings, p=probs)
            future_ratings.append(new_rating)
        
        # Count migrations
        rating_counts = {r: future_ratings.count(r) for r in ratings}
        
        # Value impact (simplified)
        current_spread = np.mean([spreads[r] for r in current_ratings])
        future_spread = np.mean([spreads[r] for r in future_ratings])
        spread_change = future_spread - current_spread
        
        return {
            "current_ratings": current_ratings,
            "future_ratings": future_ratings,
            "rating_distribution": rating_counts,
            "current_avg_spread": float(current_spread),
            "future_avg_spread": float(future_spread),
            "spread_change_bps": float(spread_change),
            "migration_matrix": migration_matrix.tolist()
        }
    
    def portfolio_concentration_risk(self, exposures: np.ndarray, 
                                      names: List[str] = None) -> Dict[str, Any]:
        """
        Analyze portfolio concentration risk.
        
        Args:
            exposures: Array of exposures
            names: Optional list of obligor names
        
        Returns:
            Dict with concentration metrics
        """
        total_exposure = np.sum(exposures)
        n = len(exposures)
        
        # Herfindahl index
        shares = exposures / total_exposure
        hhi = np.sum(shares ** 2)
        
        # Gini coefficient
        sorted_shares = np.sort(shares)
        cumsum = np.cumsum(sorted_shares)
        n_shares = len(shares)
        gini = (n_shares + 1 - 2 * np.sum(cumsum)) / n_shares
        
        # Top concentrations
        top_indices = np.argsort(exposures)[-10:][::-1]
        top_exposures = [(names[i] if names else f"Obligor_{i}", float(exposures[i])) 
                         for i in top_indices]
        
        # Effective number of obligors
        eno = 1 / hhi
        
        return {
            "total_exposure": float(total_exposure),
            "herfindahl_index": float(hhi),
            "gini_coefficient": float(gini),
            "effective_number_obligors": float(eno),
            "top_10_exposures": top_exposures,
            "max_single_exposure": float(np.max(exposures)),
            "exposure_concentration": float(np.max(exposures) / total_exposure)
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Execute complete credit risk analysis.
        
        Returns:
            Dict with all credit risk metrics
        """
        cfg = self.config
        
        # Merton model example
        merton = self.merton_model(V0=100, K=80, sigma_V=0.3, r=0.05, T=1.0)
        
        # Generate sample portfolio
        np.random.seed(cfg.random_seed)
        exposures = np.random.lognormal(2, 1, cfg.n_obligors)
        default_probs = np.random.uniform(0.001, 0.05, cfg.n_obligors)
        
        # Gaussian copula
        copula = self.gaussian_copula_simulation(exposures, default_probs)
        
        # Credit migration
        ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']
        current_ratings = list(np.random.choice(ratings[:-1], cfg.n_obligors, 
                               p=[0.05, 0.10, 0.20, 0.40, 0.15, 0.07, 0.03]))
        migration = self.credit_migration(current_ratings[:20])  # Sample for speed
        
        # Concentration analysis
        names = [f"Firm_{i}" for i in range(cfg.n_obligors)]
        concentration = self.portfolio_concentration_risk(exposures, names)
        
        # Economic capital calculation
        economic_capital = copula["var"][0.999] - copula["expected_loss"]
        
        return {
            "merton_model": merton,
            "portfolio_copula": copula,
            "credit_migration": migration,
            "concentration": concentration,
            "economic_capital": float(economic_capital),
            "risk_adjusted_return": float(np.sum(exposures) * 0.05 / economic_capital) if economic_capital > 0 else 0,
            "model_type": "credit_risk"
        }
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 56,
            "name": "Credit Risk",
            "category": "Risk Management",
            "description": "Merton model, copula simulation, and credit migration analysis",
            "author": "Merton, Li, J.P. Morgan",
            "year": 1974,
            "parameters": ["n_obligors", "recovery_rate", "correlation", "time_horizon"],
            "outputs": ["default_probability", "var", "expected_shortfall", "concentration"],
            "applications": ["credit_portfolio", "banking_regulation", "cds_pricing"]
        }


# Unit Tests
import unittest

class TestCreditRiskModel(unittest.TestCase):
    
    def test_merton_distance_to_default(self):
        """Test distance to default calculation."""
        config = CreditRiskConfig()
        model = CreditRiskModel(config)
        
        # Safe firm (high asset value, low debt)
        safe = model.merton_model(V0=150, K=80, sigma_V=0.2, r=0.05, T=1)
        
        # Risky firm (low asset value, high debt)
        risky = model.merton_model(V0=90, K=80, sigma_V=0.4, r=0.05, T=1)
        
        # Safe firm should have higher distance to default
        self.assertGreater(safe["distance_to_default"], risky["distance_to_default"])
        
        # Risky firm should have higher default probability
        self.assertGreater(risky["default_probability"], safe["default_probability"])
    
    def test_copula_correlation_effect(self):
        """Test that correlation affects portfolio risk."""
        exposures = np.ones(100) * 1000
        default_probs = np.ones(100) * 0.05
        
        # Low correlation
        config_low = CreditRiskConfig(correlation=0.1, n_simulations=5000)
        model_low = CreditRiskModel(config_low)
        result_low = model_low.gaussian_copula_simulation(exposures, default_probs)
        
        # High correlation
        config_high = CreditRiskConfig(correlation=0.5, n_simulations=5000)
        model_high = CreditRiskModel(config_high)
        result_high = model_high.gaussian_copula_simulation(exposures, default_probs)
        
        # Higher correlation should lead to higher tail risk
        self.assertGreater(result_high["var"][0.99], result_low["var"][0.99])
    
    def test_credit_migration_structure(self):
        """Test credit migration returns valid structure."""
        config = CreditRiskConfig()
        model = CreditRiskModel(config)
        
        current_ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
        result = model.credit_migration(current_ratings)
        
        self.assertIn("current_ratings", result)
        self.assertIn("future_ratings", result)
        self.assertIn("rating_distribution", result)
        self.assertEqual(len(result["current_ratings"]), len(result["future_ratings"]))
    
    def test_concentration_metrics(self):
        """Test concentration metrics."""
        config = CreditRiskConfig()
        model = CreditRiskModel(config)
        
        # Equal exposures
        equal_exposures = np.ones(100) * 1000
        equal_conc = model.portfolio_concentration_risk(equal_exposures)
        
        # Concentrated exposures
        concentrated = np.ones(100) * 1000
        concentrated[0] = 50000  # One large exposure
        conc_conc = model.portfolio_concentration_risk(concentrated)
        
        # Concentrated should have higher HHI
        self.assertGreater(conc_conc["herfindahl_index"], equal_conc["herfindahl_index"])
        
        # Equal should have effective number close to actual number
        self.assertAlmostEqual(equal_conc["effective_number_obligors"], 100, delta=5)
    
    def test_var_monotonicity(self):
        """Test VaR increases with confidence level."""
        config = CreditRiskConfig()
        model = CreditRiskModel(config)
        
        exposures = np.ones(100) * 1000
        default_probs = np.ones(100) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)
        
        var = result["var"]
        self.assertGreater(var[0.99], var[0.95])
        self.assertGreater(var[0.999], var[0.99])
    
    def test_expected_shortfall_greater_than_var(self):
        """Test ES is greater than VaR."""
        config = CreditRiskConfig()
        model = CreditRiskModel(config)
        
        exposures = np.ones(100) * 1000
        default_probs = np.ones(100) * 0.05
        result = model.gaussian_copula_simulation(exposures, default_probs)
        
        for cl in config.confidence_levels:
            self.assertGreaterEqual(result["expected_shortfall"][cl], result["var"][cl])


if __name__ == "__main__":
    # Run demonstration
    config = CreditRiskConfig(n_obligors=100, n_simulations=5000)
    model = CreditRiskModel(config)
    result = model.run()
    
    print("=" * 60)
    print("CREDIT RISK MODEL")
    print("=" * 60)
    print(f"\nMerton Model:")
    print(f"  Distance to Default: {result['merton_model']['distance_to_default']:.4f}")
    print(f"  Default Probability: {result['merton_model']['default_probability']:.4f}")
    print(f"  Credit Spread: {result['merton_model']['credit_spread']*10000:.2f} bps")
    
    print(f"\nPortfolio Copula:")
    print(f"  Expected Loss: {result['portfolio_copula']['expected_loss']:.2f}")
    print(f"  VaR 99%: {result['portfolio_copula']['var'][0.99]:.2f}")
    print(f"  ES 99%: {result['portfolio_copula']['expected_shortfall'][0.99]:.2f}")
    
    print(f"\nConcentration:")
    print(f"  Herfindahl Index: {result['concentration']['herfindahl_index']:.4f}")
    print(f"  Effective Number of Obligors: {result['concentration']['effective_number_obligors']:.1f}")
    
    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for TURBO-CDI compatibility
CreditRiskPattern = CreditRiskModel
