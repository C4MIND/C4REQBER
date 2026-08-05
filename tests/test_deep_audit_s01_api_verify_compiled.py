"""Suite 01 — API /v8/verification/verify must not paint typecheck as verified."""

from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.errors import register_error_handlers
from src.api.v8_routers.verification_v8 import router as verification_router


app = FastAPI()
app.include_router(verification_router, prefix="/v8")
register_error_handlers(app)
client = TestClient(app, raise_server_exceptions=False)


def test_agda_typecheck_success_is_compiled_not_verified() -> None:
    with patch("src.verification.agda_bridge.AgdaBridge") as mock_cls:
        inst = mock_cls.return_value
        inst.available = True
        inst.type_check.return_value = {"success": True, "error": ""}
        resp = client.post(
            "/v8/verification/verify",
            json={"code": "module M where\ndata X : Set where", "formal_method": "agda"},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("verified") is False
    assert body.get("verification_aligned") is False
    assert body.get("stamp") == "COMPILED"
    assert body.get("compiled") is True
    assert body.get("status") == "partial"


def test_lean4_typecheck_success_is_compiled_not_verified() -> None:
    with patch("src.verification.lean4_client.Lean4Client") as mock_cls:
        inst = mock_cls.return_value
        inst.available = True
        inst.verify_theorem.return_value = {"valid": True, "error": ""}
        resp = client.post(
            "/v8/verification/verify",
            json={"code": "theorem T : True := trivial", "formal_method": "lean4", "proof": ""},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("verified") is False
    assert body.get("stamp") == "COMPILED"
