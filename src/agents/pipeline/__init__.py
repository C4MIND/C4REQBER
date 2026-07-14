"""Re-export the solve-pipeline engine for ``agents.pipeline`` package compatibility.

The engine lives in the sibling module ``src/agents/solve_pipeline.py``. It
imports this package's step submodules (``agents.pipeline.steps.*``), so it
cannot live *inside* the package without a circular import — hence a sibling.
It used to be named ``pipeline.py``, shadowed by this very package, and was
loaded through an ``importlib.util`` + ``sys.path`` hack. Renamed out of the
shadow, it imports normally here.
"""
from __future__ import annotations

from src.agents.solve_pipeline import (
    PipelineEvent,
    PipelineStage,
    PipelineStep,
    SolvePipelineResult,
    UniversalSolvePipeline,
)


__all__ = [
    "PipelineStage",
    "PipelineStep",
    "PipelineEvent",
    "SolvePipelineResult",
    "UniversalSolvePipeline",
]
