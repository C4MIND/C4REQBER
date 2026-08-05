"""Wave-2 audit regression locks (search contract, citation ERROR, legacy CLI)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.knowledge.citation_verifier import CitationCheck, CitationVerifier
from src.knowledge.orchestrator import source_names_from_result


def test_build_summary_contract_sources_used_is_int() -> None:
    """_build_summary must match search_all: sources_used int + source_names list."""
    from src.knowledge.orchestrator import MultiSourceSearcher

    # Inspect source of _build_summary return keys via a tiny stub call path
    searcher = MultiSourceSearcher.__new__(MultiSourceSearcher)
    papers = [
        {
            "title": "A",
            "_source": "openalex",
            "relevance_score": 0.9,
            "year": 2020,
            "domain": "materials_science",
        }
    ]
    summary = MultiSourceSearcher._build_summary(  # type: ignore[attr-defined]
        searcher,
        papers=papers,
        sources_used={"openalex"},
        source_counts={"openalex": 1},
        errors={},
    )
    assert isinstance(summary["sources_used"], int)
    assert summary["sources_used"] == 1
    assert summary["source_names"] == ["openalex"]


@pytest.mark.asyncio
async def test_citation_verify_maps_exceptions_to_error() -> None:
    verifier = CitationVerifier.__new__(CitationVerifier)
    verifier._client = MagicMock()

    async def boom(*_a: Any, **_k: Any) -> CitationCheck:
        raise RuntimeError("network down")

    verifier._verify_single = boom  # type: ignore[method-assign]
    verifier._extract_citations = staticmethod(  # type: ignore[method-assign]
        lambda _text: [{"id": "[1]", "context": "see [1]"}]
    )
    results = await CitationVerifier.verify(verifier, "see [1] about steel")
    assert len(results) == 1
    assert results[0].verdict == "ERROR"
    assert results[0].check_error == "RuntimeError"


def test_source_names_helper_stable() -> None:
    assert source_names_from_result({"sources_used": 2, "source_names": ["a", "b"]}) == [
        "a",
        "b",
    ]


def test_legacy_typer_solve_is_fail_closed() -> None:
    """Legacy turbo solve/discover/explain must Exit(2) — no fake hypotheses."""
    from typer.testing import CliRunner

    from src.cli.typer_core import app

    runner = CliRunner()
    for args in (
        ["solve", "increase battery life"],
        ["discover", "improve heat"],
        ["explain", "discovery_001"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code == 2, (args, result.exit_code, result.output)
        assert "sample_hypotheses" not in (result.output or "")
        assert "Generated 12 novel" not in (result.output or "")
        assert (
            "disabled" in (result.output or "").lower() or "blast" in (result.output or "").lower()
        )


@pytest.mark.asyncio
async def test_flash_rejects_mlx_error_content(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.knowledge.flash_runner import run_flash

    class FakeLLM:
        async def chat(self, *a: Any, **k: Any) -> str:
            return "[MLX Error] model missing"

        async def generate(self, *a: Any, **k: Any) -> Any:
            return type("R", (), {"content": "[MLX Error] model missing"})()

    monkeypatch.setattr("src.llm.gateway.get_gateway", lambda: FakeLLM())
    monkeypatch.setattr(
        "src.config.paths.apply_config_to_env",
        lambda: None,
    )
    result = await run_flash("what is steel?", with_sources=False, deep=False)
    assert result["answer"] == ""
    assert result["status"] in {"error", "partial"}
