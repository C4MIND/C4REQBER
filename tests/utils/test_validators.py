"""
Tests for src/utils/validators.py
"""
from __future__ import annotations

import sys
from pathlib import Path


_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from src.utils.validators import (
    _validate_coq_basic,
    _validate_dafny_basic,
    _validate_lean4_basic,
    validate_hypothesis,
    validate_hypothesis_text,
    validate_proof,
    validate_required_fields,
    validate_simulation_config,
    validate_simulation_result,
)


class TestValidateHypothesis:
    def test_not_dict(self):
        result = validate_hypothesis("not a dict")
        assert result["valid"] is False
        assert "must be a dictionary" in result["errors"][0]

    def test_no_text_or_structured(self):
        result = validate_hypothesis({})
        assert result["valid"] is False
        assert "must have 'text' or be 'structured'" in result["errors"][0]

    def test_text_too_short(self):
        result = validate_hypothesis({"text": "short"})
        assert result["valid"] is False
        assert "too short" in result["errors"][0]

    def test_text_too_long_warning(self):
        result = validate_hypothesis({"text": "x" * 10001})
        assert result["valid"] is True
        assert any("very long" in w for w in result["warnings"])

    def test_non_string_text(self):
        result = validate_hypothesis({"text": 123})
        assert result["valid"] is False
        assert "must be a string" in result["errors"][0]

    def test_no_predictive_language(self):
        result = validate_hypothesis({"text": "This is a statement about something happening without any forecasting words"})
        assert result["valid"] is True
        assert any("falsifiable" in w for w in result["warnings"])

    def test_too_vague(self):
        result = validate_hypothesis({"text": "This shall forecast"})
        assert result["valid"] is True
        assert any("vague" in w for w in result["warnings"])

    def test_invalid_source(self):
        result = validate_hypothesis({"text": "This will predict something interesting", "source": 123})
        assert result["valid"] is False
        assert "source" in result["errors"][0]

    def test_invalid_confidence_type(self):
        result = validate_hypothesis({"text": "This will predict something", "confidence": "high"})
        assert result["valid"] is False
        assert "confidence" in result["errors"][0]

    def test_confidence_out_of_range(self):
        result = validate_hypothesis({"text": "This will predict something", "confidence": 1.5})
        assert result["valid"] is True
        assert any("between 0 and 1" in w for w in result["warnings"])

    def test_valid_hypothesis(self):
        result = validate_hypothesis({"text": "This will predict an interesting outcome when measured", "confidence": 0.8})
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["warnings"] == []

    def test_structured_hypothesis(self):
        result = validate_hypothesis({"structured": True})
        assert result["valid"] is True
        assert result["errors"] == []


class TestValidateHypothesisText:
    def test_not_string(self):
        result = validate_hypothesis_text(123)
        assert result["valid"] is False

    def test_too_short(self):
        result = validate_hypothesis_text("short")
        assert result["valid"] is False
        assert "too short" in result["errors"][0]

    def test_too_long(self):
        result = validate_hypothesis_text("x" * 10001)
        assert result["valid"] is True
        assert any("very long" in w for w in result["warnings"])

    def test_no_prediction(self):
        result = validate_hypothesis_text("This is just a statement")
        assert result["valid"] is True
        assert any("falsifiable" in w for w in result["warnings"])

    def test_too_vague(self):
        result = validate_hypothesis_text("This will predict")
        assert result["valid"] is True
        assert any("vague" in w for w in result["warnings"])

    def test_valid(self):
        result = validate_hypothesis_text("This will predict an interesting outcome when measured properly")
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["warnings"] == []


class TestValidateProof:
    def test_not_dict(self):
        result = validate_proof("not a dict")
        assert result["valid"] is False
        assert "must be a dictionary" in result["errors"][0]

    def test_missing_language(self):
        result = validate_proof({"proof": "some code"})
        assert result["valid"] is False
        assert "language" in result["errors"][0]

    def test_unsupported_language(self):
        result = validate_proof({"language": "python", "proof": "some code here"})
        assert result["valid"] is True
        assert any("Unsupported" in w for w in result["warnings"])

    def test_missing_proof(self):
        result = validate_proof({"language": "lean4"})
        assert result["valid"] is False
        assert "proof" in result["errors"][0]

    def test_non_string_proof(self):
        result = validate_proof({"language": "lean4", "proof": 123})
        assert result["valid"] is False
        assert "must be a string" in result["errors"][0]

    def test_proof_too_short(self):
        result = validate_proof({"language": "lean4", "proof": "short"})
        assert result["valid"] is False
        assert "too short" in result["errors"][0]

    def test_generated_not_bool(self):
        result = validate_proof({"language": "lean4", "proof": "theorem test : True := by trivial\nQed.", "generated": "yes"})
        assert result["valid"] is True
        assert any("boolean" in w for w in result["warnings"])

    def test_lean4_syntax_fail(self):
        result = validate_proof({"language": "lean4", "proof": "some random code"})
        assert result["valid"] is True
        assert any("syntax issues" in w for w in result["warnings"])

    def test_lean4_syntax_pass(self):
        result = validate_proof({"language": "lean4", "proof": "theorem test : True := by trivial\nQed."})
        assert result["valid"] is True
        assert not any("syntax issues" in w for w in result["warnings"])

    def test_coq_syntax_fail(self):
        result = validate_proof({"language": "coq", "proof": "random text"})
        assert result["valid"] is True
        assert any("syntax issues" in w for w in result["warnings"])

    def test_coq_syntax_pass(self):
        result = validate_proof({"language": "coq", "proof": "Theorem test : True.\nProof. trivial. Qed."})
        assert result["valid"] is True
        assert not any("syntax issues" in w for w in result["warnings"])

    def test_dafny_syntax_fail(self):
        result = validate_proof({"language": "dafny", "proof": "random text"})
        assert result["valid"] is True
        assert any("syntax issues" in w for w in result["warnings"])

    def test_dafny_syntax_pass(self):
        result = validate_proof({"language": "dafny", "proof": "method Test() { }"})
        assert result["valid"] is True
        assert not any("syntax issues" in w for w in result["warnings"])


