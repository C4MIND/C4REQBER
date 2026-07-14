"""Tests for reproducibility validator module."""

from __future__ import annotations

import pytest

from src.reproducibility.validator import (
    ReproducibilityReport,
    compare_runs,
    compute_experiment_hash,
    validate_experiment,
    verify_result_match,
)


class TestComputeExperimentHash:
    def test_same_input_same_hash(self) -> None:
        h1 = compute_experiment_hash({"seed": 42})
        h2 = compute_experiment_hash({"seed": 42})
        assert h1 == h2

    def test_different_input_different_hash(self) -> None:
        h1 = compute_experiment_hash({"seed": 42})
        h2 = compute_experiment_hash({"seed": 43})
        assert h1 != h2

    def test_hash_is_string(self) -> None:
        h = compute_experiment_hash({"key": "value"})
        assert isinstance(h, str)
        assert len(h) == 8

    def test_hash_list_data(self) -> None:
        h = compute_experiment_hash([1, 2, 3])
        assert isinstance(h, str)
        assert len(h) == 8


class TestVerifyResultMatch:
    def test_exact_match(self) -> None:
        r = [{"a": 1.0, "b": 2.0}]
        e = [{"a": 1.0, "b": 2.0}]
        match, detail = verify_result_match(r, e)
        assert match is True
        assert "match" in detail

    def test_mismatched_count(self) -> None:
        r = [{"a": 1.0}]
        e = [{"a": 1.0}, {"a": 2.0}]
        match, detail = verify_result_match(r, e)
        assert match is False
        assert "Count mismatch" in detail

    def test_value_mismatch(self) -> None:
        r = [{"a": 1.0}]
        e = [{"a": 2.0}]
        match, _ = verify_result_match(r, e)
        assert match is False

    def test_within_tolerance(self) -> None:
        r = [{"a": 1.0000001}]
        e = [{"a": 1.0000002}]
        match, detail = verify_result_match(r, e, tolerance=1e-5)
        assert match is True

    def test_outside_tolerance(self) -> None:
        r = [{"a": 1.01}]
        e = [{"a": 1.00}]
        match, _ = verify_result_match(r, e, tolerance=1e-6)
        assert match is False

    def test_empty_results(self) -> None:
        match, detail = verify_result_match([], [])
        assert match is True

    def test_mixed_keys(self) -> None:
        r = [{"a": 1, "b": 2}]
        e = [{"a": 1, "c": 3}]
        match, _ = verify_result_match(r, e)
        assert match is True


class TestValidateExperiment:
    def test_fully_reproducible(self) -> None:
        config = {"seed": 42, "random_state": 123}
        results = [{"mean": 0.5, "std": 0.1}]
        expected = [{"mean": 0.5, "std": 0.1}]
        report = validate_experiment(config, results, expected)
        assert report.is_reproducible is True
        assert report.score >= 80

    def test_missing_seed(self) -> None:
        config = {"model": "gpt-4"}
        results: list[dict] = []
        expected: list[dict] = []
        report = validate_experiment(config, results, expected)
        assert report.is_reproducible is False
        assert report.score < 80

    def test_mismatched_results(self) -> None:
        config = {"seed": 42}
        results = [{"a": 1.0}]
        expected = [{"a": 2.0}]
        report = validate_experiment(config, results, expected)
        assert report.score < 80

    def test_no_expected_results(self) -> None:
        config = {"seed": 7}
        results = [{"a": 1.0}]
        expected: list[dict] = []
        report = validate_experiment(config, results, expected)
        assert report.is_reproducible is True
        assert report.score >= 80

    def test_report_has_all_fields(self) -> None:
        config = {"seed": 1}
        report = validate_experiment(config, [], [])
        d = report.to_dict()
        expected_keys = {"experiment_id", "checks", "is_reproducible", "score"}
        assert set(d.keys()) == expected_keys

    def test_score_is_float(self) -> None:
        config = {"seed": 42}
        report = validate_experiment(config, [], [])
        assert isinstance(report.score, float)
        assert 0.0 <= report.score <= 100.0


class TestCompareRuns:
    def test_identical_runs(self) -> None:
        run = [{"a": 1.0, "b": 2.0}]
        result = compare_runs(run, run)
        assert result["match"] is True
        assert result["identical_hashes"] is True

    def test_matching_values_different_order(self) -> None:
        run_a = [{"a": 1.0}]
        run_b = [{"a": 1.0}]
        result = compare_runs(run_a, run_b)
        assert result["match"] is True

    def test_different_runs(self) -> None:
        result = compare_runs([{"a": 1.0}], [{"a": 2.0}])
        assert result["match"] is False

    def test_hashes_present(self) -> None:
        result = compare_runs([{"x": 1}], [{"x": 1}])
        assert "run_a_hash" in result
        assert "run_b_hash" in result
        assert len(result["run_a_hash"]) == 8


class TestReproducibilityReport:
    def test_serialization(self) -> None:
        report = ReproducibilityReport(
            experiment_id="abc123",
            checks=[{"name": "seed_check", "passed": True}],
            is_reproducible=True,
            score=100.0,
        )
        d = report.to_dict()
        assert d["experiment_id"] == "abc123"
        assert d["is_reproducible"] is True
        assert d["checks"] == [{"name": "seed_check", "passed": True}]
