"""
c4reqber: External provider integrations.

LLM providers: Liquid AI, NVIDIA NIM, YandexGPT.
Agent OS: OpenFang — Rust Agent OS, 140+ endpoints, 53 tools.
Desktop: Eigent — Electron+FastAPI multi-agent workforce.
Prior art: academic search engine.
"""
from __future__ import annotations

from .eigent import EigentDesktop
from .liquid_ai import LiquidAIClient
from .nvidia import NvidiaNimClient
from .openfang import OpenFangClient

from .scientific_bridges import (
    DeepChemBridge,
    LangGraphBridge,
    OpenMMBridge,
    PyMCBridge,
    SmitheryBridge,
    UnslothBridge,
    VLLMBridge,
)
from .yandex import YandexGPTClient


__all__ = [
    "LiquidAIClient",
    "NvidiaNimClient",
    "YandexGPTClient",
    "OpenFangClient",
    "EigentDesktop",
    "LangGraphBridge",
    "SmitheryBridge",
    "PyMCBridge",
    "OpenMMBridge",
    "DeepChemBridge",
    "UnslothBridge",
    "VLLMBridge",
]
