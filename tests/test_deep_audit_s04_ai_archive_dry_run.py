"""Suite 04 — AI-Archive dry_run must not look submitted."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_ai_archive_dry_run_status_not_submitted() -> None:
    from src.social.ai_archive_client import AIArchiveClient

    out = await AIArchiveClient(dry_run=True).submit_paper(title="t", abstract="a", content="c")
    assert out.get("_dry_run") is True
    assert out.get("status") == "dry_run"
    assert out.get("status") != "submitted"
