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
)
from src.knowledge.flash_sources import (
    gather_flash_sources,
    is_checkable_paper,
    is_checkable_url,
    sanitize_paper,
)


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
                "sources_used": ["openalex"],
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
                "sources_used": ["web"],
                "source_stats": {},
            }

    async def fake_annotate(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Fail-closed: nothing becomes verified without API proof
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
