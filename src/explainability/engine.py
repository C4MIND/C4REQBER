"""
C4REQBER: Explainability Engine
Explains WHY each C4 step works

Compatibility wrapper — imports from explainability package.
"""
from __future__ import annotations

from explainability.core import (
    ExplainabilityEngine,
    ExplanationLevel,
    PathExplanation,
    StepExplanation,
    get_explainability_engine,
)
from explainability.renderers import render_explanation


__all__ = [
    "ExplanationLevel",
    "ExplainabilityEngine",
    "PathExplanation",
    "StepExplanation",
    "get_explainability_engine",
    "render_explanation",
]
