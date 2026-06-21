"""MCP per-tool timeout configuration."""
from __future__ import annotations

from src.mcp_server.fallback_protocol import DEFAULT_TOOL_TIMEOUT, tool_timeout_seconds


def test_blast_turbo_has_long_timeout():
    assert tool_timeout_seconds("blast_turbo") >= 600.0


def test_blast_flash_shorter_than_turbo():
    assert tool_timeout_seconds("blast_flash") < tool_timeout_seconds("blast_turbo")


def test_unknown_tool_uses_default():
    assert tool_timeout_seconds("nonexistent_tool_xyz") == DEFAULT_TOOL_TIMEOUT