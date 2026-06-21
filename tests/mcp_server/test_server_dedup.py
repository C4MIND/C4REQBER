"""MCP server uses canonical fallback_protocol implementation."""
from __future__ import annotations

from src.mcp_server.fallback_protocol import _FallbackServer, tool_timeout_seconds
from src.mcp_server import server as mcp_server_module


def test_server_instance_uses_fallback_protocol_class():
    srv = mcp_server_module.server
    # Production path: official SDK lacks @server.tool — always fallback.
    assert isinstance(srv, _FallbackServer)


def test_blast_turbo_timeout_production_grade():
    assert tool_timeout_seconds("blast_turbo") >= 600.0