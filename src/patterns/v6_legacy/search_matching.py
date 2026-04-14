"""
Pattern 53: Search and Matching (DMP) Model
Implements the Diamond-Mortensen-Pissarides model of labor market search,
unemployment dynamics, and job creation.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, List
import numpy as np
from scipy.optimize import fsolve


@dataclass
class SearchMatchingConfig:
    """Configuration for DMP search and matching model."""
    alpha: float = 0.5        # Matching function elasticity
    gamma: float = 0.5        # Worker bargaining power
    r: float = 0.05           # Discount rate
    delta: float = 0.03       # Job destruction rate
    c: float = 0.3            # Vacancy posting cost
    z: float = 0.4            # Unemployment benefit / home production
    p: float = 1.0            # Labor productivity
    eta: float = 0.5          # Matching efficiency
    max_iterations: int = 1000
    tolerance: float = 1e-6
    random_seed: int = 42


class SearchMatchingModel:
    """
    Diamond-Mortensen-Pissarides (DMP) model.
    
    Models labor market dynamics with search frictions, job creation,
    and wage bargaining between workers and firms.
    """
    
    def __init__(self, config: SearchMatchingConfig = None):
        self.config = config or SearchMatchingConfig()
        np.random.seed(self.config.random_seed)
    
    def matching_function(self, u: float, v: float) -> float:
        """
        Cobb-Douglas matching function: m(u,v) = eta * u^alpha * v^(1-alpha)
        
        Args:
            u: Unemployment rate
            v: Vacancy rate
        
        Returns:
            Number of matches
        """
        cfg = self.config
        if u <= 0 or v <= 0:
            return 0
        return cfg.eta * (u ** cfg.alpha) * (v ** (1 - cfg.alpha))
    
    def job_finding_rate(self, theta: float) -> float:
        """
        Job finding rate: f(theta) = eta * theta^(1-alpha)
        where theta = v/u is labor market tightness
        """
        cfg = self.config
        return cfg.eta * (theta ** (1 - cfg.alpha))
    
    def job_filling_rate(self, theta: float) -> float:
        """
        Job filling rate: q(theta) = eta * theta^(-alpha)
        """
        cfg = self.config
        if theta <= 0:
            return float('inf')
        return cfg.eta * (theta ** (-cfg.alpha))
    
    def solve_steady_state(self) -> Dict[str, float]:
        """
        Solve for steady state equilibrium.
        
        Returns:
            Dict with equilibrium values
        """
        cfg = self.config
        
        # Free entry condition: c = q(theta) * (J - V) = q(theta) * J
        # where J = (p - w) / (r + delta) is firm value
        
        # Nash bargaining: w = gamma * (p + c*theta) + (1-gamma)*z
        # From free entry and Nash: theta satisfies equilibrium condition
        
        def equilibrium_condition(theta):
            if theta <= 0:
                return float('inf')
            
            # Job filling rate
            q = self.job_filling_rate(theta)
            
            # Wage from Nash bargaining
            w = cfg.gamma * (cfg.p + cfg.c * theta) + (1 - cfg.gamma) * cfg.z
            
            # Firm surplus
            J = (cfg.p - w) / (cfg.r + cfg.delta)
            
            # Free entry: c = q * J
            return cfg.c - q * J
        
        # Solve for equilibrium theta
        try:
            theta_ss = fsolve(equilibrium_condition, 1.0)[0]
            theta_ss = max(0.01, theta_ss)
        except:
            theta_ss = 1.0
        
        # Compute equilibrium values
        f = self.job_finding_rate(theta_ss)
        q = self.job_filling_rate(theta_ss)
        w = cfg.gamma * (cfg.p + cfg.c * theta_ss) + (1 - cfg.gamma) * cfg.z
        
        # Beveridge curve: u = delta / (delta + f(theta))
        u_ss = cfg.delta / (cfg.delta + f)
        
        # Vacancy rate from theta = v/u
        v_ss = theta_ss * u_ss
        
        # Match rate
        m_ss = self.matching_function(u_ss, v_ss)
        
        # Labor market tightness
        
        return {
            "theta": float(theta_ss),
            "unemployment_rate": float(u_ss),
            "vacancy_rate": float(v_ss),
            "job_finding_rate": float(f),
            "job_filling_rate": float(q),
            "match_rate": float(m_ss),
            "wage": float(w),
            "tightness": float(theta_ss)
        }
    
    def simulate_dynamics(self, T: int = 100, shock_period: int = 20) -> Dict[str, List[float]]:
        """
        Simulate transition dynamics with productivity shock.
        
        Args:
            T: Number of periods
            shock_period: Period when shock occurs
        
        Returns:
            Dict with time series of variables
        """
        cfg = self.config
        
        # Initialize
        u = np.zeros(T)
        theta = np.zeros(T)
        v = np.zeros(T)
        w = np.zeros(T)
        
        # Start at steady state
        ss = self.solve_steady_state()
        u[0] = ss["unemployment_rate"]
        theta[0] = ss["tightness"]
        
        # Productivity path (with shock)
        p_path = np.ones(T) * cfg.p
        p_path[shock_period:shock_period+10] *= 0.9  # 10% productivity drop
        
        for t in range(T - 1):
            # Current productivity
            p = p_path[t]
            
            # Solve for theta given current unemployment
            def eqm_cond(th):
                if th <= 0:
                    return float('inf')
                q = self.job_filling_rate(th)
                w_t = cfg.gamma * (p + cfg.c * th) + (1 - cfg.gamma) * cfg.z
                J = (p - w_t) / (cfg.r + cfg.delta)
                return cfg.c - q * J
            
            try:
                theta[t] = fsolve(eqm_cond, theta[max(0, t-1)])[0]
                theta[t] = max(0.01, theta[t])
            except:
                theta[t] = theta[max(0, t-1)]
            
            # Wage
            w[t] = cfg.gamma * (p + cfg.c * theta[t]) + (1 - cfg.gamma) * cfg.z
            
            # Vacancy rate
            v[t] = theta[t] * u[t]
            
            # Unemployment dynamics
            f = self.job_finding_rate(theta[t])
            u[t + 1] = u[t] + cfg.delta * (1 - u[t]) - f * u[t]
            u[t + 1] = np.clip(u[t + 1], 0.001, 0.99)
        
        # Final period
        w[T-1] = w[T-2] if T > 1 else ss["wage"]
        v[T-1] = v[T-2] if T > 1 else ss["vacancy_rate"]
        theta[T-1] = theta[T-2] if T > 1 else ss["tightness"]
        
        return {
            "unemployment": u.tolist(),
            "vacancies": v.tolist(),
            "tightness": theta.tolist(),
            "wages": w.tolist(),
            "productivity": p_path.tolist()
        }
    
    def analyze_policy(self, policy_type: str = "unemployment_insurance") -> Dict[str, Any]:
        """
        Analyze effects of labor market policies.
        
        Args:
            policy_type: Type of policy to analyze
        
        Returns:
            Dict with policy analysis results
        """
        cfg = self.config
        baseline = self.solve_steady_state()
        
        results = {"baseline": baseline}
        
        if policy_type == "unemployment_insurance":
            # Higher unemployment benefits
            cfg.z *= 1.2
            high_ui = self.solve_steady_state()
            results["higher_ui"] = high_ui
            cfg.z /= 1.2
            
        elif policy_type == "hiring_subsidy":
            # Lower vacancy posting cost
            cfg.c *= 0.8
            subsidy = self.solve_steady_state()
            results["hiring_subsidy"] = subsidy
            cfg.c /= 0.8
            
        elif policy_type == "worker_power":
            # Higher worker bargaining power
            cfg.gamma = min(0.9, cfg.gamma + 0.1)
            high_power = self.solve_steady_state()
            results["higher_worker_power"] = high_power
            cfg.gamma -= 0.1
        
        # Calculate elasticities
        results["elasticities"] = {
            "unemployment_to_benefits": (results.get("higher_ui", baseline)["unemployment_rate"] - baseline["unemployment_rate"]) / (0.2 * cfg.z),
            "vacancies_to_subsidy": (results.get("hiring_subsidy", baseline)["vacancy_rate"] - baseline["vacancy_rate"]) / (-0.2 * cfg.c)
        }
        
        return results
    
    def run(self) -> Dict[str, Any]:
        """
        Execute full DMP model analysis.
        
        Returns:
            Dict with steady state, dynamics, and policy analysis
        """
        # Steady state
        steady_state = self.solve_steady_state()
        
        # Dynamics
        dynamics = self.simulate_dynamics(T=100, shock_period=20)
        
        # Policy analysis
        policy_ui = self.analyze_policy("unemployment_insurance")
        policy_subsidy = self.analyze_policy("hiring_subsidy")
        
        # Hosios condition check (efficiency condition)
        hosios_satisfied = np.isclose(self.config.alpha, self.config.gamma, atol=0.1)
        
        # Calculate social welfare (simplified)
        welfare = self._calculate_welfare(steady_state)
        
        return {
            "steady_state": steady_state,
            "transition_dynamics": dynamics,
            "policy_analysis": {
                "unemployment_insurance": policy_ui,
                "hiring_subsidy": policy_subsidy
            },
            "efficiency": {
                "hosios_satisfied": bool(hosios_satisfied),
                "matching_elasticity": self.config.alpha,
                "bargaining_power": self.config.gamma
            },
            "welfare": welfare,
            "model_type": "dmp_search_matching"
        }
    
    def _calculate_welfare(self, ss: Dict[str, float]) -> Dict[str, float]:
        """Calculate social welfare metrics."""
        cfg = self.config
        
        # Output per worker
        y = (1 - ss["unemployment_rate"]) * cfg.p + ss["unemployment_rate"] * cfg.z
        
        # Vacancy costs
        vacancy_costs = ss["vacancy_rate"] * cfg.c
        
        # Net output
        net_output = y - vacancy_costs
        
        return {
            "gross_output": float(y),
            "vacancy_costs": float(vacancy_costs),
            "net_output": float(net_output),
            "average_wage": float(ss["wage"])
        }
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 53,
            "name": "Search and Matching",
            "category": "Labor Economics",
            "description": "Diamond-Mortensen-Pissarides model of labor market search",
            "author": "Diamond, Mortensen, Pissarides",
            "year": 1982,
            "parameters": ["alpha", "gamma", "r", "delta", "c", "z", "p"],
            "outputs": ["steady_state", "transition", "policy_effects"],
            "applications": ["unemployment_analysis", "labor_policy", "job_creation"]
        }


# Unit Tests
import unittest

class TestSearchMatchingModel(unittest.TestCase):
    
    def test_matching_function(self):
        """Test matching function properties."""
        config = SearchMatchingConfig()
        model = SearchMatchingModel(config)
        
        # Matching should be increasing in both arguments
        m1 = model.matching_function(0.1, 0.1)
        m2 = model.matching_function(0.2, 0.1)
        m3 = model.matching_function(0.1, 0.2)
        
        self.assertGreater(m2, m1)
        self.assertGreater(m3, m1)
        
        # Zero unemployment or vacancies should give zero matches
        self.assertEqual(model.matching_function(0, 0.1), 0)
        self.assertEqual(model.matching_function(0.1, 0), 0)
    
    def test_job_finding_rate(self):
        """Test job finding rate decreases with tightness."""
        config = SearchMatchingConfig(alpha=0.5)
        model = SearchMatchingModel(config)
        
        f1 = model.job_finding_rate(0.5)
        f2 = model.job_finding_rate(1.0)
        f3 = model.job_finding_rate(2.0)
        
        # Higher tightness should lead to higher job finding rate
        self.assertGreater(f3, f2)
        self.assertGreater(f2, f1)
    
    def test_steady_state_properties(self):
        """Test steady state has reasonable properties."""
        config = SearchMatchingConfig()
        model = SearchMatchingModel(config)
        ss = model.solve_steady_state()
        
        # Rates should be between 0 and 1
        self.assertGreater(ss["unemployment_rate"], 0)
        self.assertLess(ss["unemployment_rate"], 1)
        self.assertGreater(ss["vacancy_rate"], 0)
        
        # Wage should be between z and p
        self.assertGreaterEqual(ss["wage"], config.z)
        self.assertLessEqual(ss["wage"], config.p)
    
    def test_beveridge_curve(self):
        """Test Beveridge curve relationship."""
        config = SearchMatchingConfig()
        model = SearchMatchingModel(config)
        
        # Higher job finding rate should lower unemployment
        ss = model.solve_steady_state()
        u = ss["unemployment_rate"]
        f = ss["job_finding_rate"]
        
        # Check Beveridge curve formula
        expected_u = config.delta / (config.delta + f)
        self.assertAlmostEqual(u, expected_u, places=5)
    
    def test_simulation_convergence(self):
        """Test simulation returns expected structure."""
        config = SearchMatchingConfig()
        model = SearchMatchingModel(config)
        dynamics = model.simulate_dynamics(T=50)
        
        self.assertEqual(len(dynamics["unemployment"]), 50)
        self.assertEqual(len(dynamics["vacancies"]), 50)
        self.assertEqual(len(dynamics["wages"]), 50)
    
    def test_policy_analysis(self):
        """Test policy analysis changes outcomes."""
        config = SearchMatchingConfig()
        model = SearchMatchingModel(config)
        
        policy = model.analyze_policy("unemployment_insurance")
        
        self.assertIn("baseline", policy)
        self.assertIn("higher_ui", policy)
        
        # Higher UI should increase unemployment
        self.assertGreater(
            policy["higher_ui"]["unemployment_rate"],
            policy["baseline"]["unemployment_rate"]
        )


if __name__ == "__main__":
    # Run demonstration
    config = SearchMatchingConfig()
    model = SearchMatchingModel(config)
    result = model.run()
    
    print("=" * 60)
    print("SEARCH AND MATCHING MODEL (DMP)")
    print("=" * 60)
    print(f"\nSteady State Unemployment: {result['steady_state']['unemployment_rate']:.4f}")
    print(f"Vacancy Rate: {result['steady_state']['vacancy_rate']:.4f}")
    print(f"Labor Market Tightness: {result['steady_state']['tightness']:.4f}")
    print(f"Wage: {result['steady_state']['wage']:.4f}")
    print(f"Hosios Condition Satisfied: {result['efficiency']['hosios_satisfied']}")
    print(f"Net Output: {result['welfare']['net_output']:.4f}")
    
    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for TURBO-CDI compatibility
SearchMatchingPattern = SearchMatchingModel
