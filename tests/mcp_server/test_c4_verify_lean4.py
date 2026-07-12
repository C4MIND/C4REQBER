"""Regression: Lean4 MCP uses success key from check_proof."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.mcp_server import server as mcp_server_module


@pytest.mark.asyncio
async def test_c4_verify_lean4_uses_success_key():
    with patch("src.mcp_server.server.Lean4Client") as mock_cls:
        inst = mock_cls.return_value
        inst.available = True
        inst.check_proof.return_value = {"success": True, "errors": [], "goals": []}
        result = await mcp_server_module.c4_verify("theorem test := by rfl", language="lean4")
    assert result["valid"] is True
