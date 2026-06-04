"""Unit tests for v8 exploration router."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.errors import register_error_handlers
from src.api.v8_router import router as v8_router

app = FastAPI()
app.include_router(v8_router)
register_error_handlers(app)
client = TestClient(app)


class TestExplorationAnomalies:
    def test_detect_literature_anomalies(self) -> None:
        with patch("src.api.v8_routers.exploration.AnomalyDetector") as MockDetector:
            MockDetector.return_value.detect_literature_anomalies.return_value = [
                {"title": "Anomalous Paper"}
            ]
            resp = client.post("/v8/exploration/anomalies", json={
                "embeddings": [[0.1, 0.2], [0.9, 0.8]],
                "papers": [{"title": "P1"}, {"title": "P2"}],
                "contamination": 0.05,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_detected"] == 1

    def test_detect_simulation_residuals(self) -> None:
        with patch("src.api.v8_routers.exploration.AnomalyDetector") as MockDetector:
            MockDetector.return_value.detect_simulation_residuals.return_value = [2, 5]
            resp = client.post("/v8/exploration/anomalies", json={
                "predicted": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "expected": [1.1, 2.1, 10.0, 4.1, 5.1, 6.1],
                "threshold_sigma": 3.0,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_detected"] == 2

    def test_mismatched_embeddings_papers_count(self) -> None:
        resp = client.post("/v8/exploration/anomalies", json={
            "embeddings": [[0.1, 0.2]],
            "papers": [{"title": "P1"}, {"title": "P2"}],
        })
        assert resp.status_code == 422

    def test_mismatched_predicted_expected_length(self) -> None:
        resp = client.post("/v8/exploration/anomalies", json={
            "predicted": [1.0, 2.0],
            "expected": [1.1],
        })
        assert resp.status_code == 422

    def test_contamination_bounds(self) -> None:
        resp = client.post("/v8/exploration/anomalies", json={
            "contamination": 1.5,
        })
        assert resp.status_code == 422


class TestExplorationQuestions:
    @pytest.mark.anyio(backend="asyncio")
    def test_generate_questions(self) -> None:
        from unittest.mock import AsyncMock
        with patch("src.api.v8_routers.exploration.SurpriseDrivenQuestionGenerator") as MockGen:
            MockGen.return_value.generate = AsyncMock(return_value=["Q1", "Q2"])
            resp = client.post("/v8/exploration/questions", json={
                "existing_questions": ["What is X?"],
                "topic": "causal inference",
                "n_candidates": 10,
                "top_k": 3,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["topic"] == "causal inference"
        assert data["count"] == 2

    def test_top_k_cannot_exceed_candidates(self) -> None:
        resp = client.post("/v8/exploration/questions", json={
            "topic": "test",
            "n_candidates": 5,
            "top_k": 10,
        })
        assert resp.status_code == 422


class TestExplorationExtendFormal:
    @pytest.mark.anyio(backend="asyncio")
    def test_extend_formal(self) -> None:
        from unittest.mock import AsyncMock
        mock_proposal = MagicMock()
        mock_proposal.to_dict.return_value = {
            "language": "lean4",
            "code": "theorem test : True := by trivial",
            "description": "test",
            "compiles": True,
        }
        with patch("src.api.v8_routers.exploration.FormalFrameworkExtender") as MockExt:
            MockExt.return_value.propose = AsyncMock(return_value=mock_proposal)
            resp = client.post("/v8/exploration/extend-formal", json={
                "library": "mathlib4",
                "language": "lean4",
                "concept_gap": "continuity of composed functions",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["proposal"]["language"] == "lean4"

    def test_extend_formal_missing_concept_gap(self) -> None:
        resp = client.post("/v8/exploration/extend-formal", json={
            "library": "mathlib4",
        })
        assert resp.status_code == 422
