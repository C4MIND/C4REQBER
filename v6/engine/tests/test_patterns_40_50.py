"""
Unit tests for TURBO-CDI v6 Patterns 40-50
Biological and Ecological Modeling Patterns

Tests cover:
- Hodgkin-Huxley neuron model
- Neural mass models
- Synaptic plasticity (STDP)
- Connectome network dynamics
- Enzyme kinetics
- Signal transduction
- Gene regulatory networks
- Protein folding
- Forest gap dynamics
- Fisheries stock assessment
- Metapopulation models
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock

# Import patterns
from v6.engine.src.patterns.hodgkin_huxley import HodgkinHuxleyPattern, HHConfig, StimulusType
from v6.engine.src.patterns.neural_mass import NeuralMassPattern, NeuralMassConfig, NeuralMassModel
from v6.engine.src.patterns.synaptic_plasticity import SynapticPlasticityPattern, SynapticPlasticityConfig, PlasticityRule
from v6.engine.src.patterns.connectome import ConnectomePattern, ConnectomeConfig, NetworkModel
from v6.engine.src.patterns.enzyme_kinetics import EnzymeKineticsPattern, EnzymeKineticsConfig, KineticModel
from v6.engine.src.patterns.signal_transduction import SignalTransductionPattern, SignalTransductionConfig, SignalingModel
from v6.engine.src.patterns.gene_regulatory import GeneRegulatoryPattern, GeneRegulatoryConfig, GRNModel
from v6.engine.src.patterns.protein_folding import ProteinFoldingPattern, ProteinFoldingConfig, FoldingModel
from v6.engine.src.patterns.forest_gap import ForestGapPattern, ForestGapConfig, GapState
from v6.engine.src.patterns.fisheries import FisheriesPattern, FisheriesConfig, RecruitmentModel, ProductionModel
from v6.engine.src.patterns.metapopulation import MetapopulationPattern, MetapopulationConfig, MetapopulationModel

from v6.engine.src.core import Hypothesis, SimulationStatus


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_hypothesis():
    """Create a mock hypothesis for testing"""
    return Hypothesis(
        id="test_hypothesis",
        title="Test Hypothesis",
        description="A test hypothesis for pattern validation",
        parameters={}
    )


@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Pattern 40: Hodgkin-Huxley Tests
# ============================================================================

class TestHodgkinHuxleyPattern:
    """Test suite for Hodgkin-Huxley neuron model"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = HodgkinHuxleyPattern()
        assert pattern.id == "hodgkin_huxley"
        assert pattern.name == "Hodgkin-Huxley Neuron Model"
        assert pattern.category == "neuroscience"
        assert pattern.config is not None
    
    def test_can_simulate_matching_keywords(self):
        """Test hypothesis matching for relevant keywords"""
        pattern = HodgkinHuxleyPattern()
        
        # Should match
        h1 = Hypothesis(title="Hodgkin-Huxley model", description="Action potentials")
        h2 = Hypothesis(title="Neuron dynamics", description="Ion channel conductance")
        h3 = Hypothesis(title="Spike generation", description="Sodium and potassium currents")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_can_simulate_non_matching(self):
        """Test hypothesis rejection for irrelevant topics"""
        pattern = HodgkinHuxleyPattern()
        
        h = Hypothesis(title="Economic growth", description="GDP and inflation")
        assert not pattern.can_simulate(h)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = HHConfig(
            C_m=1.5,
            g_Na=150.0,
            I_inj=15.0,
            stim_type=StimulusType.PULSE
        )
        assert cfg.C_m == 1.5
        assert cfg.g_Na == 150.0
        assert cfg.stim_type == StimulusType.PULSE
    
    @pytest.mark.asyncio
    async def test_run_simulation(self, mock_hypothesis):
        """Test basic simulation run"""
        pattern = HodgkinHuxleyPattern()
        config = {
            "t_max": 20.0,  # Short simulation for speed
            "I_inj": 10.0,
            "stim_type": "step"
        }
        
        result = await pattern.run(mock_hypothesis, config)
        
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("hh_")
        assert len(result.logs) > 0
        assert "num_spikes" in result.metrics
    
    @pytest.mark.asyncio
    async def test_different_stimulus_types(self, mock_hypothesis):
        """Test different stimulus waveforms"""
        pattern = HodgkinHuxleyPattern()
        
        for stim_type in ["step", "ramp", "pulse"]:
            config = {"t_max": 20.0, "stim_type": stim_type}
            result = await pattern.run(mock_hypothesis, config)
            assert result.status == SimulationStatus.COMPLETED
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = HodgkinHuxleyPattern.get_metadata()
        assert metadata["id"] == "hodgkin_huxley"
        assert "parameters" in metadata
        assert "references" in metadata
    
    def test_estimate_resources(self):
        """Test resource estimation"""
        pattern = HodgkinHuxleyPattern()
        h = Hypothesis(parameters={"t_max": 100.0, "dt": 0.01})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert resources["cpu_cores"] == 1


