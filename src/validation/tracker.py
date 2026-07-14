"""
C4REQBER: Validation System v4.0
Scientific experiment tracking and hypothesis validation

Compatibility wrapper — re-exports everything from core and rules modules.
"""
from __future__ import annotations

from src.validation.core import (
    BayesianUpdater,
    CalibrationTracker,
    Experiment,
    ExperimentStatus,
    FalsifiabilityCriterion,
    Observation,
)
from src.validation.rules import (
    ValidationTracker,
    get_validation_tracker,
)


__all__ = [
    "BayesianUpdater",
    "CalibrationTracker",
    "Experiment",
    "ExperimentStatus",
    "FalsifiabilityCriterion",
    "Observation",
    "ValidationTracker",
    "get_validation_tracker",
]
