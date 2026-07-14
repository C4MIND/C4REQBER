"""Tests for meta_layer ethics module."""
from __future__ import annotations

import pytest

from src.meta_layer.ethics import (
    ETHICS_CHECKLIST,
    EthicsCheck,
    EthicsReport,
    run_ethics_check,
)


class TestEthicsCheck:
    def test_create_check_passed(self):
        check = EthicsCheck(name="bias_assessment", passed=True, score=0.9, details="ok")
        assert check.name == "bias_assessment"
        assert check.passed is True
        assert check.score == 0.9
        assert check.details == "ok"

    def test_create_check_failed(self):
        check = EthicsCheck(name="safety", passed=False, score=0.4, details="bad")
        assert check.passed is False
        assert check.score == 0.4

    def test_default_details(self):
        check = EthicsCheck(name="test", passed=True, score=1.0)
        assert check.details == ""


class TestEthicsReport:
    def test_create_report(self):
        checks = [
            EthicsCheck(name="bias_assessment", passed=True, score=0.9),
        ]
        report = EthicsReport(checks=checks, overall_score=90.0, recommendations=["ok"])
        assert len(report.checks) == 1
        assert report.overall_score == 90.0
        assert report.recommendations == ["ok"]

    def test_all_checks_passed_recommendation(self):
        report = EthicsReport(checks=[], overall_score=100.0, recommendations=["All checks passed"])
        assert "All checks passed" in report.recommendations


class TestRunEthicsCheck:
    def test_all_optimal_pass(self):
        report = run_ethics_check({
            "explainability": True,
            "no_bias": True,
            "no_pii": True,
            "fair": True,
            "safety_on": True,
        })
        assert report.overall_score > 0
        assert len(report.checks) == 5
        assert all(c.passed for c in report.checks)
        assert "All checks passed" in report.recommendations

    def test_default_context_has_failures(self):
        report = run_ethics_check({})
        failed = [c for c in report.checks if not c.passed]
        assert len(failed) >= 1

    def test_transparency_fails_without_explainability(self):
        report = run_ethics_check({"explainability": False})
        transparency = next(c for c in report.checks if c.name == "transparency")
        assert transparency.passed is False
        assert transparency.score == 0.5
        assert any(
            "explainability" in r.lower() for r in report.recommendations
        )

    def test_privacy_fails_with_pii(self):
        report = run_ethics_check({"no_pii": False})
        privacy = next(c for c in report.checks if c.name == "privacy")
        assert privacy.passed is False
        assert privacy.score == 0.3

    def test_safety_fails_when_disabled(self):
        report = run_ethics_check({"safety_on": False})
        safety = next(c for c in report.checks if c.name == "safety")
        assert safety.passed is False
        assert safety.score == 0.4

    def test_bias_fails_when_bias_detected(self):
        report = run_ethics_check({"no_bias": False})
        bias = next(c for c in report.checks if c.name == "bias_assessment")
        assert bias.passed is False
        assert bias.score == 0.4

    def test_fairness_fails_when_unfair(self):
        report = run_ethics_check({"fair": False})
        fairness = next(c for c in report.checks if c.name == "fairness")
        assert fairness.passed is False
        assert fairness.score == 0.6

    def test_multiple_failures(self):
        report = run_ethics_check({
            "explainability": False,
            "no_pii": False,
            "safety_on": False,
        })
        failed = [c for c in report.checks if not c.passed]
        assert len(failed) == 3
        assert len(report.recommendations) == 3

    def test_overall_score_range(self):
        report = run_ethics_check({})
        assert 0 <= report.overall_score <= 100

    def test_overall_score_with_all_disabled(self):
        report = run_ethics_check({
            "explainability": False,
            "no_pii": False,
            "safety_on": False,
            "no_bias": False,
            "fair": False,
        })
        assert report.overall_score < 60

    def test_weighted_score_proportional(self):
        report_all_on = run_ethics_check({
            "explainability": True,
            "no_bias": True,
            "no_pii": True,
            "fair": True,
            "safety_on": True,
        })
        report_all_off = run_ethics_check({
            "explainability": False,
            "no_bias": False,
            "no_pii": False,
            "fair": False,
            "safety_on": False,
        })
        assert report_all_on.overall_score > report_all_off.overall_score


class TestEthicsChecklist:
    def test_checklist_has_five_items(self):
        assert len(ETHICS_CHECKLIST) == 5

    def test_weights_sum_to_one(self):
        total_weight = sum(w for _, _, w in ETHICS_CHECKLIST)
        assert abs(total_weight - 1.0) < 0.01

    def test_checklist_names_unique(self):
        names = [n for n, _, _ in ETHICS_CHECKLIST]
        assert len(names) == len(set(names))
