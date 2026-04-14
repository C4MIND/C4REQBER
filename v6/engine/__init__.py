"""
TURBO-CDI v6.0 Engine Package

Re-exports from src for cleaner imports
"""

# Re-export everything from src
from .src import (
    TURBOCDIEngine,
    EngineConfig,
    Hypothesis,
    SimulationResult,
    ValidationReport,
    ValidationLevel,
    EvolutionConfig,
    simulation_pattern,
    PatternRegistry,
    # Patterns
    MonteCarloPattern,
    AgentBasedPattern,
    SystemDynamicsPattern,
    CircuitSimulationPattern,
)

# API imported separately to avoid circular imports
def get_app():
    """Get FastAPI app (lazy import)"""
    from .src.api import app
    return app

__all__ = [
    "TURBOCDIEngine",
    "EngineConfig",
    "Hypothesis",
    "SimulationResult",
    "ValidationReport",
    "ValidationLevel",
    "EvolutionConfig",
    "simulation_pattern",
    "PatternRegistry",
    # Patterns
    "MonteCarloPattern",
    "AgentBasedPattern",
    "SystemDynamicsPattern",
    "CircuitSimulationPattern",
    # API
    "get_app",
]
