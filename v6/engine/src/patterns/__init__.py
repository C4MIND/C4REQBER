"""
TURBO-CDI v6.0 - Simulation Patterns Library

Lazy-loaded ecosystem of 100+ patterns

Usage:
    from v6.engine.patterns import get_pattern_loader, PatternTier
    
    loader = get_pattern_loader()
    await loader.initialize()  # Load CORE + ESSENTIAL
    
    # Lazy load specific pattern
    await loader.load_pattern("fem")
    
    # Validation preparation
    patterns = await loader.prepare_for_validation(hypothesis)
"""

# Core patterns (always available)
from .monte_carlo import MonteCarloPattern
from .agent_based import AgentBasedPattern
from .system_dynamics import SystemDynamicsPattern
from .circuit_simulation import CircuitSimulationPattern

# New patterns (v6.1)
from .discrete_event import DiscreteEventPattern
from .optimization import LinearProgrammingPattern
from .pharmacokinetics import PKPattern
from .fem import FEMPattern

# New patterns (v6.2)
from .cfd import CFDPattern
from .neural_network import NeuralNetworkPattern
from .dsge import DSGEPattern
from .thermal import ThermalPattern

# New patterns (v6.3)
from .garch import GARCHPattern
from .game_theory import GameTheoryPattern
from .social_network import SocialNetworkPattern
from .supply_chain import SupplyChainPattern

# New patterns (v6.4) - Patterns 25-31 (Advanced Physics & Quantum)
try:
    from .maxwell_fdtd import MaxwellFDTDPattern
    from .poisson_solver import PoissonSolverPattern
    from .wave_optics import WaveOpticsPattern
    from .plasma_pic import PlasmaPICPattern
    from .dft import DFTPattern
    from .qft_lattice import LatticeQFTPattern
    from .open_quantum import OpenQuantumPattern
    V64_PATTERNS_AVAILABLE = True
except ImportError:
    V64_PATTERNS_AVAILABLE = False

# New patterns (v6.5) - Patterns 40-50 (Biological & Ecological)
from .hodgkin_huxley import HodgkinHuxleyPattern
from .neural_mass import NeuralMassPattern
from .synaptic_plasticity import SynapticPlasticityPattern
from .connectome import ConnectomePattern
from .enzyme_kinetics import EnzymeKineticsPattern
from .signal_transduction import SignalTransductionPattern
from .gene_regulatory import GeneRegulatoryPattern
from .protein_folding import ProteinFoldingPattern
from .forest_gap import ForestGapPattern
from .fisheries import FisheriesPattern
from .metapopulation import MetapopulationPattern

# Lazy loader
from .loader import (
    PatternLoader,
    PatternManifest,
    PatternTier,
    get_pattern_loader,
)

__all__ = [
    # Core patterns
    "MonteCarloPattern",
    "AgentBasedPattern", 
    "SystemDynamicsPattern",
    "CircuitSimulationPattern",
    # New patterns (v6.1)
    "DiscreteEventPattern",
    "LinearProgrammingPattern",
    "PKPattern",
    "FEMPattern",
    # New patterns (v6.2)
    "CFDPattern",
    "NeuralNetworkPattern",
    "DSGEPattern",
    "ThermalPattern",
    # New patterns (v6.3)
    "GARCHPattern",
    "GameTheoryPattern",
    "SocialNetworkPattern",
    "SupplyChainPattern",
    # New patterns (v6.4) - Patterns 25-31
    "MaxwellFDTDPattern",
    "PoissonSolverPattern",
    "WaveOpticsPattern",
    "PlasmaPICPattern",
    "DFTPattern",
    "LatticeQFTPattern",
    "OpenQuantumPattern",
    # New patterns (v6.5) - Patterns 40-50
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
    # Lazy loading
    "PatternLoader",
    "PatternManifest",
    "PatternTier",
    "get_pattern_loader",
]

__version__ = "6.0.0"


def list_available_patterns():
    """List all 100+ available patterns (metadata only)"""
    loader = get_pattern_loader()
    return loader.list_available()


def get_pattern(pattern_id: str):
    """Get pattern class (lazy load if needed)"""
    loader = get_pattern_loader()
    manifest = loader.get_manifest(pattern_id)
    if not manifest:
        raise ValueError(f"Unknown pattern: {pattern_id}")
    
    if not manifest.loaded:
        import asyncio
        asyncio.run(loader.load_pattern(pattern_id))
    
    from ..core import PatternRegistry
    pattern_class = PatternRegistry().get(pattern_id)
    if pattern_class:
        return pattern_class
    raise ValueError(f"Pattern {pattern_id} not loaded")
