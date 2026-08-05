"""MCP server smoke tests — verify tools are registered AND invokable honestly.

Audit follow-up: schema registration is necessary but not sufficient.
Honesty tools must return non-success envelopes for stub/fallback/sorry paths.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Add repo root to path for src/ imports
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _import_server_module():
    """Lazy import so test collection doesn't fail on missing heavy deps."""
    try:
        from src.mcp_server import server

        return server
    except Exception as e:  # pragma: no cover - import is the test
        pytest.skip(f"src.mcp_server.server cannot import (heavy deps): {e}")


def _registered_tools(server_mod) -> list[str]:
    """Discover @server.tool-registered tool names."""
    out: list[str] = []
    for name in dir(server_mod):
        obj = getattr(server_mod, name)
        schema = getattr(obj, "schema", None)
        if callable(obj) and isinstance(schema, dict):
            out.append(name)
    return sorted(out)


def test_at_least_15_tools_registered():
    """Hard floor: we expect 21 tools (post-audit). Allow some slack for env-deps."""
    server = _import_server_module()
    tools = _registered_tools(server)
    assert len(tools) >= 15, f"Expected at least 15 MCP tools registered, got {len(tools)}: {tools}"


def test_tools_have_schemas():
    """Every registered tool must have a .schema attribute (JSON Schema dict)."""
    server = _import_server_module()
    tools = _registered_tools(server)
    for name in tools:
        fn = getattr(server, name)
        schema = getattr(fn, "schema", None)
        assert schema is not None, f"{name} missing .schema attribute"
        assert isinstance(schema, dict), f"{name} schema is not a dict"
        assert "type" in schema, f"{name} schema missing 'type' field"
        assert "properties" in schema, f"{name} schema missing 'properties' field"


def test_schema_properties_are_objects_or_arrays():
    """Each schema property should be a dict (JSON Schema fragment)."""
    server = _import_server_module()
    tools = _registered_tools(server)
    for name in tools:
        fn = getattr(server, name)
        schema = fn.schema
        for prop_name, prop_schema in schema.get("properties", {}).items():
            assert isinstance(prop_schema, dict), (
                f"{name}.properties.{prop_name} is not a dict: {prop_schema!r}"
            )


@pytest.mark.asyncio
async def test_c4_verify_sorry_is_not_success():
    """Invoke path: placeholder proof must not paint verified/success."""
    from src.mcp_server.tools_verify import c4_verify

    out = await c4_verify("theorem T : True := by sorry", language="lean4")
    assert isinstance(out, dict)
    assert out.get("valid") is False or out.get("status") in {
        "error",
        "partial",
        "unavailable",
    }
    assert out.get("status") != "success"
    assert out.get("stamp") != "FORMALLY VERIFIED"


@pytest.mark.asyncio
async def test_c4_bayesian_empty_is_not_success():
    """Invoke path: empty/prior-only must not invent success."""
    from src.mcp_server import tools_analysis

    out = await tools_analysis.c4_bayesian(models={})
    assert isinstance(out, dict)
    # Empty models → ValueError path or partial — never silent success
    assert out.get("status") in {"partial", "unavailable", "error", "skipped"}
    assert out.get("status") != "success"


@pytest.mark.asyncio
async def test_c4_simulate_fallback_truth_is_partial(monkeypatch: pytest.MonkeyPatch):
    from src.mcp_server import tools_analysis

    monkeypatch.setattr(
        "src.simulations.runner_v2.get_runner_v2",
        lambda: MagicMock(
            run=lambda *a, **k: {
                "status": "completed",
                "executed": True,
                "engine_truth": "not_newton_physics",
                "stub": False,
            }
        ),
    )
    out = await tools_analysis.c4_simulate("newtonian", {"text": "h"})
    assert isinstance(out, dict)
    assert out.get("status") in {"partial", "unavailable", "error"}
    assert out.get("status") != "success"
