"""
c4-cdi-turbo: References Module
Reference manager integration
"""
from __future__ import annotations

from src.references.manager import (
    MendeleyImporter,
    ReferenceImport,
    ReferenceManager,
    ZoteroImporter,
    get_reference_manager,
)


__all__ = [
    "ReferenceManager",
    "ReferenceImport",
    "ZoteroImporter",
    "MendeleyImporter",
    "get_reference_manager",
]
