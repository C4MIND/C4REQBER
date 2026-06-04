"""
Re-export from pipeline.py for package compatibility.
"""
from __future__ import annotations

import sys
from pathlib import Path


# The pipeline.py is a sibling of this package (same parent directory)
# We need to import from it without causing circular imports
_pipeline_path = Path(__file__).parent.parent / "pipeline.py"
if _pipeline_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_agents_pipeline_module", _pipeline_path
    )
    _pipeline_module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["_agents_pipeline_module"] = _pipeline_module
    spec.loader.exec_module(_pipeline_module)  # type: ignore[union-attr]

    PipelineEvent = _pipeline_module.PipelineEvent
    PipelineStage = _pipeline_module.PipelineStage
    PipelineStep = _pipeline_module.PipelineStep
    SolvePipelineResult = _pipeline_module.SolvePipelineResult
    UniversalSolvePipeline = _pipeline_module.UniversalSolvePipeline
else:
    raise ImportError(f"pipeline.py not found at {_pipeline_path}")

__all__ = [
    "PipelineStage",
    "PipelineStep",
    "PipelineEvent",
    "SolvePipelineResult",
    "UniversalSolvePipeline",
]
