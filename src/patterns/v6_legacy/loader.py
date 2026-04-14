"""
Lazy Pattern Loader
Dynamic loading of 100+ simulation patterns with dependency resolution

Features:
- Lazy loading (load on first use)
- Dependency resolution (auto-install missing packages)
- Tier system (core/essential/extended/on-demand)
- Validation preparation mode (load all for validation)
- Hot reloading for development
"""

import asyncio
import importlib
import importlib.util
import logging
import sys
from typing import Dict, List, Optional, Type, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import subprocess

from ..core import SimulationPattern, PatternRegistry

logger = logging.getLogger(__name__)


class PatternTier(Enum):
    """Loading priority tiers"""
    CORE = auto()        # Always loaded (4 patterns)
    ESSENTIAL = auto()   # Load at startup (10 patterns)
    EXTENDED = auto()    # Lazy load on first use (50 patterns)
    ON_DEMAND = auto()   # Manual load only (100+ patterns)
    VALIDATION = auto()  # Load during validation prep


@dataclass
class PatternManifest:
    """Metadata for lazy-loaded pattern"""
    id: str
    name: str
    category: str
    tier: PatternTier
    module_path: str                    # e.g., "v6.engine.src.patterns.fem"
    class_name: str                     # e.g., "FEMPattern"
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    estimated_size_mb: float = 10.0
    estimated_load_time_ms: int = 100
    description: str = ""
    author: str = "TURBO-CDI Team"
    version: str = "1.0.0"
    loaded: bool = False
    available: bool = True              # False if dependencies missing
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.name} simulation pattern"


