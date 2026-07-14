"""
C4REQBER: 153 Metaprograms Library
Metaprogram (MP) filters that shape agent perception and reasoning.

Compatibility wrapper — imports from metamodels.mp package.
"""
from __future__ import annotations

from src.metamodels.mp.core import Metaprogram, MPDimension, MPProfile
from src.metamodels.mp.data import CORE_METAPROGRAMS
from src.metamodels.mp.patterns import MPLibrary


__all__ = ["CORE_METAPROGRAMS", "MPDimension", "MPProfile", "Metaprogram", "MPLibrary"]
