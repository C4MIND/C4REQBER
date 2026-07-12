"""API tests for POST /v8/verification/verify — CVC5/TLA+/Alloy routes."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.errors import register_error_handlers
from src.api.v8_routers.verification_v8 import router as verification_router


app = FastAPI()
app.include_router(verification_router, prefix="/v8")
register_error_handlers(app)
client = TestClient(app, raise_server_exceptions=False)

SMT_SAMPLE = "(declare-const x Int)\n(assert (> x 0))\n(check-sat)\n"
TLA_SAMPLE = "---- MODULE M ----\nInit == TRUE\nNext == TRUE\n====\n"
ALLOY_SAMPLE = "sig A {}\nrun {} for 3\n"


@pytest.mark.parametrize(
    ("method", "code", "patch_target"),
    [
        ("cvc5", SMT_SAMPLE, "src.verification.cvc5_client.CVC5Client"),
        ("tla", TLA_SAMPLE, "src.verification.tla_client.TLAClient"),
        ("alloy", ALLOY_SAMPLE, "src.verification.alloy_client.AlloyClient"),
    ],
)
def test_verify_endpoint_dispatches_new_backends(method: str, code: str, patch_target: str) -> None:
    with patch(patch_target) as mock_cls:
        inst = mock_cls.return_value
        inst.is_available.return_value = True
        inst.verify.return_value = {"valid": True, "output": "ok"}
        resp = client.post(
            "/v8/verification/verify",
            json={"code": code, "formal_method": method},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("verified") is True


def test_verify_endpoint_cvc5_not_installed_returns_501() -> None:
    with patch("src.verification.cvc5_client.CVC5Client") as mock_cls:
        mock_cls.return_value.is_available.return_value = False
        resp = client.post(
            "/v8/verification/verify",
            json={"code": SMT_SAMPLE, "formal_method": "cvc5"},
        )
    assert resp.status_code == 501
    assert "cvc5" in resp.json().get("error_code", "").lower() or "cvc5" in resp.text.lower()


def test_list_tools_includes_new_backends() -> None:
    resp = client.get("/v8/verification/tools")
    assert resp.status_code == 200
    tools = resp.json()
    for backend in ("cvc5", "tla", "alloy"):
        assert backend in tools
