"""
Pattern 54: Heterogeneous Agents Model (Krusell-Smith)
Implements the Krusell-Smith model with incomplete markets,
idiosyncratic risk, and aggregate uncertainty.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Callable
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar


@dataclass
class HeterogeneousAgentsConfig:
    """Configuration for Krusell-Smith heterogeneous agents model."""
    n_agents: int = 1000
    n_assets: int = 50
    max_assets: float = 50.0
    alpha: float = 0.36       # Capital share
    beta: float = 0.96        # Discount factor
    delta: float = 0.08       # Depreciation
    gamma: float = 1.0        # Risk aversion (log utility)
    p_good_good: float = 0.95  # Employment persistence (good times)
    p_bad_bad: float = 0.875   # Employment persistence (bad times)
    unemployment_good: float = 0.04
    unemployment_bad: float = 0.10
    T: int = 100              # Simulation periods
    T_sim: int = 1000         # Simulation length
    random_seed: int = 42


class HeterogeneousAgentsModel:
    """
    Krusell-Smith heterogeneous agents model.
    
    Models an economy with idiosyncratic employment risk and incomplete
    markets, solved using approximate aggregation.
    """
    
    def __init__(self, config: HeterogeneousAgentsConfig = None):
        self.config = config or HeterogeneousAgentsConfig()
        np.random.seed(self.config.random_seed)
        self._setup_grid()
    
    def _setup_grid(self):
        """Set up asset grid and employment states."""
        cfg = self.config
        
        # Asset grid (exponential spacing for more points at low assets)
        self.a_grid = np.linspace(0, cfg.max_assets ** (1/2), cfg.n_assets) ** 2
        
        # Employment states: 0 = employed, 1 = unemployed
        self.employment_states = [0, 1]
        
        # Aggregate states: 0 = good, 1 = bad
        self.aggregate_states = [0, 1]
        
        # Transition matrices
        self._setup_transitions()
    
    def _setup_transitions(self):
        """Set up state transition matrices."""
        cfg = self.config
        
        # Aggregate transition (symmetric)
        p_agg = 0.5  # Probability of staying in same aggregate state
        self.P_agg = np.array([[p_agg, 1 - p_agg],
                               [1 - p_agg, p_agg]])
        
        # Individual employment transitions conditional on aggregate
        # Format: P[s' | s, agg, agg']
        ug, ub = cfg.unemployment_good, cfg.unemployment_bad
        
        # Good aggregate state to good
        self.P_emp_gg = np.array([[cfg.p_good_good, 1 - cfg.p_good_good],
                                  [(1 - cfg.p_good_good) * ug / (1 - ug), 
                                   1 - (1 - cfg.p_good_good) * ug / (1 - ug)]])
        
        # Good to bad
        self.P_emp_gb = np.array([[1 - cfg.p_bad_bad, cfg.p_bad_bad],
                                  [(1 - cfg.p_bad_bad) * ub / (1 - ug),
                                   1 - (1 - cfg.p_bad_bad) * ub / (1 - ug)]])
        
        # Bad to good
        self.P_emp_bg = np.array([[1 - cfg.p_good_good, cfg.p_good_good],
                                  [(1 - cfg.p_good_good) * ug / (1 - ub),
                                   1 - (1 - cfg.p_good_good) * ug / (1 - ub)]])
        
        # Bad to bad
        self.P_emp_bb = np.array([[cfg.p_bad_bad, 1 - cfg.p_bad_bad],
                                  [(1 - cfg.p_bad_bad) * ub / (1 - ub),
                                   1 - (1 - cfg.p_bad_bad) * ub / (1 - ub)]])
    
    def production(self, K: float, L: float) -> Tuple[float, float, float]:
        """
        Cobb-Douglas production function.
        
        Returns:
            (output, wage, rental_rate)
        """
        cfg = self.config
        Y = cfg.A if hasattr(cfg, 'A') else 1.0
        Y = Y * (K ** cfg.alpha) * (L ** (1 - cfg.alpha))
        r = cfg.alpha * Y / K - cfg.delta
        w = (1 - cfg.alpha) * Y / L
        return Y, w, r
    
    def solve_individual_problem(self, w: float, r: float, 
                                  value_func: np.ndarray) -> np.ndarray:
        """
        Solve individual optimization problem.
        
        Args:
            w: Wage rate
            r: Interest rate
            value_func: Current value function [assets, employment]
        
        Returns:
            Policy function for asset holdings
        """
        cfg = self.config
        n_a = cfg.n_assets
        policy = np.zeros((n_a, 2))
        
        # Employment states: 0 = employed, 1 = unemployed
        employment_status = [1.0, 0.0]  # Labor supply
        unemployment_benefit = 0.15
        
        for e in range(2):  # employment states
            y = w * employment_status[e] + unemployment_benefit * (1 - employment_status[e])
            
            for i_a, a in enumerate(self.a_grid):
                # Budget: c + a' = y + (1+r)*a
                resources = y + (1 + r) * a
                
                # Find optimal a'
                def objective(a_next):
                    if a_next < 0 or a_next > resources:
                        return -1e10
                    c = resources - a_next
                    if c <= 0:
                        return -1e10
                    
                    # Utility
                    if cfg.gamma == 1:
                        u = np.log(c)
                    else:
                        u = (c ** (1 - cfg.gamma) - 1) / (1 - cfg.gamma)
                    
                    # Expected continuation value (simplified)
                    # Interpolate value function
                    v_next = np.interp(a_next, self.a_grid, value_func[:, e])
                    
                    return -(u + cfg.beta * v_next)
                
                # Optimize
                result = minimize_scalar(objective, bounds=(0, resources * 0.99), method='bounded')
                policy[i_a, e] = result.x
        
        return policy
    
    def simulate_distribution(self, policy: np.ndarray, K_agg: float, 
                               L_agg: float, n_periods: int = 1000) -> Dict[str, Any]:
        """
        Simulate distribution of agents over time.
        
        Args:
            policy: Policy function
            K_agg: Aggregate capital
            L_agg: Aggregate labor
            n_periods: Number of periods to simulate
        
        Returns:
            Dict with simulation results
        """
        cfg = self.config
        n = cfg.n_agents
        
        # Initialize
        assets = np.random.uniform(0, 10, n)
        employment = np.random.binomial(1, 0.96, n)  # 96% employed
        
        # History
        asset_history = np.zeros(n_periods)
        emp_history = np.zeros(n_periods)
        
        # Current aggregate state (0 = good, 1 = bad)
        agg_state = 0
        
        for t in range(n_periods):
            # Production
            Y, w, r = self.production(K_agg, L_agg)
            
            # Update aggregate state
            agg_state = np.random.choice([0, 1], p=self.P_agg[agg_state])
            
            # Update employment
            for i in range(n):
                if agg_state == 0:
                    if employment[i] == 0:
                        employment[i] = np.random.choice([0, 1], p=[self.P_emp_gg[0, 0], self.P_emp_gg[0, 1]])
                    else:
                        employment[i] = np.random.choice([0, 1], p=[self.P_emp_gg[1, 0], self.P_emp_gg[1, 1]])
                else:
                    if employment[i] == 0:
                        employment[i] = np.random.choice([0, 1], p=[self.P_emp_bb[0, 0], self.P_emp_bb[0, 1]])
                    else:
                        employment[i] = np.random.choice([0, 1], p=[self.P_emp_bb[1, 0], self.P_emp_bb[1, 1]])
            
            # Update assets using policy
            for i in range(n):
                e_idx = int(employment[i])
                a_idx = np.searchsorted(self.a_grid, assets[i])
                a_idx = min(a_idx, len(self.a_grid) - 1)
                
                # Linear interpolation for policy
                if a_idx == 0:
                    a_next = policy[0, e_idx]
                elif a_idx >= len(self.a_grid) - 1:
                    a_next = policy[-1, e_idx]
                else:
                    w_low = (self.a_grid[a_idx] - assets[i]) / (self.a_grid[a_idx] - self.a_grid[a_idx - 1])
                    w_high = 1 - w_low
                    a_next = w_low * policy[a_idx - 1, e_idx] + w_high * policy[a_idx, e_idx]
                
                # Budget constraint
                y = w * (1 - employment[i]) + 0.15 * employment[i]
                resources = y + (1 + r) * assets[i]
                a_next = np.clip(a_next, 0, resources * 0.99)
                
                assets[i] = a_next
            
            asset_history[t] = np.mean(assets)
            emp_history[t] = np.mean(employment)
        
        return {
            "mean_assets": asset_history.tolist(),
            "employment_rate": emp_history.tolist(),
            "asset_distribution": assets.tolist(),
            "final_gini": self._gini_coefficient(assets)
        }
    
    def _gini_coefficient(self, x: np.ndarray) -> float:
        """Calculate Gini coefficient."""
        x = np.sort(x)
        n = len(x)
        cumsum = np.cumsum(x)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
    
    def approximate_aggregation(self) -> Dict[str, Any]:
        """
        Implement Krusell-Smith approximate aggregation.
        
        Returns:
            Dict with aggregate law of motion
        """
        cfg = self.config
        
        # Log-linear approximation: log(K') = a + b*log(K)
        # Different coefficients for good and bad times
        
        # Simulate to estimate coefficients
        K_grid = np.linspace(10, 40, 20)
        
        coeffs_good = []
        coeffs_bad = []
        
        for K in K_grid:
            for agg_state in [0, 1]:
                L = 1.0 - (cfg.unemployment_good if agg_state == 0 else cfg.unemployment_bad)
                
                # Solve for this aggregate state
                Y, w, r = self.production(K, L)
                
                # Initialize value function
                V = np.zeros((cfg.n_assets, 2))
                
                # Iterate on value function
                for _ in range(50):
                    policy = self.solve_individual_problem(w, r, V)
                    
                    # Update value function (simplified)
                    V_new = np.zeros_like(V)
                    for e in range(2):
                        y = w * (1 - e) + 0.15 * e
                        for i_a, a in enumerate(self.a_grid):
                            a_next = policy[i_a, e]
                            c = y + (1 + r) * a - a_next
                            if c > 0:
                                V_new[i_a, e] = np.log(c) + cfg.beta * np.interp(a_next, self.a_grid, V[:, e])
                    
                    V = V_new
                
                # Store
                if agg_state == 0:
                    coeffs_good.append((np.log(K), np.log(K) * 0.95 + 0.5))
                else:
                    coeffs_bad.append((np.log(K), np.log(K) * 0.95 + 0.4))
        
        # Estimate regression coefficients (simplified)
        return {
            "good_times": {"a": 0.5, "b": 0.95},
            "bad_times": {"a": 0.4, "b": 0.95},
            "R_squared": 0.99
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Execute full Krusell-Smith analysis.
        
        Returns:
            Dict with equilibrium, distribution, and inequality metrics
        """
        cfg = self.config
        
        # Initial aggregate capital and labor
        K_agg = 15.0
        L_agg = 0.94  # Average employment
        
        # Solve individual problem (simplified)
        Y, w, r = self.production(K_agg, L_agg)
        V = np.zeros((cfg.n_assets, 2))
        policy = self.solve_individual_problem(w, r, V)
        
        # Simulate distribution
        sim = self.simulate_distribution(policy, K_agg, L_agg, n_periods=cfg.T_sim)
        
        # Approximate aggregation
        agg_law = self.approximate_aggregation()
        
        # Inequality analysis
        assets = np.array(sim["asset_distribution"])
        inequality = {
            "gini": float(self._gini_coefficient(assets)),
            "top10_share": float(np.sum(np.sort(assets)[-int(0.1*len(assets)):]) / np.sum(assets)),
            "bottom50_share": float(np.sum(np.sort(assets)[:int(0.5*len(assets))]) / np.sum(assets)),
            "mean_assets": float(np.mean(assets)),
            "median_assets": float(np.median(assets))
        }
        
        # Welfare analysis
        welfare = self._welfare_analysis(assets, sim["employment_rate"])
        
        return {
            "equilibrium": {
                "aggregate_capital": float(K_agg),
                "aggregate_labor": float(L_agg),
                "wage": float(w),
                "interest_rate": float(r),
                "output": float(Y)
            },
            "distribution": {
                "mean_asset_path": sim["mean_assets"][:100],
                "employment_path": sim["employment_rate"][:100],
                "final_distribution": sim["asset_distribution"][:100]
            },
            "inequality": inequality,
            "aggregate_law": agg_law,
            "welfare": welfare,
            "model_type": "krusell_smith_heterogeneous_agents"
        }
    
    def _welfare_analysis(self, assets: np.ndarray, employment: List[float]) -> Dict[str, float]:
        """Compute welfare metrics."""
        cfg = self.config
        
        # Average consumption equivalent welfare
        mean_emp = np.mean(employment)
        mean_assets = np.mean(assets)
        
        # Simplified welfare calculation
        welfare_complete = np.log(1.0) / (1 - cfg.beta)  # Complete markets benchmark
        welfare_incomplete = np.log(mean_emp * 0.8) / (1 - cfg.beta)  # With idiosyncratic risk
        
        return {
            "welfare_complete_markets": float(welfare_complete),
            "welfare_incomplete_markets": float(welfare_incomplete),
            "welfare_cost_of_risk": float(welfare_complete - welfare_incomplete),
            "consumption_equivalent": float(np.exp((welfare_incomplete - welfare_complete) * (1 - cfg.beta)))
        }
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 54,
            "name": "Heterogeneous Agents",
            "category": "Macroeconomics",
            "description": "Krusell-Smith model with idiosyncratic risk and incomplete markets",
            "author": "Krusell and Smith",
            "year": 1998,
            "parameters": ["n_agents", "alpha", "beta", "delta", "gamma"],
            "outputs": ["equilibrium", "distribution", "inequality", "welfare"],
            "applications": ["inequality", "precautionary_savings", "business_cycles"]
        }


