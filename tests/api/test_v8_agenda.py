"""Unit tests for v8 agenda router."""

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


class TestAgendaGenerate:
    @pytest.mark.anyio(backend="asyncio")
    def test_generate_agenda_success(self) -> None:
        """Test agenda generation returns scored questions."""
        mock_question = MagicMock()
        mock_question.to_dict.return_value = {"text": "Q1", "strategy": "gap"}

        with (
            patch("src.api.v8_routers.agenda.AgendaGenerator") as MockGen,
            patch("src.api.v8_routers.agenda.FeasibilityChecker") as MockCheck,
            patch("src.api.v8_routers.agenda.PriorityScorer") as MockScore,
        ):
            MockGen.return_value.generate.return_value = [mock_question]
            MockCheck.return_value.check.return_value = MagicMock(
                to_dict=lambda: {"has_tools": True}
            )
            MockScore.return_value.score.return_value = 0.85

            resp = client.post(
                "/v8/agenda/generate",
                json={
                    "knowledge_graph": {"nodes": ["A", "B"], "edges": [["A", "B"]]},
                    "recent_results": [],
                    "n_questions": 3,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "questions" in data
        assert data["count"] >= 0

    def test_generate_agenda_invalid_n_questions(self) -> None:
        """Test validation rejects n_questions > 50."""
        resp = client.post(
            "/v8/agenda/generate",
            json={
                "knowledge_graph": {},
                "n_questions": 100,
            },
        )
        assert resp.status_code == 422


class TestAgendaApprove:
    def test_approve_action(self) -> None:
        resp = client.post(
            "/v8/agenda/approve",
            json={
                "question_text": "Test question",
                "action": "approve",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"

    def test_reject_action(self) -> None:
        resp = client.post(
            "/v8/agenda/approve",
            json={
                "question_text": "Test question",
                "action": "reject",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"

    def test_modify_action_requires_modified_text(self) -> None:
        resp = client.post(
            "/v8/agenda/approve",
            json={
                "question_text": "Test question",
                "action": "modify",
                "modified_text": "Modified question",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "modified"

    def test_modify_action_missing_modified_text(self) -> None:
        resp = client.post(
            "/v8/agenda/approve",
            json={
                "question_text": "Test question",
                "action": "modify",
            },
        )
        assert resp.status_code == 422

    def test_invalid_action_rejected(self) -> None:
        """Literal validation should reject unknown actions at request parsing."""
        resp = client.post(
            "/v8/agenda/approve",
            json={
                "question_text": "Test question",
                "action": "unknown_action",
            },
        )
        assert resp.status_code == 422


class TestAgendaProgress:
    def test_get_progress(self) -> None:
        resp = client.get("/v8/agenda/progress")
        assert resp.status_code == 200
        data = resp.json()
        assert "results_count" in data
        assert "covered_topics" in data
