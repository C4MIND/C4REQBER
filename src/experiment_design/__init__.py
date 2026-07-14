"""Experiment Design & Validation module for c4-cdi-turbo.

Provides Design of Experiments (DoE), Power Analysis, and
Reproducibility Validation.
"""

from src.experiment_design.doe import (
    DesignType,
    DoEConfig,
    DoEResult,
    Factor,
    central_composite_design,
    fractional_factorial_design,
    full_factorial_design,
    generate_design,
    latin_hypercube_sampling,
    randomized_block_design,
)
from src.experiment_design.power import (
    PowerResult,
    anova_power,
    anova_sample_size,
    cohens_d,
    eta_squared,
    partial_eta_squared,
    power_curve_anova,
    power_curve_proportion,
    power_curve_ttest,
    proportion_power,
    proportion_sample_size,
    ttest_power,
    ttest_sample_size,
)
from src.experiment_design.reproducibility import (
    STANDARD_CHECKLIST,
    CheckItem,
    CheckResult,
    CheckStatus,
    ProvenanceLog,
    ProvenanceRecord,
    ReproducibilityReport,
    ReproducibilityValidator,
    compute_file_hash,
    compute_result_hash,
)


__all__ = [
    # doe
    "DoEConfig",
    "DoEResult",
    "DesignType",
    "Factor",
    "generate_design",
    "full_factorial_design",
    "fractional_factorial_design",
    "latin_hypercube_sampling",
    "central_composite_design",
    "randomized_block_design",
    # power
    "PowerResult",
    "ttest_sample_size",
    "ttest_power",
    "anova_sample_size",
    "anova_power",
    "proportion_sample_size",
    "proportion_power",
    "cohens_d",
    "eta_squared",
    "partial_eta_squared",
    "power_curve_ttest",
    "power_curve_anova",
    "power_curve_proportion",
    # reproducibility
    "CheckItem",
    "CheckResult",
    "CheckStatus",
    "ProvenanceLog",
    "ProvenanceRecord",
    "ReproducibilityReport",
    "ReproducibilityValidator",
    "STANDARD_CHECKLIST",
    "compute_result_hash",
    "compute_file_hash",
]
