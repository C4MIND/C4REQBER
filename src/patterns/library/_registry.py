"""
C4REQBER v6.5 - Pattern[str] registry, categories, and metadata.

Internal module for patterns/library/__init__.py.
Call build_registry(pattern_map) after all pattern imports are complete.
"""
from typing import Any

from src.di.container import get_container


_PATTERN_ID_LIST = sorted([
    "acoustic_waves", "adaptive_filter", "age_structured", "agent_based",
    "air_quality", "biogeochemistry", "bootstrap", "cfd", "circuit",
    "cellular_automata", "climate_gcm", "cloud_microphysics",
    "collaborative_filtering", "composite_mechanics", "conflict",
    "connectome", "continuum_mechanics", "credit_risk", "crystal_growth",
    "cultural_diffusion", "dft", "discrete_event", "double_pendulum",
    "dsge", "economic_growth", "elasticity_3d", "enzyme_kinetics",
    "epidemic_seir", "epidemic_sir", "evolutionary", "fem", "fisheries",
    "flocking", "forest_gap", "fractal_julia", "fractal_mandelbrot",
    "game_theory", "garch", "gene_regulatory", "geomagnetic",
    "gravity_trade", "groundwater", "herding", "heterogeneous_agents",
    "hodgkin_huxley", "innovation_diffusion", "input_output",
    "inverse_kinematics", "ising_model", "kalman_filter", "land_surface",
    "land_use", "language_evolution", "lotka_volterra", "mantle_convection",
    "markov_chain", "market_microstructure", "maxwell_fdtd",
    "metapopulation", "migration", "model_predictive", "molecular_dynamics",
    "monte_carlo", "monte_carlo_pi", "n_body", "neural_mass",
    "neural_network", "ocean_circulation", "open_quantum",
    "opinion_dynamics", "optimization", "option_pricing",
    "overlapping_generations", "path_planning", "pedestrian", "percolation",
    "pharmacokinetics", "phase_field", "pid_tuning", "plasma_pic",
    "poisson_solver", "population_genetics", "portfolio_optimization",
    "projectile_motion", "prospect_theory", "protein_folding", "qft_lattice",
    "quantum", "quantum_harmonic_oscillator", "queueing_networks",
    "reaction_diffusion", "rigid_body", "rumor_spreading", "search_matching",
    "sea_ice", "seismic_waves", "signal_transduction", "slam",
    "social_network", "spatial_ecology", "spectral_estimation",
    "spring_mass", "state_space", "supply_chain", "surface_water",
    "synaptic_plasticity", "system_dynamics", "thermal", "traffic_flow",
    "urban_growth", "wave_equation", "wave_optics", "wavelet_analysis",
    "wildfire",
])

_CORE_PATTERNS = ["monte_carlo", "agent_based", "system_dynamics", "circuit"]
_ESSENTIAL_PATTERNS = ["fem", "cfd"]
_ON_DEMAND_PATTERNS = [
    "climate_gcm", "quantum", "molecular_dynamics",
    "input_output", "overlapping_generations", "search_matching",
    "heterogeneous_agents", "option_pricing", "credit_risk",
    "market_microstructure", "portfolio_optimization", "gravity_trade",
    "economic_growth", "prospect_theory", "herding",
    "pid_tuning", "state_space", "model_predictive", "kalman_filter",
    "inverse_kinematics", "path_planning", "slam",
    "adaptive_filter", "spectral_estimation", "wavelet_analysis",
    "crystal_growth", "composite_mechanics", "traffic_flow",
    "queueing_networks",
    "ocean_circulation", "sea_ice", "biogeochemistry",
    "cloud_microphysics", "surface_water", "groundwater",
    "land_surface", "seismic_waves", "mantle_convection",
    "geomagnetic", "air_quality", "wildfire",
    "opinion_dynamics", "cultural_diffusion", "language_evolution",
    "urban_growth", "land_use", "migration", "flocking",
    "pedestrian", "conflict", "rumor_spreading",
    "innovation_diffusion", "collaborative_filtering",
    "dft", "open_quantum", "qft_lattice",
    # Phase 2 additions
    "quantum_harmonic_oscillator", "double_pendulum", "wave_equation",
    "spring_mass", "projectile_motion", "reaction_diffusion",
    "population_genetics", "epidemic_sir", "fractal_mandelbrot",
    "fractal_julia", "cellular_automata", "markov_chain",
    "monte_carlo_pi", "bootstrap",
]
_EXTENDED_PATTERNS = [
    p for p in _PATTERN_ID_LIST
    if p not in _CORE_PATTERNS + _ESSENTIAL_PATTERNS + _ON_DEMAND_PATTERNS
]

PATTERN_MAP: dict[str, Any] = {}
AVAILABLE_PATTERNS: list[Any] = []
PATTERN_CATEGORIES: dict[str, Any] = {}

__all__ = [
    "PATTERN_MAP", "PATTERN_CATEGORIES", "AVAILABLE_PATTERNS",
    "build_registry", "get_pattern_by_id", "list_all_patterns", "get_total_patterns",
]

def build_registry(pattern_map: dict[str, Any]) -> None:
    """Build registry from a mapping of pattern_id -> pattern_class."""
    PATTERN_MAP.clear()
    PATTERN_MAP.update(pattern_map)
    available = [k for k, v in pattern_map.items() if v is not None]
    AVAILABLE_PATTERNS.clear()
    AVAILABLE_PATTERNS.extend(available)
    total = len(AVAILABLE_PATTERNS)
    get_container().register("TOTAL_PATTERNS", total)
    PATTERN_CATEGORIES.clear()
    PATTERN_CATEGORIES.update({
        "CORE": {
            "patterns": [p for p in _CORE_PATTERNS if p in AVAILABLE_PATTERNS],
            "description": "Always loaded, fundamental building blocks",
            "memory_mb": 50,
        },
        "ESSENTIAL": {
            "patterns": [p for p in _ESSENTIAL_PATTERNS if p in AVAILABLE_PATTERNS],
            "description": "Auto-loaded for common use cases",
            "memory_mb": 100,
        },
        "EXTENDED": {
            "patterns": [p for p in _EXTENDED_PATTERNS if p in AVAILABLE_PATTERNS],
            "description": "Lazy-loaded on first use",
            "memory_mb": 500,
        },
        "ON_DEMAND": {
            "patterns": [p for p in _ON_DEMAND_PATTERNS if p in AVAILABLE_PATTERNS],
            "description": "Loaded only when explicitly requested",
            "memory_mb": 200,
        },
    })

def get_pattern_by_id(pattern_id: str) -> Any:
    """Get pattern class by ID"""
    return PATTERN_MAP.get(pattern_id)

def list_all_patterns() -> Any:
    """List all available patterns with their categories"""
    result = {}
    for category, info in PATTERN_CATEGORIES.items():
        result[category] = {
            "patterns": [p for p in info["patterns"] if p in AVAILABLE_PATTERNS],
            "memory_mb": info["memory_mb"],
            "description": info["description"],
        }
    return result

def get_total_patterns() -> int:
    """Get total number of available patterns (backed by DI container)."""
    container = get_container()
    if container.has("TOTAL_PATTERNS"):
        return container.resolve("TOTAL_PATTERNS")
    return len(AVAILABLE_PATTERNS)
