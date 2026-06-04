"""Tests for Decision Engine API Router — /v7/decisions."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.decisions.router import router


@pytest.fixture
def client():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestAHPEndpoint:
    def test_valid_ahp_request(self, client):
        payload = {
            "pairwise_matrix": [[1, 3], [1 / 3, 1]],
            "criteria": ["Cost", "Quality"],
            "alternatives": ["A", "B"],
            "alt_scores": {"A": [0.8, 0.4], "B": [0.3, 0.9]},
        }
        response = client.post("/api/v7/decisions/ahp", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "criteria_weights" in data
        assert "final_ranks" in data
        assert "consistency_ratio" in data
        assert "is_consistent" in data
        assert len(data["final_ranks"]) == 2

    def test_ahp_missing_matrix(self, client):
        response = client.post("/api/v7/decisions/ahp", json={"criteria": ["C"], "alternatives": ["A"]})
        assert response.status_code == 400
        assert "pairwise_matrix" in response.json()["detail"]

    def test_ahp_missing_criteria(self, client):
        response = client.post(
            "/api/v7/decisions/ahp",
            json={"pairwise_matrix": [[1]], "alternatives": ["A"]},
        )
        assert response.status_code == 400


class TestTOPSISEndpoint:
    def test_valid_topsis_request(self, client):
        payload = {
            "matrix": [[250, 16], [200, 20]],
            "alternatives": ["A", "B"],
            "weights": [0.5, 0.5],
            "benefits": [False, True],
        }
        response = client.post("/api/v7/decisions/topsis", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "ranks" in data
        assert "ideal_best" in data
        assert "ideal_worst" in data
        assert "distances_to_best" in data
        assert "distances_to_worst" in data
        assert len(data["ranks"]) == 2

    def test_topsis_missing_matrix(self, client):
        response = client.post("/api/v7/decisions/topsis", json={"alternatives": ["A"], "weights": [1], "benefits": [True]})
        assert response.status_code == 400

    def test_topsis_missing_weights(self, client):
        response = client.post(
            "/api/v7/decisions/topsis",
            json={"matrix": [[1]], "alternatives": ["A"], "benefits": [True]},
        )
        assert response.status_code == 400


class TestMethodsEndpoint:
    def test_list_methods(self, client):
        response = client.get("/api/v7/decisions/methods")
        assert response.status_code == 200
        data = response.json()
        assert "methods" in data
        assert len(data["methods"]) == 2
        method_names = [m["name"] for m in data["methods"]]
        assert "Analytic Hierarchy Process (AHP)" in method_names
        assert "TOPSIS" in method_names
