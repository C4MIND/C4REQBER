"""
C4 Neural Classifier Package for C4REQBER.

Provides:
- NeuralFingerprint: unified interface (ONNX → PyTorch → LLM → heuristic)
- C4 types and state definitions
- Model architectures (C4Router)
- Export utilities (ONNX)
"""

from src.c4.neural_classifier.c4_types import (
    C4_STATE_NAMES,
    C4_STATES,
    AgencyAxis,
    C4Classification,
    ScaleAxis,
    TimeAxis,
)
from src.c4.neural_classifier.neural_fingerprint import NeuralFingerprint, get_neural_fingerprint
from src.c4.state import C4State


__all__ = [
    "AgencyAxis",
    "C4Classification",
    "C4State",
    "C4_STATES",
    "C4_STATE_NAMES",
    "NeuralFingerprint",
    "ScaleAxis",
    "TimeAxis",
    "get_neural_fingerprint",
]
