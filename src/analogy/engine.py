"""
C4REQBER: Analogy Engine v4.0
Cross-domain analogy discovery using multiple methods.

This module is a thin backward-compatibility wrapper.
All implementation has been split into:
  - src.analogy.core       (AnalogyEngine, get_analogy_engine)
  - src.analogy.operations (SemanticEmbedder, Word2VecAnalogySolver, ConceptNetBridge)
  - src.analogy.utils      (AnalogyResult, helpers)
"""
from __future__ import annotations

from src.analogy.core import AnalogyEngine, get_analogy_engine
from src.analogy.operations import ConceptNetBridge, SemanticEmbedder, Word2VecAnalogySolver
from src.analogy.utils import AnalogyResult


__all__ = [
    "AnalogyEngine",
    "get_analogy_engine",
    "AnalogyResult",
    "SemanticEmbedder",
    "Word2VecAnalogySolver",
    "ConceptNetBridge",
]
