"""Suite 07 — Agent verify intent must call real verifier, not LLM prose."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.agent.core import AgentCore


@pytest.mark.asyncio
async def test_run_formal_verify_uses_c4_verify_not_llm() -> None:
    agent = AgentCore.__new__(AgentCore)
    fake = {
        "valid": True,
        "status": "partial",
        "stamp": "COMPILED",
        "verification_aligned": False,
        "error": None,
    }
    with patch(
        "src.mcp_server.tools_verify.c4_verify",
        new=AsyncMock(return_value=fake),
    ) as mocked:
        out = agent.run_formal_verify("theorem T : True := by sorry", language="lean4")
    mocked.assert_awaited()
    assert out.get("verified") is False
    assert out.get("stamp") == "COMPILED"
    assert out.get("status") != "success"


def test_run_formal_verify_strips_fake_formally_verified_stamp() -> None:
    agent = AgentCore.__new__(AgentCore)
    fake = {
        "valid": True,
        "status": "success",
        "stamp": "FORMALLY VERIFIED",
        "verification_aligned": False,
    }
    with patch(
        "src.mcp_server.tools_verify.c4_verify",
        new=AsyncMock(return_value=fake),
    ):
        out = agent.run_formal_verify("thm", language="lean4")
    assert out.get("stamp") == "COMPILED"
    assert out.get("status") == "partial"
    assert out.get("verified") is False
