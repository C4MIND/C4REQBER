"""Reproducibility engine for c4-cdi-turbo.

Provides experiment validation, result hashing, and reproducibility scoring.
"""

from src.reproducibility.validator import (
    ReproducibilityReport,
    compute_experiment_hash,
    validate_experiment,
    verify_result_match,
)


__all__ = [
    "ReproducibilityReport",
    "validate_experiment",
    "compute_experiment_hash",
    "verify_result_match",
]
