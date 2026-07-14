"""Tests for models JSON CLI exports."""

from __future__ import annotations

from src.cli.config_models import export_config_json, export_models_json


def test_export_config_json_has_phases():
    data = export_config_json()
    assert "phases" in data
    assert len(data["phases"]) == 7
    assert data["phases"][0]["phase"] == "A"
    assert "council" in data


def test_export_models_json():
    data = export_models_json()
    assert data["count"] >= 1
    assert "models" in data
    assert data["catalog_size"] >= 1
