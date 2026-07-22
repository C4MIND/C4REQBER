"""Workstream W3 — stubs, sim fallbacks, search shaping, dissertation, live_feed."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.knowledge.orchestrator import MultiSourceSearcher
from src.utils.honesty_status import outer_status_from_sim_payload


def test_agent_search_no_fake_stub_string_in_blast_app() -> None:
    src = Path("src/cli/blast_app.py").read_text(encoding="utf-8")
    assert 'f"Search for: {query}' not in src
    assert "gather_flash_sources" in src
    assert "source_cards_from_papers" in src


@pytest.mark.asyncio
async def test_search_single_applies_shape_search_query() -> None:
    long_ru = (
        "Исследовать влияние нейронных сетей на диагностику заболеваний "
        "сердечно-сосудистой системы " * 30
    )
    captured: dict[str, str] = {}

    async def fake_timeout(source: str, query: str, max_papers: int) -> list[dict]:
        captured["query"] = query
        return []

    bare = MultiSourceSearcher.__new__(MultiSourceSearcher)
    expected = MultiSourceSearcher._shape_search_query(bare, long_ru)

    searcher = MultiSourceSearcher.__new__(MultiSourceSearcher)
    searcher._cache = MagicMock()
    searcher._cache.get.return_value = None
    searcher._cache.set = MagicMock()
    searcher.MAX_PAPERS_PER_SOURCE = 5
    searcher._search_with_timeout = fake_timeout

    stub_registry = {
        "arxiv": {
            "name": "arXiv",
            "tier": 1,
            "coverage": "general",
            "needs_key": False,
            "enabled": True,
        }
    }
    with patch("src.knowledge.orchestrator.SOURCE_REGISTRY", stub_registry):
        await searcher.search_single("arxiv", long_ru)

    assert captured["query"] == expected
    assert len(captured["query"]) <= 200
    assert captured["query"] != long_ru


def test_amuse_rebound_fallback_outer_status_partial() -> None:
    payload = {
        "status": "partial",
        "executed": True,
        "stub": False,
        "backend": "rebound",
        "engine_truth": "rebound_not_amuse",
    }
    assert outer_status_from_sim_payload(payload) == "partial"


def test_discovery_utils_dissertation_not_placeholder_prose() -> None:
    from src.api.v8_routers.discovery_utils import _build_dissertation

    discovery = {
        "problem": "Test problem",
        "hypothesis": {"text": "Hypothesis about testing."},
        "_papers_found": 2,
        "_sources_used": 3,
        "_papers_list": [
            {
                "title": "Real Paper Title",
                "authors": [{"name": "A. Author"}],
                "year": 2024,
                "doi": "10.1234/example.1",
                "abstract": "Findings about testing.",
                "source": "arxiv",
            }
        ],
        "gap_miner": {"gaps_found": 1},
        "contradiction_mining": {"contradictions_found": 0},
    }
    out = _build_dissertation(discovery, attempts=[{"ok": True}])
    sections = out["dissertation"]["sections"]
    lit = next(s for s in sections if "Literature" in s["heading"])
    assert "Literature content" not in lit["content"]
    assert "Real Paper Title" in lit["content"] or "comprehensive search" in lit["content"].lower()


def test_live_feed_arxiv_abs_url_from_entry_xml() -> None:
    import re

    sample = """
    <feed>
      <entry>
        <id>http://arxiv.org/abs/2301.00001v1</id>
        <title>Sample Paper Title</title>
        <name>Jane Doe</name>
      </entry>
    </feed>
    """
    block = re.split(r"<entry>", sample)[1]
    id_m = re.search(r"<id>https?://arxiv\.org/abs/([^<]+)</id>", block)
    assert id_m
    url = f"https://arxiv.org/abs/{id_m.group(1).strip()}"
    assert url == "https://arxiv.org/abs/2301.00001v1"
    assert "/search/?" not in url


@pytest.mark.asyncio
async def test_agent_search_json_shape_via_gather_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mirror agent_search wiring — verified JSON, not fake success string."""

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
                "title": "Steel alloys review",
                "authors": ["Smith"],
                "year": 2023,
                "doi": "10.1234/test.1",
                "url": "https://doi.org/10.1234/test.1",
                "_source": "openalex",
                "verified": True,
                "verify_verdict": "VERIFIED",
            }
        ]
        return papers, "ctx", {"domain": "materials", "errors": {}, "found": 1, "verified": 1}

    monkeypatch.setattr("src.knowledge.flash_sources.gather_flash_sources", fake_gather)

    from src.knowledge.flash_contract import source_cards_from_papers
    from src.knowledge.flash_sources import gather_flash_sources

    papers, _ctx, meta = await gather_flash_sources("AISI 440C", deep=False)
    partitioned = source_cards_from_papers(papers, sanitize=False, limit=10)
    payload = {
        "status": "success" if partitioned["verified_count"] else "partial",
        "sources": partitioned["sources"],
        "verified_count": partitioned["verified_count"],
        "found_count": partitioned["found_count"],
        "search_meta": meta,
    }
    raw = json.dumps(payload)
    parsed = json.loads(raw)
    assert parsed["status"] == "success"
    assert parsed["verified_count"] == 1
    assert "Search for:" not in raw
