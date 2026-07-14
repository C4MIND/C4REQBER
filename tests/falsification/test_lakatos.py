"""Tests for Falsification Engine — Lakatos module."""

from __future__ import annotations

import pytest

from src.falsification.lakatos import (
    ProgrammeEvaluation,
    ResearchProgramme,
    evaluate_programme,
)


class TestResearchProgramme:
    def test_create_programme(self):
        rp = ResearchProgramme(
            name="Newtonian Mechanics",
            hard_core=["F=ma", "Action-Reaction"],
            protective_belt=["Friction models", "Elastic collision model"],
        )
        assert rp.name == "Newtonian Mechanics"
        assert len(rp.hard_core) == 2
        assert len(rp.protective_belt) == 2
        assert rp.novel_predictions == []
        assert rp.confirmed_predictions == []
        assert rp.anomalies == []

    def test_with_predictions_and_anomalies(self):
        rp = ResearchProgramme(
            name="Standard Model",
            hard_core=["SU(3)xSU(2)xU(1)"],
            protective_belt=["Higgs mechanism"],
            novel_predictions=["W boson", "Z boson", "Higgs boson", "Top quark"],
            confirmed_predictions=["W boson", "Z boson", "Top quark"],
            anomalies=["Neutrino mass", "Dark matter"],
        )
        assert len(rp.novel_predictions) == 4
        assert len(rp.confirmed_predictions) == 3
        assert len(rp.anomalies) == 2


class TestProgrammeEvaluation:
    def test_fields_match(self):
        ev = ProgrammeEvaluation(
            programme_name="Test",
            is_progressive=True,
            progress_score=0.8,
            anomaly_count=2,
            novel_prediction_count=10,
            recommendation="Continue funding",
        )
        assert ev.programme_name == "Test"
        assert ev.is_progressive is True
        assert ev.progress_score == 0.8


class TestEvaluateProgramme:
    def test_progressive_programme(self):
        rp = ResearchProgramme(
            name="Quantum Mechanics",
            hard_core=["Schrodinger equation"],
            protective_belt=["Born rule"],
            novel_predictions=["P1", "P2", "P3"],
            confirmed_predictions=["P1", "P2", "P3"],
            anomalies=["A1"],
        )
        result = evaluate_programme(rp)
        assert result.is_progressive is True
        assert result.recommendation == "Continue funding"

    def test_degenerating_programme(self):
        rp = ResearchProgramme(
            name="Phlogiston Theory",
            hard_core=["Phlogiston exists"],
            protective_belt=["Negative mass phlogiston"],
            novel_predictions=["P1", "P2", "P3", "P4", "P5"],
            confirmed_predictions=[],
            anomalies=["A1", "A2", "A3", "A4", "A5"],
        )
        result = evaluate_programme(rp)
        assert result.is_progressive is False
        assert result.recommendation == "Consider redirecting resources"

    def test_balanced_programme(self):
        rp = ResearchProgramme(
            name="Plate Tectonics",
            hard_core=["Continental drift"],
            protective_belt=["Subduction models"],
            novel_predictions=["P1", "P2", "P3"],
            confirmed_predictions=["P1", "P2"],
            anomalies=["A1"],
        )
        result = evaluate_programme(rp)
        assert result.progress_score == pytest.approx(2 / 3)

    def test_progress_score_zero(self):
        rp = ResearchProgramme(
            name="Empty",
            hard_core=["X"],
            protective_belt=["Y"],
            novel_predictions=[],
            confirmed_predictions=[],
            anomalies=[],
        )
        result = evaluate_programme(rp)
        assert result.progress_score == 0.0

    def test_progressive_by_margin(self):
        rp = ResearchProgramme(
            name="Darwinian Evolution",
            hard_core=["Natural selection"],
            protective_belt=["Genetics"],
            novel_predictions=[f"P{i}" for i in range(100)],
            confirmed_predictions=[f"P{i}" for i in range(90)],
            anomalies=[f"A{i}" for i in range(5)],
        )
        result = evaluate_programme(rp)
        assert result.is_progressive is True
        assert result.progress_score > 0.8

    def test_counts_are_correct(self):
        rp = ResearchProgramme(
            name="Test",
            hard_core=["Core"],
            protective_belt=["Belt"],
            novel_predictions=["N1", "N2"],
            confirmed_predictions=["N1"],
            anomalies=["A1", "A2", "A3"],
        )
        result = evaluate_programme(rp)
        assert result.novel_prediction_count == 2
        assert result.anomaly_count == 3

    def test_lakatos_threshold_behavior(self):
        rp = ResearchProgramme(
            name="Threshold",
            hard_core=["Core"],
            protective_belt=["Belt"],
            novel_predictions=["P1", "P2", "P3"],
            confirmed_predictions=["P1"],
            anomalies=["A1"],
        )
        result = evaluate_programme(rp)
        progress = 1 / 3
        anomaly_ratio = 1 / 2
        assert result.progress_score == pytest.approx(progress)
        assert result.is_progressive is (progress > anomaly_ratio)