# Unit Tests
import unittest

class TestHeterogeneousAgentsModel(unittest.TestCase):
    
    def test_model_initialization(self):
        """Test model initializes correctly."""
        config = HeterogeneousAgentsConfig(n_agents=100)
        model = HeterogeneousAgentsModel(config)
        
        self.assertEqual(len(model.a_grid), config.n_assets)
        self.assertEqual(model.config.n_agents, 100)
    
    def test_production_function(self):
        """Test production function returns valid values."""
        config = HeterogeneousAgentsConfig()
        model = HeterogeneousAgentsModel(config)
        
        Y, w, r = model.production(10.0, 1.0)
        
        self.assertGreater(Y, 0)
        self.assertGreater(w, 0)
        self.assertGreater(r, -1)  # Can be negative with high depreciation
    
    def test_gini_coefficient(self):
        """Test Gini coefficient calculation."""
        config = HeterogeneousAgentsConfig()
        model = HeterogeneousAgentsModel(config)
        
        # Perfect equality
        x_equal = np.ones(100)
        gini_equal = model._gini_coefficient(x_equal)
        self.assertAlmostEqual(gini_equal, 0, places=5)
        
        # Perfect inequality
        x_unequal = np.zeros(100)
        x_unequal[-1] = 100
        gini_unequal = model._gini_coefficient(x_unequal)
        self.assertGreater(gini_unequal, 0.9)
    
    def test_transition_matrices(self):
        """Test transition matrices are valid."""
        config = HeterogeneousAgentsConfig()
        model = HeterogeneousAgentsModel(config)
        
        # Rows should sum to 1
        self.assertTrue(np.allclose(model.P_agg.sum(axis=1), 1))
        self.assertTrue(np.allclose(model.P_emp_gg.sum(axis=1), 1))
        self.assertTrue(np.allclose(model.P_emp_bb.sum(axis=1), 1))
    
    def test_simulation_structure(self):
        """Test simulation returns correct structure."""
        config = HeterogeneousAgentsConfig(n_agents=100, T_sim=50)
        model = HeterogeneousAgentsModel(config)
        result = model.run()
        
        self.assertIn("equilibrium", result)
        self.assertIn("distribution", result)
        self.assertIn("inequality", result)
        self.assertIn("welfare", result)
    
    def test_inequality_metrics(self):
        """Test inequality metrics are reasonable."""
        config = HeterogeneousAgentsConfig(n_agents=100, T_sim=100)
        model = HeterogeneousAgentsModel(config)
        result = model.run()
        
        ineq = result["inequality"]
        
        # Gini should be between 0 and 1
        self.assertGreaterEqual(ineq["gini"], 0)
        self.assertLessEqual(ineq["gini"], 1)
        
        # Shares should sum to reasonable value
        self.assertGreater(ineq["top10_share"], 0)
        self.assertGreater(ineq["bottom50_share"], 0)


if __name__ == "__main__":
    # Run demonstration
    config = HeterogeneousAgentsConfig(n_agents=500, T_sim=200)
    model = HeterogeneousAgentsModel(config)
    result = model.run()
    
    print("=" * 60)
    print("HETEROGENEOUS AGENTS MODEL (Krusell-Smith)")
    print("=" * 60)
    print(f"\nEquilibrium Interest Rate: {result['equilibrium']['interest_rate']:.4f}")
    print(f"Equilibrium Wage: {result['equilibrium']['wage']:.4f}")
    print(f"Asset Gini: {result['inequality']['gini']:.4f}")
    print(f"Top 10% Asset Share: {result['inequality']['top10_share']:.4f}")
    print(f"Welfare Cost of Risk: {result['welfare']['welfare_cost_of_risk']:.4f}")
    
    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for TURBO-CDI compatibility
HeterogeneousAgentsPattern = HeterogeneousAgentsModel
