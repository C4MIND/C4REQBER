"""MCP c4_verify must handle HoareResult dataclass (not dict)."""
from __future__ import annotations

import pytest

z3 = pytest.importorskip("z3")

from src.mcp_server import server as mcp_server_module


@pytest.mark.asyncio
async def test_c4_verify_hoare_returns_valid_dataclass_result():
    code = "{x >= 0} x := x + 1 {x >= 1}"
    result = await mcp_server_module.c4_verify(code, language="hoare")
    assert result.get("error") is None, result
    assert result["valid"] is True
    assert result["language"] == "hoare"
    assert result["proof"] == code
    assert result["details"].get("valid") is True


@pytest.mark.asyncio
async def test_c4_verify_hoare_invalid_triple():
    code = "{x >= 0} x := x - 1 {x >= 1}"
    result = await mcp_server_module.c4_verify(code, language="hoare")
    assert result.get("error") is None, result
    assert result["valid"] is False
    assert "details" in result
