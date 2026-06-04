"""Local Model Discovery.

Auto-discovers models from Ollama and LM Studio local endpoints.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore


@dataclass
class ModelInfo:
    """Unified model info from any local provider."""

    id: str
    name: str
    provider: str  # "ollama" or "lm_studio"
    size: int = 0
    parameter_size: str = "?"
    quantization: str = "?"
    family: str = "?"
    owned_by: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "size": self.size,
            "parameter_size": self.parameter_size,
            "quantization": self.quantization,
            "family": self.family,
            "owned_by": self.owned_by,
        }


class LocalModelDiscovery:
    """
    Discovers available models from local LLM providers.

    - Ollama: http://localhost:11434/api/tags
    - LM Studio: http://localhost:1234/v1/models
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        lm_studio_url: str = "http://localhost:1234",
        timeout: float = 5.0,
    ) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required. Install: pip install httpx")

        self.ollama_url = ollama_url.rstrip("/")
        self.lm_studio_url = lm_studio_url.rstrip("/")
        self.timeout = timeout
        self._logger = logging.getLogger("c4_cdi_turbo.local_discovery")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """Check if at least one local provider is available."""
        ollama_ok = await self._check_ollama()
        lm_ok = await self._check_lm_studio()
        return ollama_ok or lm_ok

    async def _check_ollama(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.ollama_url}/api/tags", timeout=self.timeout)
            return resp.status_code == 200
        except (ConnectionError, TimeoutError, OSError):
            return False

    async def _check_lm_studio(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.lm_studio_url}/v1/models", timeout=self.timeout)
            return resp.status_code == 200
        except (ConnectionError, TimeoutError, OSError):
            return False

    async def discover_ollama(self) -> list[ModelInfo]:
        """Discover models from Ollama."""
        models: list[ModelInfo] = []
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.ollama_url}/api/tags", timeout=self.timeout)
            if resp.status_code != 200:
                self._logger.debug("Ollama returned status %s", resp.status_code)
                return models

            data = resp.json()
            for m in data.get("models", []):
                details = m.get("details", {})
                models.append(
                    ModelInfo(
                        id=m.get("name", m.get("model", "unknown")),
                        name=m.get("name", m.get("model", "unknown")),
                        provider="ollama",
                        size=m.get("size", 0),
                        parameter_size=details.get("parameter_size", "?"),
                        quantization=details.get("quantization_level", "?"),
                        family=details.get("family", "?"),
                        owned_by="local",
                    )
                )
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            self._logger.debug("Ollama discovery failed: %s", e)
        return models

    async def discover_lm_studio(self) -> list[ModelInfo]:
        """Discover models from LM Studio."""
        models: list[ModelInfo] = []
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.lm_studio_url}/v1/models", timeout=self.timeout)
            if resp.status_code != 200:
                self._logger.debug("LM Studio returned status %s", resp.status_code)
                return models

            data = resp.json()
            for m in data.get("data", []):
                model_id = m.get("id", "unknown")
                models.append(
                    ModelInfo(
                        id=model_id,
                        name=model_id.split("/")[-1],
                        provider="lm_studio",
                        size=0,
                        parameter_size="?",
                        quantization="?",
                        family="?",
                        owned_by=m.get("owned_by", "local"),
                    )
                )
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            self._logger.debug("LM Studio discovery failed: %s", e)
        return models

    async def discover_all(self) -> list[ModelInfo]:
        """
        Discover models from all local providers and deduplicate.
        Deduplication is by model id (case-insensitive).
        """
        ollama_models = await self.discover_ollama()
        lm_models = await self.discover_lm_studio()

        all_models = ollama_models + lm_models
        seen: set[str] = set()
        unique: list[ModelInfo] = []
        for m in all_models:
            key = m.id.lower()
            if key not in seen:
                seen.add(key)
                unique.append(m)
        return unique
