"""27 Functor Agents — cognitive operators based on QZRF/Fractal27."""
from .abstraction import AbstractionAgent
from .base import FunctorAgent
from .composite import _CompositeFunctor, compose, generate_all_composites
from .concretization import ConcretizationAgent
from .context import ContextAgent
from .distinction import DistinctionAgent
from .integration import IntegrationAgent
from .inversion import InversionAgent
from .meta_reflection import MetaReflectionAgent
from .resonance import ResonanceAgent
from .temporal import TemporalAgent


__all__ = [
    "FunctorAgent",
    "TemporalAgent",
    "IntegrationAgent",
    "DistinctionAgent",
    "ResonanceAgent",
    "InversionAgent",
    "AbstractionAgent",
    "ConcretizationAgent",
    "ContextAgent",
    "MetaReflectionAgent",
    "compose",
    "generate_all_composites",
    "_CompositeFunctor",
]
