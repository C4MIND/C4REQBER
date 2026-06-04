"""Tests for C4Result standardized return type and validate_result."""
from __future__ import annotations

import pytest

from src.c4.result import C4Result, validate_result


class TestValidateResult:
    def test_valid_success(self) -> None:
        result = validate_result({"status": "success", "data": {"key": "value"}})
        assert result["status"] == "success"
        assert result["data"] == {"key": "value"}

    def test_valid_error(self) -> None:
        result = validate_result({"status": "error", "errors": ["Something went wrong"]})
        assert result["status"] == "error"
        assert result["errors"] == ["Something went wrong"]

    def test_valid_partial(self) -> None:
        result = validate_result({"status": "partial", "data": {"partial": True}, "warnings": ["Missing data"]})
        assert result["status"] == "partial"

    def test_valid_not_applicable(self) -> None:
        result = validate_result({"status": "not_applicable"})
        assert result["status"] == "not_applicable"

    def test_invalid_status(self) -> None:
        with pytest.raises(ValueError, match="Invalid status"):
            validate_result({"status": "unknown_status"})

    def test_error_requires_errors(self) -> None:
        with pytest.raises(ValueError, match="non-empty 'errors'"):
            validate_result({"status": "error"})

    def test_success_requires_data(self) -> None:
        with pytest.raises(ValueError, match="requires 'data'"):
            validate_result({"status": "success"})

    def test_empty_status_passes(self) -> None:
        result = validate_result({"data": {"key": "value"}})
        assert result["data"] == {"key": "value"}

    def test_non_dict_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected dict"):
            validate_result([1, 2, 3])

    def test_invalid_errors_type(self) -> None:
        with pytest.raises(ValueError, match="'errors' must be a list"):
            validate_result({"status": "error", "errors": "not a list"})

    def test_invalid_warnings_type(self) -> None:
        with pytest.raises(ValueError, match="'warnings' must be a list"):
            validate_result({"status": "success", "data": {}, "warnings": "not a list"})

    def test_invalid_metadata_type(self) -> None:
        with pytest.raises(ValueError, match="'metadata' must be a dict"):
            validate_result({"status": "success", "data": {}, "metadata": "not a dict"})

    def test_full_c4result(self) -> None:
        result = validate_result({
            "status": "success",
            "data": {"key": "value"},
            "metadata": {"timing_ms": 42, "c4_state": "C1"},
            "warnings": ["deprecated field"],
        })
        assert result["status"] == "success"
        assert result["metadata"]["timing_ms"] == 42
