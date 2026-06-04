from __future__ import annotations

import pytest

from src.publishing.experiment_design import ExperimentalProtocol, generate_protocol


class TestGenerateProtocol:
    def test_biology_protocol_is_valid(self) -> None:
        protocol = generate_protocol("DNA repair hypothesis", "biology")
        assert isinstance(protocol, ExperimentalProtocol)
        assert protocol.domain == "biology"
        assert len(protocol.materials) > 0
        assert len(protocol.equipment) > 0
        assert len(protocol.procedure) > 0

    def test_protocol_has_all_required_fields(self) -> None:
        protocol = generate_protocol("test hypothesis", "biology")
        assert protocol.hypothesis_id is not None
        assert isinstance(protocol.domain, str)
        assert isinstance(protocol.design_type, str)
        assert isinstance(protocol.sample_size, int)
        assert isinstance(protocol.control_groups, int)
        assert isinstance(protocol.treatment_groups, int)
        assert isinstance(protocol.materials, list)
        assert isinstance(protocol.equipment, list)
        assert isinstance(protocol.procedure, list)
        assert isinstance(protocol.statistical_test, str)
        assert isinstance(protocol.effect_size_expected, float)
        assert isinstance(protocol.power, float)

    def test_biology_protocol_includes_cell_culture_materials(self) -> None:
        protocol = generate_protocol("DNA repair hypothesis", "biology")
        materials_text = " ".join(protocol.materials).lower()
        assert "cell culture" in materials_text or "media" in materials_text

    def test_chemistry_protocol_includes_synthesis_steps(self) -> None:
        protocol = generate_protocol("Catalyst optimization", "chemistry")
        procedure_text = " ".join(protocol.procedure).lower()
        assert "synthes" in procedure_text or "reaction" in procedure_text

    def test_sample_size_positive(self) -> None:
        protocol = generate_protocol("any hypothesis", "biology")
        assert protocol.sample_size > 0

    def test_to_markdown_non_empty(self) -> None:
        protocol = generate_protocol("test hypothesis", "biology")
        md = protocol.to_markdown()
        assert isinstance(md, str)
        assert len(md) > 0
        assert "Experimental Validation Protocol" in md
