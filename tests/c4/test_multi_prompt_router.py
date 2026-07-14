"""Tests for MultiPromptRouter in src/c4/multi_prompt_router.py

Pure-logic unit tests: NO MOCKS, NO NETWORK, NO LLM.
All router components (CognitiveRouter, CognitiveStateClassifier)
use keyword-based fallback classification.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from c4_analysis.multi_prompt_router import MultiPromptRouter


class TestMultiPromptRouterSplit:
    """Test _split: decomposing prompts into sub-problems."""

    def test_single_prompt_returns_single_part(self):
        router = MultiPromptRouter()
        result = router._split("explain quantum computing in detail")
        assert len(result) == 1
        assert "quantum" in result[0]

    def test_and_separator_splits_into_multiple(self):
        router = MultiPromptRouter()
        result = router._split("solve climate change and end world hunger now")
        assert len(result) >= 2
        assert any("climate" in p for p in result)
        assert any("hunger" in p for p in result)

    def test_plain_text_no_separator_returns_single(self):
        router = MultiPromptRouter()
        result = router._split("describe the process of photosynthesis")
        assert len(result) == 1

    def test_also_separator_splits(self):
        router = MultiPromptRouter()
        result = router._split("review this code also write better documentation")
        assert len(result) >= 2


class TestMultiPromptRouterVague:
    """Test _is_vague: detecting broad/underspecified prompts."""

    def test_short_prompt_is_vague(self):
        router = MultiPromptRouter()
        assert router._is_vague("hi") is True
        assert router._is_vague("what") is True

    def test_explore_without_specific_keyword_is_vague(self):
        router = MultiPromptRouter()
        assert router._is_vague("explore artificial intelligence") is True
        assert router._is_vague("investigate deep learning") is True

    def test_explore_with_specific_keyword_is_not_vague(self):
        router = MultiPromptRouter()
        assert router._is_vague("explore why gravity bends spacetime") is False

    def test_specific_question_is_not_vague(self):
        router = MultiPromptRouter()
        assert router._is_vague("how does dna replication work") is False
        assert router._is_vague("design a solar powered water purifier") is False


class TestMultiPromptRouterGoal:
    """Test _is_goal: detecting user intent signals."""

    def test_i_want_to_is_goal(self):
        router = MultiPromptRouter()
        assert router._is_goal("i want to learn quantum physics") is True

    def test_help_me_is_goal(self):
        router = MultiPromptRouter()
        assert router._is_goal("help me write a python script") is True

    def test_how_to_is_goal(self):
        router = MultiPromptRouter()
        assert router._is_goal("how to train a neural network") is True

    def test_declarative_statement_is_not_goal(self):
        router = MultiPromptRouter()
        assert router._is_goal("quantum entanglement is a physical phenomenon") is False


class TestMultiPromptRouterRoute:
    """Test route(): end-to-end prompt routing through C4 space."""

    def test_single_prompt_returns_single_route(self):
        router = MultiPromptRouter()
        result = router.route(
            "explain the theory of special relativity in simple terms"
        )
        assert result["total_paths"] == 1
        assert result["clarification_needed"] is False
        assert len(result["sub_problems"]) == 1
        assert "merged_c4" in result

    def test_and_separator_returns_multiple_routes(self):
        router = MultiPromptRouter()
        result = router.route(
            "solve the climate change crisis and end global poverty permanently"
        )
        assert result["total_paths"] >= 2
        assert len(result["sub_problems"]) >= 2
        assert result["clarification_needed"] is False

    def test_plain_text_no_and_returns_one_route(self):
        router = MultiPromptRouter()
        result = router.route(
            "describe the mathematical foundations of group theory"
        )
        assert result["total_paths"] == 1
        assert len(result["sub_problems"]) == 1

    def test_vague_prompt_requests_clarification(self):
        router = MultiPromptRouter()
        result = router.route("explore")
        assert result["clarification_needed"] is True
        assert result["sub_problems"] == []

    def test_result_contains_all_expected_keys(self):
        router = MultiPromptRouter()
        result = router.route("explain entropy in thermodynamics")
        for key in ("prompt", "sub_problems", "merged_c4", "total_paths",
                     "explanation", "clarification_needed"):
            assert key in result, f"Missing key: {key}"
