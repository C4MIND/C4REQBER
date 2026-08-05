"""Tests for shared flash sources helper and honesty gates."""

from __future__ import annotations

from typing import Any

import pytest

from src.knowledge.config import (
    flash_source_allowlist,
    infer_query_domain,
)
from src.knowledge.flash_runner import (
    build_flash_prompt,
    flash_honesty_status,
    run_flash,
)
from src.knowledge.flash_sources import (
    gather_flash_sources,
    is_checkable_paper,
    is_checkable_url,
    sanitize_paper,
)
from src.knowledge.orchestrator import source_names_from_result


def test_source_names_from_result_handles_orchestrator_int_count() -> None:
    """Regression: search_all returns sources_used as int — never list(int)."""
    result = {
        "sources_used": 2,  # int count — the real MultiSourceSearcher contract
        "source_names": ["openalex", "crossref"],
        "source_stats": {
            "openalex": {"papers": 3, "ok": True},
            "crossref": {"papers": 1, "ok": True},
            "arxiv": {"papers": 0, "ok": True},
        },
    }
    assert source_names_from_result(result) == ["openalex", "crossref"]


def test_source_names_from_result_recovers_from_stats_when_names_missing() -> None:
    result = {
        "sources_used": 1,
        "source_stats": {
            "openalex": {"papers": 2, "ok": True},
            "pubmed": {"papers": 0, "ok": False, "error": "timeout"},
        },
    }
    assert source_names_from_result(result) == ["openalex"]


def test_source_names_from_result_accepts_legacy_list_mocks() -> None:
    assert source_names_from_result({"sources_used": ["web", "tavily"]}) == ["web", "tavily"]
    assert source_names_from_result({"sources_used": 0}) == []
    assert source_names_from_result(None) == []


@pytest.mark.asyncio
async def test_gather_survives_orchestrator_int_sources_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows tester bug: list(sources_used) when sources_used is int."""

    class FakeSearcher:
        def __init__(self, *a, **k) -> None:
            self._active_sources = {"openalex": object()}

        async def search_all(
            self, query: str, domain: str = "general", include_web: bool = False
        ) -> dict:
            return {
                "papers": [
                    {
                        "title": "Deep Cryogenic Treatment of AISI 440C Steel",
                        "_source": "openalex",
                        "abstract": "Cryogenic treatment improves wear resistance",
                        "doi": "10.1234/aisi440c",
                        "url": "https://doi.org/10.1234/aisi440c",
                    }
                ],
                # Real orchestrator shape — int count + source_names list
                "sources_used": 1,
                "source_names": ["openalex"],
                "source_stats": {"openalex": {"papers": 1, "ok": True, "time": 0.4}},
            }

    async def fake_annotate(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for p in papers:
            p["verified"] = True
            p["verify_verdict"] = "VERIFIED"
        return papers

    monkeypatch.setattr(
        "src.knowledge.orchestrator.MultiSourceSearcher",
        FakeSearcher,
    )
    monkeypatch.setattr(
        "src.knowledge.flash_sources.annotate_verified",
        fake_annotate,
    )
    papers, ctx, meta = await gather_flash_sources(
        "find exactly one real peer reviewed publication specifically about "
        "cryogenic treatment of AISI 440C steel",
        deep=False,
    )
    assert "gather" not in (meta.get("errors") or {})
    assert len(papers) == 1
    assert meta["sources_used"] == ["openalex"]
    assert meta["found"] == 1
    assert meta["verified"] == 1
    assert "AISI" in ctx or "Cryogenic" in ctx


@pytest.mark.asyncio
async def test_gather_flash_sources_never_example_com(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSearcher:
        def __init__(self, *a, **k) -> None:
            self._active_sources = {}

        async def search_all(
            self, query: str, domain: str = "general", include_web: bool = False
        ) -> dict:
            return {
                "papers": [
                    {
                        "title": "Real Paper About Cryogenic Steel",
                        "_source": "openalex",
                        "abstract": "About science",
                        "doi": "10.1234/real",
                        "url": "https://doi.org/10.1234/real",
                    }
                ],
                "sources_used": 1,
                "source_names": ["openalex"],
                "source_stats": {"openalex": {"papers": 1, "ok": True}},
            }

    async def fake_annotate(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for p in papers:
            p["verified"] = True
            p["verify_verdict"] = "VERIFIED"
        return papers

    monkeypatch.setattr(
        "src.knowledge.orchestrator.MultiSourceSearcher",
        FakeSearcher,
    )
    monkeypatch.setattr(
        "src.knowledge.flash_sources.annotate_verified",
        fake_annotate,
    )
    papers, ctx, meta = await gather_flash_sources("q", deep=False)
    assert len(papers) == 1
    assert "example.com" not in ctx
    assert "Real Paper" in ctx
    assert papers[0]["verified"] is True
    assert meta["verified"] == 1


@pytest.mark.asyncio
async def test_gather_rejects_scholar_q_and_example(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSearcher:
        def __init__(self, *a, **k) -> None:
            self._active_sources = {}

        async def search_all(
            self, query: str, domain: str = "general", include_web: bool = False
        ) -> dict:
            return {
                "papers": [
                    {
                        "title": "Fake Scholar Hit",
                        "_source": "web",
                        "url": "https://scholar.google.com/scholar?q=aisi+440c",
                    },
                    {
                        "title": "Dummy",
                        "_source": "web",
                        "url": "http://example.com/1",
                    },
                ],
                "sources_used": 1,
                "source_names": ["web"],
                "source_stats": {},
            }

    async def fake_annotate(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for p in papers:
            p["verified"] = False
            p["verify_verdict"] = "UNVERIFIED"
        return papers

    monkeypatch.setattr(
        "src.knowledge.orchestrator.MultiSourceSearcher",
        FakeSearcher,
    )
    monkeypatch.setattr(
        "src.knowledge.flash_sources.annotate_verified",
        fake_annotate,
    )
    papers, ctx, meta = await gather_flash_sources("q")
    assert meta["verified"] == 0
    assert all(not p.get("url") for p in papers)
    assert "not invent" in ctx.lower() or "unverified" in ctx.lower()


@pytest.mark.asyncio
async def test_gather_tavily_no_key_when_in_allowlist_but_inactive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSearcher:
        def __init__(self, *a, **k) -> None:
            self._active_sources = {"openalex": object()}  # no tavily

        async def search_all(
            self, query: str, domain: str = "general", include_web: bool = False
        ) -> dict:
            return {
                "papers": [],
                "sources_used": 0,
                "source_names": [],
                "source_stats": {},
            }

    monkeypatch.setattr(
        "src.knowledge.orchestrator.MultiSourceSearcher",
        FakeSearcher,
    )
    _papers, _ctx, meta = await gather_flash_sources(
        "cryogenic treatment of AISI 440C steel",
        include_web=True,
        verify=False,
    )
    assert meta["tavily"] == "no_key"


@pytest.mark.asyncio
async def test_run_flash_cli_mcp_parity_on_int_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI and MCP share run_flash — int sources_used must not become gather error."""

    async def fake_gather(question: str, **kwargs: Any):
        return (
            [
                {
                    "title": "Paper",
                    "verified": True,
                    "verify_verdict": "VERIFIED",
                    "doi": "10.1/x",
                    "url": "https://doi.org/10.1/x",
                    "_source": "openalex",
                    "checkable": True,
                }
            ],
            "[1] Paper",
            {
                "domain": "materials_science",
                "sources_used": ["openalex"],
                "errors": {},
                "tavily": "no_key",
                "dedup": "lexical_fallback",
                "found": 1,
                "verified": 1,
                "warnings": ["dedup=lexical_fallback (sentence_transformers_unavailable)"],
            },
        )

    class FakeLLM:
        async def chat(self, *a, **k):
            return "Cryogenic treatment of AISI 440C is documented in [1]."

        async def generate(self, *a, **k):
            return type("R", (), {"content": "fallback"})()

    monkeypatch.setattr(
        "src.knowledge.flash_sources.gather_flash_sources",
        fake_gather,
    )
    monkeypatch.setattr("src.llm.gateway.get_gateway", lambda: FakeLLM())
    result = await run_flash(
        "cryogenic AISI 440C",
        with_sources=True,
        deep=False,
    )
    assert "gather" not in (result.get("search_meta") or {}).get("errors", {})
    assert result["verified_count"] == 1
    assert isinstance(result["search_meta"]["sources_used"], list)
    assert result["status"] in {"success", "partial"}
    assert any("lexical_fallback" in w for w in result.get("warnings") or [])


