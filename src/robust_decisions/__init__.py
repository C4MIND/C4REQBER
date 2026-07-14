"""Robust Decision Making (RDM) Engine — XLRM + PRIM scenario discovery."""

from __future__ import annotations

from src.robust_decisions.prim import PRIMBox, prim_analysis
from src.robust_decisions.xlrm import RDMResult, XLMRModel, explore_scenarios


__all__ = [
    "XLMRModel",
    "RDMResult",
    "explore_scenarios",
    "PRIMBox",
    "prim_analysis",
]