# ============================================================================
# Pattern 41: Neural Mass Tests
# ============================================================================

class TestNeuralMassPattern:
    """Test suite for Neural Mass models"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = NeuralMassPattern()
        assert pattern.id == "neural_mass"
        assert pattern.category == "neuroscience"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = NeuralMassPattern()
        
        h1 = Hypothesis(title="Neural mass model", description="EEG simulation")
        h2 = Hypothesis(title="Jansen-Rit model", description="Alpha rhythm")
        h3 = Hypothesis(title="Mean field brain dynamics", description="")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = NeuralMassConfig(
            model=NeuralMassModel.WENDLING,
            He=5.0,
            P=300.0
        )
        assert cfg.model == NeuralMassModel.WENDLING
        assert cfg.He == 5.0
    
    @pytest.mark.asyncio
    async def test_run_jansen_rit(self, mock_hypothesis):
        """Test Jansen-Rit model simulation"""
        pattern = NeuralMassPattern()
        config = {
            "model": "jansen_rit",
            "t_max": 2.0,
            "P": 220.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "eeg_mean_amplitude" in result.metrics
        assert "dominant_freq" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_wilson_cowan(self, mock_hypothesis):
        """Test Wilson-Cowan model simulation"""
        pattern = NeuralMassPattern()
        config = {
            "model": "wilson_cowan",
            "t_max": 1.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = NeuralMassPattern.get_metadata()
        assert metadata["id"] == "neural_mass"
        assert len(metadata["parameters"]) > 0


# ============================================================================
# Pattern 42: Synaptic Plasticity Tests
# ============================================================================

class TestSynapticPlasticityPattern:
    """Test suite for STDP and plasticity models"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = SynapticPlasticityPattern()
        assert pattern.id == "synaptic_plasticity"
        assert pattern.category == "neuroscience"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = SynapticPlasticityPattern()
        
        h1 = Hypothesis(title="STDP learning", description="Spike timing")
        h2 = Hypothesis(title="Hebbian plasticity", description="Synaptic weights")
        h3 = Hypothesis(title="Synaptic potentiation", description="LTP and LTD")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = SynapticPlasticityConfig(
            rule=PlasticityRule.BCM,
            A_plus=0.02,
            num_pre=50
        )
        assert cfg.rule == PlasticityRule.BCM
        assert cfg.A_plus == 0.02
    
    @pytest.mark.asyncio
    async def test_run_stdp(self, mock_hypothesis):
        """Test STDP simulation"""
        pattern = SynapticPlasticityPattern()
        config = {
            "rule": "stdp",
            "simulation_time": 1000.0,  # Short for speed
            "num_pre": 50,
            "num_post": 5
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_mean_weight" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_bcm(self, mock_hypothesis):
        """Test BCM theory simulation"""
        pattern = SynapticPlasticityPattern()
        config = {
            "rule": "bcm",
            "simulation_time": 1000.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_run_oja(self, mock_hypothesis):
        """Test Oja's rule simulation"""
        pattern = SynapticPlasticityPattern()
        config = {"rule": "oja", "simulation_time": 1000.0}
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = SynapticPlasticityPattern.get_metadata()
        assert metadata["id"] == "synaptic_plasticity"


# ============================================================================
# Pattern 43: Connectome Tests
# ============================================================================

class TestConnectomePattern:
    """Test suite for Connectome network dynamics"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = ConnectomePattern()
        assert pattern.id == "connectome"
        assert pattern.category == "neuroscience"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = ConnectomePattern()
        
        h1 = Hypothesis(title="Brain network connectivity", description="Resting state")
        h2 = Hypothesis(title="Functional connectivity", description="fMRI")
        h3 = Hypothesis(title="Kuramoto oscillators", description="Synchronization")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = ConnectomeConfig(
            model=NetworkModel.KURAMOTO,
            num_regions=34,
            coupling_strength=0.8
        )
        assert cfg.model == NetworkModel.KURAMOTO
        assert cfg.num_regions == 34
    
    @pytest.mark.asyncio
    async def test_run_kuramoto(self, mock_hypothesis):
        """Test Kuramoto model on connectome"""
        pattern = ConnectomePattern()
        config = {
            "model": "kuramoto",
            "num_regions": 20,  # Small for speed
            "t_max": 5.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "fc_mean" in result.metrics
        assert "mean_order_parameter" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_wilson_cowan_network(self, mock_hypothesis):
        """Test Wilson-Cowan network simulation"""
        pattern = ConnectomePattern()
        config = {
            "model": "wilson_cowan",
            "num_regions": 20,
            "t_max": 5.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = ConnectomePattern.get_metadata()
        assert metadata["id"] == "connectome"


# ============================================================================
# Pattern 44: Enzyme Kinetics Tests
# ============================================================================

class TestEnzymeKineticsPattern:
    """Test suite for Enzyme Kinetics models"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = EnzymeKineticsPattern()
        assert pattern.id == "enzyme_kinetics"
        assert pattern.category == "biology"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = EnzymeKineticsPattern()
        
        h1 = Hypothesis(title="Michaelis-Menten kinetics", description="Enzyme reaction")
        h2 = Hypothesis(title="Drug metabolism", description="CYP450")
        h3 = Hypothesis(title="Competitive inhibition", description="Km and Vmax")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = EnzymeKineticsConfig(
            model=KineticModel.HILL,
            Vmax=200.0,
            Km=75.0,
            n=2.5
        )
        assert cfg.model == KineticModel.HILL
        assert cfg.n == 2.5
    
    @pytest.mark.asyncio
    async def test_run_michaelis_menten(self, mock_hypothesis):
        """Test Michaelis-Menten simulation"""
        pattern = EnzymeKineticsPattern()
        config = {
            "model": "michaelis_menten",
            "Vmax": 100.0,
            "Km": 50.0,
            "t_max": 50.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "fitted_Km" in result.metrics
        assert "final_product" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_hill(self, mock_hypothesis):
        """Test Hill equation simulation"""
        pattern = EnzymeKineticsPattern()
        config = {
            "model": "hill",
            "n": 2.0,
            "t_max": 50.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "hill_coefficient" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_competitive_inhibition(self, mock_hypothesis):
        """Test competitive inhibition simulation"""
        pattern = EnzymeKineticsPattern()
        config = {
            "model": "competitive_inhibition",
            "I0": 10.0,
            "Ki": 5.0,
            "t_max": 50.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = EnzymeKineticsPattern.get_metadata()
        assert metadata["id"] == "enzyme_kinetics"


# ============================================================================
# Pattern 45: Signal Transduction Tests
# ============================================================================

class TestSignalTransductionPattern:
    """Test suite for Signal Transduction models"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = SignalTransductionPattern()
        assert pattern.id == "signal_transduction"
        assert pattern.category == "biology"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = SignalTransductionPattern()
        
        h1 = Hypothesis(title="MAPK cascade", description="Phosphorylation")
        h2 = Hypothesis(title="GPCR signaling", description="Second messenger")
        h3 = Hypothesis(title="Cellular adaptation", description="Perfect adaptation")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = SignalTransductionConfig(
            model=SignalingModel.TOGGLE_SWITCH,
            E1_total=0.2,
            alpha=500.0
        )
        assert cfg.model == SignalingModel.TOGGLE_SWITCH
    
    @pytest.mark.asyncio
    async def test_run_mapk_cascade(self, mock_hypothesis):
        """Test MAPK cascade simulation"""
        pattern = SignalTransductionPattern()
        config = {
            "model": "mapk_cascade",
            "E1_total": 0.1,
            "t_max": 200.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_MAPK_PP" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_repressilator(self, mock_hypothesis):
        """Test repressilator simulation"""
        pattern = SignalTransductionPattern()
        config = {
            "model": "repressilator",
            "alpha": 250.0,
            "beta": 5.0,
            "t_max": 100.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_run_toggle_switch(self, mock_hypothesis):
        """Test toggle switch simulation"""
        pattern = SignalTransductionPattern()
        config = {
            "model": "toggle_switch",
            "alpha": 50.0,
            "t_max": 100.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "bistable" in result.metrics
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = SignalTransductionPattern.get_metadata()
        assert metadata["id"] == "signal_transduction"


# ============================================================================
# Pattern 46: Gene Regulatory Tests
# ============================================================================

class TestGeneRegulatoryPattern:
    """Test suite for Gene Regulatory Networks"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = GeneRegulatoryPattern()
        assert pattern.id == "gene_regulatory"
        assert pattern.category == "biology"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = GeneRegulatoryPattern()
        
        h1 = Hypothesis(title="Gene regulatory network", description="Boolean dynamics")
        h2 = Hypothesis(title="Cell fate decision", description="Differentiation")
        h3 = Hypothesis(title="Attractor landscape", description="Gene expression")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = GeneRegulatoryConfig(
            model=GRNModel.BOOLEAN,
            num_genes=10,
            connectivity=0.4
        )
        assert cfg.model == GRNModel.BOOLEAN
        assert cfg.num_genes == 10
    
    @pytest.mark.asyncio
    async def test_run_boolean_grn(self, mock_hypothesis):
        """Test Boolean GRN simulation"""
        pattern = GeneRegulatoryPattern()
        config = {
            "model": "boolean",
            "num_genes": 10,
            "num_steps": 50,
            "update_mode": "synchronous"
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "attractor_type" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_ode_grn(self, mock_hypothesis):
        """Test ODE-based GRN simulation"""
        pattern = GeneRegulatoryPattern()
        config = {
            "model": "ode",
            "num_genes": 8,
            "t_max": 20.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_expression" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_hybrid_grn(self, mock_hypothesis):
        """Test hybrid GRN simulation"""
        pattern = GeneRegulatoryPattern()
        config = {
            "model": "hybrid",
            "num_genes": 8,
            "t_max": 20.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = GeneRegulatoryPattern.get_metadata()
        assert metadata["id"] == "gene_regulatory"


# ============================================================================
# Pattern 47: Protein Folding Tests
# ============================================================================

class TestProteinFoldingPattern:
    """Test suite for Protein Folding models"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = ProteinFoldingPattern()
        assert pattern.id == "protein_folding"
        assert pattern.category == "biology"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = ProteinFoldingPattern()
        
        h1 = Hypothesis(title="Protein folding", description="Go model")
        h2 = Hypothesis(title="Molecular dynamics", description="Coarse-grained")
        h3 = Hypothesis(title="Protein structure", description="Native contacts")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = ProteinFoldingConfig(
            model=FoldingModel.GO_MODEL,
            num_residues=40,
            temperature=350.0
        )
        assert cfg.model == FoldingModel.GO_MODEL
        assert cfg.num_residues == 40
    
    @pytest.mark.asyncio
    async def test_run_go_model(self, mock_hypothesis):
        """Test Go model simulation"""
        pattern = ProteinFoldingPattern()
        config = {
            "model": "go_model",
            "num_residues": 30,
            "t_max": 100.0,
            "dt": 0.01
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_q" in result.metrics  # Native contact fraction
        assert "final_rmsd" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_harmonic(self, mock_hypothesis):
        """Test harmonic/elastic network model"""
        pattern = ProteinFoldingPattern()
        config = {
            "model": "harmonic",
            "num_residues": 40,
            "temperature": 300.0
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "mean_rmsd" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_lattice(self, mock_hypothesis):
        """Test lattice model simulation"""
        pattern = ProteinFoldingPattern()
        config = {
            "model": "lattice",
            "num_residues": 20
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "max_hh_contacts" in result.metrics
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = ProteinFoldingPattern.get_metadata()
        assert metadata["id"] == "protein_folding"


# ============================================================================
# Pattern 48: Forest Gap Tests
# ============================================================================

class TestForestGapPattern:
    """Test suite for Forest Gap dynamics"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = ForestGapPattern()
        assert pattern.id == "forest_gap"
        assert pattern.category == "ecology"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = ForestGapPattern()
        
        h1 = Hypothesis(title="Forest gap dynamics", description="Succession")
        h2 = Hypothesis(title="Canopy disturbance", description="Regeneration")
        h3 = Hypothesis(title="Stand dynamics", description="Patch mosaic")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = ForestGapConfig(
            grid_size=30,
            num_species=3,
            disturbance_rate=0.02
        )
        assert cfg.grid_size == 30
        assert cfg.num_species == 3
    
    @pytest.mark.asyncio
    async def test_run_forest_gap(self, mock_hypothesis):
        """Test forest gap simulation"""
        pattern = ForestGapPattern()
        config = {
            "grid_size": 20,  # Small for speed
            "years": 50,
            "num_species": 3,
            "disturbance_rate": 0.01
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_cover" in result.metrics
        assert "mean_gap_fraction" in result.metrics
        assert "shannon_diversity" in result.metrics
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = ForestGapPattern.get_metadata()
        assert metadata["id"] == "forest_gap"


# ============================================================================
# Pattern 49: Fisheries Tests
# ============================================================================

class TestFisheriesPattern:
    """Test suite for Fisheries stock assessment"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = FisheriesPattern()
        assert pattern.id == "fisheries"
        assert pattern.category == "ecology"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = FisheriesPattern()
        
        h1 = Hypothesis(title="Stock assessment", description="Biomass dynamics")
        h2 = Hypothesis(title="Fishing mortality", description="MSY")
        h3 = Hypothesis(title="Fish recruitment", description="Beverton-Holt")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = FisheriesConfig(
            recruitment_model=RecruitmentModel.RICKER,
            production_model=ProductionModel.FOX,
            K=50000.0,
            fishing_mortality=0.3
        )
        assert cfg.recruitment_model == RecruitmentModel.RICKER
        assert cfg.production_model == ProductionModel.FOX
    
    @pytest.mark.asyncio
    async def test_run_schaefer(self, mock_hypothesis):
        """Test Schaefer surplus production"""
        pattern = FisheriesPattern()
        config = {
            "production_model": "schaefer",
            "K": 10000.0,
            "B0": 8000.0,
            "fishing_mortality": 0.2,
            "years": 30
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_biomass" in result.metrics
        assert "B_msy" in result.metrics
        assert "MSY" in result.metrics
        assert "status" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_age_structured(self, mock_hypothesis):
        """Test age-structured model"""
        pattern = FisheriesPattern()
        config = {
            "production_model": "thompson_bell",
            "recruitment_model": "beverton_holt",
            "max_age": 10,
            "years": 30
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_biomass" in result.metrics
        assert "mean_recruitment" in result.metrics
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = FisheriesPattern.get_metadata()
        assert metadata["id"] == "fisheries"


# ============================================================================
# Pattern 50: Metapopulation Tests
# ============================================================================

class TestMetapopulationPattern:
    """Test suite for Metapopulation models"""
    
    def test_initialization(self):
        """Test pattern initialization"""
        pattern = MetapopulationPattern()
        assert pattern.id == "metapopulation"
        assert pattern.category == "ecology"
    
    def test_can_simulate_matching(self):
        """Test hypothesis matching"""
        pattern = MetapopulationPattern()
        
        h1 = Hypothesis(title="Metapopulation dynamics", description="Patch occupancy")
        h2 = Hypothesis(title="Fragmentation effects", description="Connectivity")
        h3 = Hypothesis(title="Habitat patches", description="Colonization extinction")
        
        assert pattern.can_simulate(h1)
        assert pattern.can_simulate(h2)
        assert pattern.can_simulate(h3)
    
    def test_config_dataclass(self):
        """Test configuration dataclass"""
        cfg = MetapopulationConfig(
            model=MetapopulationModel.INCIDENCE_FUNCTION,
            num_patches=30,
            alpha=2.0,
            rescue_effect=True
        )
        assert cfg.model == MetapopulationModel.INCIDENCE_FUNCTION
        assert cfg.rescue_effect == True
    
    @pytest.mark.asyncio
    async def test_run_levins(self, mock_hypothesis):
        """Test classic Levins model"""
        pattern = MetapopulationPattern()
        config = {
            "model": "levins",
            "c": 0.15,
            "e": 0.05,
            "years": 50
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_occupancy" in result.metrics
        assert "equilibrium_occupancy" in result.metrics
        assert "metapopulation_capacity" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_incidence_function(self, mock_hypothesis):
        """Test incidence function model"""
        pattern = MetapopulationPattern()
        config = {
            "model": "incidence_function",
            "num_patches": 20,
            "alpha": 1.5,
            "xi": 1.0,
            "years": 50
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_occupancy_rate" in result.metrics
        assert "area_occupancy_correlation" in result.metrics
    
    @pytest.mark.asyncio
    async def test_run_spatial(self, mock_hypothesis):
        """Test spatial metapopulation model"""
        pattern = MetapopulationPattern()
        config = {
            "model": "spatial",
            "num_patches": 15,
            "years": 50
        }
        
        result = await pattern.run(mock_hypothesis, config)
        assert result.status == SimulationStatus.COMPLETED
    
    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = MetapopulationPattern.get_metadata()
        assert metadata["id"] == "metapopulation"


# ============================================================================
# Integration Tests
# ============================================================================

class TestPatternIntegration:
    """Integration tests for all patterns"""
    
    @pytest.mark.asyncio
    async def test_all_patterns_complete(self, mock_hypothesis):
        """Test that all patterns can complete a basic simulation"""
        patterns = [
            (HodgkinHuxleyPattern(), {"t_max": 20.0}),
            (NeuralMassPattern(), {"t_max": 2.0}),
            (SynapticPlasticityPattern(), {"simulation_time": 500.0}),
            (ConnectomePattern(), {"num_regions": 15, "t_max": 3.0}),
            (EnzymeKineticsPattern(), {"t_max": 30.0}),
            (SignalTransductionPattern(), {"t_max": 100.0}),
            (GeneRegulatoryPattern(), {"num_genes": 8, "t_max": 15.0}),
            (ProteinFoldingPattern(), {"num_residues": 25, "t_max": 50.0}),
            (ForestGapPattern(), {"grid_size": 15, "years": 30}),
            (FisheriesPattern(), {"years": 20}),
            (MetapopulationPattern(), {"num_patches": 15, "years": 30}),
        ]
        
        for pattern, config in patterns:
            result = await pattern.run(mock_hypothesis, config)
            assert result.status == SimulationStatus.COMPLETED, f"{pattern.id} failed"
            assert len(result.metrics) > 0, f"{pattern.id} returned no metrics"
    
    def test_all_patterns_have_metadata(self):
        """Test that all patterns provide metadata"""
        patterns = [
            HodgkinHuxleyPattern,
            NeuralMassPattern,
            SynapticPlasticityPattern,
            ConnectomePattern,
            EnzymeKineticsPattern,
            SignalTransductionPattern,
            GeneRegulatoryPattern,
            ProteinFoldingPattern,
            ForestGapPattern,
            FisheriesPattern,
            MetapopulationPattern,
        ]
        
        for pattern_class in patterns:
            metadata = pattern_class.get_metadata()
            assert "id" in metadata
            assert "name" in metadata
            assert "parameters" in metadata
            assert len(metadata["parameters"]) >= 3  # At least 3 parameters


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
