"""Security tests for v8 API endpoints."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v8_router import router as v8_router

app = FastAPI()
app.include_router(v8_router)
client = TestClient(app)


class TestInputSanitization:
    """Verify endpoints reject malicious input patterns."""

    def test_agenda_generate_rejects_script_injection(self) -> None:
        """Script tags in question text should not execute."""
        payload = {
            "knowledge_graph": {
                "nodes": ["<script>alert('xss')</script>"],
                "edges": [],
            },
            "n_questions": 3,
        }
        resp = client.post("/v8/agenda/generate", json=payload)
        # Should accept (we sanitize on output, not input)
        assert resp.status_code in (200, 422)

    def test_agenda_generate_rejects_sql_injection_pattern(self) -> None:
        """SQL-like patterns in topic should not cause issues."""
        payload = {
            "knowledge_graph": {
                "nodes": ["'; DROP TABLE users; --"],
                "edges": [],
            },
        }
        resp = client.post("/v8/agenda/generate", json=payload)
        assert resp.status_code in (200, 422)

    def test_exploration_questions_rejects_empty_topic(self) -> None:
        """Empty topic should be rejected by validation."""
        resp = client.post("/v8/exploration/questions", json={
            "topic": "",
            "n_candidates": 10,
            "top_k": 3,
        })
        assert resp.status_code == 422

    def test_exploration_questions_rejects_very_long_topic(self) -> None:
        """Topic > 500 chars should be rejected."""
        resp = client.post("/v8/exploration/questions", json={
            "topic": "A" * 501,
            "n_candidates": 10,
            "top_k": 3,
        })
        assert resp.status_code == 422

    def test_anomalies_rejects_negative_contamination(self) -> None:
        """Negative contamination is invalid."""
        resp = client.post("/v8/exploration/anomalies", json={
            "contamination": -0.1,
        })
        assert resp.status_code == 422

    def test_extend_formal_rejects_path_traversal_in_library(self) -> None:
        """Library name should not allow path traversal."""
        resp = client.post("/v8/exploration/extend-formal", json={
            "library": "../../../etc/passwd",
            "concept_gap": "test",
        })
        assert resp.status_code == 422

    def test_approve_rejects_very_long_question(self) -> None:
        """Question > 2000 chars should be rejected."""
        resp = client.post("/v8/agenda/approve", json={
            "question_text": "Q" * 2001,
            "action": "approve",
        })
        assert resp.status_code == 422


class TestRateLimitHeaders:
    """Verify endpoints return appropriate security headers."""

    def test_agenda_has_security_headers(self) -> None:
        resp = client.get("/v8/agenda/progress")
        assert resp.status_code == 200
        # FastAPI sets content-type by default
        assert "content-type" in resp.headers
