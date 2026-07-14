"""
Tests for TRIZ Su-Field Analysis.
Verifies model extraction, completeness checking, and transformation rules.
"""
import pytest

from src.c4.types import C4State
from src.triz.sufield import (
    FIELD_KEYWORDS,
    TEXTBOOK_SUFIELD_EXAMPLES,
    FieldType,
    SuFieldAnalyzer,
    SuFieldModel,
    analyze_sufield,
)


# =============================================================================
# MODEL CONSTRUCTION TESTS
# =============================================================================

class TestSuFieldModel:
    def test_complete_model(self):
        model = SuFieldModel(
            s1="metal plate",
            s2="laser",
            f=FieldType.OPTICAL,
            status="complete",
        )
        assert model.is_complete()
        assert model.to_notation() == "laser —Optical→ metal plate"
        assert model.missing_elements() == []

    def test_incomplete_model_missing_s2(self):
        model = SuFieldModel(s1="workpiece", f=FieldType.MECHANICAL)
        assert not model.is_complete()
        assert "S2 (tool)" in model.missing_elements()

    def test_incomplete_model_missing_f(self):
        model = SuFieldModel(s1="workpiece", s2="hammer")
        assert not model.is_complete()
        assert "F (field)" in model.missing_elements()

    def test_model_to_dict(self):
        model = SuFieldModel(
            s1="battery", s2="heater", f=FieldType.THERMAL,
            status="harmful", harmful_effect="overheating",
        )
        d = model.to_dict()
        assert d["s1"] == "battery"
        assert d["status"] == "harmful"
        assert d["is_complete"] is True

    def test_all_field_types_have_keywords(self):
        for ft in FieldType:
            assert ft in FIELD_KEYWORDS
            assert len(FIELD_KEYWORDS[ft]) > 5


# =============================================================================
# ANALYZER EXTRACTION TESTS
# =============================================================================

class TestSuFieldExtraction:
    def test_extract_hammer_nail(self):
        text = "A hammer strikes a nail into wood."
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(text)
        assert model.s1 is not None
        assert model.s2 is not None
        assert model.f is not None

    def test_extract_laser_cutting(self):
        text = "A laser beam cuts through a steel plate."
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(text)
        assert model.s1 is not None
        assert model.s2 is not None
        assert model.f == FieldType.OPTICAL or model.f == FieldType.THERMAL

    def test_extract_incomplete(self):
        text = "We need to measure the temperature of molten metal."
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(text)
        assert model.status == "incomplete"

    def test_detect_harmful(self):
        text = "The excessive heat damages the electronic components."
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(text)
        assert model.harmful_effect is not None

    def test_field_detection_mechanical(self):
        analyzer = SuFieldAnalyzer()
        f = analyzer._detect_field("force pressure friction wear stress")
        assert f == FieldType.MECHANICAL

    def test_field_detection_thermal(self):
        analyzer = SuFieldAnalyzer()
        f = analyzer._detect_field("heat temperature thermal cooling warm")
        assert f == FieldType.THERMAL

    def test_field_detection_electrical(self):
        analyzer = SuFieldAnalyzer()
        f = analyzer._detect_field("electric current voltage resistance circuit")
        assert f == FieldType.ELECTRICAL

    def test_field_detection_magnetic(self):
        analyzer = SuFieldAnalyzer()
        f = analyzer._detect_field("magnetic field flux magnet levitation")
        assert f == FieldType.MAGNETIC

    def test_field_detection_chemical(self):
        analyzer = SuFieldAnalyzer()
        f = analyzer._detect_field("chemical reaction catalyst corrosion acid")
        assert f == FieldType.CHEMICAL

    def test_field_detection_optical(self):
        analyzer = SuFieldAnalyzer()
        f = analyzer._detect_field("light laser optical radiation infrared")
        assert f == FieldType.OPTICAL


# =============================================================================
# COMPLETENESS CHECK TESTS
# =============================================================================

class TestCompleteness:
    def test_complete_model_check(self):
        model = SuFieldModel(s1="plate", s2="laser", f=FieldType.OPTICAL, status="complete")
        analyzer = SuFieldAnalyzer()
        result = analyzer.check_completeness(model)
        assert result["is_complete"] is True
        assert result["completeness_score"] == 1.0
        assert len(result["missing_elements"]) == 0

    def test_incomplete_recommendations(self):
        model = SuFieldModel(s1="workpiece", status="incomplete")
        analyzer = SuFieldAnalyzer()
        result = analyzer.check_completeness(model)
        assert result["is_complete"] is False
        assert len(result["recommendations"]) >= 2
        assert result["completeness_score"] == 1 / 3

    def test_harmful_recommendations(self):
        model = SuFieldModel(
            s1="circuit", s2="current", f=FieldType.ELECTRICAL,
            status="harmful", harmful_effect="overheating",
        )
        analyzer = SuFieldAnalyzer()
        result = analyzer.check_completeness(model)
        assert result["is_complete"] is True
        assert any("harmful" in r.lower() for r in result["recommendations"])