def test_infer_materials_domain_excludes_aflow() -> None:
    d = infer_query_domain(
        "find peer reviewed publication about cryogenic treatment of AISI 440C steel"
    )
    assert d == "materials_science"
    allow = flash_source_allowlist(d, include_web=True)
    assert "pubchem" not in allow
    assert "clinicaltrials" not in allow
    assert "uci_ml" not in allow
    assert "aflow" not in allow
    assert "materials_project" not in allow
    assert "openalex" in allow
    assert "tavily" in allow


def test_url_and_checkable_helpers() -> None:
    assert is_checkable_url("https://doi.org/10.1/x")
    assert not is_checkable_url("http://example.com/1")
    assert not is_checkable_url("https://scholar.google.com/scholar?q=foo")
    assert is_checkable_paper({"doi": "10.1234/abc"})
    assert not is_checkable_paper({"doi": "not-a-doi"})
    assert not is_checkable_paper({"title": "x", "url": ""})
    cleaned = sanitize_paper({"title": "t", "url": "http://example.com/2", "doi": "10.1234/x"})
    assert cleaned["url"] == ""
    assert cleaned["verified"] is False  # pending verifier
    assert cleaned["checkable"] is True


def test_grounding_prompt_forbids_not_found_when_verified() -> None:
    prompt = build_flash_prompt(
        "q",
        context="[1] Paper",
        usp_section="",
        format_instructions="Be brief.",
        verified_count=1,
    )
    assert "MUST use them" in prompt


def test_flash_honesty_partial_when_unverified_only() -> None:
    status, warnings = flash_honesty_status(
        answer="Here is an answer.",
        with_sources=True,
        verified_count=0,
        found_count=3,
        deep=False,
        usp_context={},
    )
    assert status == "partial"
    assert any("CitationVerifier" in w or "verified" in w for w in warnings)


def test_flash_honesty_flags_not_found_contradiction() -> None:
    status, warnings = flash_honesty_status(
        answer="As of October 2023, I am unable to identify a specific peer-reviewed publication.",
        with_sources=True,
        verified_count=2,
        found_count=2,
        deep=False,
        usp_context={},
    )
    assert status == "partial"
    assert any("grounding" in w for w in warnings)
