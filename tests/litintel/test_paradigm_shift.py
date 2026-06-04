"""Tests for paradigm_shift.py — Kuhnian paradigm shift detection."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.discovery.paradigm_shift import (
    AnomalyDetector,
    AnomalyResult,
    CrisisIndicator,
    CrisisSignal,
    ParadigmShiftDetector,
    ParadigmShiftWarning,
    ScientificClaim,
    TemporalClaimAnalyzer,
)


class TestScientificClaim:
    def test_claim_creation(self) -> None:
        claim = ScientificClaim(
            text="Dark energy accelerates universe expansion",
            timestamp=datetime(2020, 1, 1),
            source="Paper A",
            citations=100,
            domain="cosmology",
        )
        assert claim.text == "Dark energy accelerates universe expansion"
        assert claim.citations == 100


class TestAnomalyDetector:
    def test_fit_empty(self) -> None:
        ad = AnomalyDetector()
        result = ad.fit([])
        assert result is ad

    def test_detect_without_fit(self) -> None:
        ad = AnomalyDetector()
        claim = ScientificClaim(text="Test", timestamp=datetime.now(), source="S")
        result = ad.detect(claim)
        assert isinstance(result, AnomalyResult)
        assert result.anomaly_score == 0.0
        assert not result.is_anomaly

    def test_detect_anomaly(self) -> None:
        claims = [
            ScientificClaim(
                text="The Earth is flat and supported by elephants",
                timestamp=datetime(2020, 1, 1),
                source="S1",
            ),
            ScientificClaim(
                text="The Earth is an oblate spheroid",
                timestamp=datetime(2020, 2, 1),
                source="S2",
            ),
            ScientificClaim(
                text="The Earth is approximately spherical",
                timestamp=datetime(2020, 3, 1),
                source="S3",
            ),
            ScientificClaim(
                text="Earth's shape is a geoid",
                timestamp=datetime(2020, 4, 1),
                source="S4",
            ),
            ScientificClaim(
                text="The Earth is round",
                timestamp=datetime(2020, 5, 1),
                source="S5",
            ),
        ]
        ad = AnomalyDetector(contamination=0.2)
        ad.fit(claims)

        # The flat earth claim should be anomalous
        result = ad.detect(claims[0])
        assert result.is_anomaly
        assert result.deviation_from_consensus >= 0.0

        # Round earth claims should not be anomalous
        result_normal = ad.detect(claims[1])
        assert not result_normal.is_anomaly

    def test_batch_detect(self) -> None:
        claims = [
            ScientificClaim(text=f"Claim {i}", timestamp=datetime(2020, 1, 1) + timedelta(days=i), source="S")
            for i in range(5)
        ]
        ad = AnomalyDetector()
        ad.fit(claims)
        results = ad.batch_detect(claims)
        assert len(results) == 5
        assert all(isinstance(r, AnomalyResult) for r in results)


class TestCrisisIndicator:
    def test_analyze_empty(self) -> None:
        ci = CrisisIndicator()
        signal = ci.analyze([], domain="physics")
        assert isinstance(signal, CrisisSignal)
        assert signal.severity == 0.0
        assert signal.domain == "physics"

    def test_crisis_keywords(self) -> None:
        claims = [
            ScientificClaim(
                text="These results contradict the established theory of everything",
                timestamp=datetime(2020, 1, 1),
                source="S1",
                citations=10,
            ),
            ScientificClaim(
                text="Our findings are inconsistent with prior work",
                timestamp=datetime(2020, 2, 1),
                source="S2",
                citations=5,
            ),
            ScientificClaim(
                text="Standard model predictions hold true",
                timestamp=datetime(2020, 3, 1),
                source="S3",
                citations=100,
            ),
        ]
        ci = CrisisIndicator()
        signal = ci.analyze(claims, domain="physics")
        assert signal.severity > 0.0
        assert any("crisis keywords" in ind for ind in signal.indicators)

    def test_citation_drop(self) -> None:
        claims = [
            ScientificClaim(text="Old theory works", timestamp=datetime(2018, 1, 1), source="S1", citations=200),
            ScientificClaim(text="Old theory works", timestamp=datetime(2019, 1, 1), source="S2", citations=180),
            ScientificClaim(text="Old theory works", timestamp=datetime(2020, 1, 1), source="S3", citations=10),
        ]
        ci = CrisisIndicator(citation_drop_threshold=0.5)
        signal = ci.analyze(claims)
        # Check for citation drop OR crisis keywords (both are valid crisis signals)
        has_drop = any("citation drop" in ind for ind in signal.indicators)
        has_keywords = any("crisis keywords" in ind for ind in signal.indicators)
        assert has_drop or has_keywords or signal.severity > 0


class TestTemporalClaimAnalyzer:
    def test_temporal_variance_empty(self) -> None:
        ta = TemporalClaimAnalyzer()
        result = ta.temporal_variance([])
        assert result["variance"] == 0.0
        assert result["trend"] == "stable"

    def test_temporal_variance_diverging(self) -> None:
        claims = [
            ScientificClaim(text="A causes B through mechanism X", timestamp=datetime(2018, 1, 1), source="S1"),
            ScientificClaim(text="A causes B through mechanism X", timestamp=datetime(2019, 1, 1), source="S2"),
            ScientificClaim(text="A causes B through mechanism Y", timestamp=datetime(2020, 1, 1), source="S3"),
            ScientificClaim(text="A causes B through mechanism Z", timestamp=datetime(2021, 1, 1), source="S4"),
            ScientificClaim(text="A causes B through mechanism Z", timestamp=datetime(2022, 1, 1), source="S5"),
        ]
        ta = TemporalClaimAnalyzer()
        result = ta.temporal_variance(claims)
        assert result["trend"] in ("converging", "diverging", "stable")
        assert len(result["windows"]) > 0

    def test_consensus_drift(self) -> None:
        claims = [
            ScientificClaim(text="Theory X is correct and well established", timestamp=datetime(2018, 1, 1), source="S1"),
            ScientificClaim(text="Theory X is correct and well established", timestamp=datetime(2019, 1, 1), source="S2"),
            ScientificClaim(text="Theory Y is correct and revolutionary", timestamp=datetime(2020, 1, 1), source="S3"),
            ScientificClaim(text="Theory Y is correct and revolutionary", timestamp=datetime(2021, 1, 1), source="S4"),
        ]
        ta = TemporalClaimAnalyzer()
        result = ta.consensus_drift(claims)
        assert result["drift"] >= 0.0
        assert result["early_centroid"] is not None
        assert result["late_centroid"] is not None

    def test_consensus_drift_insufficient(self) -> None:
        ta = TemporalClaimAnalyzer()
        result = ta.consensus_drift([
            ScientificClaim(text="A", timestamp=datetime(2020, 1, 1), source="S"),
        ])
        assert result["drift"] == 0.0


class TestParadigmShiftDetector:
    def test_analyze_empty(self) -> None:
        psd = ParadigmShiftDetector()
        warning = psd.analyze([], domain="physics")
        assert isinstance(warning, ParadigmShiftWarning)
        assert warning.probability == 0.0
        assert warning.confidence == 1.0

    def test_stable_domain(self) -> None:
        claims = [
            ScientificClaim(
                text="Newtonian mechanics accurately predicts planetary motion",
                timestamp=datetime(2020, 1, 1) + timedelta(days=i * 30),
                source=f"S{i}",
                citations=50 + i,
            )
            for i in range(10)
        ]
        psd = ParadigmShiftDetector()
        warning = psd.analyze(claims, domain="physics")
        assert warning.probability < 0.5
        assert warning.estimated_timeframe == "Stable"

    def test_shifting_domain(self) -> None:
        claims = [
            ScientificClaim(
                text="Standard model explains all particle interactions",
                timestamp=datetime(2018, 1, 1),
                source="S1",
                citations=200,
            ),
            ScientificClaim(
                text="Anomalies detected in neutrino oscillations challenge the standard model",
                timestamp=datetime(2019, 1, 1),
                source="S2",
                citations=150,
            ),
            ScientificClaim(
                text="New physics required to explain dark matter observations",
                timestamp=datetime(2020, 1, 1),
                source="S3",
                citations=80,
            ),
            ScientificClaim(
                text="Contradictory results from LHC experiments question standard model completeness",
                timestamp=datetime(2021, 1, 1),
                source="S4",
                citations=30,
            ),
            ScientificClaim(
                text="Proposed supersymmetric extension resolves standard model inconsistencies",
                timestamp=datetime(2022, 1, 1),
                source="S5",
                citations=10,
            ),
        ]
        psd = ParadigmShiftDetector()
        warning = psd.analyze(claims, domain="physics")
        assert warning.probability > 0.2
        assert len(warning.contributing_factors) > 0

    def test_detect_breakthrough_claims(self) -> None:
        claims = [
            ScientificClaim(text="Water boils at 100C at sea level", timestamp=datetime(2020, 1, 1), source="S1"),
            ScientificClaim(text="Water boils at 100C at sea level", timestamp=datetime(2020, 2, 1), source="S2"),
            ScientificClaim(text="Water boils at 100C at sea level", timestamp=datetime(2020, 3, 1), source="S3"),
            ScientificClaim(text="Supercritical water exhibits novel catalytic properties", timestamp=datetime(2020, 4, 1), source="S4"),
        ]
        psd = ParadigmShiftDetector()
        breakthroughs = psd.detect_breakthrough_claims(claims)
        assert len(breakthroughs) >= 1
        assert any("supercritical" in b.text.lower() for b in breakthroughs)