# =============================================================================
# TRANSFORMATION RULES TESTS
# =============================================================================

class TestTransformationRules:
    def test_incomplete_rules(self):
        model = SuFieldModel(s1="workpiece", status="incomplete")
        analyzer = SuFieldAnalyzer()
        rules = analyzer.apply_transformation_rules(model)
        assert len(rules) > 0
        assert any("Complete" in r["name"] for r in rules)

    def test_harmful_rules(self):
        model = SuFieldModel(
            s1="bearing", s2="shaft", f=FieldType.MECHANICAL,
            status="harmful", harmful_effect="wear",
        )
        analyzer = SuFieldAnalyzer()
        rules = analyzer.apply_transformation_rules(model)
        assert len(rules) > 0
        assert any("Protect" in r["name"] or "harmful" in r["name"].lower() for r in rules)

    def test_insufficient_rules(self):
        model = SuFieldModel(
            s1="sample", s2="heater", f=FieldType.THERMAL,
            status="insufficient",
        )
        analyzer = SuFieldAnalyzer()
        rules = analyzer.apply_transformation_rules(model)
        assert len(rules) > 0
        assert any("Intensify" in r["name"] for r in rules)

    def test_enhancement_rules(self):
        model = SuFieldModel(
            s1="plate", s2="laser", f=FieldType.OPTICAL,
            status="complete",
        )
        analyzer = SuFieldAnalyzer()
        rules = analyzer.apply_transformation_rules(model)
        assert len(rules) > 0
        assert any("Super-System" in r["name"] for r in rules)

    def test_all_rules_have_c4_shift(self):
        for status in ["incomplete", "harmful", "insufficient", "complete"]:
            model = SuFieldModel(s1="a", s2="b", f=FieldType.MECHANICAL, status=status)
            analyzer = SuFieldAnalyzer()
            rules = analyzer.apply_transformation_rules(model)
            for rule in rules:
                assert "c4_shift" in rule
                assert rule["c4_shift"] in {"time_shift", "scale_shift", "agency_shift", "combined_shift"}


# =============================================================================
# FULL PIPELINE TESTS
# =============================================================================

class TestFullPipeline:
    def test_analyze_complete(self):
        text = "A magnetic field levitates a train above the tracks, eliminating friction."
        result = analyze_sufield(text)
        assert "model" in result
        assert "completeness" in result
        assert "transformations" in result
        assert "c4_mapping" in result
        assert result["model"]["is_complete"] is True

    def test_analyze_incomplete(self):
        text = "We need to detect cracks inside a ceramic component without destroying it."
        result = analyze_sufield(text)
        assert result["model"]["is_complete"] is False
        assert len(result["transformations"]) > 0

    def test_c4_mapping_present(self):
        text = "A laser cuts metal."
        result = analyze_sufield(text)
        c4 = result["c4_mapping"]
        assert "start_state" in c4
        assert "end_state" in c4
        assert "trajectory" in c4
        assert "shift_type" in c4


# =============================================================================
# TEXTBOOK EXAMPLES TESTS
# =============================================================================

class TestTextbookExamples:
    def test_all_textbook_examples_present(self):
        assert len(TEXTBOOK_SUFIELD_EXAMPLES) == 5

    def test_textbook_hammer_nail(self):
        ex = TEXTBOOK_SUFIELD_EXAMPLES[0]
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(ex["text"])
        assert model.status == "harmful"
        assert model.f == FieldType.MECHANICAL

    def test_textbook_laser_steel(self):
        ex = TEXTBOOK_SUFIELD_EXAMPLES[1]
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(ex["text"])
        assert model.status == "complete"
        assert model.f in (FieldType.OPTICAL, FieldType.THERMAL)

    def test_textbook_ceramic_crack(self):
        ex = TEXTBOOK_SUFIELD_EXAMPLES[2]
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(ex["text"])
        assert model.status == "incomplete"

    def test_textbook_resistor_heat(self):
        ex = TEXTBOOK_SUFIELD_EXAMPLES[3]
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(ex["text"])
        assert model.status == "harmful"
        assert model.f in (FieldType.ELECTRICAL, FieldType.THERMAL)

    def test_textbook_maglev(self):
        ex = TEXTBOOK_SUFIELD_EXAMPLES[4]
        analyzer = SuFieldAnalyzer()
        model = analyzer.extract(ex["text"])
        assert model.f == FieldType.MAGNETIC
        assert model.status == "complete"
