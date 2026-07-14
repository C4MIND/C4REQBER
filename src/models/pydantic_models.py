"""
C4REQBER: Pydantic Models v4.0
Production-grade type safety with strict validation

.. deprecated::
    This module is a compatibility wrapper. Import from ``src.models.core_models`` instead.
"""
from __future__ import annotations

from .core_models.core import (
    AgencyAxis,
    BaseOperator,
    C4StateModel,
    C4TransitionModel,
    ContradictionType,
    DiscoveryStatus,
    ScaleAxis,
    TimeAxis,
)
from .core_models.schemas import (
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
    "TimeAxis",
    "ScaleAxis",
    "AgencyAxis",
    "ContradictionType",
    "DiscoveryStatus",
    "BaseOperator",
    "C4StateModel",
    "C4TransitionModel",
    "PhysicalContradictionModel",
    "FalsifiabilityCriterionModel",
    "DiscoveryModel",
    "ResearchProjectModel",
    "AnalogyMappingModel",
    "SystemHealthModel",
    "DISCOVERY_SCHEMA",
    "FALSIFIABILITY_SCHEMA",
]
