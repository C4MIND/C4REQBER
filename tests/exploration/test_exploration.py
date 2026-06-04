"""Tests for open-ended exploration module."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from src.exploration.anomaly_detector import AnomalyDetector
from src.exploration.formal_extender import FormalFrameworkExtender
from src.exploration.question_generator import SurpriseDrivenQuestionGenerator


class TestAnomalyDetector:
    def test_detect_literature_anomalies(self) -> None:
        detector = AnomalyDetector()
        rng = np.random.default_rng(42)
        # 20 normal points + 1 outlier
        embeddings = rng.normal(0, 1, (21, 10))
        embeddings[-1] = rng.normal(10, 1, 10)  # outlier
        papers = [{"title": f"P{i}"} for i in range(21)]
        anomalies = detector.detect_literature_anomalies(embeddings, papers, contamination=0.05)
        assert len(anomalies) >= 1

    def test_detect_literature_anomalies_small_input(self) -> None:
        detector = AnomalyDetector()
        embeddings = np.random.randn(5, 10)
        papers = [{"title": f"P{i}"} for i in range(5)]
        anomalies = detector.detect_literature_anomalies(embeddings, papers)
        assert anomalies == []  # Too small

    def test_detect_simulation_residuals(self) -> None:
        detector = AnomalyDetector()
        predicted = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
        expected = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        anomalies = detector.detect_simulation_residuals(predicted, expected, threshold_sigma=2.0)
        assert 4 in anomalies

    def test_detect_embedding_outliers(self) -> None:
        detector = AnomalyDetector()
        rng = np.random.default_rng(42)
        embeddings = rng.normal(0, 1, (50, 10))
        outliers = detector.detect_embedding_outliers(embeddings, threshold_percentile=95.0)
        assert len(outliers) > 0
        assert len(outliers) <= 5  # ~5% of 50


class TestSurpriseDrivenQuestionGenerator:
    @pytest.mark.anyio(backend="asyncio")
    async def test_generate_without_existing(self) -> None:
        gen = SurpriseDrivenQuestionGenerator()
        with patch.object(gen._router, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value.content = "Q1?\nQ2?\nQ3?\nQ4?\nQ5?"
            result = await gen.generate([], "physics", n_candidates=5, top_k=3)

        assert len(result) == 3
        assert all("?" in q for q in result)

    @pytest.mark.anyio(backend="asyncio")
    async def test_generate_with_existing(self) -> None:
        gen = SurpriseDrivenQuestionGenerator()
        with patch.object(gen._router, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value.content = "Q1?\nQ2?\nQ3?\nQ4?\nQ5?"
            with patch.object(gen._embedding, "embed", return_value=np.random.randn(5, 384)):
                result = await gen.generate(["Old question?"], "physics", n_candidates=5, top_k=3)

        assert len(result) == 3


class TestFormalFrameworkExtender:
    def test_extract_code(self) -> None:
        extender = FormalFrameworkExtender()
        code = extender._extract_code("```lean4\ntheorem test : True := by trivial\n```", "lean4")
        assert "theorem test" in code

    def test_extract_code_no_fence(self) -> None:
        extender = FormalFrameworkExtender()
        code = extender._extract_code("theorem test : True := by trivial", "lean4")
        assert "theorem test" in code

    @pytest.mark.anyio(backend="asyncio")
    async def test_propose_extension(self) -> None:
        extender = FormalFrameworkExtender()
        mock_response = AsyncMock()
        mock_response.content = "```lean4\ntheorem ext : True := by trivial\n```"

        with patch.object(extender._router, "generate", return_value=mock_response):
            with patch.object(extender, "_verify_compilation", return_value=(True, None)):
                result = await extender.propose_extension("mathlib", "test concept", "lean4")

        assert result is not None
        assert result.compiles is True
        assert "ext" in result.code
