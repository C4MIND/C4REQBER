"""Tests for Prometheus metrics middleware."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.metrics import add_metrics_middleware

app = FastAPI()
add_metrics_middleware(app)


@app.get("/ok")
def endpoint_ok():
    return {"status": "ok"}


@app.get("/error")
def endpoint_error():
    raise RuntimeError("boom")


client = TestClient(app, raise_server_exceptions=False)


class TestMetricsMiddleware:
    def test_metrics_endpoint_exists(self) -> None:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "c4_api_requests_total" in resp.text
        assert "c4_api_request_duration_seconds" in resp.text
        assert "c4_api_active_requests" in resp.text

    def test_successful_request_increments_counter(self) -> None:
        # Prime the counter
        client.get("/ok")
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert 'status="200"' in resp.text
        assert 'endpoint="/ok"' in resp.text

    def test_error_request_increments_counter(self) -> None:
        client.get("/error")
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert 'status="500"' in resp.text
        assert 'endpoint="/error"' in resp.text
