from __future__ import annotations

import pytest

from src.discovery.kuhn_criteria import KuhnCriteria, ParadigmShiftAssessment


class TestKuhnCriteria:
    def test_assess_empty_inputs_returns_valid_assessment(self):
        discovery: dict = {}
        gaps: list[dict] = []
        hypotheses: list[dict] = []
        verification: dict = {}
        novelty: dict = {}

        result = KuhnCriteria.assess(discovery, gaps, hypotheses, verification, novelty)
        assert isinstance(result, ParadigmShiftAssessment)
        assert isinstance(result.stage, str)
        assert len(result.stage) > 0
        assert 0.0 <= result.stage_confidence <= 1.0
        assert 0.0 <= result.paradigm_shift_score <= 1.0
        assert isinstance(result.is_paradigm_shift, bool)

    def test_high_anomaly_content_category_a(self):
        gaps = [
            {
                "area": "contradiction in standard model",
                "evidence": "The experimental results falsifies the existing theory. This contradiction remains unresolved.",
                "novelty_score": 0.9,
                "hypothesis_seed": "A new framework is needed",
            },
            {
                "area": "paradox in quantum foundations",
                "evidence": "This paradox cannot explain observed entanglement patterns.",
                "novelty_score": 0.85,
                "hypothesis_seed": "Non-local hidden variables may resolve",
            },
            {
                "area": "inconsistent cosmological data",
                "evidence": "The data violates standard predictions and fundamentally incompatible with Lambda-CDM.",
                "novelty_score": 0.95,
                "hypothesis_seed": "Modified gravity theory",
            },
            {
                "area": "unexplained biological pathway",
                "evidence": "This breaks the central dogma of molecular biology.",
                "novelty_score": 0.9,
                "hypothesis_seed": "Reverse information flow mechanism",
            },
        ]
        hypotheses = [
            {"title": "A novel quantum gravity paradigm reframing spacetime", "confidence": 0.9},
            {"title": "Revolutionary reinterpretation of biological inheritance", "confidence": 0.85},
        ]
        discovery = {"domain": "theoretical physics"}
        verification = {"passed": True, "status": "verified"}
        novelty = {"shift_detected": True, "confidence": 0.8, "score": 0.85}

        result = KuhnCriteria.assess(discovery, gaps, hypotheses, verification, novelty)
        assert result.anomaly_count >= 1
        assert result.anomaly_severity > 0.6
        assert result.paradigm_shift_score > 0.5

    def test_qualitative_text_category_c(self):
        gaps = [
            {
                "area": "understanding of basic mechanism",
                "evidence": "The mechanism is well established and widely accepted.",
                "novelty_score": 0.2,
                "hypothesis_seed": "Further refinement possible",
            }
        ]
        hypotheses = [
            {"title": "A small improvement to existing model", "confidence": 0.4},
            {"title": "Minor refinement of current theory", "confidence": 0.35},
        ]
        discovery = {"domain": "basic science"}
        verification = {"passed": False, "status": "unverified"}
        novelty = {"shift_detected": False, "confidence": 0.1, "score": 0.2}

        result = KuhnCriteria.assess(discovery, gaps, hypotheses, verification, novelty)
        assert result.anomaly_count == 0
        assert result.anomaly_severity < 0.5
        assert result.paradigm_shift_score <= 0.6
        assert result.is_paradigm_shift is False

    def test_paradigm_shift_score_between_zero_and_one(self):
        gaps = [
            {
                "area": "test gap",
                "evidence": "remains unclear paradox",
                "novelty_score": 0.5,
                "hypothesis_seed": "test hypothesis",
            }
        ]
        hypotheses = [{"title": "A test hypothesis title", "confidence": 0.6}]
        discovery = {"domain": "test"}
        verification = {"passed": True, "status": "verified"}
        novelty = {"shift_detected": False, "score": 0.4}

        result = KuhnCriteria.assess(discovery, gaps, hypotheses, verification, novelty)
        assert 0.0 <= result.paradigm_shift_score <= 1.0

    def test_is_paradigm_shift_matches_score_threshold(self):
        gaps = [
            {
                "area": "fundamental contradiction in theory",
                "evidence": "Experimental data falsifies the core tenet of the theory. The anomaly challenges fundamental assumptions.",
                "novelty_score": 0.95,
                "hypothesis_seed": "Complete theoretical overhaul",
            },
            {
                "area": "paradox in framework assumptions",
                "evidence": "The framework cannot explain key observations and violates established principles.",
                "novelty_score": 0.9,
                "hypothesis_seed": "New axioms required",
            },
            {
                "area": "unexplained phenomenon in classical domain",
                "evidence": "This fundamentally incompatible observation breaks the existing classification.",
                "novelty_score": 0.88,
                "hypothesis_seed": "Category expansion needed",
            },
        ]
        hypotheses = [
            {"title": "paradigm reframing of fundamental physics see differently", "confidence": 0.92},
            {"title": "new perspective on gestalt theoretical foundations", "confidence": 0.88},
            {"title": "reinterpretation of cosmological framework structure paradigm", "confidence": 0.90},
        ]
        discovery = {"domain": "foundations of physics"}
        verification = {"passed": True, "status": "verified"}
        novelty = {"shift_detected": True, "confidence": 0.85, "score": 0.9}

        result = KuhnCriteria.assess(discovery, gaps, hypotheses, verification, novelty)
        assert isinstance(result.paradigm_shift_score, float)
        if result.paradigm_shift_score > 0.6:
            assert result.is_paradigm_shift is True
        else:
            assert result.is_paradigm_shift is False

    def test_empty_inputs_stage_is_normal_science(self):
        discovery: dict = {}
        gaps: list[dict] = []
        hypotheses: list[dict] = []
        verification: dict = {}
        novelty: dict = {}

        result = KuhnCriteria.assess(discovery, gaps, hypotheses, verification, novelty)
        assert result.stage == "normal_science"
        assert result.anomaly_count == 0

    def test_crisis_stage_with_indicators(self):
        gaps = [
            {
                "area": "proliferation of competing models in dark energy",
                "evidence": "There is proliferation of competing explanations and debate over fundamentals. Researchers show willingness to try anything.",
                "novelty_score": 0.9,
                "hypothesis_seed": "Unified dark sector model",
            },
            {
                "area": "explicit discontent with standard cosmology",
                "evidence": "Many researchers express explicit discontent and questioning the paradigm. There is loss of confidence.",
                "novelty_score": 0.88,
                "hypothesis_seed": "New cosmological paradigm",
            },
            {
                "area": "recourse to philosophy in quantum foundations",
                "evidence": "Leading physicists show recourse to philosophy and pushing boundaries of current theory.",
                "novelty_score": 0.92,
                "hypothesis_seed": "Information-theoretic foundation",
            },
        ]
        hypotheses = [
            {"title": "extraordinary research program for new physics", "confidence": 0.9},
            {"title": "paradigm shift in cosmological model", "confidence": 0.85},
        ]
        discovery = {"domain": "cosmology"}
        verification = {"passed": False, "status": "partial"}
        novelty = {"shift_detected": True, "confidence": 0.75, "score": 0.8}

        result = KuhnCriteria.assess(discovery, gaps, hypotheses, verification, novelty)
        assert len(result.crisis_indicators) >= 1
        assert result.stage in ("crisis", "anomaly_accumulation", "revolution")
