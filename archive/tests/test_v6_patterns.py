"""
Test suite for TURBO-CDI v6.0 simulation patterns
"""

import pytest
import asyncio
import numpy as np

import sys
sys.path.insert(0, '/Users/figuramax/LocalProjects/TURBO-CDI')

from src.patterns.core import Hypothesis
from src.patterns.library.monte_carlo import MonteCarloPattern
from src.patterns.library.agent_based import AgentBasedPattern
from src.patterns.library.system_dynamics import SystemDynamicsPattern
from src.patterns.library.circuit_simulation import CircuitSimulationPattern


class TestMonteCarloPattern:
    """Test Monte Carlo simulation pattern"""
    
    @pytest.fixture
    def pattern(self):
        return MonteCarloPattern()
    
    @pytest.fixture
    def risk_hypothesis(self):
        return Hypothesis(
            title="Financial risk assessment",
            description="Monte Carlo simulation of portfolio risk with uncertainty",
            parameters={"base_value": 1000.0, "noise_scale": 0.2}
        )
    
    def test_can_simulate(self, pattern, risk_hypothesis):
        """Test pattern matching"""
        assert pattern.can_simulate(risk_hypothesis) is True
    
    @pytest.mark.asyncio
    async def test_run_simulation(self, pattern, risk_hypothesis):
        """Test running Monte Carlo simulation"""
        config = {"n_samples": 1000, "variance_reduction": "stratified"}
        result = await pattern.run(risk_hypothesis, config)
        
        assert result.status.value == "completed"
        assert "mean" in result.metrics
        assert "ci_lower" in result.metrics
        assert "ci_upper" in result.metrics
        assert result.confidence_score > 0.5


class TestAgentBasedPattern:
    """Test Agent-Based simulation pattern"""
    
    @pytest.fixture
    def pattern(self):
        return AgentBasedPattern()
    
    @pytest.fixture
    def market_hypothesis(self):
        return Hypothesis(
            title="Market diffusion dynamics",
            description="Agent-based simulation of product adoption in social network",
            parameters={
                "n_agents": 100,
                "n_steps": 500,
                "network_type": "small_world",
                "agent_behavior": "adaptive",
                "innovation_rate": 0.1,
            }
        )
    
    def test_can_simulate(self, pattern, market_hypothesis):
        """Test pattern matching"""
        assert pattern.can_simulate(market_hypothesis) is True
    
    @pytest.mark.asyncio
    async def test_run_simulation(self, pattern, market_hypothesis):
        """Test running ABM simulation"""
        config = {"n_agents": 50, "n_steps": 100, "grid_size": 20}
        result = await pattern.run(market_hypothesis, config)
        
        assert result.status.value == "completed"
        assert "final_mean_wealth" in result.metrics
        assert "final_gini" in result.metrics
        assert "equilibrium_reached" in result.metrics


class TestSystemDynamicsPattern:
    """Test System Dynamics simulation pattern"""
    
    @pytest.fixture
    def pattern(self):
        return SystemDynamicsPattern()
    
    @pytest.fixture
    def epidemic_hypothesis(self):
        return Hypothesis(
            title="Epidemic spread model",
            description="SIR model for disease transmission dynamics",
            parameters={
                "model_type": "epidemic",
                "S0": 990,
                "I0": 10,
                "R0": 0,
                "beta": 0.3,
                "gamma": 0.1,
                "stocks": ["susceptible", "infected", "recovered"],
            }
        )
    
    def test_can_simulate(self, pattern, epidemic_hypothesis):
        """Test pattern matching"""
        assert pattern.can_simulate(epidemic_hypothesis) is True
    
    @pytest.mark.asyncio
    async def test_run_simulation(self, pattern, epidemic_hypothesis):
        """Test running system dynamics simulation"""
        config = {
            "t_end": 100.0,
            "dt": 0.1,
            "solver": "RK45",
            "sensitivity_analysis": False,
        }
        result = await pattern.run(epidemic_hypothesis, config)
        
        assert result.status.value == "completed"
        assert "susceptible_final" in result.metrics
        assert "infected_final" in result.metrics
        assert "recovered_final" in result.metrics


class TestCircuitSimulationPattern:
    """Test Circuit simulation pattern"""
    
    @pytest.fixture
    def pattern(self):
        return CircuitSimulationPattern()
    
    @pytest.fixture
    def filter_hypothesis(self):
        return Hypothesis(
            title="RC low-pass filter design",
            description="Frequency response analysis of RC filter circuit",
            parameters={
                "circuit_type": "rc_filter",
                "resistance": 1000.0,
                "capacitance": 1e-6,
                "input_voltage": 5.0,
            }
        )
    
    def test_can_simulate(self, pattern, filter_hypothesis):
        """Test pattern matching"""
        assert pattern.can_simulate(filter_hypothesis) is True
    
    @pytest.mark.asyncio
    async def test_run_simulation(self, pattern, filter_hypothesis):
        """Test running circuit simulation"""
        config = {
            "analysis_type": "transient",
            "t_stop": 1e-3,
            "t_step": 1e-6,
        }
        result = await pattern.run(filter_hypothesis, config)
        
        assert result.status.value == "completed"
        assert "rc_time_constant" in result.metrics or "v_output_mean" in result.metrics
        assert "cutoff_frequency" in result.metrics or "total_power" in result.metrics


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
