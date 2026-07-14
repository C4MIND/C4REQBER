"""c4reqber: ai-archive.io MCP Bridge — submit AI-friendly preprints."""
from __future__ import annotations

import os
from typing import Any

import httpx


class AIArchiveClient:
    """ai-archive.io client for submitting AI-generated research papers.

    ai-archive.io is specifically designed for AI-agent-generated papers
    with AI-generated reviews. MCP-native via AI-Archive-io/MCP-server.

    Auth: AI_ARCHIVE_API_KEY from https://ai-archive.io account.
    """

    API = "https://ai-archive.io/api"

    def __init__(self, dry_run: bool = False) -> None:
        self.api_key = os.getenv("AI_ARCHIVE_API_KEY", "")
        self.dry_run = dry_run

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def submit_paper(self, title: str, abstract: str, content: str, authors: list[dict[str, str]] | None = None) -> dict[str, Any]:
        """Submit a paper to ai-archive.io."""
        if self.dry_run:
            return {"id": "ai-arxiv-dry-run", "status": "submitted", "_dry_run": True}
        if not self.api_key:
            return {"error": "AI_ARCHIVE_API_KEY not configured. Get key: https://ai-archive.io"}

        payload = {
            "title": title[:500],
            "abstract": abstract[:2000],
            "content": content[:50000],
            "authors": authors or [{"name": "c4reqber Researcher"}],
            "category": "cs.AI",
        }
        async with httpx.AsyncClient() as c:
            resp = await c.post(
                f"{self.API}/papers",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload, timeout=30,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            return {"error": f"ai-archive HTTP {resp.status_code}: {resp.text[:200]}"}

    async def list_papers(self, query: str = "", limit: int = 10) -> list[dict[str, Any]]:
        """Search papers on ai-archive.io."""
        if self.dry_run:
            return []
        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"{self.API}/papers",
                params={"q": query, "limit": limit},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15,
            )
            return resp.json() if resp.status_code == 200 else []
