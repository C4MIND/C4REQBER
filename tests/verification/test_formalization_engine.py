"""Tests for FormalizationEngine."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.verification.formalization_engine import (
    FormalizationEngine,
    FormalizationResult,
    _sanitize_for_prompt,
)



class TestSanitizeForPrompt:
    def test_strips_control_chars(self) -> None:
        result = _sanitize_for_prompt("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_strips_bidi_overrides(self) -> None:
        result = _sanitize_for_prompt("hello\u202eworld")
        assert "\u202e" not in result

    def test_neutralizes_role_tags(self) -> None:
        result = _sanitize_for_prompt("<system>alert</system>")
        assert "<system>" not in result
        assert "[SYSTEM_TAG_REMOVED]" in result

    def test_limits_length(self) -> None:
        long_text = "a" * 3000
        result = _sanitize_for_prompt(long_text, max_len=100)
        assert len(result) == 100


class TestFormalizationResult:
    def test_defaults(self) -> None:
        r = FormalizationResult()
        assert r.theorem_statement == ""
        assert r.assumptions == []
        assert r.formalizability_score == 0.0

    def test_to_dict(self) -> None:
        r = FormalizationResult(
            theorem_statement="forall x, P(x)",
            assumptions=["A1", "A2"],
            domain="mathematics",
            formalizability_score=0.85,
        )
        d = r.to_dict()
        assert d["theorem_statement"] == "forall x, P(x)"
        assert d["formalizability_score"] == 0.85
        assert d["not_formalizable_reason"] is None


class TestFormalizationEngine:
    @pytest.mark.anyio(backend="asyncio")
    async def test_formalize_success(self) -> None:
        engine = FormalizationEngine()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "theorem_statement": "forall n : Nat, n + 0 = n",
            "assumptions": ["n is a natural number"],
            "domain": "mathematics",
            "formalizability_score": 0.9,
        })

        with patch.object(
            engine._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await engine.formalize({"text": "Adding zero to a number gives the same number"})

        assert result.formalizability_score == 0.9
        assert result.theorem_statement == "forall n : Nat, n + 0 = n"
        assert result.domain == "mathematics"
        assert result.not_formalizable_reason is None

    @pytest.mark.anyio(backend="asyncio")
    async def test_formalize_not_formalizable(self) -> None:
        engine = FormalizationEngine()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "theorem_statement": "",
            "assumptions": [],
            "domain": "",
            "formalizability_score": 0.1,
            "not_formalizable_reason": "Too vague",
        })

        with patch.object(
            engine._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await engine.formalize({"text": "Something about stuff"})

        assert result.formalizability_score == 0.1
        assert result.not_formalizable_reason == "Too vague"
        assert result.theorem_statement == ""

    @pytest.mark.anyio(backend="asyncio")
    async def test_formalize_json_parse_error(self) -> None:
        engine = FormalizationEngine()
        mock_response = MagicMock()
        mock_response.content = "not valid json"

        with patch.object(
            engine._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await engine.formalize({"text": "test"})

        assert result.formalizability_score == 0.0
        assert "JSON parse error" in (result.not_formalizable_reason or "")

    @pytest.mark.anyio(backend="asyncio")
    async def test_formalize_llm_error(self) -> None:
        engine = FormalizationEngine()
        with patch.object(
            engine._router, "generate_for_stage", new_callable=AsyncMock, side_effect=RuntimeError("API down")
        ):
            result = await engine.formalize({"text": "test"})

        assert result.formalizability_score == 0.0
        assert "API down" in (result.not_formalizable_reason or "")

    @pytest.mark.anyio(backend="asyncio")
    async def test_formalize_with_evidence(self) -> None:
        engine = FormalizationEngine()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "theorem_statement": "T",
            "assumptions": [],
            "domain": "physics",
            "formalizability_score": 0.8,
        })

        with patch.object(
            engine._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ) as mock_gen:
            result = await engine.formalize(
                {"text": "Gravity affects time"},
                evidence=["Paper A", "Paper B"],
            )

        assert result.formalizability_score == 0.8
        prompt = mock_gen.call_args[1]["prompt"]
        assert "Paper A" in prompt
        assert "Paper B" in prompt

    @pytest.mark.anyio(backend="asyncio")
    async def test_formalize_extracts_json_from_markdown(self) -> None:
        engine = FormalizationEngine()
        mock_response = MagicMock()
        mock_response.content = """Here is the result:
```json
{
  "theorem_statement": "test",
  "assumptions": [],
  "domain": "math",
  "formalizability_score": 0.75
}
```
"""

        with patch.object(
            engine._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await engine.formalize({"text": "test"})

        assert result.formalizability_score == 0.75
        assert result.theorem_statement == "test"
