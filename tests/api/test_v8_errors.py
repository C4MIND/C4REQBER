"""Tests for centralized API error handling."""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.errors import C4APIError, NotFoundError, ValidationError, register_error_handlers


app = FastAPI()
register_error_handlers(app)


@app.get("/test-c4-error")
def raise_c4_error():
    raise C4APIError("something went wrong", status_code=500, error_code="test_error")


@app.get("/test-not-found")
def raise_not_found():
    raise NotFoundError("resource not found")


@app.get("/test-validation")
def raise_validation():
    raise ValidationError("invalid input", detail={"field": "name"})


@app.get("/test-unexpected")
def raise_unexpected():
    raise RuntimeError("unexpected boom")


client = TestClient(app, raise_server_exceptions=False)


class TestC4APIErrorHandler:
    def test_c4_error_response(self) -> None:
        resp = client.get("/test-c4-error")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] is True
        assert data["error_code"] == "test_error"
        assert data["message"] == "something went wrong"
        assert "status_code" in data

    def test_not_found_error(self) -> None:
        resp = client.get("/test-not-found")
        assert resp.status_code == 404
        data = resp.json()
        assert data["error_code"] == "not_found"

    def test_validation_error(self) -> None:
        resp = client.get("/test-validation")
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_code"] == "validation_error"
        assert data["detail"]["field"] == "name"

    def test_unexpected_error_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Detail leak requires DEV_MODE + DEV_MODE_BYPASS_TOKEN (same gate as auth)."""
        monkeypatch.setenv("DEV_MODE", "1")
        monkeypatch.setenv("DEV_MODE_BYPASS_TOKEN", "test-bypass-token")
        resp = client.get("/test-unexpected")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error_code"] == "internal_error"
        assert data["detail"]["exception_type"] == "RuntimeError"

    def test_unexpected_error_hides_detail_without_bypass_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEV_MODE", "1")
        monkeypatch.delenv("DEV_MODE_BYPASS_TOKEN", raising=False)
        resp = client.get("/test-unexpected")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error_code"] == "internal_error"
        assert data["detail"] == {}
