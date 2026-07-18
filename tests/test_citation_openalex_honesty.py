"""Anti-fraud tests for CitationVerifier OpenAlex title matching."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.knowledge.citation_verifier import (
    CitationVerifier,
    normalize_title,
    title_similarity,
)


def test_title_similarity_exact():
    assert title_similarity("Attention Is All You Need", "Attention Is All You Need") == 1.0


def test_title_similarity_rejects_unrelated():
    score = title_similarity(
        "Attention Is All You Need",
        "A Survey of Deep Learning for Cat Detection",
    )
    assert score < 0.5


def test_normalize_strips_punctuation():
    assert normalize_title("Hello, World!") == "hello world"


@pytest.mark.asyncio
async def test_openalex_first_hit_alone_is_not_match():
    """Green-fake: any search hit with a title must NOT count as match."""
    v = CitationVerifier()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"title": "Completely Unrelated Paper About Potatoes"},
        ]
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.aclose = AsyncMock()
    v._client = mock_client

    out = await v._check_openalex("Attention Is All You Need")
    assert out["ok"] is False
    assert out["score"] < 0.82
    await v.close()


@pytest.mark.asyncio
async def test_openalex_close_title_is_match():
    v = CitationVerifier()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"display_name": "Attention Is All You Need"},
        ]
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.aclose = AsyncMock()
    v._client = mock_client

    out = await v._check_openalex("Attention Is All You Need")
    assert out["ok"] is True
    assert out["score"] >= 0.82
    await v.close()


@pytest.mark.asyncio
async def test_verified_requires_title_matched_openalex():
    """CrossRef DOI + unrelated OpenAlex hit → PARTIAL, not VERIFIED."""
    v = CitationVerifier()
    v._client.aclose = AsyncMock()  # type: ignore[method-assign]

    async def fake_crossref(_doi: str) -> dict:
        return {"ok": True}

    async def fake_openalex(_title: str) -> dict:
        return {"ok": False, "score": 0.12}

    v._check_crossref = fake_crossref  # type: ignore[method-assign]
    v._check_openalex = fake_openalex  # type: ignore[method-assign]

    check = await v._verify_single(
        {"id": "[1]", "context": "See Attention Is All You Need [1]"},
        [{"title": "Attention Is All You Need", "doi": "10.5555/fake"}],
    )
    assert check.crossref_match is True
    assert check.openalex_match is False
    assert check.verdict == "PARTIAL"
    await v.close()
