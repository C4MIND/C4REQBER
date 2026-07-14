"""Tests for src/publishing/blueprint.py — BlueprintGenerator."""
from __future__ import annotations

from src.publishing.blueprint import BlueprintGenerator


class TestBlueprintGenerator:
    def setup_method(self):
        self.gen = BlueprintGenerator()
        self.sample_components = [
            {"name": "Laser Diode", "material": "GaAs", "dimensions": "10x5x5mm"},
            {"name": "Lens Assembly", "material": "BK7 Glass", "dimensions": "25x25x10mm"},
            {"name": "Detector Array", "material": "Si", "dimensions": "50x50x2mm"},
        ]

    def test_ascii_schematic_not_empty(self):
        result = self.gen.generate_ascii_schematic("Test Device", self.sample_components)
        assert "TEST DEVICE" in result
        assert "Laser Diode" in result
        assert "GaAs" in result

    def test_ascii_schematic_empty_components(self):
        result = self.gen.generate_ascii_schematic("Empty", [])
        assert "EMPTY" in result

    def test_ascii_schematic_missing_keys(self):
        bad = [{"bad": "thing"}, {}]
        result = self.gen.generate_ascii_schematic("Test", bad)
        assert "?" in result

    def test_svg_schematic_not_empty(self):
        result = self.gen.generate_svg_schematic("Device", self.sample_components)
        assert "<svg" in result
        assert "Device" in result
        assert "</svg>" in result

    def test_svg_schematic_empty(self):
        result = self.gen.generate_svg_schematic("Empty", [])
        assert "<svg" in result
        assert "</svg>" in result

    def test_cad_spec_structure(self):
        result = self.gen.generate_cad_spec("Widget", self.sample_components)
        assert result["project"] == "Widget"
        assert result["format"] == "STEP/STL"
        assert len(result["components"]) == 3
        assert result["components"][0]["id"] == "COMP-001"

    def test_cad_spec_empty(self):
        result = self.gen.generate_cad_spec("None", [])
        assert result["components"] == []

    def test_triz_rationale(self):
        triz = ["Segmentation", "Taking out", "Local quality"]
        result = self.gen.generate_triz_rationale(self.sample_components, triz)
        assert "TRIZ" in result
        assert "Component 1" in result

    def test_triz_rationale_empty_principles(self):
        result = self.gen.generate_triz_rationale(
            [{"name": "X"}], []
        )
        assert "N/A" in result
