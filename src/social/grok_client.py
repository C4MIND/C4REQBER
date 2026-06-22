"""
Grok (X.ai) Client — PAID API
License: ⚠️ Proprietary (paid tokens)
Note: X.ai API requires paid subscription
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from src.config import get_key


class GrokClient:
    """X.ai Grok API client (paid, token-based)."""

    BASE_URL = "https://api.x.ai/v1"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_key("xai") or os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def chat(self, message: str, model: str = "grok-beta") -> str:
        """Chat with Grok."""
        if not self.api_key:
            return "Error: XAI_API_KEY required (paid tier)"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": message}],
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def get_trending(self) -> list[dict[str, Any]]:
        """Get trending topics (via Grok analysis)."""
        if not self.api_key:
            return []

        prompt = (
            "List the top 10 current trending topics in science and technology. "
            "Return as JSON array with 'topic' and 'category' fields."
        )
        result = await self.chat(prompt)
        return [{"topic": result, "category": "ai_generated"}]

    async def analyze_paper(self, abstract: str) -> dict[str, Any]:
        """Analyze research paper with Grok."""
        if not self.api_key:
            return {"error": "XAI_API_KEY required (paid tier)"}

        prompt = f"""Analyze this research paper abstract and provide:
1. Key findings (list)
2. Methodology assessment
3. Novelty score (0-10)
4. Related fields
5. Potential applications

Abstract: {abstract}

Return as JSON."""

        result = await self.chat(prompt)
        return {"analysis": result, "provider": "grok", "model": "grok-beta"}

    async def summarize_discussion(self, posts: list[str]) -> str:
        """Summarize a discussion from multiple posts."""
        if not self.api_key:
            return "Error: XAI_API_KEY required"

        combined = "\n---\n".join(posts[:20])
        prompt = f"Summarize the key points from this discussion:\n\n{combined}"
        return await self.chat(prompt)
