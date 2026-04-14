"""
TURBO-CDI: References Module
Reference manager integration
"""

from src.references.manager import (
    ReferenceManager,
    ReferenceImport,
    ZoteroImporter,
    MendeleyImporter,
    get_reference_manager,
)

__all__ = [
    "ReferenceManager",
    "ReferenceImport",
    "ZoteroImporter",
    "MendeleyImporter",
    "get_reference_manager",
]
