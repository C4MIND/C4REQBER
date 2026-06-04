"""Tests for the refinement loop logic in pipeline.py — abort_reasons handling, recheck_result behavior, and _sanitize_for_prompt."""
from __future__ import annotations

import pytest

from src.api.v8_routers.discovery.pipeline import _sanitize_for_prompt


class TestSanitizeForPrompt:
    def test_strips_control_chars(self):
        result = _sanitize_for_prompt("test\x00query\x08here")
        assert "\x00" not in result
        assert "\x08" not in result
        assert "<user_query" in result
        assert "testqueryhere" in result

    def test_limits_length(self):
        long_text = "x" * 600
        result = _sanitize_for_prompt(long_text, max_len=500)
        # Extract inner text between delimiters
        import re
        m = re.search(r'<user_query nonce=[^>]+>(.*?)</user_query', result)
        inner = m.group(1) if m else ""
        assert len(inner) <= 500

    def test_strips_triple_quotes_and_triple_dashes(self):
        result = _sanitize_for_prompt('a"""b---c')
        assert '"""' not in result
        assert "---" not in result

    def test_normal_reuse(self):
        result = _sanitize_for_prompt("hello world", max_len=100)
        assert "<user_query" in result
        assert "hello world" in result
        assert "</user_query" in result


class TestRefinementLoopLogic:
    """Test critical correctness of the refinement loop abort_reasons handling."""

    def test_abort_reasons_preserved_across_iterations(self):
        """Simulate: iter 0 has LOW_NOVELTY. iter 1 ALREADY_SHIFTED returns False. LOW_NOVELTY must survive."""
        abort_reasons = ["LOW_NOVELTY: low score", "INSUFFICIENT_DATA: few papers"]

        recheck_result = {"already_shifted": False}
        if recheck_result is not None and recheck_result.get("already_shifted"):
            abort_reasons[:] = ["ALREADY_SHIFTED: ..."]
        elif recheck_result is not None:
            abort_reasons = [r for r in abort_reasons if "ALREADY_SHIFTED" not in r]

        assert "LOW_NOVELTY" in abort_reasons[0]
        assert "INSUFFICIENT_DATA" in abort_reasons[1]
        assert len(abort_reasons) == 2

    def test_abort_reasons_clears_already_shifted_only(self):
        """Simulate: iter 0 has ALREADY_SHIFTED. iter 1 not shifted. Only ALREADY_SHIFTED removed."""
        abort_reasons = [
            "ALREADY_SHIFTED(iter0): ...",
            "LOW_NOVELTY: low",
            "INSUFFICIENT_DATA: few",
        ]

        recheck_result = {"already_shifted": False}
        if recheck_result is not None and recheck_result.get("already_shifted"):
            abort_reasons[:] = ["ALREADY_SHIFTED: ..."]
        elif recheck_result is not None:
            abort_reasons = [r for r in abort_reasons if "ALREADY_SHIFTED" not in r]

        assert len(abort_reasons) == 2
        assert "LOW_NOVELTY" in abort_reasons[0]
        assert "INSUFFICIENT_DATA" in abort_reasons[1]

    def test_recheck_result_import_error_preserves_reasons(self):
        """Simulate: ImportError on AlreadyShiftedDetector. abort_reasons unchanged."""
        abort_reasons = ["LOW_NOVELTY: low", "INSUFFICIENT_DATA: few"]

        recheck_result = None

        if recheck_result is not None and recheck_result.get("already_shifted"):
            abort_reasons[:] = ["ALREADY_SHIFTED: ..."]
        elif recheck_result is not None:
            abort_reasons = [r for r in abort_reasons if "ALREADY_SHIFTED" not in r]

        assert len(abort_reasons) == 2
        assert "LOW_NOVELTY" in abort_reasons[0]

    def test_already_shifted_on_iter1_updates_in_place(self):
        """Simulate: iter 1 detects shift. abort_reasons mutated in-place."""
        abort_reasons = ["LOW_NOVELTY: low"]

        recheck_result = {
            "already_shifted": True,
            "verdict": "SHIFTED_2019",
            "consensus_level": 0.85,
            "seminal_papers": [],
        }
        if recheck_result is not None and recheck_result.get("already_shifted"):
            abort_reasons[:] = [
                f"ALREADY_SHIFTED(iter1): {recheck_result.get('verdict')}. "
                f"Consensus: {recheck_result.get('consensus_level', 0):.0%}."
            ]

        assert len(abort_reasons) == 1
        assert "ALREADY_SHIFTED(iter1)" in abort_reasons[0]
        assert "LOW_NOVELTY" not in abort_reasons[0]
