"""Workstream W3 — stubs, sim fallbacks, search shaping, dissertation, live_feed."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.knowledge.orchestrator import MultiSourceSearcher
from src.utils.honesty_status import outer_status_from_sim_payload


@pytest.mark.asyncio
async def test_agent_search_empty_query_is_error() -> None:
    from src.knowledge.agent_search import run_agent_search

    out = await run_agent_search("  ", max_results=5)
    assert out["status"] == "error"
    assert out["verified_count"] == 0
    assert "Search for:" not in json.dumps(out)


@pytest.mark.asyncio
async def test_agent_search_uses_gather_and_partition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real agent_search path — verified JSON, not fake success string."""

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

    from src.knowledge.agent_search import run_agent_search

    out = await run_agent_search("AISI 440C", max_results=10)
    assert out["status"] == "success"
    assert out["verified_count"] == 1
    assert "Search for:" not in json.dumps(out)


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
    from src.intel.live_feed import LiveFeed

    sample = """
    <feed>
      <entry>
        <id>http://arxiv.org/abs/2301.00001v1</id>
        <title>Sample Paper Title</title>
        <name>Jane Doe</name>
      </entry>
    </feed>
    """
    items = LiveFeed.parse_arxiv_atom_entries(sample, "cs.AI")
    assert len(items) == 1
    assert items[0]["url"] == "https://arxiv.org/abs/2301.00001v1"
    assert "/search/?" not in items[0]["url"]
    assert "Sample Paper Title" in items[0]["title"]
