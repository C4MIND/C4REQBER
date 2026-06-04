"""
c4-cdi-turbo: Models Package
Production-grade type safety with strict validation.
"""
from __future__ import annotations

from .core import (
    AgencyAxis,
    BaseOperator,
    C4StateModel,
    C4TransitionModel,
    ContradictionType,
    DiscoveryStatus,
    ScaleAxis,
    TimeAxis,
)
from .schemas import (
    DISCOVERY_SCHEMA,
    FALSIFIABILITY_SCHEMA,
    AnalogyMappingModel,
    DiscoveryModel,
    FalsifiabilityCriterionModel,
    PhysicalContradictionModel,
    ResearchProjectModel,
    SystemHealthModel,
)


__all__ = [
    # Core enums
    "TimeAxis",
    "ScaleAxis",
    "AgencyAxis",
    "ContradictionType",
    "DiscoveryStatus",
    "BaseOperator",
    # Core models
    "C4StateModel",
    "C4TransitionModel",
    # Schema models
    "PhysicalContradictionModel",
    "FalsifiabilityCriterionModel",
    "DiscoveryModel",
    "ResearchProjectModel",
    "AnalogyMappingModel",
    "SystemHealthModel",
    # Schema exports
    "DISCOVERY_SCHEMA",
    "FALSIFIABILITY_SCHEMA",
]
