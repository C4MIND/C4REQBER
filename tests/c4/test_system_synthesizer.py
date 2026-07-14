"""Tests for SystemSynthesizer in src/c4/system_synthesizer.py

Pure-logic unit tests: NO MOCKS, NO NETWORK, NO LLM.
All router components use keyword-based fallback classification.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from c4_analysis.system_synthesizer import SYSTEMIC_INDICATORS, SystemSynthesizer


class TestSystemicIndicators:
    """Test SYSTEMIC_INDICATORS — the keyword patterns for systemic detection."""

    def test_indicators_are_non_empty(self):
        assert len(SYSTEMIC_INDICATORS) > 0

    def test_indicators_contain_causal_keywords(self):
        assert "causes" in SYSTEMIC_INDICATORS
        assert "leads to" in SYSTEMIC_INDICATORS
        assert "therefore" in SYSTEMIC_INDICATORS
        assert "feedback" in SYSTEMIC_INDICATORS

    def test_all_indicators_are_lowercase(self):
        for ind in SYSTEMIC_INDICATORS:
            assert ind == ind.lower(), f"Indicator '{ind}' is not lowercase"


class TestIsSystemic:
    """Test is_systemic: detecting systemic (interconnected) problem descriptions."""

    def test_causes_keyword_returns_true(self):
        synth = SystemSynthesizer()
        assert synth.is_systemic("pollution causes health problems") is True

    def test_leads_to_returns_true(self):
        synth = SystemSynthesizer()
        assert synth.is_systemic("climate change leads to mass migration") is True

    def test_feedback_returns_true(self):
        synth = SystemSynthesizer()
        assert synth.is_systemic("positive feedback loops in ecosystem collapse") is True

    def test_simple_query_returns_false(self):
        synth = SystemSynthesizer()
        assert synth.is_systemic("what is the capital of France") is False

    def test_plain_description_returns_false(self):
        synth = SystemSynthesizer()
        assert synth.is_systemic("the sky is blue on a clear day") is False

    def test_case_insensitive(self):
        synth = SystemSynthesizer()
        assert synth.is_systemic("Pollution CAUSES Health Problems") is True

    def test_interconnected_keyword(self):
        synth = SystemSynthesizer()
        assert synth.is_systemic("these are interconnected problems in a network of dependencies") is True


class TestSplitSystemic:
    """Test _split_systemic: decomposing systemic prompts by causal connectors."""

    def test_single_prompt_no_causal_connector(self):
        synth = SystemSynthesizer()
        parts = synth._split_systemic("explain quantum computing")
        assert len(parts) == 1

    def test_causes_connector_splits(self):
        synth = SystemSynthesizer()
        parts = synth._split_systemic(
            "pollution of water sources causes widespread health problems"
        )
        assert len(parts) >= 2

    def test_because_connector_splits(self):
        synth = SystemSynthesizer()
        parts = synth._split_systemic(
            "economic growth slowed because interest rates increased significantly"
        )
        assert len(parts) >= 2

    def test_fallback_and_split(self):
        synth = SystemSynthesizer()
        parts = synth._split_systemic(
            "study ocean acidification and research coral bleaching patterns"
        )
        assert len(parts) >= 2


class TestDecomposeAndMerge:
    """Test decompose_and_merge: full systemic analysis pipeline."""

    def test_basic_flow_systemic_problem(self):
        synth = SystemSynthesizer()
        result = synth.decompose_and_merge(
            "pollution of water sources causes widespread health problems in communities"
        )
        assert "systemic" in result
        assert "sub_paths" in result
        assert "intersections" in result
        assert "merged_path" in result
        assert "synthesis_points" in result
        assert "total_c4_states" in result
        assert "engines_engaged" in result
        assert "explanation" in result

    def test_non_systemic_returns_single_path(self):
        synth = SystemSynthesizer()
        result = synth.decompose_and_merge("explain gravity in simple terms")
        assert result["systemic"] is False
        assert len(result["sub_paths"]) == 1
        assert result["intersections"] == []

    def test_decompose_and_merge_systemic_is_true(self):
        synth = SystemSynthesizer()
        result = synth.decompose_and_merge(
            "deforestation causes soil erosion which leads to reduced agricultural yields"
        )
        assert result["systemic"] is True
        assert len(result["sub_paths"]) >= 2

    def test_merged_path_contains_states(self):
        synth = SystemSynthesizer()
        result = synth.decompose_and_merge(
            "carbon emissions drive global warming which causes ice caps to melt "
            "resulting in sea level rise"
        )
        assert result["total_c4_states"] > 0
        assert len(result["merged_path"]) > 0

    def test_single_problem_no_merging_needed(self):
        synth = SystemSynthesizer()
        result = synth.decompose_and_merge("how fast does light travel in a vacuum")
        assert result["systemic"] is False
        assert "no merging needed" in result["explanation"].lower()
