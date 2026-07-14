from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mcp_server import server as mcp
from src.mcp_server.fallback_protocol import _FallbackServer
from src.mcp_server.tool_schemas import INPUT_SCHEMAS


@pytest.mark.asyncio
async def test_c4_search_uses_orchestrator_result_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    class Searcher:
        async def search_all(self, query: str, **kwargs: object) -> dict[str, object]:
            assert query == "gravity"
            assert "sources" not in kwargs
            return {
                "papers": [{"title": "A"}, {"title": "B"}],
                "total_papers": 2,
                "source_names": ["arxiv"],
            }

    monkeypatch.setattr(mcp, "HAS_TOOLS", True)
    monkeypatch.setattr(mcp, "MultiSourceSearcher", Searcher)

    result = await mcp.c4_search("gravity")

    assert result["status"] == "success"
    assert result["data"] == [{"title": "A"}, {"title": "B"}]
    assert result["metadata"]["total_found"] == 2
    assert result["metadata"]["source_names"] == ["arxiv"]


@pytest.mark.asyncio
async def test_c4_search_honors_explicit_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    class Searcher:
        async def search_single(self, source: str, query: str) -> list[dict[str, str]]:
            return [{"title": f"{source}:{query}", "_source": source}]

    monkeypatch.setattr(mcp, "HAS_TOOLS", True)
    monkeypatch.setattr(mcp, "MultiSourceSearcher", Searcher)

    result = await mcp.c4_search("gravity", sources=["arxiv", "pubmed"])

    assert result["status"] == "success"
    assert [paper["_source"] for paper in result["data"]] == ["arxiv", "pubmed"]
    assert result["metadata"]["source_names"] == ["arxiv", "pubmed"]


@pytest.mark.asyncio
async def test_c4_bayesian_calls_bma_with_valid_request(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run_bma(request: object) -> dict[str, object]:
        assert request.models[0]["name"] == "m1"  # type: ignore[attr-defined]
        return {
            "weighted_prediction": 0.7,
            "uncertainty": 0.1,
            "models": [{"name": "m1", "posterior_prob": 1.0, "prediction": 0.7}],
        }

    monkeypatch.setattr(mcp, "HAS_TOOLS", True)
    monkeypatch.setattr(mcp, "run_bma", fake_run_bma)

    result = await mcp.c4_bayesian([{"name": "m1", "probability": 1.0, "prediction": 0.7}])

    assert result["status"] == "success"
    assert result["data"]["weighted_prediction"] == 0.7


@pytest.mark.asyncio
async def test_c4_causal_builds_scm_and_returns_identification() -> None:
    result = await mcp.c4_causal(
        [
            {"name": "X", "parents": []},
            {"name": "Y", "parents": ["X"]},
        ],
        treatment="X",
        outcome="Y",
    )

    assert result["status"] == "success"
    assert result["data"]["identifiable"] is True
    assert "P(Y | do(X))" in result["data"]["formula"]


@pytest.mark.asyncio
async def test_c4_autoresearch_uses_src_import_and_serializes_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.operators import autoresearch

    report = SimpleNamespace(
        best_metric=0.2,
        best_iteration=2,
        total_iterations=3,
        total_duration_seconds=1.5,
        improvement_trace=[(2, 0.2)],
    )
    monkeypatch.setattr(autoresearch, "run_autoresearch", lambda **_: report)

    result = await mcp.c4_autoresearch("train.py", max_iter=3)

    assert result["status"] == "success"
    assert result["data"]["best_metric"] == 0.2


def test_live_tool_schemas_come_from_registry() -> None:
    for name, schema in INPUT_SCHEMAS.items():
        fn = getattr(mcp, name)
        assert fn.schema == schema, f"{name} schema drifted from INPUT_SCHEMAS"


def test_all_21_tools_are_registered_through_public_facade() -> None:
    registered = mcp.server._tools
    assert set(registered) == set(INPUT_SCHEMAS)
    assert len(registered) == 21
    for name, tool in registered.items():
        assert tool is getattr(mcp, name)


def test_split_mcp_modules_stay_within_size_target() -> None:
    package = Path(mcp.__file__).parent
    modules = [
        "server.py",
        "tool_dependencies.py",
        "tools_analysis.py",
        "tools_blast.py",
        "tools_discovery.py",
        "tools_factory.py",
        "tools_prove.py",
        "tools_research.py",
        "tools_verify.py",
    ]
    for module in modules:
        lines = (package / module).read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 300, f"{module} grew to {len(lines)} lines"


@pytest.mark.asyncio
async def test_fallback_protocol_initialize_and_tool_result_envelope() -> None:
    fallback = _FallbackServer("c4reqber")

    @fallback.tool("echo")
    async def echo(value: str) -> dict[str, object]:
        return {"status": "success", "data": {"value": value}}

    echo.schema = {
        "type": "object",
        "properties": {"value": {"type": "string"}},
        "required": ["value"],
        "additionalProperties": False,
    }

    initialized = await fallback.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert initialized is not None
    assert initialized["result"]["serverInfo"]["name"] == "c4reqber"
    assert "protocolVersion" in initialized["result"]

    response = await fallback.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"value": "ok"}},
        }
    )
    assert response is not None
    payload = response["result"]
    assert payload["isError"] is False
    assert json.loads(payload["content"][0]["text"])["data"]["value"] == "ok"


@pytest.mark.asyncio
async def test_fallback_protocol_rejects_unknown_method() -> None:
    fallback = _FallbackServer("c4reqber")
    response = await fallback.handle_request(
        {"jsonrpc": "2.0", "id": 9, "method": "unknown", "params": {}}
    )
    assert response == {
        "jsonrpc": "2.0",
        "id": 9,
        "error": {"code": -32601, "message": "Method not found: unknown"},
    }