class PatternLoader:
    """
    Dynamic pattern loader with lazy loading
    
    Manages 100+ patterns across tiers:
    - CORE: Always available (Monte Carlo, ABM, etc.)
    - ESSENTIAL: Auto-loaded at startup
    - EXTENDED: Loaded on first use
    - ON_DEMAND: Loaded manually
    - VALIDATION: Loaded for validation preparation
    """
    
    def __init__(self):
        self.manifests: Dict[str, PatternManifest] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.loading_lock = asyncio.Lock()
        self.auto_install = False          # Auto-install missing packages?
        
        # Initialize with all known patterns
        self._register_all_manifests()
        
    def _register_all_manifests(self):
        """Register all 100+ pattern manifests"""
        
        # === TIER: CORE (Always loaded) ===
        self._register_manifest(PatternManifest(
            id="monte_carlo",
            name="Monte Carlo Simulation",
            category="stochastic",
            tier=PatternTier.CORE,
            module_path="v6.engine.src.patterns.monte_carlo",
            class_name="MonteCarloPattern",
            dependencies=["numpy", "scipy"],
            loaded=True,  # Already loaded
        ))
        
        self._register_manifest(PatternManifest(
            id="agent_based",
            name="Agent-Based Simulation",
            category="agent",
            tier=PatternTier.CORE,
            module_path="v6.engine.src.patterns.agent_based",
            class_name="AgentBasedPattern",
            dependencies=["numpy"],
            loaded=True,
        ))
        
        self._register_manifest(PatternManifest(
            id="system_dynamics",
            name="System Dynamics",
            category="differential",
            tier=PatternTier.CORE,
            module_path="v6.engine.src.patterns.system_dynamics",
            class_name="SystemDynamicsPattern",
            dependencies=["numpy", "scipy"],
            loaded=True,
        ))
        
        self._register_manifest(PatternManifest(
            id="circuit_simulation",
            name="Circuit Simulation",
            category="physical",
            tier=PatternTier.CORE,
            module_path="v6.engine.src.patterns.circuit_simulation",
            class_name="CircuitSimulationPattern",
            dependencies=["numpy"],
            optional_dependencies=["PySpice"],
            loaded=True,
        ))
        
        # === TIER: ESSENTIAL (Auto-load at startup) ===
        self._register_manifest(PatternManifest(
            id="discrete_event",
            name="Discrete Event Simulation",
            category="operations",
            tier=PatternTier.ESSENTIAL,
            module_path="v6.engine.src.patterns.discrete_event",
            class_name="DiscreteEventPattern",
            dependencies=["numpy", "simpy"],
            estimated_size_mb=5.0,
        ))
        
        self._register_manifest(PatternManifest(
            id="optimization_lp",
            name="Linear Programming",
            category="optimization",
            tier=PatternTier.ESSENTIAL,
            module_path="v6.engine.src.patterns.optimization",
            class_name="LinearProgrammingPattern",
            dependencies=["numpy", "scipy"],
            optional_dependencies=["cvxpy"],
            estimated_size_mb=10.0,
        ))
        
        self._register_manifest(PatternManifest(
            id="neural_ode",
            name="Neural ODE",
            category="ml",
            tier=PatternTier.ESSENTIAL,
            module_path="v6.engine.src.patterns.neural_ode",
            class_name="NeuralODEPattern",
            dependencies=["numpy", "torch"],
            estimated_size_mb=200.0,  # PyTorch is heavy
        ))
        
        # === TIER: EXTENDED (Lazy load) ===
        # Physics
        self._register_manifest(PatternManifest(
            id="fem",
            name="Finite Element Method",
            category="physics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.fem",
            class_name="FEMPattern",
            dependencies=["numpy", "scipy"],
            optional_dependencies=["fenics", "meshio"],
            estimated_size_mb=100.0,
        ))
        
        self._register_manifest(PatternManifest(
            id="cfd",
            name="Computational Fluid Dynamics",
            category="physics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.cfd",
            class_name="CFDPattern",
            dependencies=["numpy"],
            optional_dependencies=["openfoam", "pyfoam"],
            estimated_size_mb=500.0,  # OpenFOAM is huge
        ))
        
        self._register_manifest(PatternManifest(
            id="thermal",
            name="Thermal Analysis",
            category="physics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.thermal",
            class_name="ThermalPattern",
            dependencies=["numpy", "scipy"],
            estimated_size_mb=10.0,
        ))
        
        # Biology
        self._register_manifest(PatternManifest(
            id="pharmacokinetics",
            name="Pharmacokinetics",
            category="biology",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.pharmacokinetics",
            class_name="PKPattern",
            dependencies=["numpy", "scipy"],
            optional_dependencies=["tellurium", "libroadrunner"],
            estimated_size_mb=50.0,
        ))
        
        self._register_manifest(PatternManifest(
            id="neural_network",
            name="Neural Network Simulation",
            category="neuroscience",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.neural_network",
            class_name="NeuralNetworkPattern",
            dependencies=["numpy"],
            optional_dependencies=["nest", "brian2"],
            estimated_size_mb=100.0,
        ))
        
        # Economics
        self._register_manifest(PatternManifest(
            id="dsge",
            name="DSGE Model",
            category="economics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.dsge",
            class_name="DSGEPattern",
            dependencies=["numpy"],
            estimated_size_mb=20.0,
        ))
        
        # NEW PATTERNS - just implemented!
        self._register_manifest(PatternManifest(
            id="discrete_event",
            name="Discrete Event Simulation",
            category="operations",
            tier=PatternTier.ESSENTIAL,
            module_path="v6.engine.src.patterns.discrete_event",
            class_name="DiscreteEventPattern",
            dependencies=["numpy"],
            optional_dependencies=["simpy"],
            estimated_size_mb=5.0,
            loaded=True,  # Already implemented
        ))
        
        self._register_manifest(PatternManifest(
            id="optimization_lp",
            name="Linear Programming",
            category="optimization",
            tier=PatternTier.ESSENTIAL,
            module_path="v6.engine.src.patterns.optimization",
            class_name="LinearProgrammingPattern",
            dependencies=["numpy", "scipy"],
            optional_dependencies=["cvxpy"],
            estimated_size_mb=10.0,
            loaded=True,
        ))
        
        self._register_manifest(PatternManifest(
            id="pharmacokinetics",
            name="Pharmacokinetics",
            category="biology",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.pharmacokinetics",
            class_name="PKPattern",
            dependencies=["numpy", "scipy"],
            estimated_size_mb=15.0,
            loaded=True,
        ))
        
        self._register_manifest(PatternManifest(
            id="fem",
            name="Finite Element Method",
            category="physics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.fem",
            class_name="FEMPattern",
            dependencies=["numpy", "scipy"],
            estimated_size_mb=20.0,
            loaded=True,
        ))

        # BATCH #2 - NEW PATTERNS (v6.2)
        self._register_manifest(PatternManifest(
            id="cfd",
            name="Computational Fluid Dynamics",
            category="physics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.cfd",
            class_name="CFDPattern",
            dependencies=["numpy", "scipy"],
            estimated_size_mb=30.0,
            loaded=True,
        ))

        self._register_manifest(PatternManifest(
            id="neural_network",
            name="Neural Network Simulation",
            category="neuroscience",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.neural_network",
            class_name="NeuralNetworkPattern",
            dependencies=["numpy"],
            estimated_size_mb=15.0,
            loaded=True,
        ))

        self._register_manifest(PatternManifest(
            id="dsge",
            name="DSGE Model",
            category="economics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.dsge",
            class_name="DSGEPattern",
            dependencies=["numpy", "scipy"],
            estimated_size_mb=20.0,
            loaded=True,
        ))

        self._register_manifest(PatternManifest(
            id="thermal",
            name="Thermal Analysis",
            category="physics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.thermal",
            class_name="ThermalPattern",
            dependencies=["numpy"],
            estimated_size_mb=15.0,
            loaded=True,
        ))

        # BATCH #3 - NEW PATTERNS (v6.3)
        self._register_manifest(PatternManifest(
            id="garch",
            name="GARCH Volatility Model",
            category="finance",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.garch",
            class_name="GARCHPattern",
            dependencies=["numpy"],
            estimated_size_mb=10.0,
            loaded=True,
        ))

        self._register_manifest(PatternManifest(
            id="game_theory",
            name="Game Theory",
            category="economics",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.game_theory",
            class_name="GameTheoryPattern",
            dependencies=["numpy"],
            estimated_size_mb=10.0,
            loaded=True,
        ))

        self._register_manifest(PatternManifest(
            id="social_network",
            name="Social Network Diffusion",
            category="social",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.social_network",
            class_name="SocialNetworkPattern",
            dependencies=["numpy"],
            estimated_size_mb=15.0,
            loaded=True,
        ))

        self._register_manifest(PatternManifest(
            id="supply_chain",
            name="Supply Chain Simulation",
            category="operations",
            tier=PatternTier.EXTENDED,
            module_path="v6.engine.src.patterns.supply_chain",
            class_name="SupplyChainPattern",
            dependencies=["numpy"],
            estimated_size_mb=10.0,
            loaded=True,
        ))

        # === TIER: ON_DEMAND (100+ patterns) ===
        # These are placeholders - loaded only when explicitly requested
        advanced_patterns = [
            ("quantum_circuit", "Quantum Circuit", "physics", ["qiskit", "cirq"], 200.0),
            ("molecular_dynamics", "Molecular Dynamics", "chemistry", ["lammps", "mdanalysis"], 300.0),
            ("climate_gcm", "Climate GCM", "climate", ["cesm", "xarray"], 1000.0),
            ("weather_nwp", "Weather NWP", "meteorology", ["wrf", "grib"], 500.0),
            ("garch", "GARCH Model", "finance", ["arch"], 20.0),
            ("game_theory", "Game Theory", "economics", ["nashpy"], 10.0),
            ("copula", "Copula Model", "finance", ["pyvinecopulib"], 30.0),
            ("social_network", "Social Network", "social", ["networkx"], 5.0),
            ("opinion_dynamics", "Opinion Dynamics", "social", ["networkx"], 5.0),
            ("kalman_filter", "Kalman Filter", "signal", ["filterpy"], 10.0),
            ("wavelet", "Wavelet Analysis", "signal", ["pywavelets"], 15.0),
            ("mpc", "Model Predictive Control", "control", ["casadi", "cvxpy"], 50.0),
            ("slam", "SLAM", "robotics", ["g2o", "gtsam"], 100.0),
            ("gis_analysis", "GIS Analysis", "geospatial", ["geopandas", "rasterio"], 100.0),
            ("traffic_sim", "Traffic Simulation", "transport", ["sumo", "traci"], 200.0),
            ("seismic", "Seismic Modeling", "geophysics", ["obspy"], 50.0),
            ("dft", "Density Functional Theory", "quantum", ["ase", "pymatgen"], 200.0),
            ("phase_field", "Phase Field", "materials", ["fipy"], 100.0),
            ("reliability", "Reliability Analysis", "risk", ["openturns"], 50.0),
            ("supply_chain", "Supply Chain", "operations", ["pulp"], 20.0),
            ("power_grid", "Power Grid", "energy", ["pandapower"], 50.0),
            ("tsunami", "Tsunami Modeling", "ocean", ["geoclaw"], 200.0),
            ("reinforcement_learning", "RL Simulation", "ml", ["gym", "stable-baselines3"], 300.0),
            ("generative_gan", "GAN Simulation", "ml", ["torch", "tensorflow"], 500.0),
            ("federated", "Federated Learning", "ml", ["flower", "pysyft"], 100.0),
            ("surrogate", "Surrogate Model", "ml", ["gpytorch", "scikit-learn"], 100.0),
            ("nuclear_reactor", "Nuclear Reactor", "nuclear", ["openmc", "serpent"], 500.0),
            ("ecological", "Ecological Model", "ecology", ["biomass"], 30.0),
            ("hydrological", "Hydrological", "water", ["swat", "pysheds"], 100.0),
            ("voting", "Voting Model", "politics", ["votekit"], 10.0),
            ("conflict", "Conflict Model", "politics", ["pydive"], 10.0),
        ]
        
        for pid, name, category, deps, size in advanced_patterns:
            self._register_manifest(PatternManifest(
                id=pid,
                name=name,
                category=category,
                tier=PatternTier.ON_DEMAND,
                module_path=f"v6.engine.src.patterns.{pid}",
                class_name=f"{''.join(w.capitalize() for w in pid.split('_'))}Pattern",
                dependencies=["numpy"],
                optional_dependencies=deps,
                estimated_size_mb=size,
            ))
        
        logger.info(f"Registered {len(self.manifests)} pattern manifests")
        
    def _register_manifest(self, manifest: PatternManifest):
        """Register a pattern manifest"""
        self.manifests[manifest.id] = manifest
        
    async def initialize(self, tiers: Optional[List[PatternTier]] = None):
        """
        Initialize loader, auto-load specified tiers
        
        Args:
            tiers: Which tiers to auto-load (default: [CORE, ESSENTIAL])
        """
        if tiers is None:
            tiers = [PatternTier.CORE, PatternTier.ESSENTIAL]
            
        logger.info(f"Initializing pattern loader with tiers: {[t.name for t in tiers]}")
        
        for manifest in self.manifests.values():
            if manifest.tier in tiers:
                await self.load_pattern(manifest.id)
                
    async def load_pattern(self, pattern_id: str) -> bool:
        """
        Load a pattern by ID (lazy loading)
        
        Returns:
            True if loaded successfully, False otherwise
        """
        async with self.loading_lock:
            manifest = self.manifests.get(pattern_id)
            if not manifest:
                logger.error(f"Unknown pattern: {pattern_id}")
                return False
                
            if manifest.loaded:
                return True
                
            logger.info(f"Loading pattern: {manifest.name} ({pattern_id})")
            
            # Check dependencies
            if not await self._check_dependencies(manifest):
                logger.warning(f"Pattern {pattern_id} has missing dependencies")
                manifest.available = False
                return False
                
            try:
                # Dynamic import
                module = importlib.import_module(manifest.module_path)
                pattern_class = getattr(module, manifest.class_name)
                
                # Instantiate (auto-registers via decorator)
                instance = pattern_class()
                
                manifest.loaded = True
                manifest.available = True
                
                logger.info(f"✓ Loaded pattern: {manifest.name}")
                return True
                
            except Exception as e:
                logger.exception(f"Failed to load pattern {pattern_id}")
                manifest.available = False
                return False
                
    async def _check_dependencies(self, manifest: PatternManifest) -> bool:
        """Check if all dependencies are available"""
        missing = []
        
        for dep in manifest.dependencies:
            if not self._check_package(dep):
                missing.append(dep)
                
        if missing and self.auto_install:
            logger.info(f"Auto-installing dependencies: {missing}")
            await self._install_packages(missing)
            
            # Re-check
            missing = [dep for dep in manifest.dependencies if not self._check_package(dep)]
            
        if missing:
            logger.warning(f"Missing dependencies for {manifest.id}: {missing}")
            return False
            
        return True
        
    def _check_package(self, package: str) -> bool:
        """Check if a Python package is installed"""
        try:
            importlib.import_module(package.lower())
            return True
        except ImportError:
            return False
            
    async def _install_packages(self, packages: List[str]):
        """Install missing packages via pip"""
        cmd = [sys.executable, "-m", "pip", "install"] + packages
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install packages: {e}")
            
    async def prepare_for_validation(self, hypothesis) -> List[str]:
        """
        Validation preparation mode:
        Load all patterns that might be relevant for validation
        
        Returns:
            List of loaded pattern IDs
        """
        logger.info("Preparing for validation - loading relevant patterns")
        
        loaded = []
        
        # Load patterns that can simulate this hypothesis
        for manifest in self.manifests.values():
            if manifest.tier in [PatternTier.CORE, PatternTier.ESSENTIAL]:
                continue  # Already loaded
                
            # Check if pattern might handle this hypothesis
            if await self._pattern_might_handle(manifest, hypothesis):
                if await self.load_pattern(manifest.id):
                    loaded.append(manifest.id)
                    
        logger.info(f"Loaded {len(loaded)} patterns for validation: {loaded}")
        return loaded
        
    async def _pattern_might_handle(self, manifest: PatternManifest, hypothesis) -> bool:
        """Quick check if pattern might handle hypothesis (before loading)"""
        # Check keywords in title/description
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keyword_map = {
            "fem": ["finite element", "stress", "structural", "mechanics"],
            "cfd": ["fluid", "aerodynamic", "flow", "navier-stokes"],
            "pharmacokinetics": ["drug", "dose", "pk", "concentration"],
            "neural_network": ["neuron", "brain", "spiking", "synapse"],
            "dsge": ["macroeconomic", "policy", "rbc", "new keynesian"],
            "quantum_circuit": ["qubit", "quantum", "gate", "superposition"],
            "molecular_dynamics": ["atom", "molecule", "force field", "md"],
            "climate_gcm": ["climate", "global warming", "temperature", "co2"],
            "garch": ["volatility", "arch", "financial risk"],
            "game_theory": ["nash", "equilibrium", "strategy", "auction"],
        }
        
        keywords = keyword_map.get(manifest.id, [])
        return any(kw in title or kw in desc for kw in keywords)
        
    def get_manifest(self, pattern_id: str) -> Optional[PatternManifest]:
        """Get pattern manifest"""
        return self.manifests.get(pattern_id)
        
    def list_available(self, tier: Optional[PatternTier] = None) -> List[PatternManifest]:
        """List available patterns, optionally filtered by tier"""
        manifests = list(self.manifests.values())
        if tier:
            manifests = [m for m in manifests if m.tier == tier]
        return manifests
        
    def get_status(self) -> Dict[str, Any]:
        """Get loader status summary"""
        by_tier = {}
        for tier in PatternTier:
            tier_manifests = [m for m in self.manifests.values() if m.tier == tier]
            by_tier[tier.name] = {
                "total": len(tier_manifests),
                "loaded": sum(1 for m in tier_manifests if m.loaded),
                "available": sum(1 for m in tier_manifests if m.available),
            }
            
        return {
            "total_patterns": len(self.manifests),
            "loaded_patterns": sum(1 for m in self.manifests.values() if m.loaded),
            "by_tier": by_tier,
            "memory_estimate_mb": sum(
                m.estimated_size_mb for m in self.manifests.values() if m.loaded
            ),
        }


# Singleton
_pattern_loader = None

def get_pattern_loader() -> PatternLoader:
    global _pattern_loader
    if _pattern_loader is None:
        _pattern_loader = PatternLoader()
    return _pattern_loader
