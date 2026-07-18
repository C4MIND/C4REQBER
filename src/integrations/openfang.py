"""OpenFang Agent OS integration.

OpenFang (github.com/RightNow-AI/openfang) is a Rust-based Agent OS with:
- 140+ REST/WS/SSE endpoints on localhost:4200
- OpenAI-compatible API at /v1/chat/completions
- 53 built-in tools, 60 bundled skills
- FangHub marketplace for skills
- 27 LLM providers, 123+ models
- 16 security layers, WASM sandbox

Default API: http://localhost:4200
Config: ~/.openfang/config.toml
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class OpenFangClient:
    """Client for a locally running OpenFang Agent OS daemon.

    Connects to the OpenFang API at localhost:4200 (configurable via
    OPENFANG_API_URL env var). Provides access to agents, skills,
    search, memory, and the FangHub marketplace.
    """

    def __init__(self, api_url: str | None = None, timeout: float = 30.0) -> None:
        self.api_url = api_url or os.getenv("OPENFANG_API_URL", "http://localhost:4200")
        self.timeout = timeout
        self.api_key = os.getenv("OPENFANG_API_KEY", "")
        self.config_path = Path.home() / ".openfang" / "config.toml"

    @property
    def available(self) -> bool:
        """True only if the OpenFang daemon answers /health quickly."""
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(f"{self.api_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout)

    async def health(self) -> dict[str, Any]:
        """Check OpenFang daemon health."""
        try:
            async with self._client() as client:
                resp = await client.get(f"{self.api_url}/health")
                return resp.json() if resp.status_code == 200 else {"healthy": False}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def list_agents(self) -> list[dict[str, Any]]:
        """List active agents."""
        try:
            async with self._client() as client:
                resp = await client.get(
                    f"{self.api_url}/v1/agents",
                    headers=self._headers(),
                )
                return resp.json().get("agents", []) if resp.status_code == 200 else []
        except Exception as e:
            logger.debug("OpenFang list_agents failed: %s", e)
            return []

    async def chat(
        self,
        messages: list[dict],
        agent: str = "assistant",
        stream: bool = False,
    ) -> dict[str, Any]:
        """Send chat completion via OpenFang's OpenAI-compatible API."""
        try:
            async with self._client() as client:
                resp = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": agent,
                        "messages": messages,
                        "stream": stream,
                    },
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def search_skills(self, query: str) -> list[dict[str, Any]]:
        """Search FangHub marketplace for skills."""
        try:
            async with self._client() as client:
                resp = await client.get(
                    f"{self.api_url}/v1/skills/search",
                    headers=self._headers(),
                    params={"q": query},
                )
                return resp.json().get("skills", []) if resp.status_code == 200 else []
        except Exception as e:
            logger.debug("OpenFang skill search failed: %s", e)
            return []

    async def list_skills(self) -> list[dict[str, Any]]:
        """List all bundled skills."""
        try:
            async with self._client() as client:
                resp = await client.get(
                    f"{self.api_url}/v1/skills",
                    headers=self._headers(),
                )
                return resp.json().get("skills", []) if resp.status_code == 200 else []
        except Exception as e:
            logger.debug("OpenFang list_skills failed: %s", e)
            return []

    async def search_knowledge(self, query: str) -> dict[str, Any]:
        """Search OpenFang's memory and knowledge graph."""
        try:
            async with self._client() as client:
                resp = await client.get(
                    f"{self.api_url}/v1/search",
                    headers=self._headers(),
                    params={"q": query},
                )
                return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.debug("OpenFang search failed: %s", e)
            return {}

    async def test_connection(self) -> dict[str, Any]:
        """Test daemon connectivity."""
        health = await self.health()
        if health.get("healthy"):
            agents = await self.list_agents()
            return {"healthy": True, "agents_found": len(agents)}
        return health
