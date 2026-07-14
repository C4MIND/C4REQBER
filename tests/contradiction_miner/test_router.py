"""Tests for Contradiction Miner — API Router."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.contradiction_miner.router import router


@pytest.fixture
def client():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestRouterMethods:
    def test_list_methods(self, client):
        response = client.get("/api/v7/contradiction-miner/methods")
        assert response.status_code == 200
        data = response.json()
        assert "methods" in data
        assert len(data["methods"]) >= 2


class TestRouterExtract:
    def test_extract_success(self, client):
        payload = {"text": "Coffee increases alertness. Tea reduces stress."}
        response = client.post("/api/v7/contradiction-miner/extract", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "claims" in data
        assert data["total_sentences"] == 2
        assert len(data["claims"]) >= 2

    def test_extract_missing_text(self, client):
        response = client.post("/api/v7/contradiction-miner/extract", json={})
        assert response.status_code == 400
        assert "text" in response.json()["detail"].lower()

    def test_extract_empty_text(self, client):
        payload = {"text": ""}
        response = client.post("/api/v7/contradiction-miner/extract", json=payload)
        assert response.status_code == 400


class TestRouterDetect:
    def test_detect_success(self, client):
        payload = {
            "claims": [
                {"id": "C0", "text": "Coffee is beneficial", "subject": "Coffee", "predicate": "is beneficial", "polarity": "positive"},
                {"id": "C1", "text": "Coffee is harmful", "subject": "Coffee", "predicate": "is harmful", "polarity": "negative"},
            ],
        }
        response = client.post("/api/v7/contradiction-miner/detect", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "contradictions" in data
        assert "total_pairs_checked" in data

    def test_detect_missing_claims(self, client):
        response = client.post("/api/v7/contradiction-miner/detect", json={})
        assert response.status_code == 400

    def test_detect_empty_claims(self, client):
        payload = {"claims": []}
        response = client.post("/api/v7/contradiction-miner/detect", json=payload)
        assert response.status_code == 400


class TestRouterPipeline:
    def test_pipeline_success(self, client):
        payload = {"text": "Coffee increases alertness. Coffee decreases cognitive function."}
        response = client.post("/api/v7/contradiction-miner/pipeline", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "extraction" in data
        assert "contradictions" in data

    def test_pipeline_missing_text(self, client):
        response = client.post("/api/v7/contradiction-miner/pipeline", json={})
        assert response.status_code == 400
