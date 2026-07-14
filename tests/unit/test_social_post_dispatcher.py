"""Tests for social post dispatcher."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.social.post_dispatcher import (
    ALL_SOCIAL_PLATFORMS,
    build_post_content,
    dispatch_social_posts,
    normalize_platform,
    post_draft,
    post_to_platform,
)


def test_normalize_platform_aliases() -> None:
    assert normalize_platform("twitter") == "x_twitter"
    assert normalize_platform("X") == "x_twitter"
    assert normalize_platform("mastodon") == "mastodon"


def test_normalize_platform_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown platform"):
        normalize_platform("myspace")


def test_build_post_content_with_url() -> None:
    text = build_post_content("Sleep Study", "https://doi.org/10.1234/zenodo.1", lang="en")
    assert "Sleep Study" in text
    assert "https://doi.org/10.1234/zenodo.1" in text


@pytest.mark.asyncio
async def test_post_to_platform_dry_run() -> None:
    result = await post_to_platform(
        "mastodon",
        "Hello world",
        dry_run=True,
        draft_id="test_draft",
    )
    assert result["status"] == "dry_run"
    assert result["platform"] == "mastodon"


@pytest.mark.asyncio
async def test_dispatch_social_posts_dry_run() -> None:
    result = await dispatch_social_posts(
        draft_id="2026_test",
        zenodo_result={"doi": "10.1234/zenodo.1", "title": "Test Paper"},
        dry_run=True,
    )
    assert result["language"]
    assert len(result["posts"]) == len(ALL_SOCIAL_PLATFORMS)
    for _plat, res in result["posts"].items():
        assert res["status"] == "dry_run"


@pytest.mark.asyncio
async def test_post_draft_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.social.post_dispatcher.DRAFTS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        await post_draft("missing_id", platform="mastodon", dry_run=True)


@pytest.mark.asyncio
async def test_post_draft_single_platform(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.social.post_dispatcher.DRAFTS_DIR", tmp_path)
    draft_dir = tmp_path / "2026_test_topic"
    draft_dir.mkdir()
    (draft_dir / "metadata.json").write_text(
        json.dumps({"title": "Topic Title", "doi": "10.1234/zenodo.99"}),
        encoding="utf-8",
    )
    result = await post_draft("2026_test_topic", platform="discord", dry_run=True)
    assert result["draft_id"] == "2026_test_topic"
    assert "discord" in result["results"]
    assert result["results"]["discord"]["status"] == "dry_run"
