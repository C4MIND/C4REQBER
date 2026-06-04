"""Local LLM Client — Client implementation.

Unified interface for Ollama and LM Studio local inference.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from src.llm.local.core import HAS_HTTPX, LocalLLMResponse, LocalProvider


class LocalLLMClient:
    """
    Unified local LLM client supporting Ollama and LM Studio.

    Auto-detects available providers and falls back gracefully.
    """

    DEFAULT_MODELS = {
        LocalProvider.OLLAMA: "qwen2.5:14b",
        LocalProvider.LM_STUDIO: "local-model",
    }

    def __init__(
        self,
        ollama_url: str | None = None,
        lm_studio_url: str | None = None,
        timeout: float = 120.0,
        preferred_provider: LocalProvider | None = None,
    ) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required. Install: pip install httpx")

        ollama_raw = (  # type: ignore[union-attr]
            ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        ).rstrip("/")
        lm_raw = (  # type: ignore[union-attr]
            lm_studio_url or os.getenv("LM_STUDIO_URL", "http://localhost:1234")
        ).rstrip("/")
        # Basic SSRF protection: reject non-HTTP(S) schemes
        for url, name in [(ollama_raw, "OLLAMA_URL"), (lm_raw, "LM_STUDIO_URL")]:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"{name} must be an HTTP(S) URL, got: {url}")
        self.ollama_url = ollama_raw
        self.lm_studio_url = lm_raw
        self.timeout = timeout
        self.preferred_provider = preferred_provider
        self._client = None
        self._available_providers: list[LocalProvider] | None = None
        self._logger = logging.getLogger("c4_cdi_turbo.local_llm")

    async def _init_client(self) -> None:
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(  # type: ignore[assignment]
                timeout=httpx.Timeout(self.timeout),
                headers={"Content-Type": "application/json"},
            )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()  # type: ignore[unreachable]
            self._client = None

    async def _detect_providers(self) -> list[LocalProvider]:
        """Detect which local providers are available."""
        if self._available_providers is not None:
            return self._available_providers

        providers = []

        # Check Ollama
        try:
            resp = await self._client.get(f"{self.ollama_url}/api/tags", timeout=5.0)  # type: ignore[attr-defined]
            if resp.status_code == 200:
                providers.append(LocalProvider.OLLAMA)
        except Exception as e:
            self._logger.debug("Ollama detection failed: %s", e)

        # Check LM Studio
        try:
            resp = await self._client.get(  # type: ignore[attr-defined]
                f"{self.lm_studio_url}/v1/models", timeout=5.0
            )
            if resp.status_code == 200:
                providers.append(LocalProvider.LM_STUDIO)
        except Exception as e:
            self._logger.debug("LM Studio detection failed: %s", e)

        self._available_providers = providers
        return providers

    async def list_models(
        self, provider: LocalProvider | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        """List available models from local providers using discovery."""
        from src.llm.local_discovery import LocalModelDiscovery

        discovery = LocalModelDiscovery(
            ollama_url=self.ollama_url,
            lm_studio_url=self.lm_studio_url,
            timeout=10.0,
        )
        result: dict[str, Any] = {}

        try:
            if provider is None:
                all_models = await discovery.discover_all()
                result["ollama"] = [m.to_dict() for m in all_models if m.provider == "ollama"]
                result["lm_studio"] = [m.to_dict() for m in all_models if m.provider == "lm_studio"]
            elif provider == LocalProvider.OLLAMA:
                models = await discovery.discover_ollama()
                result["ollama"] = [m.to_dict() for m in models]
            elif provider == LocalProvider.LM_STUDIO:
                models = await discovery.discover_lm_studio()
                result["lm_studio"] = [m.to_dict() for m in models]
        except Exception as e:
            result["error"] = str(e)
        finally:
            await discovery.close()

        return result

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
        provider: LocalProvider | None = None,
    ) -> LocalLLMResponse:
        """Generate text using local LLM."""
        await self._init_client()

        # Auto-detect if no provider specified
        if provider is None:
            available = await self._detect_providers()
            if not available:
                raise RuntimeError(
                    "No local LLM providers available. Start Ollama or LM Studio."
                )
            # Respect preferred provider, otherwise use first available
            if self.preferred_provider and self.preferred_provider in available:
                provider = self.preferred_provider
            else:
                provider = available[0]

        if provider == LocalProvider.OLLAMA:
            return await self._generate_ollama(
                prompt, model, temperature, max_tokens, system_prompt
            )
        elif provider == LocalProvider.LM_STUDIO:
            return await self._generate_lm_studio(
                prompt, model, temperature, max_tokens, system_prompt
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _generate_ollama(
        self,
        prompt: str,
        model: str | None,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
    ) -> LocalLLMResponse:
        """Generate via Ollama native API."""
        model = model or self.DEFAULT_MODELS[LocalProvider.OLLAMA]

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        start = time.time()
        resp = await self._client.post(  # type: ignore[attr-defined]
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.time() - start) * 1000

        return LocalLLMResponse(
            content=data.get("response", ""),
            model=model,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            latency_ms=latency,
            provider="ollama",
        )

    async def _generate_lm_studio(
        self,
        prompt: str,
        model: str | None,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
    ) -> LocalLLMResponse:
        """Generate via LM Studio OpenAI-compatible API."""
        model = model or self.DEFAULT_MODELS[LocalProvider.LM_STUDIO]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        start = time.time()
        resp = await self._client.post(  # type: ignore[attr-defined]
            f"{self.lm_studio_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.time() - start) * 1000

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        return LocalLLMResponse(
            content=message.get("content", ""),
            model=data.get("model", model),
            usage=data.get("usage", {}),
            latency_ms=latency,
            provider="lm_studio",
        )

    async def generate_batch(
        self,
        prompts: list[str],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_concurrent: int = 3,
        provider: LocalProvider | None = None,
    ) -> list[LocalLLMResponse]:
        """Generate multiple responses concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def gen(prompt: str) -> LocalLLMResponse:
            async with semaphore:
                return await self.generate(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    provider=provider,
                )

        tasks = [gen(p) for p in prompts]
        return await asyncio.gather(*tasks)

    async def health_check(self) -> dict[str, Any]:
        """Check health of all local providers."""
        await self._init_client()
        result = {}

        # Ollama
        try:
            resp = await self._client.get(f"{self.ollama_url}/api/tags", timeout=5.0)  # type: ignore[attr-defined]
            result["ollama"] = {
                "available": resp.status_code == 200,
                "status_code": resp.status_code,
                "url": self.ollama_url,
            }
            if resp.status_code == 200:
                data = resp.json()
                result["ollama"]["models_count"] = len(data.get("models", []))
        except Exception as e:
            result["ollama"] = {
                "available": False,
                "error": str(e),
                "url": self.ollama_url,
            }

        # LM Studio
        try:
            resp = await self._client.get(  # type: ignore[attr-defined]
                f"{self.lm_studio_url}/v1/models", timeout=5.0
            )
            result["lm_studio"] = {
                "available": resp.status_code == 200,
                "status_code": resp.status_code,
                "url": self.lm_studio_url,
            }
            if resp.status_code == 200:
                data = resp.json()
                result["lm_studio"]["models_count"] = len(data.get("data", []))
        except Exception as e:
            result["lm_studio"] = {
                "available": False,
                "error": str(e),
                "url": self.lm_studio_url,
            }

        return result
