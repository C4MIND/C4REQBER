"""Suite 09 — Novelty API must not default missing score to PASS@1.0."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.errors import register_error_handlers
from src.api.v8_routers.novelty_v8 import router as novelty_router


app = FastAPI()
app.include_router(novelty_router, prefix="/v8")
register_error_handlers(app)
client = TestClient(app, raise_server_exceptions=False)


def test_missing_score_is_unchecked_not_pass() -> None:
    with patch(
        "src.api.v8_routers.novelty_v8.ThreePassNoveltyValidator.validate",
        new=AsyncMock(
            return_value={
                "status": "UNCHECKED",
                "overall_novelty_score": None,
                "passes": [],
                "closest_papers": [],
                "recommendation": "unchecked",
                "errors": [],
            }
        ),
    ):
        resp = client.post(
            "/v8/novelty/check",
            json={"hypothesis": "Something novel maybe", "domain": "general"},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("status") == "UNCHECKED"
    assert body.get("overall_novelty_score") is None
    assert body.get("status") != "PASS"


def test_empty_corpus_validate_returns_unchecked() -> None:
    from src.api.v8_routers.novelty_v8 import ThreePassNoveltyValidator

    v = ThreePassNoveltyValidator()

    async def empty_pass1(*_a, **_k):
        return {
            "potential_overlaps": [],
            "papers_checked": 0,
            "overlap_detected": False,
            "max_similarity": 0.0,
            "time_seconds": 0,
            "closest_similarity": 0,
        }

    async def empty_pass2(*_a, **_k):
        return {
            "papers_analyzed": 0,
            "overlap_detected": False,
            "overall_overlap_score": 0.0,
            "overlapping_claims": [],
        }

    async def empty_pass3(*_a, **_k):
        return {"papers_analyzed": 0, "is_established_paradigm": False}

    v._pass1_broad_scan = empty_pass1  # type: ignore[method-assign]
    v._pass2_deep_dive = empty_pass2  # type: ignore[method-assign]
    v._pass3_citation_context = empty_pass3  # type: ignore[method-assign]

    import asyncio

    out = asyncio.run(v.validate("hypothesis with no hits", domain="general", keywords=[]))
    assert out["status"] == "UNCHECKED"
    assert out["overall_novelty_score"] is None
