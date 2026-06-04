"""NVIDIA NIM integration — real async client for 200+ models."""

from __future__ import annotations

import os
from typing import Any

import httpx


class NvidiaNimClient:
    """Client for NVIDIA NIM inference endpoints (200+ models)."""

    def __init__(self, api_key: str | None = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.base_url = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[dict],
        model: str = "meta/llama-3.1-8b-instruct",
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> dict:
        """Send chat completion request to NVIDIA NIM."""
        if not self.available:
            return {"error": "NVIDIA_API_KEY not configured"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def list_models(self) -> list[dict[str, Any]]:
        """List available NVIDIA NIM models."""
        if not self.available:
            return []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/models",
                headers=self._headers(),
            )
            return resp.json().get("data", []) if resp.status_code == 200 else []

    async def embeddings(
        self, texts: list[str], model: str = "nvidia/nv-embedqa-e5-v5"
    ) -> dict[str, Any]:
        """Generate embeddings via NVIDIA NIM."""
        if not self.available:
            return {"error": "NVIDIA_API_KEY not configured"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json={"model": model, "input": texts, "encoding_format": "float"},
            )
            resp.raise_for_status()
            return resp.json()

    async def test_connection(self) -> dict[str, Any]:
        """Test API connectivity."""
        try:
            models = await self.list_models()
            return {"healthy": True, "models_found": len(models)}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
