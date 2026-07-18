"""Tests for shared flash sources helper."""

from __future__ import annotations

import pytest

from src.knowledge.flash_sources import gather_flash_sources


@pytest.mark.asyncio
async def test_gather_flash_sources_never_example_com(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSearcher:
        async def search_all(self, query: str, include_web: bool = False) -> dict:
            return {
                "papers": [
                    {
                        "title": "Real Paper",
                        "_source": "openalex",
                        "abstract": "About science",
                    }
                ],
                "sources_used": 1,
            }

    monkeypatch.setattr(
        "src.knowledge.orchestrator.MultiSourceSearcher",
        lambda *a, **k: FakeSearcher(),
    )
    papers, ctx = await gather_flash_sources("q", deep=False)
    assert len(papers) == 1
    assert "example.com" not in ctx
    assert "Real Paper" in ctx
