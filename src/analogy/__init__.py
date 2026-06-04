from __future__ import annotations


"""c4-cdi-turbo Analogy Module"""

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
