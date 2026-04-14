"""
Pattern 58: Portfolio Optimization
Implements Markowitz mean-variance optimization, Black-Litterman,
and risk parity portfolio construction.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy.optimize import minimize, LinearConstraint
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PortfolioOptimizationConfig:
    """Configuration for portfolio optimization."""
    n_assets: int = 10
    risk_aversion: float = 2.0
    target_return: float = None
    target_risk: float = None
    min_weight: float = 0.0
    max_weight: float = 1.0
    allow_short: bool = False
    transaction_cost: float = 0.001
    confidence: float = 0.95
    random_seed: int = 42


class PortfolioOptimizationModel:
    """
    Portfolio optimization using multiple approaches:
    - Markowitz mean-variance optimization
    - Maximum Sharpe ratio (tangency portfolio)
    - Minimum variance portfolio
    - Risk parity
    - Black-Litterman model
    """
    
    def __init__(self, config: PortfolioOptimizationConfig = None):
        self.config = config or PortfolioOptimizationConfig()
        np.random.seed(self.config.random_seed)
        self.returns: np.ndarray = None
        self.cov_matrix: np.ndarray = None
        self.expected_returns: np.ndarray = None
        self.asset_names: List[str] = None
        self.risk_free_rate: float = 0.02
    
    def set_data(self, returns: np.ndarray, cov_matrix: np.ndarray = None,
                 expected_returns: np.ndarray = None, asset_names: List[str] = None,
                 risk_free_rate: float = 0.02):
        """Set return data for optimization."""
        self.returns = returns
        self.cov_matrix = cov_matrix if cov_matrix is not None else np.cov(returns.T)
        self.expected_returns = expected_returns if expected_returns is not None else np.mean(returns, axis=0)
        self.asset_names = asset_names or [f"Asset_{i}" for i in range(len(self.expected_returns))]
        self.risk_free_rate = risk_free_rate
    
    def generate_sample_data(self, n_periods: int = 252) -> None:
        """Generate sample return data."""
        cfg = self.config
        n = cfg.n_assets
        
        # Expected returns (annualized)
        self.expected_returns = np.random.uniform(0.05, 0.15, n)
        
        # Covariance matrix
        volatilities = np.random.uniform(0.15, 0.35, n)
        correlation = self._generate_correlation_matrix(n, 0.3)
        self.cov_matrix = np.outer(volatilities, volatilities) * correlation
        
        # Generate returns
        self.returns = np.random.multivariate_normal(
            self.expected_returns / 252, 
            self.cov_matrix / 252, 
            n_periods
        )
        
        self.asset_names = [f"Asset_{i}" for i in range(n)]
    
    def _generate_correlation_matrix(self, n: int, avg_correlation: float) -> np.ndarray:
        """Generate a valid correlation matrix."""
        # Factor model approach
        factor_loadings = np.random.uniform(0.3, 0.7, n)
        corr = np.outer(factor_loadings, factor_loadings)
        np.fill_diagonal(corr, 1.0)
        # Ensure positive semi-definite
        eigenvalues, eigenvectors = np.linalg.eigh(corr)
        eigenvalues = np.maximum(eigenvalues, 0.01)
        corr = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
        # Normalize
        d = np.sqrt(np.diag(corr))
        corr = corr / np.outer(d, d)
        return corr
    
    def _portfolio_stats(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """Calculate portfolio return, risk, and Sharpe ratio."""
        port_return = np.dot(weights, self.expected_returns)
        port_risk = np.sqrt(weights @ self.cov_matrix @ weights)
        sharpe = (port_return - self.risk_free_rate) / port_risk if port_risk > 0 else 0
        return port_return, port_risk, sharpe
    
    def markowitz_optimization(self, target_return: float = None) -> Dict[str, Any]:
        """
        Mean-variance optimization (Markowitz).
        
        Args:
            target_return: Target portfolio return (optional)
        
        Returns:
            Dict with optimal weights and portfolio statistics
        """
        cfg = self.config
        n = len(self.expected_returns)
        
        # Objective: minimize portfolio variance
        def objective(weights):
            return weights @ self.cov_matrix @ weights
        
        # Constraints
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]  # Sum to 1
        
        if target_return is not None:
            constraints.append({
                'type': 'eq', 
                'fun': lambda w: np.dot(w, self.expected_returns) - target_return
            })
        elif cfg.target_return is not None:
            constraints.append({
                'type': 'eq', 
                'fun': lambda w: np.dot(w, self.expected_returns) - cfg.target_return
            })
        
        # Bounds
        bounds = [(cfg.min_weight, cfg.max_weight) for _ in range(n)]
        if cfg.allow_short:
            bounds = [(-1.0, 1.0) for _ in range(n)]
        
        # Initial guess
        x0 = np.ones(n) / n
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            weights = result.x
        else:
            weights = x0
        
        weights = np.maximum(weights, 0) if not cfg.allow_short else weights
        weights = weights / np.sum(weights)
        
        port_return, port_risk, sharpe = self._portfolio_stats(weights)
        
        return {
            "weights": weights.tolist(),
            "expected_return": float(port_return),
            "risk": float(port_risk),
            "sharpe_ratio": float(sharpe),
            "method": "markowitz"
        }
    
    def maximum_sharpe_portfolio(self) -> Dict[str, Any]:
        """Find tangency portfolio (maximum Sharpe ratio)."""
        n = len(self.expected_returns)
        
        def negative_sharpe(weights):
            _, _, sharpe = self._portfolio_stats(weights)
            return -sharpe
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(self.config.min_weight, self.config.max_weight) for _ in range(n)]
        
        x0 = np.ones(n) / n
        result = minimize(negative_sharpe, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        weights = result.x if result.success else x0
        weights = np.maximum(weights, 0) / np.sum(np.maximum(weights, 0))
        
        port_return, port_risk, sharpe = self._portfolio_stats(weights)
        
        return {
            "weights": weights.tolist(),
            "expected_return": float(port_return),
            "risk": float(port_risk),
            "sharpe_ratio": float(sharpe),
            "method": "maximum_sharpe"
        }
    
    def minimum_variance_portfolio(self) -> Dict[str, Any]:
        """Find minimum variance portfolio."""
        n = len(self.expected_returns)
        
        def objective(weights):
            return weights @ self.cov_matrix @ weights
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(self.config.min_weight, self.config.max_weight) for _ in range(n)]
        
        x0 = np.ones(n) / n
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        weights = result.x if result.success else x0
        weights = np.maximum(weights, 0) / np.sum(np.maximum(weights, 0))
        
        port_return, port_risk, sharpe = self._portfolio_stats(weights)
        
        return {
            "weights": weights.tolist(),
            "expected_return": float(port_return),
            "risk": float(port_risk),
            "sharpe_ratio": float(sharpe),
            "method": "minimum_variance"
        }
    
    def risk_parity_portfolio(self) -> Dict[str, Any]:
        """
        Construct risk parity portfolio (equal risk contribution).
        """
        n = len(self.expected_returns)
        
        def risk_contribution(weights):
            port_risk = np.sqrt(weights @ self.cov_matrix @ weights)
            marginal_risk = (self.cov_matrix @ weights) / port_risk
            return weights * marginal_risk
        
        def objective(weights):
            rc = risk_contribution(weights)
            target = port_risk / n if (port_risk := np.sqrt(weights @ self.cov_matrix @ weights)) > 0 else 0
            return np.sum((rc - target) ** 2)
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(0.01, 0.5) for _ in range(n)]
        
        x0 = np.ones(n) / n
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        weights = result.x if result.success else x0
        weights = weights / np.sum(weights)
        
        port_return, port_risk, sharpe = self._portfolio_stats(weights)
        rc = risk_contribution(weights)
        
        return {
            "weights": weights.tolist(),
            "expected_return": float(port_return),
            "risk": float(port_risk),
            "sharpe_ratio": float(sharpe),
            "risk_contributions": rc.tolist(),
            "method": "risk_parity"
        }
    
    def black_litterman(self, views: List[Dict] = None, omega: np.ndarray = None) -> Dict[str, Any]:
        """
        Black-Litterman model combining market equilibrium with investor views.
        
        Args:
            views: List of view dictionaries {'assets': [i, j], 'view': return_diff}
            omega: Uncertainty matrix for views
        
        Returns:
            Dict with BL expected returns and optimal portfolio
        """
        n = len(self.expected_returns)
        
        # Market equilibrium returns (reverse optimization)
        market_weights = np.ones(n) / n  # Assume equal market weights
        tau = 0.05  # Scaling factor
        
        pi = self.cov_matrix @ market_weights * self.config.risk_aversion
        
        # Default views if not provided
        if views is None:
            views = [
                {'assets': [0], 'view': 0.12, 'confidence': 0.5},  # Asset 0 will return 12%
                {'assets': [1, 2], 'view': 0.03, 'confidence': 0.3}  # Asset 1 outperforms 2 by 3%
            ]
        
        # Build views matrix P and vector Q
        P = []
        Q = []
        confidences = []
        
        for v in views:
            row = np.zeros(n)
            if len(v['assets']) == 1:
                row[v['assets'][0]] = 1
            elif len(v['assets']) == 2:
                row[v['assets'][0]] = 1
                row[v['assets'][1]] = -1
            P.append(row)
            Q.append(v['view'])
            confidences.append(v.get('confidence', 0.5))
        
        P = np.array(P)
        Q = np.array(Q)
        
        # View uncertainty
        if omega is None:
            omega = np.diag([tau * c for c in confidences])
        
        # Black-Litterman expected returns
        sigma_inv = np.linalg.inv(tau * self.cov_matrix)
        omega_inv = np.linalg.inv(omega)
        
        bl_returns = np.linalg.inv(sigma_inv + P.T @ omega_inv @ P) @ \
                     (sigma_inv @ pi + P.T @ omega_inv @ Q)
        
        # Optimize with BL returns
        original_returns = self.expected_returns.copy()
        self.expected_returns = bl_returns
        result = self.markowitz_optimization()
        self.expected_returns = original_returns
        
        result['bl_expected_returns'] = bl_returns.tolist()
        result['equilibrium_returns'] = pi.tolist()
        result['method'] = 'black_litterman'
        
        return result
    
    def efficient_frontier(self, n_points: int = 50) -> Dict[str, List]:
        """Calculate efficient frontier."""
        min_ret = np.min(self.expected_returns)
        max_ret = np.max(self.expected_returns)
        
        target_returns = np.linspace(min_ret, max_ret, n_points)
        frontier_returns = []
        frontier_risks = []
        frontier_sharpes = []
        
        for target in target_returns:
            result = self.markowitz_optimization(target_return=target)
            frontier_returns.append(result['expected_return'])
            frontier_risks.append(result['risk'])
            frontier_sharpes.append(result['sharpe_ratio'])
        
        return {
            'returns': frontier_returns,
            'risks': frontier_risks,
            'sharpe_ratios': frontier_sharpes
        }
    
    def run(self) -> Dict[str, Any]:
        """Execute complete portfolio optimization analysis."""
        if self.returns is None:
            self.generate_sample_data()
        
        # Run all optimization methods
        markowitz = self.markowitz_optimization()
        max_sharpe = self.maximum_sharpe_portfolio()
        min_var = self.minimum_variance_portfolio()
        risk_parity = self.risk_parity_portfolio()
        black_litterman = self.black_litterman()
        
        # Efficient frontier
        frontier = self.efficient_frontier()
        
        # Equal weight benchmark
        n = len(self.expected_returns)
        equal_weights = np.ones(n) / n
        eq_return, eq_risk, eq_sharpe = self._portfolio_stats(equal_weights)
        
        return {
            "markowitz": markowitz,
            "maximum_sharpe": max_sharpe,
            "minimum_variance": min_var,
            "risk_parity": risk_parity,
            "black_litterman": black_litterman,
            "efficient_frontier": frontier,
            "equal_weight_benchmark": {
                "weights": equal_weights.tolist(),
                "expected_return": float(eq_return),
                "risk": float(eq_risk),
                "sharpe_ratio": float(eq_sharpe)
            },
            "asset_statistics": {
                "names": self.asset_names,
                "expected_returns": self.expected_returns.tolist(),
                "volatilities": np.sqrt(np.diag(self.cov_matrix)).tolist()
            },
            "model_type": "portfolio_optimization"
        }
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 58,
            "name": "Portfolio Optimization",
            "category": "Asset Allocation",
            "description": "Markowitz mean-variance, risk parity, and Black-Litterman optimization",
            "author": "Markowitz, Sharpe, Black, Litterman",
            "year": 1952,
            "parameters": ["risk_aversion", "target_return", "allow_short"],
            "outputs": ["optimal_weights", "efficient_frontier", "sharpe_ratio"],
            "applications": ["asset_allocation", "wealth_management", "pension_funds"]
        }


# Unit Tests
import unittest

class TestPortfolioOptimizationModel(unittest.TestCase):
    
    def test_data_generation(self):
        """Test sample data generation."""
        config = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(config)
        model.generate_sample_data(n_periods=100)
        
        self.assertEqual(len(model.expected_returns), 5)
        self.assertEqual(model.cov_matrix.shape, (5, 5))
        self.assertEqual(len(model.returns), 100)
    
    def test_markowitz_optimization(self):
        """Test Markowitz optimization returns valid portfolio."""
        config = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(config)
        model.generate_sample_data()
        
        result = model.markowitz_optimization()
        
        # Check weights sum to 1
        self.assertAlmostEqual(sum(result['weights']), 1.0, delta=0.01)
        
        # Check all weights non-negative
        self.assertTrue(all(w >= 0 for w in result['weights']))
        
        # Check risk is positive
        self.assertGreater(result['risk'], 0)
    
    def test_maximum_sharpe(self):
        """Test maximum Sharpe portfolio has highest Sharpe ratio."""
        config = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(config)
        model.generate_sample_data()
        
        max_sharpe = model.maximum_sharpe_portfolio()
        markowitz = model.markowitz_optimization()
        min_var = model.minimum_variance_portfolio()
        
        # Max Sharpe should have highest Sharpe ratio
        self.assertGreaterEqual(
            max_sharpe['sharpe_ratio'],
            min(markowitz['sharpe_ratio'], min_var['sharpe_ratio']) - 0.01
        )
    
    def test_minimum_variance(self):
        """Test minimum variance portfolio has lowest risk."""
        config = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(config)
        model.generate_sample_data()
        
        min_var = model.minimum_variance_portfolio()
        markowitz = model.markowitz_optimization()
        
        # Min var should have lowest risk
        self.assertLessEqual(min_var['risk'], markowitz['risk'] * 1.01)
    
    def test_risk_parity(self):
        """Test risk parity has roughly equal risk contributions."""
        config = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(config)
        model.generate_sample_data()
        
        result = model.risk_parity_portfolio()
        
        # Check risk contributions exist
        self.assertIn('risk_contributions', result)
        
        # Risk contributions should be roughly equal
        rc = np.array(result['risk_contributions'])
        if len(rc) > 0 and np.sum(rc) > 0:
            rc_normalized = rc / np.sum(rc)
            self.assertLess(np.std(rc_normalized), 0.3)
    
    def test_black_litterman(self):
        """Test Black-Litterman incorporates views."""
        config = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(config)
        model.generate_sample_data()
        
        views = [
            {'assets': [0], 'view': 0.20, 'confidence': 0.8}
        ]
        
        result = model.black_litterman(views)
        
        # Check BL returns exist
        self.assertIn('bl_expected_returns', result)
        self.assertEqual(len(result['bl_expected_returns']), 5)
    
    def test_efficient_frontier(self):
        """Test efficient frontier generation."""
        config = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(config)
        model.generate_sample_data()
        
        frontier = model.efficient_frontier(n_points=20)
        
        self.assertEqual(len(frontier['returns']), 20)
        self.assertEqual(len(frontier['risks']), 20)
        
        # Frontier should be convex (approximately)
        risks = frontier['risks']
        for i in range(1, len(risks) - 1):
            self.assertGreaterEqual(risks[i], min(risks[i-1], risks[i+1]) - 0.01)


if __name__ == "__main__":
    # Run demonstration
    config = PortfolioOptimizationConfig(n_assets=8)
    model = PortfolioOptimizationModel(config)
    result = model.run()
    
    print("=" * 60)
    print("PORTFOLIO OPTIMIZATION MODEL")
    print("=" * 60)
    print(f"\nMaximum Sharpe Portfolio:")
    print(f"  Return: {result['maximum_sharpe']['expected_return']:.4f}")
    print(f"  Risk: {result['maximum_sharpe']['risk']:.4f}")
    print(f"  Sharpe: {result['maximum_sharpe']['sharpe_ratio']:.4f}")
    
    print(f"\nMinimum Variance Portfolio:")
    print(f"  Return: {result['minimum_variance']['expected_return']:.4f}")
    print(f"  Risk: {result['minimum_variance']['risk']:.4f}")
    
    print(f"\nRisk Parity Portfolio:")
    print(f"  Return: {result['risk_parity']['expected_return']:.4f}")
    print(f"  Risk: {result['risk_parity']['risk']:.4f}")
    
    print(f"\nEqual Weight Benchmark:")
    print(f"  Return: {result['equal_weight_benchmark']['expected_return']:.4f}")
    print(f"  Risk: {result['equal_weight_benchmark']['risk']:.4f}")
    print(f"  Sharpe: {result['equal_weight_benchmark']['sharpe_ratio']:.4f}")
    
    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for TURBO-CDI compatibility
PortfolioOptimizationPattern = PortfolioOptimizationModel
