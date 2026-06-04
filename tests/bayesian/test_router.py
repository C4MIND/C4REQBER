"""Tests for src/bayesian/router.py."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.bayesian.router import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestMCMCEndpoint:
    def test_basic_mcmc(self):
        response = client.post(
            "/api/v7/bayesian/mcmc",
            json={"target_type": "gaussian", "mu": 0.0, "sigma": 1.0, "n_samples": 500, "burn_in": 100},
        )
        assert response.status_code == 200
        data = response.json()
        assert "mean" in data
        assert "std" in data
        assert "acceptance_rate" in data
        assert data["acceptance_rate"] > 0.0

    def test_mcmc_defaults(self):
        response = client.post("/api/v7/bayesian/mcmc", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["n_samples"] == 10000


class TestBMAEndpoint:
    def test_basic_bma(self):
        response = client.post(
            "/api/v7/bayesian/bma",
            json={
                "models": [
                    {"name": "M1", "probability": 0.5, "prediction": 10.0},
                    {"name": "M2", "probability": 0.5, "prediction": 20.0},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["weighted_prediction"] == pytest.approx(15.0)

    def test_bma_single_model(self):
        response = client.post(
            "/api/v7/bayesian/bma",
            json={"models": [{"name": "Solo", "probability": 1.0, "prediction": 42.0}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["weighted_prediction"] == pytest.approx(42.0)


class TestOptimizeEndpoint:
    def test_quadratic(self):
        response = client.post(
            "/api/v7/bayesian/optimize",
            json={
                "function_type": "quadratic",
                "bounds": [0.0, 1.0],
                "n_iter": 30,
                "n_init": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "best_x" in data
        assert "best_y" in data
        assert 0.0 <= data["best_x"] <= 1.0


class TestDSTCombineEndpoint:
    def test_dst_combine(self):
        response = client.post(
            "/api/v7/bayesian/dst/combine",
            json={
                "frame_elements": ["A", "B"],
                "masses": [
                    {"A": 0.7, "A,B": 0.3},
                    {"B": 0.6, "A,B": 0.4},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "belief" in data
        assert "plausibility" in data
        assert "A" in data["belief"]


class TestFuzzyInferEndpoint:
    def test_fuzzy_infer(self):
        response = client.post(
            "/api/v7/bayesian/fuzzy/infer",
            json={"crisp_input": 25.0, "rules": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["crisp_input"] == 25.0
