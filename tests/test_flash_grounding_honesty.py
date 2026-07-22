"""Flash grounding / CLI-MCP parity honesty tests."""

from __future__ import annotations

from typing import Any

import pytest

from src.knowledge.flash_runner import run_flash


@pytest.mark.asyncio
async def test_run_flash_cli_mcp_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_gather(
        question: str,
        *,
        deep: bool = False,
        include_web: bool = True,
        domain: str | None = None,
        verify: bool = True,
    ):
        papers = [
            {
                "title": "Deep Cryogenic Treatment: Effects on Mechanical Properties of AISI 440C",
                "authors": ["A Author"],
                "year": 2019,
                "doi": "10.1000/test.440c",
                "url": "https://doi.org/10.1000/test.440c",
                "_source": "openalex",
                "abstract": "Cryogenic treatment of AISI 440C steel.",
                "verified": True,
                "verify_verdict": "VERIFIED",
                "checkable": True,
            }
        ]
        from src.knowledge.flash_sources import build_flash_context

        meta = {
            "domain": "materials_science",
            "sources_used": ["openalex"],
            "errors": {},
            "tavily": "no_key",
            "found": 1,
            "verified": 1,
        }
        return papers, build_flash_context(papers, verified_only=True), meta

    class FakeGW:
        async def chat(self, messages: list, **kwargs: Any) -> str:
            return "The paper [1] Deep Cryogenic Treatment covers cryogenic treatment of AISI 440C."

    monkeypatch.setattr("src.knowledge.flash_sources.gather_flash_sources", fake_gather)
    monkeypatch.setattr("src.llm.gateway.get_gateway", lambda: FakeGW())

    result = await run_flash("cryogenic AISI 440C", with_sources=True, deep=False)
    assert result["status"] == "success"
    assert result["verified_count"] == 1
    assert result["source_count"] == 1
    assert len(result["sources"]) == 1
    src = result["sources"][0]
    assert src["doi"]
    assert src["url"]
    assert src["verified"] is True
    assert "unable to" not in result["answer"].lower()


@pytest.mark.asyncio
async def test_run_flash_no_sources_when_unverified(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_gather(
        question: str,
        *,
        deep: bool = False,
        include_web: bool = True,
        domain: str | None = None,
        verify: bool = True,
    ):
        papers = [
            {
                "title": "Something without confirmation",
                "_source": "openalex",
                "abstract": "x",
                "verified": False,
                "verify_verdict": "UNVERIFIED",
                "checkable": True,
                "url": "https://example.org/paper",
                "doi": "10.9999/unconfirmed",
            }
        ]
        meta = {
            "domain": "general",
            "sources_used": ["openalex"],
            "errors": {},
            "tavily": "off",
            "found": 1,
            "verified": 0,
        }
        ctx = (
            "(No CitationVerifier-confirmed sources. 1 raw hits were found but remain "
            "unverified — do not invent DOI/URL or claim a specific paper was confirmed.)"
        )
        return papers, ctx, meta

    class FakeGW:
        async def chat(self, messages: list, **kwargs: Any) -> str:
            return "No verified publication was confirmed for this query."

    monkeypatch.setattr("src.knowledge.flash_sources.gather_flash_sources", fake_gather)
    monkeypatch.setattr("src.llm.gateway.get_gateway", lambda: FakeGW())

    result = await run_flash("q", with_sources=True)
    assert result["status"] == "partial"
    assert result["verified_count"] == 0
    assert result["source_count"] == 0
    assert result["sources"] == []
    assert len(result.get("unverified_hits") or []) == 1


@pytest.mark.asyncio
async def test_annotate_verified_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.knowledge.citation_verifier import CitationCheck
    from src.knowledge.flash_sources import annotate_verified, sanitize_paper

    class FakeVerifier:
        async def verify_paper_dicts(self, papers):
            return [
                CitationCheck(
                    citation_id="[1]",
                    title=papers[0].get("title", ""),
                    doi=papers[0].get("doi"),
                    verdict="UNVERIFIED",
                )
            ]

        async def close(self) -> None:
            return None

    monkeypatch.setattr(
        "src.knowledge.citation_verifier.CitationVerifier",
        lambda: FakeVerifier(),
    )
    papers = [
        sanitize_paper(
            {
                "title": "Invented DOI Paper",
                "doi": "10.9999/fake.doi",
                "url": "https://doi.org/10.9999/fake.doi",
            }
        )
    ]
    assert papers[0]["checkable"] is True
    assert papers[0]["verified"] is False
    out = await annotate_verified(papers)
    assert out[0]["verified"] is False
    assert out[0]["verify_verdict"] == "UNVERIFIED"
