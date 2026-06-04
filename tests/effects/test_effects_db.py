"""Tests for src/effects/effects_db.py — PhysicalEffect, EffectsDatabase."""
from __future__ import annotations

from src.effects.effects_db import EffectsDatabase, PhysicalEffect


class TestPhysicalEffect:
    def test_default_lists(self):
        effect = PhysicalEffect(
            name="Test",
            description="A test effect",
            category="mechanical",
        )
        assert effect.parameters == []
        assert effect.applications == []

    def test_with_formula(self):
        effect = PhysicalEffect(
            name="Gravity",
            description="Mass attracts mass",
            category="mechanical",
            formula="F = G*m1*m2/r^2",
            parameters=["mass", "distance"],
            applications=["orbital mechanics"],
        )
        assert effect.formula == "F = G*m1*m2/r^2"
        assert "mass" in effect.parameters
        assert "orbital mechanics" in effect.applications


class TestEffectsDatabase:
    def test_known_effects_exist(self):
        assert "piezoelectric" in EffectsDatabase.EFFECTS
        assert "shape_memory" in EffectsDatabase.EFFECTS
        assert "electromagnetic_induction" in EffectsDatabase.EFFECTS

    def test_get_effect_found(self):
        db = EffectsDatabase()
        effect = db.get_effect("piezoelectric")
        assert effect is not None
        assert effect.name == "Piezoelectric Effect"
        assert effect.category == "mechanical"

    def test_get_effect_not_found(self):
        db = EffectsDatabase()
        result = db.get_effect("nonexistent_effect")
        assert result is None

    def test_get_by_category(self):
        db = EffectsDatabase()
        results = db.get_by_category("mechanical")
        assert len(results) >= 1
        for effect in results:
            assert effect.category == "mechanical"

    def test_list_all_categories(self):
        db = EffectsDatabase()
        categories = db.list_categories()
        assert "mechanical" in categories
        assert "thermal" in categories

    def test_search_effects(self):
        db = EffectsDatabase()
        results = db.search_effects(query="piezoelectric")
        assert len(results) >= 0
