"""Tests for SemanticAlignmentChecker."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.verification.semantic_alignment import AlignmentResult, SemanticAlignmentChecker



class TestAlignmentResult:
    def test_to_dict(self) -> None:
        r = AlignmentResult(aligned=True, explanation="Proof matches theorem", confidence=0.95)
        d = r.to_dict()
        assert d["aligned"] is True
        assert d["confidence"] == 0.95


class TestSemanticAlignmentChecker:
    @pytest.mark.anyio(backend="asyncio")
    async def test_empty_inputs(self) -> None:
        checker = SemanticAlignmentChecker()
        result = await checker.check_alignment("", "proof", "lean4")
        assert result.aligned is False
        assert "Empty" in result.explanation

    @pytest.mark.anyio(backend="asyncio")
    async def test_keyword_mismatch_short_circuits(self) -> None:
        checker = SemanticAlignmentChecker()
        result = await checker.check_alignment(
            "forall n : Prime, n > 1",
            "theorem foo : 1 + 1 = 2 := by rfl",
            "lean4",
        )
        assert result.aligned is False
        assert "no overlapping keywords" in result.explanation.lower()

    @pytest.mark.anyio(backend="asyncio")
    async def test_alignment_success(self) -> None:
        checker = SemanticAlignmentChecker()
        mock_response = MagicMock()
        mock_response.content = '{"aligned": true, "explanation": "Proof proves the theorem", "confidence": 0.92}'

        with patch.object(
            checker._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await checker.check_alignment(
                "forall n, n + 0 = n",
                "theorem add_zero : forall n, n + 0 = n := by induction n; simp",
                "lean4",
            )

        assert result.aligned is True
        assert result.confidence == 0.92

    @pytest.mark.anyio(backend="asyncio")
    async def test_alignment_failure(self) -> None:
        checker = SemanticAlignmentChecker()
        mock_response = MagicMock()
        mock_response.content = '{"aligned": false, "explanation": "Proof is for different theorem", "confidence": 0.85}'

        with patch.object(
            checker._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await checker.check_alignment(
                "forall n, n + 0 = n",
                "theorem add_zero_wrong : forall n, n + 0 = n + 1 := by rfl",
                "lean4",
            )

        assert result.aligned is False
        assert result.confidence == 0.85

    @pytest.mark.anyio(backend="asyncio")
    async def test_extracts_json_from_markdown(self) -> None:
        checker = SemanticAlignmentChecker()
        mock_response = MagicMock()
        mock_response.content = """```json
{"aligned": true, "explanation": "ok", "confidence": 0.9}
```"""

        with patch.object(
            checker._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await checker.check_alignment(
                "forall x, P(x",
                "theorem proof_P : forall x, P(x) := by intro x; exact h x",
                "coq",
            )

        assert result.aligned is True
        assert result.confidence == 0.9

    @pytest.mark.anyio(backend="asyncio")
    async def test_llm_error(self) -> None:
        checker = SemanticAlignmentChecker()
        with patch.object(
            checker._router, "generate_for_stage", new_callable=AsyncMock, side_effect=RuntimeError("API down")
        ):
            result = await checker.check_alignment(
                "forall x, P(x",
                "theorem proof_P : forall x, P(x) := by intro x; exact h x",
                "lean4",
            )

        assert result.aligned is False
        assert result.confidence == 0.0
        assert "API down" in result.explanation

    @pytest.mark.anyio(backend="asyncio")
    async def test_json_parse_error(self) -> None:
        checker = SemanticAlignmentChecker()
        mock_response = MagicMock()
        mock_response.content = "not json"

        with patch.object(
            checker._router, "generate_for_stage", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await checker.check_alignment(
                "forall x, P(x",
                "theorem proof_P : forall x, P(x) := by intro x; exact h x",
                "lean4",
            )

        assert result.aligned is False
        assert result.confidence == 0.0
