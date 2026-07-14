"""Tests for src/archetypes/ — smoke tests for archetypes module."""
from __future__ import annotations


def test_import_smoke():
    from src.archetypes import data, engine


def test_archetype_data():
    from src.archetypes.data import ARCHETYPE_MAP, get_all_archetypes
    from src.c4.state import C4State
    assert len(ARCHETYPE_MAP) > 0
    archetypes = get_all_archetypes()
    assert len(archetypes) > 0


def test_archetype_state():
    from src.archetypes.data import ARCHETYPE_MAP
    s = ARCHETYPE_MAP.get("000")
    assert s is not None
    assert s.time == "Past"


def test_engine_functions():
    from src.archetypes.engine import _dimension_distance
    assert callable(_dimension_distance)
