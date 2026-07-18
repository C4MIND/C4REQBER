from __future__ import annotations


"""Backward-compatibility shim — re-exports the canonical MultiSourceSearcher from orchestrator.py.

Phase 0 (P0.1): All 8 production imports migrated to orchestrator.py.
This file preserved for backward compatibility only.
"""

from src.knowledge.orchestrator import MultiSourceSearcher


SOURCE_REGISTRY: dict = {}
DOMAIN_KEYWORDS: dict[str, list[str]] = {}

try:
    from src.knowledge.config import DOMAIN_KEYWORDS as _DK
    from src.knowledge.config import SOURCE_REGISTRY as _SR

    SOURCE_REGISTRY = _SR
    DOMAIN_KEYWORDS = _DK
except ImportError:
    pass

__all__ = ["MultiSourceSearcher", "SOURCE_REGISTRY", "DOMAIN_KEYWORDS"]
