"""
C44TCDI: Pipeline package.
"""
from __future__ import annotations

from .ab_testing import ABTestManager, Variant
from .config import PipelineConfig
from .meta_pipeline import (
    C4_STATE_MAP,
    META_STEP_DESCRIPTIONS,
    META_STEP_ICONS,
    META_STEP_LABELS,
    STEP_MAP,
    MetaPipeline,
    MetaPipelineState,
    MetaStep,
)
from .quality import QualityGates, QualityReport
from .result import PipelineResult
from .ucos_qzrf import QZRFAnalyzer, UCOSAnalyzer


# Backward compatibility alias
PipelineStepConfig = PipelineConfig

__all__ = [
    "PipelineConfig",
    "PipelineResult",
    "PipelineStepConfig",
    "QualityGates",
    "QualityReport",
    "ABTestManager",
    "Variant",
    "UCOSAnalyzer",
    "QZRFAnalyzer",
    "MetaPipeline",
    "MetaPipelineState",
    "MetaStep",
    "META_STEP_LABELS",
    "META_STEP_ICONS",
    "META_STEP_DESCRIPTIONS",
    "STEP_MAP",
    "C4_STATE_MAP",
]
