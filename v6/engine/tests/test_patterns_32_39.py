"""
Unit tests for Patterns 32-39 (v6.4)
- Ising Model
- Phase Field
- Percolation
- Lotka-Volterra
- Epidemic SEIR
- Age-Structured
- Spatial Ecology
- Evolutionary
"""

import pytest
import numpy as np
from typing import Dict, Any
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import Hypothesis, SimulationStatus
from src.patterns.ising_model import IsingModelPattern, IsingConfig
from src.patterns.phase_field import PhaseFieldPattern, PhaseFieldConfig
from src.patterns.percolation import PercolationPattern, PercolationConfig
from src.patterns.lotka_volterra import LotkaVolterraPattern, LotkaVolterraConfig
from src.patterns.epidemic_seir import EpidemicSEIRPattern, SEIRConfig
from src.patterns.age_structured import AgeStructuredPattern, AgeStructuredConfig
from src.patterns.spatial_ecology import SpatialEcologyPattern, SpatialEcologyConfig
from src.patterns.evolutionary import EvolutionaryPattern, EvolutionaryConfig


# ============================================================================
# ISING MODEL TESTS
# ============================================================================

class TestIsingModel:
    """Test suite for Ising Model pattern"""

    @pytest.fixture
    def pattern(self):
        return IsingModelPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Ising model phase transition study",
            description="Investigate ferromagnetic phase transition using Monte Carlo simulation",
            parameters={}
        )

    def test_can_simulate_magnet_keywords(self, pattern):
        """Test detection of Ising model keywords"""
        h = Hypothesis(
            title="Magnetic phase transitions",
            description="Study spontaneous symmetry breaking in spin systems"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_percolation(self, pattern):
        """Test that percolation keywords don't trigger Ising"""
        h = Hypothesis(
            title="Percolation threshold analysis",
            description="Network connectivity and percolation theory"
        )
        assert pattern.can_simulate(h) is False

    def test_parse_config_defaults(self, pattern):
        """Test config parsing with defaults"""
        config = pattern._parse_config({})
        assert config.lattice_size == 32
        assert config.temperature == 2.27
        assert config.algorithm == "metropolis"

    def test_parse_config_custom(self, pattern):
        """Test config parsing with custom values"""
        config = pattern._parse_config({
            "lattice_size": 64,
            "temperature": 3.0,
            "algorithm": "wolff"
        })
        assert config.lattice_size == 64
        assert config.temperature == 3.0
        assert config.algorithm == "wolff"

    @pytest.mark.asyncio
    async def test_run_metropolis(self, pattern, hypothesis):
        """Test full Metropolis simulation"""
        result = await pattern.run(hypothesis, {
            "lattice_size": 16,
            "n_sweeps": 100,
            "thermalization": 10,
            "algorithm": "metropolis",
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "magnetization" in result.metrics
        assert result.metrics["n_measurements"] > 0

    @pytest.mark.asyncio
    async def test_run_wolff(self, pattern, hypothesis):
        """Test Wolff cluster algorithm"""
        result = await pattern.run(hypothesis, {
            "lattice_size": 16,
            "n_sweeps": 50,
            "thermalization": 10,
            "algorithm": "wolff",
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "magnetization" in result.metrics

    @pytest.mark.asyncio
    async def test_phase_transition_detection(self, pattern, hypothesis):
        """Test detection of ordered phase below Tc"""
        result = await pattern.run(hypothesis, {
            "lattice_size": 16,
            "temperature": 1.5,  # Below Tc ≈ 2.27
            "n_sweeps": 200,
            "thermalization": 50,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        # Below Tc should have high magnetization
        assert result.metrics["magnetization"] > 0.3

    def test_gini_coefficient(self, pattern):
        """Test Gini coefficient calculation"""
        values = [1, 2, 3, 4, 5]
        gini = pattern._gini_coefficient(values)
        assert 0 <= gini <= 1

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert resources["gpu_required"] is False


# ============================================================================
# PHASE FIELD TESTS
# ============================================================================

class TestPhaseField:
    """Test suite for Phase Field pattern"""

    @pytest.fixture
    def pattern(self):
        return PhaseFieldPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Phase separation in binary alloy",
            description="Study spinodal decomposition using Cahn-Hilliard equation"
        )

    def test_can_simulate_phase_field(self, pattern):
        """Test detection of phase field keywords"""
        h = Hypothesis(
            title="Cahn-Hilliard simulation",
            description="Phase field modeling of microstructure evolution"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_spinodal(self, pattern):
        """Test detection of spinodal decomposition"""
        h = Hypothesis(
            title="Spinodal decomposition analysis",
            description="Phase separation dynamics"
        )
        assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        """Test config parsing"""
        config = pattern._parse_config({
            "grid_size": 64,
            "M": 0.5,
            "gamma": 0.3
        })
        assert config.grid_size == 64
        assert config.M == 0.5
        assert config.gamma == 0.3

    @pytest.mark.asyncio
    async def test_run_cahn_hilliard(self, pattern, hypothesis):
        """Test Cahn-Hilliard simulation"""
        result = await pattern.run(hypothesis, {
            "grid_size": 32,
            "n_steps": 500,
            "dt": 0.005,
            "record_interval": 50,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "final_variance" in result.metrics
        assert "domain_size" in result.metrics

    @pytest.mark.asyncio
    async def test_phase_separation(self, pattern, hypothesis):
        """Test that phase separation occurs"""
        result = await pattern.run(hypothesis, {
            "grid_size": 32,
            "n_steps": 1000,
            "dt": 0.005,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        # Should show phase separation
        assert result.metrics["final_variance"] > 0.05

    def test_chemical_potential(self, pattern):
        """Test chemical potential calculation"""
        pattern.config = PhaseFieldConfig(epsilon=2.0)
        phi = np.random.randn(10, 10)
        mu = pattern._chemical_potential(phi, 2.0)
        assert mu.shape == phi.shape

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources


# ============================================================================
# PERCOLATION TESTS
# ============================================================================

class TestPercolation:
    """Test suite for Percolation pattern"""

    @pytest.fixture
    def pattern(self):
        return PercolationPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Site percolation threshold",
            description="Study percolation transition on square lattice"
        )

    def test_can_simulate_percolation(self, pattern):
        """Test detection of percolation keywords"""
        h = Hypothesis(
            title="Network connectivity threshold",
            description="Percolation and cluster analysis"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_cluster(self, pattern):
        """Test detection of cluster keywords"""
        h = Hypothesis(
            title="Cluster size distribution",
            description="Spanning cluster detection in random media"
        )
        assert pattern.can_simulate(h) is True

    def test_union_find_operations(self, pattern):
        """Test Union-Find data structure"""
        from src.patterns.percolation import UnionFind
        uf = UnionFind(10)
        
        # Initially all separate
        assert uf.find(0) != uf.find(1)
        
        # Union
        uf.union(0, 1)
        assert uf.find(0) == uf.find(1)
        
        # Size tracking
        assert uf.get_size(0) == 2

    def test_parse_config(self, pattern):
        """Test config parsing"""
        config = pattern._parse_config({
            "lattice_size": 50,
            "dimension": 3,
            "n_realizations": 50
        })
        assert config.lattice_size == 50
        assert config.dimension == 3
        assert config.n_realizations == 50

    @pytest.mark.asyncio
    async def test_run_percolation_2d(self, pattern, hypothesis):
        """Test 2D percolation simulation"""
        result = await pattern.run(hypothesis, {
            "lattice_size": 30,
            "dimension": 2,
            "n_realizations": 20,
            "n_p_values": 10,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "percolation_threshold" in result.metrics
        assert 0.5 < result.metrics["percolation_threshold"] < 0.7

    @pytest.mark.asyncio
    async def test_threshold_accuracy(self, pattern, hypothesis):
        """Test that threshold is close to theoretical value"""
        result = await pattern.run(hypothesis, {
            "lattice_size": 40,
            "dimension": 2,
            "n_realizations": 50,
            "n_p_values": 20,
            "random_seed": 42
        })
        # 2D site percolation threshold ≈ 0.5927
        error = abs(result.metrics["percolation_threshold"] - 0.592746)
        assert error < 0.1  # Within 10%

    def test_cluster_finding(self, pattern):
        """Test cluster identification"""
        pattern.config = PercolationConfig(lattice_size=5, dimension=2)
        occupied = np.array([
            [1, 1, 0, 0, 0],
            [1, 0, 0, 1, 1],
            [0, 0, 0, 1, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0]
        ], dtype=bool)
        
        clusters = pattern._find_clusters_union_find(occupied, 5, 2)
        assert len(clusters) >= 2  # Should have multiple clusters

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources


# ============================================================================
# LOTKA-VOLTERRA TESTS
# ============================================================================

class TestLotkaVolterra:
    """Test suite for Lotka-Volterra pattern"""

    @pytest.fixture
    def pattern(self):
        return LotkaVolterraPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Predator-prey dynamics",
            description="Lotka-Volterra oscillations in ecological system",
            parameters={"alpha": 1.0, "beta": 0.1, "gamma": 1.5, "delta": 0.075}
        )

    def test_can_simulate_predator_prey(self, pattern):
        """Test detection of predator-prey keywords"""
        h = Hypothesis(
            title="Predator-prey oscillations",
            description="Lotka-Volterra population cycles"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_competition(self, pattern):
        """Test detection of competition keywords"""
        h = Hypothesis(
            title="Species competition dynamics",
            description="Competitive exclusion in ecological communities"
        )
        assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        """Test config parsing"""
        config = pattern._parse_config({
            "model_type": "competitive",
            "n_species": 3,
            "t_max": 200.0
        })
        assert config.model_type == "competitive"
        assert config.t_max == 200.0

    @pytest.mark.asyncio
    async def test_run_predator_prey(self, pattern, hypothesis):
        """Test predator-prey simulation"""
        result = await pattern.run(hypothesis, {
            "model_type": "predator_prey",
            "t_max": 50.0,
            "dt": 0.01
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "final_populations" in result.metrics

    @pytest.mark.asyncio
    async def test_oscillation_detection(self, pattern, hypothesis):
        """Test detection of limit cycle oscillations"""
        result = await pattern.run(hypothesis, {
            "model_type": "predator_prey",
            "t_max": 100.0,
            "dt": 0.01
        })
        assert result.status == SimulationStatus.COMPLETED
        # Should show oscillations
        assert result.metrics["oscillation_period"] > 0

    @pytest.mark.asyncio
    async def test_stable_equilibrium(self, pattern):
        """Test competitive model reaching equilibrium"""
        h = Hypothesis(
            title="Competitive dynamics",
            description="Stable coexistence",
            parameters={}
        )
        result = await pattern.run(h, {
            "model_type": "competitive",
            "n_species": 2,
            "t_max": 100.0
        })
        assert result.status == SimulationStatus.COMPLETED

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "estimated_time_seconds" in resources


# ============================================================================
# EPIDEMIC SEIR TESTS
# ============================================================================

class TestEpidemicSEIR:
    """Test suite for Epidemic SEIR pattern"""

    @pytest.fixture
    def pattern(self):
        return EpidemicSEIRPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="COVID-19 outbreak dynamics",
            description="SEIR model for infectious disease transmission"
        )

    def test_can_simulate_epidemic(self, pattern):
        """Test detection of epidemic keywords"""
        h = Hypothesis(
            title="Disease outbreak modeling",
            description="Epidemic dynamics and herd immunity"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_r0(self, pattern):
        """Test detection of R0 keywords"""
        h = Hypothesis(
            title="Basic reproduction number analysis",
            description="R0 and transmission dynamics"
        )
        assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        """Test config parsing"""
        config = pattern._parse_config({
            "model_type": "seir",
            "N": 10000,
            "beta": 0.8,
            "gamma": 0.2
        })
        assert config.model_type == "seir"
        assert config.N == 10000
        assert config.beta == 0.8

    @pytest.mark.asyncio
    async def test_run_seir(self, pattern, hypothesis):
        """Test SEIR simulation"""
        result = await pattern.run(hypothesis, {
            "model_type": "seir",
            "N": 10000,
            "I0": 10,
            "beta": 0.5,
            "gamma": 0.1,
            "t_max": 100.0,
            "stochastic": False
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "R0" in result.metrics
        assert "final_epidemic_size" in result.metrics

    @pytest.mark.asyncio
    async def test_r0_calculation(self, pattern, hypothesis):
        """Test R0 calculation"""
        result = await pattern.run(hypothesis, {
            "beta": 0.6,
            "gamma": 0.2,
            "t_max": 50.0,
            "stochastic": False
        })
        # R0 = beta / gamma = 0.6 / 0.2 = 3.0
        assert abs(result.metrics["R0"] - 3.0) < 0.1

    @pytest.mark.asyncio
    async def test_epidemic_vs_no_epidemic(self, pattern, hypothesis):
        """Test R0 > 1 leads to epidemic, R0 < 1 doesn't"""
        # R0 > 1 should cause epidemic
        result_epidemic = await pattern.run(hypothesis, {
            "beta": 0.6,
            "gamma": 0.2,  # R0 = 3
            "t_max": 50.0,
            "stochastic": False
        })
        
        # R0 < 1 should die out
        result_no_epidemic = await pattern.run(hypothesis, {
            "beta": 0.1,
            "gamma": 0.2,  # R0 = 0.5
            "t_max": 50.0,
            "stochastic": False
        })
        
        assert result_epidemic.metrics["final_epidemic_size"] > result_no_epidemic.metrics["final_epidemic_size"]

    @pytest.mark.asyncio
    async def test_stochastic_simulation(self, pattern, hypothesis):
        """Test stochastic Gillespie simulation"""
        result = await pattern.run(hypothesis, {
            "N": 1000,
            "stochastic": True,
            "n_realizations": 10,
            "t_max": 50.0
        })
        assert result.status == SimulationStatus.COMPLETED

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources


# ============================================================================
# AGE-STRUCTURED TESTS
# ============================================================================

class TestAgeStructured:
    """Test suite for Age-Structured pattern"""

    @pytest.fixture
    def pattern(self):
        return AgeStructuredPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Demographic transition",
            description="Age-structured population dynamics with declining fertility"
        )

    def test_can_simulate_demography(self, pattern):
        """Test detection of demography keywords"""
        h = Hypothesis(
            title="Population aging dynamics",
            description="Age structure and demographic transition"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_life_table(self, pattern):
        """Test detection of life table keywords"""
        h = Hypothesis(
            title="Life table analysis",
            description="Survival curves and cohort dynamics"
        )
        assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        """Test config parsing"""
        config = pattern._parse_config({
            "max_age": 120,
            "age_groups": 30,
            "birth_rate": 0.02
        })
        assert config.max_age == 120
        assert config.age_groups == 30
        assert config.birth_rate == 0.02

    def test_survival_curve_type1(self, pattern):
        """Test Type I survival curve (human-like)"""
        pattern.config = AgeStructuredConfig(
            max_age=100,
            age_groups=20,
            survival_type="type1"
        )
        survival = pattern._get_survival_curve()
        assert len(survival) == 20
        assert survival[0] > survival[-1]  # Survival decreases with age

    def test_survival_curve_type2(self, pattern):
        """Test Type II survival curve (constant mortality)"""
        pattern.config = AgeStructuredConfig(
            max_age=100,
            age_groups=20,
            survival_type="type2"
        )
        survival = pattern._get_survival_curve()
        # Type II should have more uniform decline
        diffs = np.diff(survival)
        assert np.std(diffs) < 0.2  # Relatively constant

    @pytest.mark.asyncio
    async def test_run_simulation(self, pattern, hypothesis):
        """Test age-structured simulation"""
        result = await pattern.run(hypothesis, {
            "max_age": 100,
            "age_groups": 20,
            "t_max": 50.0,
            "birth_rate": 0.025,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "final_population" in result.metrics
        assert "mean_age_final" in result.metrics

    @pytest.mark.asyncio
    async def test_population_growth(self, pattern, hypothesis):
        """Test that population grows with high birth rate"""
        result = await pattern.run(hypothesis, {
            "t_max": 50.0,
            "birth_rate": 0.03,  # High birth rate
            "carrying_capacity": 2000000,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["growth_rate"] > 0

    def test_fertility_rates(self, pattern):
        """Test age-specific fertility rates"""
        pattern.config = AgeStructuredConfig(
            max_age=100,
            age_groups=20,
            birth_rate=0.025
        )
        fertility = pattern._get_fertility_rates()
        assert len(fertility) == 20
        # Peak fertility should be in middle age groups
        peak_idx = np.argmax(fertility)
        assert 3 < peak_idx < 12  # Roughly ages 15-45

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources


# ============================================================================
# SPATIAL ECOLOGY TESTS
# ============================================================================

class TestSpatialEcology:
    """Test suite for Spatial Ecology pattern"""

    @pytest.fixture
    def pattern(self):
        return SpatialEcologyPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Species invasion wave",
            description="Fisher-KPP equation for range expansion"
        )

    def test_can_simulate_invasion(self, pattern):
        """Test detection of invasion keywords"""
        h = Hypothesis(
            title="Invasive species spread",
            description="Spatial spread and reaction-diffusion"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_turing(self, pattern):
        """Test detection of Turing pattern keywords"""
        h = Hypothesis(
            title="Turing pattern formation",
            description="Activator-inhibitor system and morphogenesis"
        )
        assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        """Test config parsing"""
        config = pattern._parse_config({
            "model_type": "fisher_kpp",
            "grid_size": 64,
            "D": 0.2,
            "r": 1.5
        })
        assert config.model_type == "fisher_kpp"
        assert config.grid_size == 64

    @pytest.mark.asyncio
    async def test_run_fisher_kpp(self, pattern, hypothesis):
        """Test Fisher-KPP simulation"""
        result = await pattern.run(hypothesis, {
            "model_type": "fisher_kpp",
            "grid_size": 32,
            "n_steps": 1000,
            "dt": 0.005,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_wave_speed(self, pattern, hypothesis):
        """Test invasion wave speed calculation"""
        result = await pattern.run(hypothesis, {
            "model_type": "fisher_kpp",
            "grid_size": 64,
            "n_steps": 2000,
            "D": 0.1,
            "r": 1.0,
            "dt": 0.005,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        # Check wave speed exists and is reasonable
        if "wave_speed" in result.metrics:
            # Theoretical: v = 2*sqrt(D*r) = 2*sqrt(0.1) ≈ 0.63
            assert result.metrics["wave_speed"] > 0

    @pytest.mark.asyncio
    async def test_turing_patterns(self, pattern):
        """Test Turing pattern formation"""
        h = Hypothesis(
            title="Turing pattern formation",
            description="Test morphogenesis patterns"
        )
        result = await pattern.run(h, {
            "model_type": "turing",
            "grid_size": 32,
            "n_steps": 2000,
            "dt": 0.01,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED

    def test_laplacian_calculation(self, pattern):
        """Test Laplacian calculation"""
        from scipy.ndimage import laplace
        field = np.random.randn(10, 10)
        lap = laplace(field)
        assert lap.shape == field.shape

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources


# ============================================================================
# EVOLUTIONARY TESTS
# ============================================================================

class TestEvolutionary:
    """Test suite for Evolutionary Dynamics pattern"""

    @pytest.fixture
    def pattern(self):
        return EvolutionaryPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(
            title="Fixation probability in Moran process",
            description="Evolutionary dynamics and genetic drift"
        )

    def test_can_simulate_evolution(self, pattern):
        """Test detection of evolution keywords"""
        h = Hypothesis(
            title="Evolutionary dynamics",
            description="Moran process and fixation probability"
        )
        assert pattern.can_simulate(h) is True

    def test_can_simulate_fixation(self, pattern):
        """Test detection of fixation keywords"""
        h = Hypothesis(
            title="Allele fixation analysis",
            description="Genetic drift in finite populations"
        )
        assert pattern.can_simulate(h) is True

    def test_parse_config(self, pattern):
        """Test config parsing"""
        config = pattern._parse_config({
            "model_type": "moran",
            "N": 200,
            "selection_strength": 0.5,
            "n_realizations": 50
        })
        assert config.model_type == "moran"
        assert config.N == 200

    @pytest.mark.asyncio
    async def test_run_moran(self, pattern, hypothesis):
        """Test Moran process simulation"""
        result = await pattern.run(hypothesis, {
            "model_type": "moran",
            "N": 50,
            "n_generations": 500,
            "n_realizations": 20,
            "selection_strength": 1.0,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "fixation_prob_A" in result.metrics

    @pytest.mark.asyncio
    async def test_run_wright_fisher(self, pattern, hypothesis):
        """Test Wright-Fisher simulation"""
        result = await pattern.run(hypothesis, {
            "model_type": "wright_fisher",
            "N": 50,
            "n_generations": 500,
            "n_realizations": 20,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED
        assert "fixation_prob_A" in result.metrics

    @pytest.mark.asyncio
    async def test_fixation_probability_advantageous(self, pattern, hypothesis):
        """Test that advantageous allele has higher fixation probability"""
        # Neutral
        result_neutral = await pattern.run(hypothesis, {
            "N": 100,
            "selection_strength": 0.0,
            "n_realizations": 50,
            "n_generations": 1000,
            "random_seed": 42
        })
        
        # Advantageous
        result_advantageous = await pattern.run(hypothesis, {
            "N": 100,
            "selection_strength": 1.0,
            "n_realizations": 50,
            "n_generations": 1000,
            "random_seed": 43
        })
        
        # Advantageous allele should have higher fixation prob
        # Neutral: ~1/N = 0.01, Advantageous: higher
        assert result_advantageous.metrics["fixation_prob_A"] > result_neutral.metrics["fixation_prob_A"]

    @pytest.mark.asyncio
    async def test_fixation_theory_agreement(self, pattern, hypothesis):
        """Test agreement with theoretical fixation probability"""
        result = await pattern.run(hypothesis, {
            "N": 100,
            "selection_strength": 1.0,
            "n_realizations": 100,
            "n_generations": 2000,
            "random_seed": 42
        })
        
        # Check that simulation agrees with theory within reasonable bounds
        error = result.metrics.get("fixation_error", 1.0)
        assert error < 0.3  # Within 30% for stochastic simulation

    def test_estimate_resources(self, pattern, hypothesis):
        """Test resource estimation"""
        resources = pattern.estimate_resources(hypothesis)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPatternIntegration:
    """Integration tests for all patterns"""

    @pytest.mark.asyncio
    async def test_all_patterns_load(self):
        """Test that all patterns can be imported and instantiated"""
        patterns = [
            IsingModelPattern(),
            PhaseFieldPattern(),
            PercolationPattern(),
            LotkaVolterraPattern(),
            EpidemicSEIRPattern(),
            AgeStructuredPattern(),
            SpatialEcologyPattern(),
            EvolutionaryPattern(),
        ]
        
        for pattern in patterns:
            assert pattern.id is not None
            assert pattern.name is not None
            assert len(pattern.parameters) > 0

    @pytest.mark.asyncio
    async def test_all_patterns_run(self):
        """Test that all patterns can run basic simulations"""
        test_configs = [
            (IsingModelPattern(), {"lattice_size": 8, "n_sweeps": 50, "thermalization": 10}),
            (PhaseFieldPattern(), {"grid_size": 16, "n_steps": 100, "dt": 0.005}),
            (PercolationPattern(), {"lattice_size": 20, "n_realizations": 10, "n_p_values": 5}),
            (LotkaVolterraPattern(), {"t_max": 20.0, "model_type": "predator_prey"}),
            (EpidemicSEIRPattern(), {"N": 1000, "t_max": 30.0, "stochastic": False}),
            (AgeStructuredPattern(), {"age_groups": 10, "t_max": 20.0}),
            (SpatialEcologyPattern(), {"grid_size": 16, "n_steps": 200}),
            (EvolutionaryPattern(), {"N": 30, "n_realizations": 10, "n_generations": 100}),
        ]
        
        h = Hypothesis(title="Test", description="Test hypothesis")
        
        for pattern, config in test_configs:
            result = await pattern.run(h, config)
            assert result.status == SimulationStatus.COMPLETED, f"{pattern.name} failed"
            assert result.confidence_score >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
