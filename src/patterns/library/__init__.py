"""
c4-cdi-turbo v6.5 - Simulation Patterns Module (73 Patterns)

Exports all available simulation patterns organized by category:
- CORE: Always loaded (4 patterns)
- ESSENTIAL: Auto-loaded (2 patterns)
- EXTENDED: Lazy-loaded (35 patterns)
- ON_DEMAND: Loaded on request (32 patterns)

Total: 73 patterns implemented
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)


# Helper to safely import patterns
def _safe_import(module_name: Any, class_name: Any) -> None:
    """Safely import a pattern class using relative imports"""
    try:
        import importlib
        module = importlib.import_module(f"src.patterns.library.{module_name}")
        return getattr(module, class_name)  # type: ignore[no-any-return]
    except Exception as e:
        logger.debug(f"Could not import {class_name} from {module_name}: {e}")
        return None


# ==================== CORE PATTERNS (4) ====================
MonteCarloPattern = _safe_import("monte_carlo", "MonteCarloPattern")  # type: ignore[func-returns-value]
AgentBasedPattern = _safe_import("agent_based", "AgentBasedPattern")  # type: ignore[func-returns-value]
SystemDynamicsPattern = _safe_import("system_dynamics", "SystemDynamicsPattern")  # type: ignore[func-returns-value]
CircuitSimulationPattern = _safe_import(  # type: ignore[func-returns-value]
    "circuit_simulation", "CircuitSimulationPattern"
)

# ==================== ESSENTIAL PATTERNS (2) ====================
FiniteElementPattern = _safe_import("fem", "FEMPattern")  # type: ignore[func-returns-value]
CFDPattern = _safe_import("cfd", "CFDPattern")  # type: ignore[func-returns-value]

# ==================== EXTENDED PATTERNS (35) ====================
# Physics
DiscreteEventPattern = _safe_import("discrete_event", "DiscreteEventPattern")  # type: ignore[func-returns-value]
ThermalPattern = _safe_import("thermal", "ThermalPattern")  # type: ignore[func-returns-value]
NBodyPattern = _safe_import("n_body", "NBodyGravity")  # type: ignore[func-returns-value]
RigidBodyPattern = _safe_import("rigid_body", "RigidBody")  # type: ignore[func-returns-value]
ContinuumMechanicsPattern = _safe_import(  # type: ignore[func-returns-value]
    "continuum_mechanics", "ContinuumMechanics"
)
AcousticWavesPattern = _safe_import("acoustic_waves", "AcousticWaves")  # type: ignore[func-returns-value]
Elasticity3DPattern = _safe_import("elasticity_3d", "Elasticity3D")  # type: ignore[func-returns-value]

# EM & Quantum
MaxwellFDTDPattern = _safe_import("maxwell_fdtd", "MaxwellFDTDPattern")  # type: ignore[func-returns-value]
PoissonSolverPattern = _safe_import("poisson_solver", "PoissonSolverPattern")  # type: ignore[func-returns-value]
WaveOpticsPattern = _safe_import("wave_optics", "WaveOpticsPattern")  # type: ignore[func-returns-value]
PlasmaPICPattern = _safe_import("plasma_pic", "PlasmaPICPattern")  # type: ignore[func-returns-value]

# Statistics & Physics
IsingModelPattern = _safe_import("ising_model", "IsingModelPattern")  # type: ignore[func-returns-value]
PhaseFieldPattern = _safe_import("phase_field", "PhaseFieldPattern")  # type: ignore[func-returns-value]
PercolationPattern = _safe_import("percolation", "PercolationPattern")  # type: ignore[func-returns-value]

# Biology - Population
LotkaVolterraPattern = _safe_import("lotka_volterra", "LotkaVolterraPattern")  # type: ignore[func-returns-value]
EpidemicSEIRPattern = _safe_import("epidemic_seir", "EpidemicSEIRPattern")  # type: ignore[func-returns-value]
AgeStructuredPattern = _safe_import("age_structured", "AgeStructuredPattern")  # type: ignore[func-returns-value]
SpatialEcologyPattern = _safe_import(  # type: ignore[func-returns-value]
    "spatial_ecology", "SpatialEcologyPattern"
)
EvolutionaryPattern = _safe_import("evolutionary", "EvolutionaryPattern")  # type: ignore[func-returns-value]

# Biology - Neuroscience
HodgkinHuxleyPattern = _safe_import("hodgkin_huxley", "HodgkinHuxleyPattern")  # type: ignore[func-returns-value]
NeuralMassPattern = _safe_import("neural_mass", "NeuralMassPattern")  # type: ignore[func-returns-value]
SynapticPlasticityPattern = _safe_import(  # type: ignore[func-returns-value]
    "synaptic_plasticity", "SynapticPlasticityPattern"
)
ConnectomePattern = _safe_import("connectome", "ConnectomePattern")  # type: ignore[func-returns-value]

# Biology - Biochemistry & Ecology
EnzymeKineticsPattern = _safe_import(  # type: ignore[func-returns-value]
    "enzyme_kinetics", "EnzymeKineticsPattern"
)
SignalTransductionPattern = _safe_import(  # type: ignore[func-returns-value]
    "signal_transduction", "SignalTransductionPattern"
)
GeneRegulatoryPattern = _safe_import(  # type: ignore[func-returns-value]
    "gene_regulatory", "GeneRegulatoryPattern"
)
ProteinFoldingPattern = _safe_import(  # type: ignore[func-returns-value]
    "protein_folding", "ProteinFoldingPattern"
)
ForestGapPattern = _safe_import("forest_gap", "ForestGapPattern")  # type: ignore[func-returns-value]
FisheriesPattern = _safe_import("fisheries", "FisheriesPattern")  # type: ignore[func-returns-value]
MetapopulationPattern = _safe_import("metapopulation", "MetapopulationPattern")  # type: ignore[func-returns-value]

# Optimization & Operations
OptimizationPattern = _safe_import("optimization", "LinearProgrammingPattern")  # type: ignore[func-returns-value]
SupplyChainPattern = _safe_import("supply_chain", "SupplyChainPattern")  # type: ignore[func-returns-value]
PharmacokineticsPattern = _safe_import("pharmacokinetics", "PKPattern")  # type: ignore[func-returns-value]

# Economics
GameTheoryPattern = _safe_import("game_theory", "GameTheoryPattern")  # type: ignore[func-returns-value]
DSGEPattern = _safe_import("dsge", "DSGEPattern")  # type: ignore[func-returns-value]
GARCHPattern = _safe_import("garch", "GARCHPattern")  # type: ignore[func-returns-value]
SocialNetworkPattern = _safe_import("social_network", "SocialNetworkPattern")  # type: ignore[func-returns-value]
NeuralNetworkPattern = _safe_import("neural_network", "NeuralNetworkPattern")  # type: ignore[func-returns-value]

# NEW: Physics & Engineering (Phase 2)
QuantumHarmonicOscillatorPattern = _safe_import("quantum_harmonic_oscillator", "QuantumHarmonicOscillatorPattern")  # type: ignore[func-returns-value]
DoublePendulumPattern = _safe_import("double_pendulum", "DoublePendulumPattern")  # type: ignore[func-returns-value]
WaveEquationPattern = _safe_import("wave_equation", "WaveEquationPattern")  # type: ignore[func-returns-value]
SpringMassPattern = _safe_import("spring_mass", "SpringMassPattern")  # type: ignore[func-returns-value]
ProjectileMotionPattern = _safe_import("projectile_motion", "ProjectileMotionPattern")  # type: ignore[func-returns-value]

# NEW: Biology & Chemistry (Phase 2)
ReactionDiffusionPattern = _safe_import("reaction_diffusion", "ReactionDiffusionPattern")  # type: ignore[func-returns-value]
PopulationGeneticsPattern = _safe_import("population_genetics", "PopulationGeneticsPattern")  # type: ignore[func-returns-value]
SIREpidemicPattern = _safe_import("epidemic_sir", "SIREpidemicPattern")  # type: ignore[func-returns-value]

# NEW: Math & Statistics (Phase 2)
MandelbrotPattern = _safe_import("fractal_mandelbrot", "MandelbrotPattern")  # type: ignore[func-returns-value]
JuliaPattern = _safe_import("fractal_julia", "JuliaPattern")  # type: ignore[func-returns-value]
CellularAutomataPattern = _safe_import("cellular_automata", "CellularAutomataPattern")  # type: ignore[func-returns-value]
MarkovChainPattern = _safe_import("markov_chain", "MarkovChainPattern")  # type: ignore[func-returns-value]
MonteCarloPiPattern = _safe_import("monte_carlo_pi", "MonteCarloPiPattern")  # type: ignore[func-returns-value]
BootstrapPattern = _safe_import("bootstrap", "BootstrapPattern")  # type: ignore[func-returns-value]

# ==================== ON_DEMAND PATTERNS (32) ====================
# Phase 4 Core
ClimateGCMPattern = _safe_import("climate_gcm", "ClimateGCMPattern")  # type: ignore[func-returns-value]
QuantumPattern = _safe_import("quantum", "QuantumPattern")  # type: ignore[func-returns-value]
MolecularDynamicsPattern = _safe_import(  # type: ignore[func-returns-value]
    "molecular_dynamics", "MolecularDynamicsPattern"
)

# Economics Extended
InputOutputPattern = _safe_import("input_output", "InputOutputPattern")  # type: ignore[func-returns-value]
OverlappingGenerationsPattern = _safe_import(  # type: ignore[func-returns-value]
    "overlapping_generations", "OverlappingGenerationsPattern"
)
SearchMatchingPattern = _safe_import(  # type: ignore[func-returns-value]
    "search_matching", "SearchMatchingPattern"
)
HeterogeneousAgentsPattern = _safe_import(  # type: ignore[func-returns-value]
    "heterogeneous_agents", "HeterogeneousAgentsPattern"
)
OptionPricingPattern = _safe_import("option_pricing", "OptionPricingPattern")  # type: ignore[func-returns-value]
CreditRiskPattern = _safe_import("credit_risk", "CreditRiskPattern")  # type: ignore[func-returns-value]
MarketMicrostructurePattern = _safe_import(  # type: ignore[func-returns-value]
    "market_microstructure", "MarketMicrostructurePattern"
)
PortfolioOptimizationPattern = _safe_import(  # type: ignore[func-returns-value]
    "portfolio_optimization", "PortfolioOptimizationPattern"
)
GravityTradePattern = _safe_import("gravity_trade", "GravityTradePattern")  # type: ignore[func-returns-value]
EconomicGrowthPattern = _safe_import(  # type: ignore[func-returns-value]
    "economic_growth", "EconomicGrowthPattern"
)
ProspectTheoryPattern = _safe_import(  # type: ignore[func-returns-value]
    "prospect_theory", "ProspectTheoryPattern"
)
HerdingPattern = _safe_import("herding", "HerdingPattern")  # type: ignore[func-returns-value]

# Engineering & Control
PIDTuningPattern = _safe_import("pid_tuning", "PIDTuningPattern")  # type: ignore[func-returns-value]
StateSpacePattern = _safe_import("state_space", "StateSpacePattern")  # type: ignore[func-returns-value]
ModelPredictivePattern = _safe_import(  # type: ignore[func-returns-value]
    "model_predictive", "ModelPredictivePattern"
)
KalmanFilterPattern = _safe_import("kalman_filter", "KalmanFilterPattern")  # type: ignore[func-returns-value]
InverseKinematicsPattern = _safe_import(  # type: ignore[func-returns-value]
    "inverse_kinematics", "InverseKinematicsPattern"
)
PathPlanningPattern = _safe_import("path_planning", "PathPlanningPattern")  # type: ignore[func-returns-value]
SLAMPattern = _safe_import("slam", "SLAMPattern")  # type: ignore[func-returns-value]

# Signal Processing & Materials
AdaptiveFilterPattern = _safe_import(  # type: ignore[func-returns-value]
    "adaptive_filter", "AdaptiveFilterPattern"
)
SpectralEstimationPattern = _safe_import(  # type: ignore[func-returns-value]
    "spectral_estimation", "SpectralEstimationPattern"
)
WaveletAnalysisPattern = _safe_import(  # type: ignore[func-returns-value]
    "wavelet_analysis", "WaveletAnalysisPattern"
)
CrystalGrowthPattern = _safe_import("crystal_growth", "CrystalGrowthPattern")  # type: ignore[func-returns-value]
CompositeMechanicsPattern = _safe_import(  # type: ignore[func-returns-value]
    "composite_mechanics", "CompositeMechanicsPattern"
)
TrafficFlowPattern = _safe_import("traffic_flow", "TrafficFlowPattern")  # type: ignore[func-returns-value]
QueueingNetworksPattern = _safe_import(  # type: ignore[func-returns-value]
    "queueing_networks", "QueueingNetworksPattern"
)

# Earth Systems
OceanCirculationPattern = _safe_import(  # type: ignore[func-returns-value]
    "ocean_circulation", "OceanCirculationPattern"
)
SeaIcePattern = _safe_import("sea_ice", "SeaIcePattern")  # type: ignore[func-returns-value]
BiogeochemistryPattern = _safe_import(  # type: ignore[func-returns-value]
    "biogeochemistry", "BiogeochemistryPattern"
)
CloudMicrophysicsPattern = _safe_import(  # type: ignore[func-returns-value]
    "cloud_microphysics", "CloudMicrophysicsPattern"
)
SurfaceWaterPattern = _safe_import("surface_water", "SurfaceWaterPattern")  # type: ignore[func-returns-value]
GroundwaterPattern = _safe_import("groundwater", "GroundwaterPattern")  # type: ignore[func-returns-value]
LandSurfacePattern = _safe_import("land_surface", "LandSurfacePattern")  # type: ignore[func-returns-value]
SeismicWavesPattern = _safe_import("seismic_waves", "SeismicWavesPattern")  # type: ignore[func-returns-value]
MantleConvectionPattern = _safe_import(  # type: ignore[func-returns-value]
    "mantle_convection", "MantleConvectionPattern"
)
GeomagneticPattern = _safe_import("geomagnetic", "GeomagneticPattern")  # type: ignore[func-returns-value]
AirQualityPattern = _safe_import("air_quality", "AirQualityPattern")  # type: ignore[func-returns-value]
WildfirePattern = _safe_import("wildfire", "WildfirePattern")  # type: ignore[func-returns-value]

# Social Systems
OpinionDynamicsPattern = _safe_import(  # type: ignore[func-returns-value]
    "opinion_dynamics", "OpinionDynamicsPattern"
)
CulturalDiffusionPattern = _safe_import(  # type: ignore[func-returns-value]
    "cultural_diffusion", "CulturalDiffusionPattern"
)
LanguageEvolutionPattern = _safe_import(  # type: ignore[func-returns-value]
    "language_evolution", "LanguageEvolutionPattern"
)
UrbanGrowthPattern = _safe_import("urban_growth", "UrbanGrowthPattern")  # type: ignore[func-returns-value]
LandUsePattern = _safe_import("land_use", "LandUsePattern")  # type: ignore[func-returns-value]
MigrationPattern = _safe_import("migration", "MigrationPattern")  # type: ignore[func-returns-value]
FlockingPattern = _safe_import("flocking", "FlockingPattern")  # type: ignore[func-returns-value]
PedestrianPattern = _safe_import("pedestrian", "PedestrianPattern")  # type: ignore[func-returns-value]
ConflictPattern = _safe_import("conflict", "ConflictPattern")  # type: ignore[func-returns-value]
RumorSpreadingPattern = _safe_import(  # type: ignore[func-returns-value]
    "rumor_spreading", "RumorSpreadingPattern"
)
InnovationDiffusionPattern = _safe_import(  # type: ignore[func-returns-value]
    "innovation_diffusion", "InnovationDiffusionPattern"
)
CollaborativeFilteringPattern = _safe_import(  # type: ignore[func-returns-value]
    "collaborative_filtering", "CollaborativeFilteringPattern"
)

# Quantum Chemistry/Physics
DFTPattern = _safe_import("dft", "DFTPattern")  # type: ignore[func-returns-value]
OpenQuantumPattern = _safe_import("open_quantum", "OpenQuantumPattern")  # type: ignore[func-returns-value]
QFTLatticePattern = _safe_import("qft_lattice", "LatticeQFTPattern")  # type: ignore[func-returns-value]

# GPU acceleration
try:
    from .gpu_compat import (
        GPUMixin,
        detect_gpu,
        detect_mpi,
        get_hardware_summary,
        make_gpu_compatible,
    )
except Exception as e:
    logger.debug(f"GPU compat not available: {e}")
    make_gpu_compatible = None
    GPUMixin = None
    detect_gpu = None
    detect_mpi = None
    get_hardware_summary = None

# ==================== METADATA ====================


def _collect_available_patterns() -> Any:
    """Collect all available pattern classes"""
    patterns = {
        # CORE
        "monte_carlo": MonteCarloPattern,
        "agent_based": AgentBasedPattern,
        "system_dynamics": SystemDynamicsPattern,
        "circuit": CircuitSimulationPattern,
        # ESSENTIAL
        "fem": FiniteElementPattern,
        "cfd": CFDPattern,
        # EXTENDED - Physics
        "discrete_event": DiscreteEventPattern,
        "thermal": ThermalPattern,
        "n_body": NBodyPattern,
        "rigid_body": RigidBodyPattern,
        "continuum_mechanics": ContinuumMechanicsPattern,
        "acoustic_waves": AcousticWavesPattern,
        "elasticity_3d": Elasticity3DPattern,
        "maxwell_fdtd": MaxwellFDTDPattern,
        "poisson_solver": PoissonSolverPattern,
        "wave_optics": WaveOpticsPattern,
        "plasma_pic": PlasmaPICPattern,
        # EXTENDED - Statistics
        "ising_model": IsingModelPattern,
        "phase_field": PhaseFieldPattern,
        "percolation": PercolationPattern,
        # EXTENDED - Biology
        "lotka_volterra": LotkaVolterraPattern,
        "epidemic_seir": EpidemicSEIRPattern,
        "age_structured": AgeStructuredPattern,
        "spatial_ecology": SpatialEcologyPattern,
        "evolutionary": EvolutionaryPattern,
        "hodgkin_huxley": HodgkinHuxleyPattern,
        "neural_mass": NeuralMassPattern,
        "synaptic_plasticity": SynapticPlasticityPattern,
        "connectome": ConnectomePattern,
        "enzyme_kinetics": EnzymeKineticsPattern,
        "signal_transduction": SignalTransductionPattern,
        "gene_regulatory": GeneRegulatoryPattern,
        "protein_folding": ProteinFoldingPattern,
        "forest_gap": ForestGapPattern,
        "fisheries": FisheriesPattern,
        "metapopulation": MetapopulationPattern,
        # EXTENDED - Operations
        "optimization": OptimizationPattern,
        "supply_chain": SupplyChainPattern,
        "pharmacokinetics": PharmacokineticsPattern,
        # EXTENDED - Economics
        "game_theory": GameTheoryPattern,
        "dsge": DSGEPattern,
        "garch": GARCHPattern,
        "social_network": SocialNetworkPattern,
        "neural_network": NeuralNetworkPattern,
        # NEW: Phase 2 - Physics & Engineering
        "quantum_harmonic_oscillator": QuantumHarmonicOscillatorPattern,
        "double_pendulum": DoublePendulumPattern,
        "wave_equation": WaveEquationPattern,
        "spring_mass": SpringMassPattern,
        "projectile_motion": ProjectileMotionPattern,
        # NEW: Phase 2 - Biology & Chemistry
        "reaction_diffusion": ReactionDiffusionPattern,
        "population_genetics": PopulationGeneticsPattern,
        "epidemic_sir": SIREpidemicPattern,
        # NEW: Phase 2 - Math & Statistics
        "fractal_mandelbrot": MandelbrotPattern,
        "fractal_julia": JuliaPattern,
        "cellular_automata": CellularAutomataPattern,
        "markov_chain": MarkovChainPattern,
        "monte_carlo_pi": MonteCarloPiPattern,
        "bootstrap": BootstrapPattern,
        # ON_DEMAND - Phase 4 Core
        "climate_gcm": ClimateGCMPattern,
        "quantum": QuantumPattern,
        "molecular_dynamics": MolecularDynamicsPattern,
        # ON_DEMAND - Economics Extended
        "input_output": InputOutputPattern,
        "overlapping_generations": OverlappingGenerationsPattern,
        "search_matching": SearchMatchingPattern,
        "heterogeneous_agents": HeterogeneousAgentsPattern,
        "option_pricing": OptionPricingPattern,
        "credit_risk": CreditRiskPattern,
        "market_microstructure": MarketMicrostructurePattern,
        "portfolio_optimization": PortfolioOptimizationPattern,
        "gravity_trade": GravityTradePattern,
        "economic_growth": EconomicGrowthPattern,
        "prospect_theory": ProspectTheoryPattern,
        "herding": HerdingPattern,
        # ON_DEMAND - Engineering
        "pid_tuning": PIDTuningPattern,
        "state_space": StateSpacePattern,
        "model_predictive": ModelPredictivePattern,
        "kalman_filter": KalmanFilterPattern,
        "inverse_kinematics": InverseKinematicsPattern,
        "path_planning": PathPlanningPattern,
        "slam": SLAMPattern,
        "adaptive_filter": AdaptiveFilterPattern,
        "spectral_estimation": SpectralEstimationPattern,
        "wavelet_analysis": WaveletAnalysisPattern,
        "crystal_growth": CrystalGrowthPattern,
        "composite_mechanics": CompositeMechanicsPattern,
        "traffic_flow": TrafficFlowPattern,
        "queueing_networks": QueueingNetworksPattern,
        # ON_DEMAND - Earth
        "ocean_circulation": OceanCirculationPattern,
        "sea_ice": SeaIcePattern,
        "biogeochemistry": BiogeochemistryPattern,
        "cloud_microphysics": CloudMicrophysicsPattern,
        "surface_water": SurfaceWaterPattern,
        "groundwater": GroundwaterPattern,
        "land_surface": LandSurfacePattern,
        "seismic_waves": SeismicWavesPattern,
        "mantle_convection": MantleConvectionPattern,
        "geomagnetic": GeomagneticPattern,
        "air_quality": AirQualityPattern,
        "wildfire": WildfirePattern,
        # ON_DEMAND - Social
        "opinion_dynamics": OpinionDynamicsPattern,
        "cultural_diffusion": CulturalDiffusionPattern,
        "language_evolution": LanguageEvolutionPattern,
        "urban_growth": UrbanGrowthPattern,
        "land_use": LandUsePattern,
        "migration": MigrationPattern,
        "flocking": FlockingPattern,
        "pedestrian": PedestrianPattern,
        "conflict": ConflictPattern,
        "rumor_spreading": RumorSpreadingPattern,
        "innovation_diffusion": InnovationDiffusionPattern,
        "collaborative_filtering": CollaborativeFilteringPattern,
        # ON_DEMAND - Quantum
        "dft": DFTPattern,
        "open_quantum": OpenQuantumPattern,
        "qft_lattice": QFTLatticePattern,
    }
    return patterns


PATTERN_MAP = _collect_available_patterns()
AVAILABLE_PATTERNS = [k for k, v in PATTERN_MAP.items() if v is not None]
TOTAL_PATTERNS = len(AVAILABLE_PATTERNS)

# Categories
PATTERN_CATEGORIES = {
    "CORE": {
        "patterns": ["monte_carlo", "agent_based", "system_dynamics", "circuit"],
        "description": "Always loaded, fundamental building blocks",
        "memory_mb": 50,
    },
    "ESSENTIAL": {
        "patterns": ["fem", "cfd"],
        "description": "Auto-loaded for common use cases",
        "memory_mb": 100,
    },
    "EXTENDED": {
        "patterns": [
            p
            for p in [
                "discrete_event",
                "thermal",
                "n_body",
                "rigid_body",
                "continuum_mechanics",
                "acoustic_waves",
                "elasticity_3d",
                "maxwell_fdtd",
                "poisson_solver",
                "wave_optics",
                "plasma_pic",
                "ising_model",
                "phase_field",
                "percolation",
                "lotka_volterra",
                "epidemic_seir",
                "age_structured",
                "spatial_ecology",
                "evolutionary",
                "hodgkin_huxley",
                "neural_mass",
                "synaptic_plasticity",
                "connectome",
                "enzyme_kinetics",
                "signal_transduction",
                "gene_regulatory",
                "protein_folding",
                "forest_gap",
                "fisheries",
                "metapopulation",
                "optimization",
                "supply_chain",
                "pharmacokinetics",
                "game_theory",
                "dsge",
                "garch",
                "social_network",
                "neural_network",
            ]
            if p in AVAILABLE_PATTERNS
        ],
        "description": "Lazy-loaded on first use",
        "memory_mb": 500,
    },
    "ON_DEMAND": {
        "patterns": [
            p
            for p in [
                "climate_gcm",
                "quantum",
                "molecular_dynamics",
                "input_output",
                "overlapping_generations",
                "search_matching",
                "heterogeneous_agents",
                "option_pricing",
                "credit_risk",
                "market_microstructure",
                "portfolio_optimization",
                "gravity_trade",
                "economic_growth",
                "prospect_theory",
                "herding",
                "pid_tuning",
                "state_space",
                "model_predictive",
                "kalman_filter",
                "inverse_kinematics",
                "path_planning",
                "slam",
                "adaptive_filter",
                "spectral_estimation",
                "wavelet_analysis",
                "crystal_growth",
                "composite_mechanics",
                "traffic_flow",
                "queueing_networks",
                "ocean_circulation",
                "sea_ice",
                "biogeochemistry",
                "cloud_microphysics",
                "surface_water",
                "groundwater",
                "land_surface",
                "seismic_waves",
                "mantle_convection",
                "geomagnetic",
                "air_quality",
                "wildfire",
                "opinion_dynamics",
                "cultural_diffusion",
                "language_evolution",
                "urban_growth",
                "land_use",
                "migration",
                "flocking",
                "pedestrian",
                "conflict",
                "rumor_spreading",
                "innovation_diffusion",
                "collaborative_filtering",
                "dft",
                "open_quantum",
                "qft_lattice",
            ]
            if p in AVAILABLE_PATTERNS
        ],
        "description": "Loaded only when explicitly requested",
        "memory_mb": 200,
    },
}

__version__ = "6.5.0"

__all__ = [
    # Pattern classes
    "MonteCarloPattern",
    "AgentBasedPattern",
    "SystemDynamicsPattern",
    "CircuitSimulationPattern",
    "FiniteElementPattern",
    "CFDPattern",
    "DiscreteEventPattern",
    "ThermalPattern",
    "NBodyPattern",
    "RigidBodyPattern",
    "ContinuumMechanicsPattern",
    "AcousticWavesPattern",
    "Elasticity3DPattern",
    "MaxwellFDTDPattern",
    "PoissonSolverPattern",
    "WaveOpticsPattern",
    "PlasmaPICPattern",
    "IsingModelPattern",
    "PhaseFieldPattern",
    "PercolationPattern",
    "LotkaVolterraPattern",
    "EpidemicSEIRPattern",
    "AgeStructuredPattern",
    "SpatialEcologyPattern",
    "EvolutionaryPattern",
    "HodgkinHuxleyPattern",
    "NeuralMassPattern",
    "SynapticPlasticityPattern",
    "ConnectomePattern",
    "EnzymeKineticsPattern",
    "SignalTransductionPattern",
    "GeneRegulatoryPattern",
    "ProteinFoldingPattern",
    "ForestGapPattern",
    "FisheriesPattern",
    "MetapopulationPattern",
    "OptimizationPattern",
    "SupplyChainPattern",
    "PharmacokineticsPattern",
    "GameTheoryPattern",
    "DSGEPattern",
    "GARCHPattern",
    "SocialNetworkPattern",
    "NeuralNetworkPattern",
    # NEW: Phase 2 - Physics & Engineering
    "QuantumHarmonicOscillatorPattern",
    "DoublePendulumPattern",
    "WaveEquationPattern",
    "SpringMassPattern",
    "ProjectileMotionPattern",
    # NEW: Phase 2 - Biology & Chemistry
    "ReactionDiffusionPattern",
    "PopulationGeneticsPattern",
    "SIREpidemicPattern",
    # NEW: Phase 2 - Math & Statistics
    "MandelbrotPattern",
    "JuliaPattern",
    "CellularAutomataPattern",
    "MarkovChainPattern",
    "MonteCarloPiPattern",
    "BootstrapPattern",
    "ClimateGCMPattern",
    "QuantumPattern",
    "MolecularDynamicsPattern",
    "InputOutputPattern",
    "OverlappingGenerationsPattern",
    "SearchMatchingPattern",
    "HeterogeneousAgentsPattern",
    "OptionPricingPattern",
    "CreditRiskPattern",
    "MarketMicrostructurePattern",
    "PortfolioOptimizationPattern",
    "GravityTradePattern",
    "EconomicGrowthPattern",
    "ProspectTheoryPattern",
    "HerdingPattern",
    "PIDTuningPattern",
    "StateSpacePattern",
    "ModelPredictivePattern",
    "KalmanFilterPattern",
    "InverseKinematicsPattern",
    "PathPlanningPattern",
    "SLAMPattern",
    "AdaptiveFilterPattern",
    "SpectralEstimationPattern",
    "WaveletAnalysisPattern",
    "CrystalGrowthPattern",
    "CompositeMechanicsPattern",
    "TrafficFlowPattern",
    "QueueingNetworksPattern",
    "OceanCirculationPattern",
    "SeaIcePattern",
    "BiogeochemistryPattern",
    "CloudMicrophysicsPattern",
    "SurfaceWaterPattern",
    "GroundwaterPattern",
    "LandSurfacePattern",
    "SeismicWavesPattern",
    "MantleConvectionPattern",
    "GeomagneticPattern",
    "AirQualityPattern",
    "WildfirePattern",
    "OpinionDynamicsPattern",
    "CulturalDiffusionPattern",
    "LanguageEvolutionPattern",
    "UrbanGrowthPattern",
    "LandUsePattern",
    "MigrationPattern",
    "FlockingPattern",
    "PedestrianPattern",
    "ConflictPattern",
    "RumorSpreadingPattern",
    "InnovationDiffusionPattern",
    "CollaborativeFilteringPattern",
    "DFTPattern",
    "OpenQuantumPattern",
    "QFTLatticePattern",
    # GPU utilities
    "make_gpu_compatible",
    "GPUMixin",
    "detect_gpu",
    "detect_mpi",
    "get_hardware_summary",
    # Metadata
    "PATTERN_MAP",
    "PATTERN_CATEGORIES",
    "AVAILABLE_PATTERNS",
    "TOTAL_PATTERNS",
    # Functions
    "get_pattern_by_id",
    "list_all_patterns",
]


def get_pattern_by_id(pattern_id: str) -> Any:
    """Get pattern class by ID"""
    return PATTERN_MAP.get(pattern_id)


def list_all_patterns() -> Any:
    """List all available patterns with their categories"""
    result = {}
    for category, info in PATTERN_CATEGORIES.items():
        result[category] = {
            "patterns": [p for p in info["patterns"] if p in AVAILABLE_PATTERNS],  # type: ignore[attr-defined]
            "memory_mb": info["memory_mb"],
            "description": info["description"],
        }
    return result