class TestValidateSimulationConfig:
    def test_not_dict(self):
        result = validate_simulation_config("not a dict")
        assert result["valid"] is False

    def test_missing_domain(self):
        result = validate_simulation_config({})
        assert result["valid"] is False
        assert "domain" in result["errors"][0]

    def test_invalid_duration_type(self):
        result = validate_simulation_config({"domain": "physics", "duration": "long"})
        assert result["valid"] is False
        assert "duration" in result["errors"][0]

    def test_negative_duration(self):
        result = validate_simulation_config({"domain": "physics", "duration": -1})
        assert result["valid"] is False
        assert "positive" in result["errors"][0]

    def test_duration_too_large(self):
        result = validate_simulation_config({"domain": "physics", "duration": 1001})
        assert result["valid"] is True
        assert any("very large" in w for w in result["warnings"])

    def test_invalid_dt_type(self):
        result = validate_simulation_config({"domain": "physics", "dt": "small"})
        assert result["valid"] is False
        assert "dt" in result["errors"][0]

    def test_negative_dt(self):
        result = validate_simulation_config({"domain": "physics", "dt": -0.1})
        assert result["valid"] is False
        assert "positive" in result["errors"][0]

    def test_dt_too_large(self):
        result = validate_simulation_config({"domain": "physics", "dt": 2.0})
        assert result["valid"] is True
        assert any("large" in w for w in result["warnings"])

    def test_dt_gte_duration(self):
        result = validate_simulation_config({"domain": "physics", "duration": 1.0, "dt": 1.0})
        assert result["valid"] is False
        assert "less than" in result["errors"][0]

    def test_missing_pattern_id_and_engine(self):
        result = validate_simulation_config({"domain": "physics"})
        assert result["valid"] is True
        assert any("pattern_id" in w for w in result["warnings"])

    def test_invalid_hypothesis_type(self):
        result = validate_simulation_config({"domain": "physics", "hypothesis": 123})
        assert result["valid"] is False
        assert "hypothesis" in result["errors"][0]

    def test_unsupported_domain(self):
        result = validate_simulation_config({"domain": "alchemy"})
        assert result["valid"] is True
        assert any("may not be supported" in w for w in result["warnings"])

    def test_valid_config(self):
        result = validate_simulation_config({
            "domain": "physics",
            "duration": 10.0,
            "dt": 0.1,
            "pattern_id": "p1",
            "hypothesis": "test",
        })
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["warnings"] == []


class TestValidateSimulationResult:
    def test_not_dict(self):
        result = validate_simulation_result("not a dict")
        assert result["valid"] is False

    def test_error_status(self):
        result = validate_simulation_result({"status": "error", "error": "sim failed"})
        assert result["valid"] is False
        assert "sim failed" in result["errors"][0]

    def test_timeout_status(self):
        result = validate_simulation_result({"status": "timeout"})
        assert result["valid"] is True
        assert any("timed out" in w for w in result["warnings"])

    def test_invalid_time_steps_type(self):
        result = validate_simulation_result({"status": "success", "time_steps": "many"})
        assert result["valid"] is False
        assert "integer" in result["errors"][0]

    def test_negative_time_steps(self):
        result = validate_simulation_result({"status": "success", "time_steps": -1})
        assert result["valid"] is False
        assert "non-negative" in result["errors"][0]

    def test_valid_result(self):
        result = validate_simulation_result({"status": "success", "time_steps": 100})
        assert result["valid"] is True
        assert result["errors"] == []


class TestValidateRequiredFields:
    def test_missing_field(self):
        errors = validate_required_fields({}, ["name"])
        assert "Missing required field: name" in errors

    def test_wrong_type(self):
        errors = validate_required_fields({"name": 123}, ["name"], {"name": str})
        assert "must be of type str" in errors[0]

    def test_valid(self):
        errors = validate_required_fields({"name": "test", "age": 25}, ["name", "age"], {"name": str, "age": int})
        assert errors == []

    def test_optional_type_check(self):
        errors = validate_required_fields({"name": "test"}, ["name", "age"])
        assert "Missing required field: age" in errors
        assert len(errors) == 1


class TestInternalValidators:
    def test_lean4_no_keyword(self):
        assert _validate_lean4_basic("random text") is False

    def test_lean4_no_terminator(self):
        assert _validate_lean4_basic("theorem test") is False

    def test_lean4_valid(self):
        assert _validate_lean4_basic("theorem test : True := by trivial\nQed.") is True

    def test_coq_no_keyword(self):
        assert _validate_coq_basic("random text") is False

    def test_coq_no_qed(self):
        assert _validate_coq_basic("Theorem test.") is False

    def test_coq_defined(self):
        assert _validate_coq_basic("Theorem test. Proof. trivial. Defined.") is True

    def test_dafny_no_keyword(self):
        assert _validate_dafny_basic("random text") is False

    def test_dafny_no_braces(self):
        assert _validate_dafny_basic("method Test()") is False

    def test_dafny_valid(self):
        assert _validate_dafny_basic("method Test() { }") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
